# -*- coding: utf-8 -*-
"""
工具函数模块 - 提供坐标计算、绘图等辅助功能
作者：创新创业项目组
日期：2025年10月16日
"""

import cv2
import numpy as np
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import os
import config


def draw_chinese_text(img, text, position, font_size=30, color=(255, 255, 255)):
    """
    在OpenCV图像上绘制中文文字

    Args:
        img: OpenCV图像 (BGR格式)
        text (str): 要绘制的文字
        position (tuple): 文字位置 (x, y)
        font_size (int): 字体大小
        color (tuple): 文字颜色 (B, G, R)

    Returns:
        numpy.ndarray: 绘制后的图像
    """
    # 将OpenCV图像转换为PIL图像
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)

    # 创建绘制对象
    draw = ImageDraw.Draw(pil_img)

    # 尝试使用系统中文字体
    font_paths = [
        "C:/Windows/Fonts/simhei.ttf",  # 黑体
        "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
        "C:/Windows/Fonts/simsun.ttc",  # 宋体
        "/System/Library/Fonts/PingFang.ttc",  # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
    ]

    font = None
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue

    # 如果没有找到字体，使用默认字体
    if font is None:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

    # 绘制文字（PIL使用RGB格式）
    pil_color = (color[2], color[1], color[0])  # BGR转RGB
    draw.text(position, text, font=font, fill=pil_color)

    # 转换回OpenCV格式
    result_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return result_img


def point_in_rectangle(point, rectangle):
    """
    判断点是否在矩形内

    Args:
        point (tuple): 点坐标 (x, y)
        rectangle (list): 矩形坐标 [x1, y1, x2, y2]

    Returns:
        bool: 点是否在矩形内
    """
    x, y = point
    x1, y1, x2, y2 = rectangle

    return x1 <= x <= x2 and y1 <= y <= y2


def calculate_overlap(bbox1, bbox2):
    """
    计算两个边界框的重叠面积和重叠比例

    Args:
        bbox1 (list): 第一个边界框 [x1, y1, x2, y2]
        bbox2 (list): 第二个边界框 [x1, y1, x2, y2]

    Returns:
        tuple: (重叠面积, 重叠比例)
    """
    x1_1, y1_1, x2_1, y2_1 = bbox1
    x1_2, y1_2, x2_2, y2_2 = bbox2

    # 计算重叠区域
    x1_overlap = max(x1_1, x1_2)
    y1_overlap = max(y1_1, y1_2)
    x2_overlap = min(x2_1, x2_2)
    y2_overlap = min(y2_1, y2_2)

    # 检查是否有重叠
    if x1_overlap < x2_overlap and y1_overlap < y2_overlap:
        overlap_area = (x2_overlap - x1_overlap) * (y2_overlap - y1_overlap)
    else:
        overlap_area = 0

    # 计算两个框的面积
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)

    # 计算重叠比例（相对于较小的框）
    if area1 > 0 and area2 > 0:
        overlap_ratio = overlap_area / min(area1, area2)
    else:
        overlap_ratio = 0

    return overlap_area, overlap_ratio


def calculate_distance(point1, point2):
    """
    计算两点之间的欧几里得距离

    Args:
        point1 (tuple): 第一个点 (x, y)
        point2 (tuple): 第二个点 (x, y)

    Returns:
        float: 两点间距离
    """
    x1, y1 = point1
    x2, y2 = point2
    return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def calculate_iou(bbox1, bbox2):
    """计算两个边界框的IoU (Intersection over Union)"""
    if bbox1 is None or bbox2 is None:
        return 0.0

    x1_1, y1_1, x2_1, y2_1 = bbox1
    x1_2, y1_2, x2_2, y2_2 = bbox2

    x1_inter = max(x1_1, x1_2)
    y1_inter = max(y1_1, y1_2)
    x2_inter = min(x2_1, x2_2)
    y2_inter = min(y2_1, y2_2)

    if x1_inter >= x2_inter or y1_inter >= y2_inter:
        return 0.0

    inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)
    area1 = max((x2_1 - x1_1), 0) * max((y2_1 - y1_1), 0)
    area2 = max((x2_2 - x1_2), 0) * max((y2_2 - y1_2), 0)
    union_area = area1 + area2 - inter_area

    if union_area <= 0:
        return 0.0

    return inter_area / union_area


