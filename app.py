# -*- coding: utf-8 -*-
"""
人员在岗行为识别与实时告警系统 - Flask 主程序
作者：创新创业项目组
日期：2025年10月16日
"""

from flask import Flask, render_template, Response, request, jsonify
from datetime import datetime
import cv2
import threading
import time
import webbrowser
from detector import DutyDetector
from utils import draw_status_text
import config
import os
import signal
import requests
import sqlite3

app = Flask(__name__)


# 全局变量
detector = None
camera = None
latest_frame = None
latest_status = "系统初始化中..."
frame_lock = threading.Lock()
system_paused = False
pause_lock = threading.Lock()
stats_lock = threading.Lock()
stats_db_lock = threading.Lock()
stats_csv_lock = threading.Lock()
on_duty_seconds = 0.0
off_duty_seconds = 0.0
total_monitor_seconds = 0.0
last_status_eval_time = time.time()
last_frame_on_duty = False
continuous_on_duty_seconds = 0.0
last_time_sync = 0.0
time_offset_seconds = 0.0
time_sync_lock = threading.Lock()
time_sync_source = "local"
stats_db_conn = None
csv_header_checked = False
WORK_DAY_SET = set()
for _day in getattr(config, "WORK_DAYS", [0, 1, 2, 3, 4]):
    try:
        WORK_DAY_SET.add(int(_day))
    except (TypeError, ValueError):
        continue


def _update_time_metrics(frame_on_duty: bool) -> None:
    """根据当前帧状态累计在岗/离岗时长"""
    global on_duty_seconds, off_duty_seconds, total_monitor_seconds, last_status_eval_time, last_frame_on_duty, continuous_on_duty_seconds
    now = time.time()
    frame_on_duty = bool(frame_on_duty)
    with stats_lock:
        elapsed = max(0.0, now - last_status_eval_time)
        total_monitor_seconds += elapsed
        if _within_work_hours():
            if last_frame_on_duty:
                on_duty_seconds += elapsed
            else:
                off_duty_seconds += elapsed
        if frame_on_duty:
            continuous_on_duty_seconds += elapsed
        else:
            continuous_on_duty_seconds = 0.0
        last_status_eval_time = now
        last_frame_on_duty = frame_on_duty


def _current_durations() -> dict:
    """获取当前累计的在岗/离岗时长"""
    with stats_lock:
        now = time.time()
        elapsed = max(0.0, now - last_status_eval_time)
        on_duty = on_duty_seconds
        off_duty = off_duty_seconds
        total = total_monitor_seconds + elapsed
        if _within_work_hours():
            on_duty += elapsed if last_frame_on_duty else 0.0
            off_duty += elapsed if not last_frame_on_duty else 0.0
        return {
            "on": on_duty,
            "off": off_duty,
            "total": total,
            "continuous_on": continuous_on_duty_seconds
            + (elapsed if last_frame_on_duty else 0.0),
        }


def _within_work_hours() -> bool:
    """判断当前是否处于工作统计时段"""
    if not config.WORK_HOURS_ENABLED:
        return True
    now = datetime.now()
    if now.weekday() not in WORK_DAY_SET:
        return False
    try:
        start = datetime.strptime(config.WORK_HOURS_START, "%H:%M").time()
        end = datetime.strptime(config.WORK_HOURS_END, "%H:%M").time()
    except ValueError:
        return True
    current = now.time()
    if start <= end:
        return start <= current <= end
    return current >= start or current <= end


def _continuous_warning_state(continuous_seconds: float) -> dict:
    threshold = max(0.0, config.CONTINUOUS_WORK_THRESHOLD)
    if threshold <= 0:
        return {
            "active": False,
            "threshold": threshold,
            "continuous_seconds": continuous_seconds,
        }
    return {
        "active": continuous_seconds >= threshold,
        "threshold": threshold,
        "continuous_seconds": continuous_seconds,
    }


