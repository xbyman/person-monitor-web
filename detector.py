# -*- coding: utf-8 -*-
"""多模态在岗检测 - 目标检测 + 姿态估计 + 多条件融合"""

import cv2
import numpy as np
from ultralytics import YOLO
import time

import config
from utils import (
    calculate_distance,
    calculate_iou,
    draw_chinese_text,
    draw_keypoints,
    draw_status_text,
    estimate_head_pose,
    temporal_smoothing,
)


class DutyDetector:
    """融合多模态信息的在岗检测器"""

    KEYPOINT_INDEX = {
        "nose": 0,
        "left_eye": 1,
        "right_eye": 2,
        "left_ear": 3,
        "right_ear": 4,
        "left_shoulder": 5,
        "right_shoulder": 6,
        "neck": 7,  # 一些模型没有neck，可回退到肩膀平均值
    }

    def __init__(
        self,
        model_path=None,
        pose_model_path=None,
        confidence_threshold=None,
        pose_confidence_threshold=None,
        device=None,
    ):
        self.model_path = model_path or config.MODEL_PATH
        self.pose_model_path = pose_model_path or config.POSE_MODEL_PATH
        self.confidence_threshold = confidence_threshold or config.CONFIDENCE_THRESHOLD
        self.pose_confidence_threshold = (
            pose_confidence_threshold or config.POSE_CONFIDENCE_THRESHOLD
        )
        self.device = device or config.DEVICE

        self.model = self._load_model(self.model_path)
        self.pose_model = self._load_model(self.pose_model_path)
        self.class_names = self.model.names

        self.on_duty_history = []
        self.smoothing_window = config.SMOOTHING_WINDOW
        self.smoothing_ratio = config.SMOOTHING_RATIO

        self.last_detection_time = time.time()
        self._debug_print_interval = 10.0  # 秒
        self._last_debug_print_time = 0.0

    def _load_model(self, model_path):
        try:
            model = YOLO(model_path)
            if self.device:
                model.to(self.device)
            print(f"✓ 模型加载成功: {model_path}")
            return model
        except Exception as exc:
            print(f"✗ 模型加载失败 {model_path}: {exc}")
            raise

    def detect(self, frame):
        if frame is None:
            return None, "输入帧为空"

        try:
            obj_results = self.model(frame, conf=0.25, verbose=False)
            now = time.time()
            if now - self._last_debug_print_time >= self._debug_print_interval:
                print("[Debug] 目标检测原始结果:", obj_results)
                self._last_debug_print_time = now
            pose_results = self.pose_model(
                frame, conf=self.pose_confidence_threshold, verbose=False
            )

            detections = self._parse_object_detections(obj_results[0])
            pose_persons = self._parse_pose_detections(pose_results[0])
            self._associate_pose_to_persons(detections["persons"], pose_persons)

            status_detail = self._analyze_duty_status(detections)
            frame_on_duty = status_detail["frame_on_duty"]
            self._update_history(frame_on_duty)
            smoothed_on_duty = temporal_smoothing(
                self.on_duty_history,
                window_size=self.smoothing_window,
                threshold=self.smoothing_ratio,
            )
            status_text = self._format_status(status_detail, smoothed_on_duty)

            self.last_detection_time = time.time()
            return detections, status_text

        except Exception as exc:
            print(f"检测失败: {exc}")
            return None, f"检测失败: {exc}"

    def _parse_object_detections(self, result):
        detections = {"persons": [], "chairs": [], "monitors": [], "desks": []}

        if result.boxes is None:
            return detections

        boxes = result.boxes.xyxy.cpu().numpy()
        scores = result.boxes.conf.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy().astype(int)

        for box, score, cls_id in zip(boxes, scores, classes):
            cls_name = self._get_class_name(cls_id)
            class_threshold = config.CLASS_CONFIDENCE.get(
                cls_name, self.confidence_threshold
            )
            if score < class_threshold:
                continue
            det = {
                "bbox": box,
                "confidence": float(score),
                "class_id": cls_id,
                "class_name": cls_name,
            }

            if cls_name == "person":
                detections["persons"].append(det)
            elif cls_name == "chair":
                detections["chairs"].append(det)
            elif cls_name in ("monitor", "tv", "tvmonitor", "laptop"):
                detections["monitors"].append(det)
            elif cls_name in ("desk", "table"):
                detections["desks"].append(det)

        return detections

    def _get_class_name(self, cls_id):
        if isinstance(self.class_names, dict):
            return self.class_names.get(cls_id, str(cls_id))
        if isinstance(self.class_names, (list, tuple)) and 0 <= cls_id < len(
            self.class_names
        ):
            return self.class_names[cls_id]
        return str(cls_id)

    def _parse_pose_detections(self, result):
        pose_persons = []
        if result.boxes is None or result.keypoints is None:
            return pose_persons

        boxes = result.boxes.xyxy.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()
        keypoints = result.keypoints.xy.cpu().numpy()

        for box, score, kps in zip(boxes, confidences, keypoints):
            pose_persons.append(
                {
                    "bbox": box,
                    "confidence": float(score),
                    "keypoints": self._extract_keypoints(kps),
                }
            )

        return pose_persons

    def _extract_keypoints(self, keypoint_array):
        kp_dict = {}
        for name, idx in self.KEYPOINT_INDEX.items():
            if idx < len(keypoint_array):
                point = keypoint_array[idx]
                if not np.any(np.isnan(point)):
                    kp_dict[name] = (float(point[0]), float(point[1]))
                else:
                    kp_dict[name] = None
            else:
                kp_dict[name] = None

        # 补充neck (若不存在则由双肩平均)
        if kp_dict.get("neck") is None:
            ls = kp_dict.get("left_shoulder")
            rs = kp_dict.get("right_shoulder")
            if ls and rs:
                kp_dict["neck"] = ((ls[0] + rs[0]) / 2, (ls[1] + rs[1]) / 2)

        return kp_dict

    def _associate_pose_to_persons(self, persons, pose_persons):
        if not persons:
            persons.extend(
                {
                    "bbox": pose_person["bbox"],
                    "confidence": pose_person["confidence"],
                    "class_name": "person",
                    "keypoints": pose_person["keypoints"],
                }
                for pose_person in pose_persons
            )
            return

        for person in persons:
            best_match = None
            best_iou = 0.0
            for pose_person in pose_persons:
                iou = calculate_iou(person["bbox"], pose_person["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_match = pose_person

            if best_match and best_iou >= config.POSE_ASSOCIATION_IOU:
                person["keypoints"] = best_match["keypoints"]

    def _analyze_duty_status(self, detections):
        persons = detections["persons"]
        if not persons:
            return {"status": "未检测到人员", "frame_on_duty": False, "details": []}

        chairs = detections["chairs"]
        desks = detections["desks"]
        monitors = detections["monitors"]

        details = []
        on_duty_count = 0

        for person in persons:
            person_status = self._evaluate_person(person, chairs, desks, monitors)
            if person_status["on_duty"]:
                on_duty_count += 1
            details.append(person_status)

        total = len(persons)
        frame_on_duty = on_duty_count == total and total > 0
        if on_duty_count == total and total > 0:
            status = f"在岗 ({on_duty_count}/{total}人)"
        elif on_duty_count > 0:
            status = f"部分在岗 ({on_duty_count}/{total}人)"
        else:
            status = f"离岗 ({total}人)"

        return {
            "status": status,
            "frame_on_duty": frame_on_duty,
            "details": details,
        }

    def _evaluate_person(self, person, chairs, desks, monitors):
        bbox = person["bbox"]
        keypoints = person.get("keypoints", {}) or {}
        head_point = keypoints.get("nose") or keypoints.get("neck")

        chair_iou = max(
            (calculate_iou(bbox, chair["bbox"]) for chair in chairs), default=0.0
        )

        desk_iou = max(
            (calculate_iou(bbox, desk["bbox"]) for desk in desks), default=0.0
        )

        head_above_chair = False
        if head_point and chairs:
            for chair in chairs:
                chair_top = chair["bbox"][1]
                if head_point[1] < chair_top - config.HEAD_ABOVE_MARGIN:
                    head_above_chair = True
                    break

        monitor_near = False
        if monitors:
            person_center = self._get_bbox_center(bbox)
            for monitor in monitors:
                monitor_center = self._get_bbox_center(monitor["bbox"])
                dist = calculate_distance(person_center, monitor_center)
                if dist < config.MONITOR_DISTANCE_THRESHOLD:
                    monitor_near = True
                    break

        head_pose = None
        pose_ok = False
        if keypoints:
            head_pose = estimate_head_pose(
                keypoints.get("nose"),
                keypoints.get("left_eye"),
                keypoints.get("right_eye"),
                keypoints.get("left_ear"),
                keypoints.get("right_ear"),
            )
            if head_pose:
                pose_ok = (
                    config.HEAD_POSE_PITCH_RANGE[0]
                    <= head_pose["pitch"]
                    <= config.HEAD_POSE_PITCH_RANGE[1]
                    and config.HEAD_POSE_YAW_RANGE[0]
                    <= head_pose["yaw"]
                    <= config.HEAD_POSE_YAW_RANGE[1]
                )

        conditions = {
            "chair_iou": chair_iou >= config.CHAIR_IOU_THRESHOLD,
            "head_above_chair": head_above_chair,
            "desk_iou": desk_iou >= config.DESK_IOU_THRESHOLD,
            "monitor_distance": monitor_near,
            "head_pose": pose_ok,
        }

        on_duty = any(conditions.values())

        person["keypoints"] = keypoints
        person["head_pose"] = head_pose
        person["on_duty"] = on_duty
        person["conditions"] = conditions

        return {
            "bbox": bbox,
            "keypoints": keypoints,
            "head_pose": head_pose,
            "conditions": conditions,
            "on_duty": on_duty,
        }

    def _update_history(self, frame_on_duty):
        self.on_duty_history.append(frame_on_duty)
        if len(self.on_duty_history) > self.smoothing_window:
            self.on_duty_history.pop(0)

    def _format_status(self, status_detail, smoothed_on_duty):
        base = status_detail["status"]
        if smoothed_on_duty:
            return f"在岗(平滑) - {base}"
        else:
            return f"离岗(平滑) - {base}"

    def _get_bbox_center(self, bbox):
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def draw_detections(self, frame, detections, status_text=None):
        if detections is None or frame is None:
            return frame

        annotated = frame.copy()

        for chair in detections.get("chairs", []):
            annotated = self._draw_box(
                annotated, chair["bbox"], config.COLORS["chair_box"], "椅子"
            )

        for desk in detections.get("desks", []):
            annotated = self._draw_box(
                annotated,
                desk["bbox"],
                config.COLORS.get("desk_box", (0, 128, 255)),
                "桌面",
            )

        for monitor in detections.get("monitors", []):
            annotated = self._draw_box(
                annotated,
                monitor["bbox"],
                config.COLORS.get("monitor_box", (255, 255, 0)),
                "显示器",
            )

        for idx, person in enumerate(detections.get("persons", []), start=1):
            bbox = person["bbox"]
            annotated = self._draw_box(
                annotated, bbox, config.COLORS["person_box"], f"人员{idx}"
            )
            if person.get("keypoints"):
                annotated = draw_keypoints(annotated, person["keypoints"])
            if person.get("head_pose"):
                pose = person["head_pose"]
                text = f"P:{pose['pitch']:.1f} Y:{pose['yaw']:.1f}"
                x1, y1, _, _ = bbox
                annotated = draw_chinese_text(
                    annotated, text, (int(x1), int(y1) - 50), 18, (0, 255, 255)
                )

        if status_text:
            annotated = draw_status_text(annotated, status_text, position="top-left")

        return annotated

    def _draw_box(self, frame, bbox, color, label):
        x1, y1, x2, y2 = map(int, bbox)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        return draw_chinese_text(frame, label, (x1, max(0, y1 - 25)), 18, color)

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