def estimate_head_pose(nose, left_eye, right_eye, left_ear, right_ear):
    """使用PnP方法估计头部姿态 (pitch/yaw/roll 单位:度)"""
    required_points = [nose, left_eye, right_eye, left_ear, right_ear]
    if any(pt is None for pt in required_points):
        return None

    model_points = np.array(
        [
            (0.0, 0.0, 0.0),  # 鼻尖
            (-30.0, 65.0, -5.0),  # 左眼
            (30.0, 65.0, -5.0),  # 右眼
            (-60.0, 50.0, -20.0),  # 左耳
            (60.0, 50.0, -20.0),  # 右耳
        ],
        dtype=np.float64,
    )

    image_points = np.array(required_points, dtype=np.float64)

    focal_length = max(image_points[:, 0].max(), image_points[:, 1].max(), 1.0) * 1.5
    center = (image_points[:, 0].mean(), image_points[:, 1].mean())
    camera_matrix = np.array(
        [[focal_length, 0, center[0]], [0, focal_length, center[1]], [0, 0, 1]],
        dtype=np.float64,
    )

    dist_coeffs = np.zeros((4, 1))

    try:
        success, rotation_vec, translation_vec = cv2.solvePnP(
            model_points,
            image_points,
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )

        if not success:
            return None

        rotation_mat, _ = cv2.Rodrigues(rotation_vec)
        proj_matrix = np.hstack((rotation_mat, translation_vec))
        _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)

        return {
            "pitch": float(euler_angles[0]),
            "yaw": float(euler_angles[1]),
            "roll": float(euler_angles[2]),
        }
    except cv2.error:
        return None


def temporal_smoothing(history, window_size=10, threshold=0.7):
    """对历史状态进行平滑，返回布尔状态"""
    if not history:
        return False

    recent = history[-window_size:]
    positive = sum(1 for status in recent if status)
    return positive / len(recent) >= threshold


def draw_keypoints(frame, keypoints, color=(0, 255, 255)):
    """在帧上绘制人体关键点"""
    if frame is None or not keypoints:
        return frame

    annotated = frame.copy()
    for point in keypoints.values():
        if point is None:
            continue
        cv2.circle(annotated, (int(point[0]), int(point[1])), 4, color, -1)
    return annotated


