# -*- coding: utf-8 -*-
"""
人员在岗行为识别与实时告警系统 - Flask 主程序
作者：创新创业项目组
日期：2025年10月16日
"""

from flask import Flask, render_template, Response, request, jsonify
import cv2
import threading
import time
from detector import DutyDetector
from utils import draw_status_text
import config

app = Flask(__name__)

# 全局变量
detector = None
camera = None
latest_frame = None
latest_status = "系统初始化中..."
frame_lock = threading.Lock()
system_paused = False
pause_lock = threading.Lock()


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
                        detection_result, status = detector.detect(frame)

                        # 在帧上绘制检测结果和状态
                        if detection_result is not None:
                            annotated_frame = detector.draw_detections(
                                frame, detection_result, status_text=status
                            )
                        else:
                            annotated_frame = draw_status_text(
                                frame, status, position="top-left"
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
    return render_template("index.html")


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
    return {"status": latest_status, "paused": paused, "timestamp": time.time()}


@app.route("/api/analytics")
def get_analytics():
    """预留的数据分析接口，后续可扩展"""
    # TODO: 实现统计分析功能
    return {"total_time": 0, "on_duty_time": 0, "off_duty_time": 0, "alerts_count": 0}


# 预留扩展接口
@app.route("/api/pose")
def get_pose_data():
    """预留的姿态估计接口"""
    # TODO: 集成OpenPose姿态估计
    return {"pose_data": None, "message": "OpenPose模块待开发"}


@app.route("/api/alert")
def trigger_alert():
    """预留的告警接口"""
    # TODO: 实现MQTT告警推送
    return {"alert_sent": False, "message": "MQTT告警模块待开发"}


@app.route("/api/pause", methods=["POST"])
def set_pause_state():
    """前端控制暂停/恢复检测"""
    global system_paused
    data = request.get_json(silent=True) or {}
    paused = bool(data.get("paused", False))
    with pause_lock:
        system_paused = paused
    return jsonify({"paused": system_paused})


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

        print("系统启动成功！")
        print(f"访问地址: http://{config.HOST}:{config.PORT}")
        print("按 Ctrl+C 退出系统")

        try:
            # 启动Flask应用
            app.run(
                debug=config.DEBUG, host=config.HOST, port=config.PORT, threaded=True
            )
        except KeyboardInterrupt:
            print("\n正在关闭系统...")
        finally:
            if camera is not None:
                camera.release()
            cv2.destroyAllWindows()
    else:
        print("系统启动失败，请检查环境配置")
