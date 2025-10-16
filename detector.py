# -*- coding: utf-8 -*-
"""
人员在岗检测器 - YOLOv8 核心检测逻辑
作者：创新创业项目组
日期：2025年10月16日
"""

import cv2
import numpy as np
from ultralytics import YOLO
import time
from utils import calculate_overlap, point_in_rectangle


class DutyDetector:
    """人员在岗检测器类"""

    def __init__(self, model_path="models/yolov8s.pt", confidence_threshold=0.5):
        """
        初始化检测器

        Args:
            model_path (str): YOLOv8模型文件路径
            confidence_threshold (float): 检测置信度阈值
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.class_names = None

        # 状态记录
        self.last_detection_time = time.time()
        self.detection_history = []  # 保存最近的检测历史，用于平滑判断
        self.max_history_length = 5  # 保存最近5次检测结果

        # 初始化模型
        self._load_model()

    def _load_model(self):
        """加载YOLOv8模型"""
        try:
            print(f"正在加载模型: {self.model_path}")
            self.model = YOLO(self.model_path)
            self.class_names = self.model.names
            print("模型加载成功")
            print(f"支持的类别: {list(self.class_names.values())}")

        except Exception as e:
            print(f"模型加载失败: {str(e)}")
            # 尝试下载默认模型
            try:
                print("尝试下载YOLOv8s模型...")
                self.model = YOLO("yolov8s.pt")
                self.class_names = self.model.names
                print("默认模型下载并加载成功")
            except Exception as e2:
                print(f"默认模型加载也失败: {str(e2)}")
                raise e2

    def detect(self, frame):
        """
        检测帧中的人员和椅子，判断在岗状态

        Args:
            frame: 输入视频帧

        Returns:
            tuple: (检测结果, 在岗状态)
        """
        if self.model is None:
            return None, "模型未加载"

        try:
            # 使用YOLOv8进行检测
            results = self.model(frame, conf=self.confidence_threshold, verbose=False)

            # 解析检测结果
            detection_result = self._parse_detections(results[0])

            # 判断在岗状态
            duty_status = self._analyze_duty_status(detection_result)

            # 更新检测历史
            self._update_history(duty_status)

            # 获取平滑后的状态
            final_status = self._get_smoothed_status()

            self.last_detection_time = time.time()

            return detection_result, final_status

        except Exception as e:
            print(f"检测过程出错: {str(e)}")
            return None, f"检测错误: {str(e)}"

    def _parse_detections(self, result):
        """解析YOLO检测结果"""
        detections = {"persons": [], "chairs": [], "other_objects": []}

        if result.boxes is not None:
            boxes = result.boxes.xyxy.cpu().numpy()  # 边界框坐标
            scores = result.boxes.conf.cpu().numpy()  # 置信度
            classes = result.boxes.cls.cpu().numpy()  # 类别ID

            for box, score, cls_id in zip(boxes, scores, classes):
                cls_name = self.class_names[int(cls_id)]

                detection = {
                    "bbox": box,  # [x1, y1, x2, y2]
                    "confidence": score,
                    "class_name": cls_name,
                    "class_id": int(cls_id),
                }

                # 根据类别分类存储
                if cls_name == "person":
                    detections["persons"].append(detection)
                elif cls_name == "chair":
                    detections["chairs"].append(detection)
                else:
                    detections["other_objects"].append(detection)

        return detections

    def _analyze_duty_status(self, detections):
        """分析在岗状态"""
        persons = detections["persons"]
        chairs = detections["chairs"]

        if not persons:
            return "未检测到人员"

        if not chairs:
            return "未检测到椅子"

        # 寻找最佳的人员-椅子匹配
        on_duty_count = 0
        total_persons = len(persons)

        for person in persons:
            person_center = self._get_bbox_center(person["bbox"])

            # 检查人员中心点是否在任何椅子区域内
            for chair in chairs:
                chair_bbox = chair["bbox"]

                if point_in_rectangle(person_center, chair_bbox):
                    on_duty_count += 1
                    break  # 一个人只匹配一把椅子

        # 生成状态描述
        if on_duty_count == total_persons:
            return f"在岗 ({on_duty_count}/{total_persons}人)"
        elif on_duty_count > 0:
            return f"部分在岗 ({on_duty_count}/{total_persons}人)"
        else:
            return f"离岗 ({total_persons}人均不在座位)"

    def _get_bbox_center(self, bbox):
        """计算边界框中心点"""
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        return (center_x, center_y)

    def _update_history(self, status):
        """更新检测历史"""
        self.detection_history.append(status)

        # 保持历史记录长度
        if len(self.detection_history) > self.max_history_length:
            self.detection_history.pop(0)

    def _get_smoothed_status(self):
        """获取平滑处理后的状态（减少抖动）"""
        if not self.detection_history:
            return "状态未知"

        # 简单多数投票平滑
        if len(self.detection_history) < 3:
            return self.detection_history[-1]

        # 统计最近几次检测中的状态
        status_counts = {}
        for status in self.detection_history[-3:]:
            key = "在岗" if "在岗" in status else "离岗" if "离岗" in status else "其他"
            status_counts[key] = status_counts.get(key, 0) + 1

        # 返回最多的状态类型，但保留具体信息
        if status_counts.get("在岗", 0) >= 2:
            return (
                self.detection_history[-1]
                if "在岗" in self.detection_history[-1]
                else "在岗"
            )
        elif status_counts.get("离岗", 0) >= 2:
            return (
                self.detection_history[-1]
                if "离岗" in self.detection_history[-1]
                else "离岗"
            )
        else:
            return self.detection_history[-1]

    def draw_detections(self, frame, detections):
        """在帧上绘制检测结果"""
        if detections is None:
            return frame

        annotated_frame = frame.copy()

        # 绘制人员检测框（绿色）
        for person in detections["persons"]:
            bbox = person["bbox"].astype(int)
            confidence = person["confidence"]

            cv2.rectangle(
                annotated_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2
            )

            # 绘制人员中心点
            center = self._get_bbox_center(bbox)
            cv2.circle(
                annotated_frame, (int(center[0]), int(center[1])), 5, (0, 255, 0), -1
            )

            # 标注信息（中文）
            label = f"人员 {confidence:.2f}"
            # 使用utils中的中文绘制函数
            from utils import draw_chinese_text

            annotated_frame = draw_chinese_text(
                annotated_frame, label, (bbox[0], bbox[1] - 30), 20, (0, 255, 0)
            )

        # 绘制椅子检测框（蓝色）
        for chair in detections["chairs"]:
            bbox = chair["bbox"].astype(int)
            confidence = chair["confidence"]

            cv2.rectangle(
                annotated_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2
            )

            # 标注信息（中文）
            label = f"椅子 {confidence:.2f}"
            # 使用utils中的中文绘制函数
            from utils import draw_chinese_text

            annotated_frame = draw_chinese_text(
                annotated_frame, label, (bbox[0], bbox[1] - 30), 20, (255, 0, 0)
            )

        return annotated_frame

    # 预留扩展方法
    def detect_pose(self, frame):
        """预留的姿态检测接口"""
        # TODO: 集成OpenPose进行姿态估计
        pass

    def analyze_behavior_sequence(self, frame_sequence):
        """预留的行为序列分析接口（LSTM）"""
        # TODO: 使用LSTM分析时序行为
        pass

    def get_detection_statistics(self):
        """获取检测统计信息"""
        return {
            "total_detections": len(self.detection_history),
            "last_detection_time": self.last_detection_time,
            "model_path": self.model_path,
            "confidence_threshold": self.confidence_threshold,
        }