def draw_status_text(
    frame,
    status_text,
    position="top-left",
    background_color=None,
    text_color=None,
):
    """
    在帧上绘制状态文字（支持中文）

    Args:
        frame: 输入帧
        status_text (str): 状态文字
        position (str): 文字位置 ('top-left', 'top-right', 'bottom-left', 'bottom-right', 'center')
        background_color (tuple): 背景颜色 (B, G, R)
        text_color (tuple): 文字颜色 (B, G, R)

    Returns:
        numpy.ndarray: 绘制后的帧
    """
    if frame is None:
        return None

    # 使用配置的默认颜色
    if background_color is None:
        background_color = config.COLORS["status_bg"]
    if text_color is None:
        text_color = config.COLORS["status_text"]

    annotated_frame = frame.copy()
    h, w = frame.shape[:2]

    # 设置字体参数
    font_size = config.STATUS_FONT_SIZE
    padding = 15

    # 估算文字尺寸（中文字符大致尺寸）
    char_width = font_size * 0.8
    char_height = font_size
    text_w = int(len(status_text) * char_width)
    text_h = int(char_height)

    # 计算文字位置
    if position == "top-left":
        x, y = padding, padding
    elif position == "top-right":
        x, y = w - text_w - padding, padding
    elif position == "bottom-left":
        x, y = padding, h - text_h - padding
    elif position == "bottom-right":
        x, y = w - text_w - padding, h - text_h - padding
    elif position == "center":
        x, y = (w - text_w) // 2, (h - text_h) // 2
    else:
        x, y = padding, padding

    # 绘制背景矩形
    cv2.rectangle(
        annotated_frame,
        (x - padding // 2, y - padding // 2),
        (x + text_w + padding // 2, y + text_h + padding // 2),
        background_color,
        -1,
    )

    # 使用支持中文的绘制函数
    annotated_frame = draw_chinese_text(
        annotated_frame, status_text, (x, y), font_size, text_color
    )

    return annotated_frame


def draw_fps(frame, fps, position="top-right"):
    """
    在帧上绘制FPS信息

    Args:
        frame: 输入帧
        fps (float): 当前FPS值
        position (str): FPS显示位置

    Returns:
        numpy.ndarray: 绘制后的帧
    """
    fps_text = f"FPS: {fps:.1f}"
    return draw_status_text(
        frame, fps_text, position, background_color=(50, 50, 50), text_color=(0, 255, 0)
    )


def draw_timestamp(frame, position="bottom-right"):
    """
    在帧上绘制时间戳

    Args:
        frame: 输入帧
        position (str): 时间戳显示位置

    Returns:
        numpy.ndarray: 绘制后的帧
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return draw_status_text(
        frame,
        timestamp,
        position,
        background_color=(30, 30, 30),
        text_color=(200, 200, 200),
    )


def resize_frame(frame, max_width=800, max_height=600):
    """
    按比例调整帧大小

    Args:
        frame: 输入帧
        max_width (int): 最大宽度
        max_height (int): 最大高度

    Returns:
        numpy.ndarray: 调整后的帧
    """
    if frame is None:
        return None

    h, w = frame.shape[:2]

    # 计算缩放比例
    scale_w = max_width / w
    scale_h = max_height / h
    scale = min(scale_w, scale_h, 1.0)  # 不放大，只缩小

    if scale < 1.0:
        new_w = int(w * scale)
        new_h = int(h * scale)
        resized_frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return resized_frame

    return frame


class PerformanceMonitor:
    """性能监控器类"""

    def __init__(self, window_size=30):
        """
        初始化性能监控器

        Args:
            window_size (int): 滑动窗口大小（用于计算平均FPS）
        """
        self.window_size = window_size
        self.frame_times = []
        self.last_time = time.time()

    def update(self):
        """更新帧时间记录"""
        current_time = time.time()
        frame_time = current_time - self.last_time
        self.last_time = current_time

        self.frame_times.append(frame_time)

        # 保持滑动窗口大小
        if len(self.frame_times) > self.window_size:
            self.frame_times.pop(0)

    def get_fps(self):
        """获取当前FPS"""
        if len(self.frame_times) == 0:
            return 0.0

        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0

    def get_avg_processing_time(self):
        """获取平均处理时间（毫秒）"""
        if len(self.frame_times) == 0:
            return 0.0

        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return avg_frame_time * 1000  # 转换为毫秒


class AlertManager:
    """告警管理器类（预留扩展）"""

    def __init__(self):
        """初始化告警管理器"""
        self.alert_history = []
        self.alert_cooldown = config.ALERT_COOLDOWN  # 使用配置的告警冷却时间
        self.last_alert_time = 0

    def should_trigger_alert(self, status):
        """
        判断是否应该触发告警

        Args:
            status (str): 当前状态

        Returns:
            bool: 是否应该触发告警
        """
        current_time = time.time()

        # 检查是否在冷却期内
        if current_time - self.last_alert_time < self.alert_cooldown:
            return False

        # 检查状态是否需要告警
        if "离岗" in status or "未检测到人员" in status:
            return True

        return False

    def trigger_alert(self, status, method="log"):
        """
        触发告警

        Args:
            status (str): 触发告警的状态
            method (str): 告警方式 ('log', 'mqtt', 'email', 'webhook')
        """
        current_time = time.time()
        self.last_alert_time = current_time

        alert_info = {"timestamp": current_time, "status": status, "method": method}

        self.alert_history.append(alert_info)

        # 执行告警
        if method == "log":
            print(f"[告警] {datetime.now().strftime('%H:%M:%S')} - {status}")
        elif method == "mqtt":
            # TODO: 实现MQTT推送
            print(f"[MQTT告警] {status}")
        elif method == "email":
            # TODO: 实现邮件告警
            print(f"[邮件告警] {status}")
        elif method == "webhook":
            # TODO: 实现Webhook告警
            print(f"[Webhook告警] {status}")

    def get_alert_statistics(self):
        """获取告警统计信息"""
        return {
            "total_alerts": len(self.alert_history),
            "last_alert": self.alert_history[-1] if self.alert_history else None,
            "cooldown_remaining": max(
                0, self.alert_cooldown - (time.time() - self.last_alert_time)
            ),
        }


def create_test_frame(width=640, height=480, text="测试帧"):
    """
    创建测试帧（当摄像头不可用时使用）

    Args:
        width (int): 帧宽度
        height (int): 帧高度
        text (str): 显示的文字

    Returns:
        numpy.ndarray: 测试帧
    """
    # 创建黑色背景
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # 添加一些图案
    cv2.rectangle(frame, (50, 50), (width - 50, height - 50), (64, 64, 64), 2)
    cv2.circle(frame, (width // 2, height // 2), 50, (128, 128, 128), -1)

    # 添加文字
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    thickness = 2

    # 获取文字尺寸并居中显示
    (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)
    x = (width - text_w) // 2
    y = (height + text_h) // 2 + 80

    cv2.putText(frame, text, (x, y), font, font_scale, (255, 255, 255), thickness)

    # 添加时间戳
    timestamp = datetime.now().strftime("%H:%M:%S")
    cv2.putText(frame, timestamp, (10, height - 10), font, 0.5, (200, 200, 200), 1)

    return frame
