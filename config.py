# -*- coding: utf-8 -*-
"""
人员在岗行为识别系统 - 配置文件
作者：创新创业项目组
日期：2025年10月18日
"""

import os

# =============================================================================
# 摄像头配置
# =============================================================================

# 摄像头源选择
# 0 = 默认摄像头（通常是笔记本内置摄像头）
# 1 = 第一个USB摄像头
# 2 = 第二个USB摄像头
# "rtmp://192.168.1.100/live" = 网络摄像头RTMP流
# "test_video.mp4" = 视频文件
CAMERA_SOURCE = 1

# 摄像头参数
CAMERA_WIDTH = 640  # 视频宽度
CAMERA_HEIGHT = 480  # 视频高度
CAMERA_FPS = 30  # 帧率

# 自动摄像头检测
AUTO_DETECT_CAMERA = True  # 是否自动检测可用摄像头
MAX_CAMERA_INDEX = 3  # 最大摄像头索引检测范围

# =============================================================================
# AI检测配置
# =============================================================================

# 模型配置
MODEL_PATH = "models/yolov8x.pt"  # 目标检测模型
POSE_MODEL_PATH = "models/yolov8n-pose.pt"  # 姿态估计模型
CONFIDENCE_THRESHOLD = 0.5  # 目标检测置信度
POSE_CONFIDENCE_THRESHOLD = 0.4  # 姿态估计置信度
DEVICE = "cuda"  # 推理设备 ("cpu" 或 "cuda")

# 按类别细化的置信度阈值
CLASS_CONFIDENCE = {
    "person": 0.5,
    "chair": 0.45,
    "monitor": 0.5,
    "desk": 0.4,
}

# 状态平滑配置
STATUS_SMOOTH_FRAMES = 5  # 旧参数，兼容保留
DETECTION_HISTORY_LENGTH = 5
SMOOTHING_WINDOW = 10  # 时序平滑窗口
SMOOTHING_RATIO = 0.6  # 至少60%帧为在岗

# 支持的检测类别
TARGET_CLASSES = ["person", "chair", "monitor", "desk"]

# 多条件判定阈值
CHAIR_IOU_THRESHOLD = 0.2
DESK_IOU_THRESHOLD = 0.1
MONITOR_DISTANCE_THRESHOLD = 200  # 像素
HEAD_ABOVE_MARGIN = 15  # 头部相对椅子顶部偏移
HEAD_POSE_PITCH_RANGE = (-25.0, 25.0)
HEAD_POSE_YAW_RANGE = (-30.0, 30.0)
POSE_ASSOCIATION_IOU = 0.3

# =============================================================================
# Web服务配置
# =============================================================================

# Flask服务器配置
HOST = "0.0.0.0"  # 服务器主机地址
PORT = 5000  # 服务器端口
DEBUG = False  # 调试模式

# 线程配置
THREAD_TIMEOUT = 30  # 线程超时时间（秒）

# =============================================================================
# 视频流配置
# =============================================================================

# MJPEG流配置
JPEG_QUALITY = 80  # JPEG压缩质量 (1-100)
STREAM_FPS = 40  # 流输出帧率

# 视频处理配置
FRAME_BUFFER_SIZE = 3  # 帧缓冲区大小
MAX_FRAME_WIDTH = 1920  # 最大帧宽度
MAX_FRAME_HEIGHT = 1080  # 最大帧高度

# =============================================================================
# 界面显示配置
# =============================================================================

# 中文字体配置
CHINESE_FONT_PATHS = [
    "C:/Windows/Fonts/simhei.ttf",  # 黑体
    "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
    "C:/Windows/Fonts/simsun.ttc",  # 宋体
    "/System/Library/Fonts/PingFang.ttc",  # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
]

# 文字显示配置
DEFAULT_FONT_SIZE = 30  # 默认字体大小
STATUS_FONT_SIZE = 25  # 状态文字大小
LABEL_FONT_SIZE = 20  # 标签文字大小