def _current_server_time() -> dict:
    with time_sync_lock:
        offset = time_offset_seconds
        source = time_sync_source
        last_sync = last_time_sync
    epoch = time.time() + offset
    return {
        "epoch": epoch,
        "iso": datetime.fromtimestamp(epoch).isoformat(timespec="seconds"),
        "source": source,
        "last_sync": last_sync,
    }


def _sync_time_once():
    global time_offset_seconds, last_time_sync, time_sync_source
    if not config.ENABLE_TIME_SYNC:
        return
    try:
        response = requests.get(config.TIME_SYNC_API, timeout=config.TIME_SYNC_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if "unixtime" in data:
            network_epoch = float(data["unixtime"])
        elif "datetime" in data:
            network_epoch = datetime.fromisoformat(
                data["datetime"].replace("Z", "+00:00")
            ).timestamp()
        else:
            return
        local_epoch = time.time()
        with time_sync_lock:
            time_offset_seconds = network_epoch - local_epoch
            last_time_sync = local_epoch
            time_sync_source = "network"
    except Exception as sync_error:
        with time_sync_lock:
            time_sync_source = "local"
        print(f"⚠️ 时间同步失败: {sync_error}")


def _time_sync_worker():
    while True:
        _sync_time_once()
        sleep_interval = max(60, config.TIME_SYNC_INTERVAL)
        time.sleep(sleep_interval)


def _ensure_stats_db():
    global stats_db_conn
    if not config.ENABLE_STATISTICS:
        return None
    if stats_db_conn is not None:
        return stats_db_conn
    try:
        db_path = config.STATS_DB_PATH
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        with stats_db_lock:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recorded_at REAL NOT NULL,
                    work_hours_active INTEGER NOT NULL,
                    on_duty_seconds REAL NOT NULL,
                    off_duty_seconds REAL NOT NULL,
                    total_seconds REAL NOT NULL,
                    continuous_seconds REAL NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_session_stats_time ON session_stats(recorded_at)"
            )
            conn.commit()
        stats_db_conn = conn
        return conn
    except Exception as db_error:
        print(f"⚠️ 无法初始化统计数据库: {db_error}")
        return None


def _append_stats_csv(snapshot: dict) -> None:
    path = getattr(config, "STATS_CSV_PATH", "")
    if not path:
        return
    try:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        header = (
            "recorded_at,recorded_at_iso,work_hours_active,on_duty_seconds,"
            "off_duty_seconds,total_seconds,continuous_seconds\n"
        )
        line = (
            f"{snapshot['recorded_at']:.3f},{snapshot['recorded_at_iso']},{int(snapshot['work_hours_active'])},"
            f"{snapshot['on_duty_seconds']:.3f},{snapshot['off_duty_seconds']:.3f},"
            f"{snapshot['total_seconds']:.3f},{snapshot['continuous_seconds']:.3f}\n"
        )
        write_header = False
        with stats_csv_lock:
            global csv_header_checked
            if not csv_header_checked:
                write_header = not os.path.exists(path) or os.path.getsize(path) == 0
                csv_header_checked = True
            with open(path, "a", encoding="utf-8", newline="") as csv_file:
                if write_header:
                    csv_file.write(header)
                csv_file.write(line)
    except Exception as csv_error:
        print(f"⚠️ 写入CSV失败: {csv_error}")


