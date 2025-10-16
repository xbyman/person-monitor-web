# YOLOv8预训练模型文件说明

此文件夹用于存放YOLOv8预训练模型文件。

## 模型下载

1. **自动下载**（推荐）：
   首次运行程序时，如果检测到模型文件不存在，系统会自动下载 `yolov8s.pt` 模型。

2. **手动下载**：
   您也可以手动下载模型文件并放置在此目录下：
   
   ```bash
   # 下载YOLOv8s模型（推荐，平衡精度和速度）
   wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt
   
   # 或者使用Python下载
   from ultralytics import YOLO
   model = YOLO('yolov8s.pt')  # 首次运行会自动下载
   ```

## 可用模型

根据您的性能需求，可以选择不同大小的模型：

| 模型文件 | 大小 | mAP | 速度 | 推荐用途 |
|---------|------|-----|------|----------|
| yolov8n.pt | ~6MB | 37.3 | 最快 | 低配置设备 |
| yolov8s.pt | ~22MB | 44.9 | 快 | **推荐使用** |
| yolov8m.pt | ~52MB | 50.2 | 中等 | 高精度需求 |
| yolov8l.pt | ~87MB | 52.9 | 慢 | 服务器部署 |
| yolov8x.pt | ~136MB | 53.9 | 最慢 | 最高精度 |

## 使用说明

- 默认使用 `yolov8s.pt` 模型，在准确性和速度之间取得很好的平衡
- 如需更换模型，请修改 `detector.py` 中的 `model_path` 参数
- 确保模型文件名与代码中指定的路径一致

## 支持的检测类别

YOLOv8模型支持80个COCO数据集类别，本项目主要使用：
- `person`（人员）- 类别ID: 0
- `chair`（椅子）- 类别ID: 56

完整类别列表请参考：https://github.com/ultralytics/ultralytics/blob/main/ultralytics/cfg/datasets/coco.yaml

## 注意事项

1. 首次运行时请确保网络连接正常，以便自动下载模型
2. 模型文件较大，请确保有足够的磁盘空间
3. 如果下载失败，可以手动下载模型文件到此目录
4. 建议使用 `yolov8s.pt` 作为默认模型，性能表现最佳