# 颜色配置 (BGR格式)
COLORS = {
    "person_box": (0, 255, 0),  # 人员检测框颜色 - 绿色
    "chair_box": (255, 0, 0),  # 椅子检测框颜色 - 蓝色
    "desk_box": (0, 128, 255),  # 桌面
    "monitor_box": (255, 255, 0),  # 显示器
    "person_center": (0, 255, 0),  # 人员中心点颜色 - 绿色
    "status_bg": (0, 0, 0),  # 状态背景颜色 - 黑色
    "status_text": (255, 255, 255),  # 状态文字颜色 - 白色
    "on_duty": (0, 255, 0),  # 在岗状态颜色 - 绿色
    "off_duty": (0, 0, 255),  # 离岗状态颜色 - 红色
    "unknown": (0, 255, 255),  # 未知状态颜色 - 黄色
}

# =============================================================================
# 日志配置
# =============================================================================

# 日志级别
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# 日志输出
ENABLE_CONSOLE_LOG = True  # 是否启用控制台日志
ENABLE_FILE_LOG = False  # 是否启用文件日志
LOG_FILE_PATH = "logs/system.log"  # 日志文件路径

# =============================================================================
# 扩展功能配置（预留）
# =============================================================================

# OpenPose配置（已由YOLOv8-Pose替换，保留开关供扩展）
ENABLE_POSE_DETECTION = True  # 是否启用姿态检测

# LSTM配置
ENABLE_BEHAVIOR_ANALYSIS = False  # 是否启用行为分析
LSTM_MODEL_PATH = "models/lstm"  # LSTM模型路径
BEHAVIOR_SEQUENCE_LENGTH = 30  # 行为序列长度
BEHAVIOR_FEATURE_SIZE = 12  # 单帧特征维度
LSTM_ON_DUTY_THRESHOLD = 0.6  # LSTM输出阈值
LSTM_FUSION_WEIGHT = 0.5  # 与传统平滑结果融合的权重
LSTM_FUSION_THRESHOLD = 0.5  # 融合结果阈值

# =============================================================================
# 性能优化配置
# =============================================================================

# 性能监控
ENABLE_PERFORMANCE_MONITOR = True  # 是否启用性能监控
FPS_WINDOW_SIZE = 30  # FPS计算窗口大小

# 内存管理
MAX_MEMORY_USAGE_MB = 2048  # 最大内存使用量(MB)
ENABLE_MEMORY_CLEANUP = True  # 是否启用内存清理

# GPU配置
PREFER_GPU = True  # 是否优先使用GPU
GPU_MEMORY_FRACTION = 0.7  # GPU内存使用比例

# =============================================================================
# 开发和调试配置
# =============================================================================

# 调试选项
ENABLE_DEBUG_MODE = False  # 调试模式
SAVE_DEBUG_FRAMES = False  # 保存调试帧
DEBUG_FRAME_PATH = "debug_frames"  # 调试帧保存路径

# 测试配置
ENABLE_TEST_MODE = False  # 测试模式
TEST_VIDEO_PATH = "test_video.mp4"  # 测试视频路径
ENABLE_MOCK_CAMERA = False  # 是否启用模拟摄像头

# 统计配置
ENABLE_STATISTICS = True  # 是否启用统计
STATS_UPDATE_INTERVAL = 1.0  # 统计更新间隔（秒）
STATUS_REFRESH_INTERVAL = 1.0  # 前端状态刷新间隔（秒）
STATS_DB_PATH = "data/monitor_stats.db"  # 监测统计数据库路径
STATS_PERSIST_INTERVAL = 60  # 写入数据库的时间间隔（秒）
STATS_CSV_PATH = "data/monitor_stats.csv"  # 可读的CSV导出文件

# =============================================================================
# 健康守护与时间同步配置
# =============================================================================

# 工作时段统计
WORK_HOURS_ENABLED = True  # 是否启用工作时段过滤
WORK_DAYS = [0, 1, 2, 3, 4, 5, 6]  # 允许统计的工作日（周一=0）
WORK_HOURS_START = "09:00"  # 工作开始时间（24小时制）
WORK_HOURS_END = "22:00"  # 工作结束时间

# 连续工作提醒
CONTINUOUS_WORK_THRESHOLD = 30  # 连续在岗阈值（秒）

# 联网时间同步
ENABLE_TIME_SYNC = True  # 是否启用联网时间同步
TIME_SYNC_API = "https://worldtimeapi.org/api/ip"  # 时间源API
TIME_SYNC_INTERVAL = 30 * 60  # 同步间隔（秒）
TIME_SYNC_TIMEOUT = 5  # 同步请求超时（秒）