def _persist_stats_snapshot():
    conn = _ensure_stats_db()
    if conn is None:
        return
    try:
        durations = _current_durations()
        recorded_at = time.time()
        work_active = _within_work_hours()
        snapshot = {
            "recorded_at": recorded_at,
            "recorded_at_iso": datetime.fromtimestamp(recorded_at).isoformat(
                timespec="seconds"
            ),
            "work_hours_active": work_active,
            "on_duty_seconds": durations["on"],
            "off_duty_seconds": durations["off"],
            "total_seconds": durations["total"],
            "continuous_seconds": durations.get("continuous_on", 0.0),
        }
        payload = (
            snapshot["recorded_at"],
            1 if snapshot["work_hours_active"] else 0,
            snapshot["on_duty_seconds"],
            snapshot["off_duty_seconds"],
            snapshot["total_seconds"],
            snapshot["continuous_seconds"],
        )
        with stats_db_lock:
            conn.execute(
                """
                INSERT INTO session_stats (
                    recorded_at,
                    work_hours_active,
                    on_duty_seconds,
                    off_duty_seconds,
                    total_seconds,
                    continuous_seconds
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            conn.commit()
        _append_stats_csv(snapshot)
    except Exception as db_error:
        print(f"⚠️ 写入统计数据失败: {db_error}")


def _stats_persist_worker():
    interval = max(5.0, float(config.STATS_PERSIST_INTERVAL))
    while True:
        _persist_stats_snapshot()
        time.sleep(interval)


def _parse_time_param(raw_value):
    if raw_value is None:
        return None
    raw_value = raw_value.strip()
    if not raw_value:
        return None
    try:
        return float(raw_value)
    except ValueError:
        try:
            normalized = raw_value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized).timestamp()
        except ValueError:
            return None


def init_camera_source():
    """智能摄像头源选择"""
    # 如果启用自动检测
    if config.AUTO_DETECT_CAMERA:
        print("正在自动检测可用摄像头...")
        for i in range(config.MAX_CAMERA_INDEX):
            print(f"尝试摄像头 {i}...")
            camera = cv2.VideoCapture(i)
            if camera.isOpened():
                # 测试是否能读取帧
                ret, frame = camera.read()
                if ret:
                    print(f"✅ 成功连接摄像头 {i}")
                    return camera
                else:
                    camera.release()
            print(f"❌ 摄像头 {i} 不可用")

    # 使用配置指定的摄像头源
    print(f"使用配置的摄像头源: {config.CAMERA_SOURCE}")
    camera = cv2.VideoCapture(config.CAMERA_SOURCE)

    if camera.isOpened():
        ret, frame = camera.read()
        if ret:
            print("✅ 摄像头连接成功")
            return camera
        else:
            camera.release()

    print("⚠️ 无法连接任何摄像头")
    return None


def init_system():
    """初始化系统组件"""
    global detector, camera

    try:
        # 验证配置
        if not config.validate_config():
            return False

        # 初始化检测器
        print("正在加载YOLOv8模型...")
        detector = DutyDetector(
            model_path=config.MODEL_PATH,
            pose_model_path=config.POSE_MODEL_PATH,
            confidence_threshold=config.CONFIDENCE_THRESHOLD,
            pose_confidence_threshold=config.POSE_CONFIDENCE_THRESHOLD,
            device=config.DEVICE,
        )
        print("模型加载完成")

        # 初始化摄像头
        print("正在连接摄像头...")
        camera = init_camera_source()

        if camera is None:
            print("错误：无法连接摄像头")
            return False

        # 设置摄像头参数
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
        camera.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)

        print("系统初始化完成")
        return True

    except Exception as e:
        print(f"系统初始化失败: {str(e)}")
        return False


def capture_frames():
    """视频帧捕获线程"""
    global latest_frame, latest_status, detector, camera, system_paused

    while True:
        if camera is not None and camera.isOpened():
            with pause_lock:
                paused = system_paused

            if paused:
                time.sleep(0.2)
                continue

            ret, frame = camera.read()

            if ret:
                try:
                    # 使用检测器分析帧
                    if detector is not None:
                        detection_result, status, status_detail = detector.detect(frame)

                        # 在帧上绘制检测结果和状态
                        if detection_result is not None:
                            annotated_frame = detector.draw_detections(
                                frame, detection_result, status_text=status
                            )
                        else:
                            annotated_frame = draw_status_text(
                                frame, status, position="top-left"
                            )

                        if status_detail is not None:
                            _update_time_metrics(
                                bool(status_detail.get("frame_on_duty", False))
                            )

                        with frame_lock:
                            latest_frame = annotated_frame.copy()
                            latest_status = status
                    else:
                        with frame_lock:
                            latest_frame = frame.copy()
                            latest_status = "检测器未初始化"

                except Exception as e:
                    print(f"帧处理错误: {str(e)}")
                    with frame_lock:
                        latest_frame = frame.copy()
                        latest_status = f"处理错误: {str(e)}"
            else:
                print("无法读取摄像头帧")
                time.sleep(0.1)
        else:
            print("摄像头未连接")
            time.sleep(1)


def generate_frames():
    """生成视频流的生成器函数"""
    global latest_frame

    while True:
        with frame_lock:
            if latest_frame is not None:
                # 将帧编码为JPEG格式
                ret, buffer = cv2.imencode(
                    ".jpg", latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 80]
                )

                if ret:
                    frame_bytes = buffer.tobytes()

                    # 返回MJPEG流格式
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                    )

        time.sleep(1.0 / config.STREAM_FPS)  # 使用配置的流输出帧率


@app.route("/")
def index():
    """主页面"""
    status_interval_ms = int(max(0.2, config.STATUS_REFRESH_INTERVAL) * 1000)
    return render_template("index.html", status_interval_ms=status_interval_ms)


@app.route("/video_feed")
def video_feed():
    """视频流推送接口"""
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/status")
def get_status():
    """获取当前状态的API接口"""
    global latest_status, system_paused
    with pause_lock:
        paused = system_paused
    durations = _current_durations()
    warning = _continuous_warning_state(durations.get("continuous_on", 0.0))
    server_time = _current_server_time()
    work_hours_active = _within_work_hours()
    return {
        "status": latest_status,
        "paused": paused,
        "timestamp": time.time(),
        "on_duty_seconds": durations["on"],
        "off_duty_seconds": durations["off"],
        "total_seconds": durations["total"],
        "continuous_warning": warning,
        "server_time": server_time,
        "work_hours_active": work_hours_active,
    }


@app.route("/api/analytics")
def get_analytics():
    """预留的数据分析接口，后续可扩展"""
    durations = _current_durations()
    total = durations["total"]
    return {
        "total_time": total,
        "on_duty_time": durations["on"],
        "off_duty_time": durations["off"],
        "continuous_on_duty": durations.get("continuous_on", 0.0),
    }


@app.route("/api/stats")
def get_stats_history():
    if not config.ENABLE_STATISTICS:
        return jsonify({"enabled": False, "records": [], "summary": {}})
    conn = _ensure_stats_db()
    if conn is None:
        return (
            jsonify(
                {
                    "enabled": False,
                    "records": [],
                    "summary": {},
                    "error": "database unavailable",
                }
            ),
            500,
        )

    start_ts = _parse_time_param(request.args.get("start"))
    end_ts = _parse_time_param(request.args.get("end"))
    try:
        limit = int(request.args.get("limit", 200))
    except (TypeError, ValueError):
        limit = 200
    limit = max(1, min(limit, 1000))

    query = (
        "SELECT recorded_at, work_hours_active, on_duty_seconds, off_duty_seconds, total_seconds, continuous_seconds "
        "FROM session_stats WHERE 1=1"
    )
    params = []
    if start_ts is not None:
        query += " AND recorded_at >= ?"
        params.append(start_ts)
    if end_ts is not None:
        query += " AND recorded_at <= ?"
        params.append(end_ts)
    query += " ORDER BY recorded_at DESC LIMIT ?"
    params.append(limit)

    with stats_db_lock:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

    records = []
    for row in reversed(rows):
        ts, active, on_val, off_val, total_val, cont_val = row
        records.append(
            {
                "recorded_at": ts,
                "recorded_at_iso": datetime.fromtimestamp(ts).isoformat(
                    timespec="seconds"
                ),
                "work_hours_active": bool(active),
                "on_duty_seconds": on_val,
                "off_duty_seconds": off_val,
                "total_seconds": total_val,
                "continuous_seconds": cont_val,
            }
        )

    summary = {
        "count": len(records),
        "on_duty_total": sum(r["on_duty_seconds"] for r in records),
        "off_duty_total": sum(r["off_duty_seconds"] for r in records),
        "total_monitor_time": sum(r["total_seconds"] for r in records),
        "continuous_max": max((r["continuous_seconds"] for r in records), default=0.0),
    }

    return jsonify({"enabled": True, "records": records, "summary": summary})


# 预留扩展接口
@app.route("/api/pose")
def get_pose_data():
    """预留的姿态估计接口"""
    # TODO: 集成OpenPose姿态估计
    return {"pose_data": None, "message": "OpenPose模块待开发"}


@app.route("/api/pause", methods=["POST"])
def set_pause_state():
    """前端控制暂停/恢复检测"""
    global system_paused
    data = request.get_json(silent=True) or {}
    paused = bool(data.get("paused", False))
    with pause_lock:
        system_paused = paused
    return jsonify({"paused": system_paused})


@app.route("/api/shutdown", methods=["POST"])
def shutdown_system():
    """停止系统运行"""

    def _shutdown():
        time.sleep(0.1)
        os.kill(os.getpid(), signal.SIGINT)

    threading.Thread(target=_shutdown, daemon=True).start()
    return jsonify({"stopping": True})


if __name__ == "__main__":
    print("=" * 50)
    print("人员在岗行为识别与实时告警系统")
    print("=" * 50)
    print(f"配置信息:")
    print(f"  摄像头源: {config.CAMERA_SOURCE}")
    print(f"  分辨率: {config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT}")
    print(f"  帧率: {config.CAMERA_FPS} FPS")
    print(f"  服务地址: http://{config.HOST}:{config.PORT}")
    print(f"  检测阈值: {config.CONFIDENCE_THRESHOLD}")
    print("-" * 50)
    print(f"配置信息:")
    print(f"  摄像头源: {config.CAMERA_SOURCE}")
    print(f"  分辨率: {config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT}")
    print(f"  帧率: {config.CAMERA_FPS} FPS")
    print(f"  服务地址: http://{config.HOST}:{config.PORT}")
    print(f"  检测阈值: {config.CONFIDENCE_THRESHOLD}")
    print("-" * 50)

    # 初始化系统
    if init_system():
        # 启动视频捕获线程
        capture_thread = threading.Thread(target=capture_frames, daemon=True)
        capture_thread.start()

        if config.ENABLE_TIME_SYNC:
            _sync_time_once()
            time_sync_thread = threading.Thread(target=_time_sync_worker, daemon=True)
            time_sync_thread.start()

        if config.ENABLE_STATISTICS:
            _ensure_stats_db()
            stats_thread = threading.Thread(target=_stats_persist_worker, daemon=True)
            stats_thread.start()

        print("系统启动成功！")
        print(f"访问地址: http://{config.HOST}:{config.PORT}")
        print("按 Ctrl+C 退出系统")

        display_host = (
            "localhost" if str(config.HOST) in ("0.0.0.0", "127.0.0.1") else config.HOST
        )
        target_url = f"http://{display_host}:{config.PORT}"
        try:
            webbrowser.open_new_tab(target_url)
            print(f"已自动在浏览器中打开: {target_url}")
        except Exception as browser_exc:
            print(f"⚠️ 浏览器自动打开失败: {browser_exc}")

        try:
            # 启动Flask应用
            app.run(
                debug=config.DEBUG,
                host=config.HOST,
                port=config.PORT,
                use_reloader=False,
            )
        except KeyboardInterrupt:
            print("\n正在关闭系统...")
        finally:
            if camera is not None:
                camera.release()
            cv2.destroyAllWindows()
    else:
        print("系统启动失败，请检查环境配置")