# =============================================================================
# 环境变量支持
# =============================================================================


def get_env_or_default(env_var, default_value, var_type=str):
    """
    从环境变量获取配置值，如果不存在则使用默认值

    Args:
        env_var (str): 环境变量名
        default_value: 默认值
        var_type: 变量类型 (str, int, float, bool)

    Returns:
        配置值
    """
    value = os.getenv(env_var)
    if value is None:
        return default_value

    try:
        if var_type == bool:
            return value.lower() in ("true", "1", "yes", "on")
        else:
            return var_type(value)
    except (ValueError, TypeError):
        return default_value


# 支持环境变量覆盖配置
CAMERA_SOURCE = get_env_or_default("CAMERA_SOURCE", CAMERA_SOURCE, int)
CONFIDENCE_THRESHOLD = get_env_or_default(
    "CONFIDENCE_THRESHOLD", CONFIDENCE_THRESHOLD, float
)
POSE_MODEL_PATH = get_env_or_default("POSE_MODEL_PATH", POSE_MODEL_PATH, str)
POSE_CONFIDENCE_THRESHOLD = get_env_or_default(
    "POSE_CONFIDENCE_THRESHOLD", POSE_CONFIDENCE_THRESHOLD, float
)
HOST = get_env_or_default("HOST", HOST, str)
PORT = get_env_or_default("PORT", PORT, int)
DEBUG = get_env_or_default("DEBUG", DEBUG, bool)
STATUS_REFRESH_INTERVAL = get_env_or_default(
    "STATUS_REFRESH_INTERVAL", STATUS_REFRESH_INTERVAL, float
)
STATS_DB_PATH = get_env_or_default("STATS_DB_PATH", STATS_DB_PATH, str)
STATS_PERSIST_INTERVAL = get_env_or_default(
    "STATS_PERSIST_INTERVAL", STATS_PERSIST_INTERVAL, float
)
STATS_CSV_PATH = get_env_or_default("STATS_CSV_PATH", STATS_CSV_PATH, str)
WORK_HOURS_ENABLED = get_env_or_default("WORK_HOURS_ENABLED", WORK_HOURS_ENABLED, bool)
WORK_HOURS_START = get_env_or_default("WORK_HOURS_START", WORK_HOURS_START, str)
WORK_HOURS_END = get_env_or_default("WORK_HOURS_END", WORK_HOURS_END, str)
CONTINUOUS_WORK_THRESHOLD = get_env_or_default(
    "CONTINUOUS_WORK_THRESHOLD", CONTINUOUS_WORK_THRESHOLD, float
)
ENABLE_TIME_SYNC = get_env_or_default("ENABLE_TIME_SYNC", ENABLE_TIME_SYNC, bool)
TIME_SYNC_API = get_env_or_default("TIME_SYNC_API", TIME_SYNC_API, str)
TIME_SYNC_INTERVAL = get_env_or_default("TIME_SYNC_INTERVAL", TIME_SYNC_INTERVAL, int)
TIME_SYNC_TIMEOUT = get_env_or_default("TIME_SYNC_TIMEOUT", TIME_SYNC_TIMEOUT, int)

# =============================================================================
# 配置验证
# =============================================================================


def validate_config():
    """验证配置参数的有效性"""
    errors = []

    # 验证摄像头配置
    if isinstance(CAMERA_SOURCE, int) and CAMERA_SOURCE < 0:
        errors.append("CAMERA_SOURCE 不能为负数")

    # 验证置信度阈值
    if not 0 <= CONFIDENCE_THRESHOLD <= 1:
        errors.append("CONFIDENCE_THRESHOLD 必须在 0-1 之间")

    # 验证端口号
    if not 1 <= PORT <= 65535:
        errors.append("PORT 必须在 1-65535 之间")

    # 验证帧率
    if CAMERA_FPS <= 0:
        errors.append("CAMERA_FPS 必须大于 0")

    # 验证分辨率
    if CAMERA_WIDTH <= 0 or CAMERA_HEIGHT <= 0:
        errors.append("摄像头分辨率必须大于 0")

    if errors:
        print("配置验证错误:")
        for error in errors:
            print(f"  - {error}")
        return False

    return True


# 自动验证配置
if __name__ == "__main__":
    if validate_config():
        print("✅ 配置验证通过")
    else:
        print("❌ 配置验证失败")
