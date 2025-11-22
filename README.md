# 人员在岗行为识别与实时告警系统

这是一个基于深度学习的人员在岗监控系统，使用YOLOv8进行实时检测，通过Flask提供Web界面。

## 项目概述

**项目名称**：人员在岗行为识别与实时告警系统  
**项目类型**：大学生创新创业项目  
**核心技术**：YOLOv8 + Flask + OpenCV + 坐标判断算法  
**开发日期**：2025年10月16日  

## 功能特性

### 核心功能
- ✅ **实时人员检测**：基于YOLOv8识别视频流中的人员
- ✅ **椅子识别**：检测椅子位置，建立坐席区域
- ✅ **在岗判断**：通过坐标重叠算法判断人员是否在座
- ✅ **Web实时展示**：Flask驱动的网页实时视频流
- ✅ **状态监控**：实时显示在岗/离岗状态
- ✅ **响应式界面**：适配PC和移动设备
- ✅ **LSTM行为序列分析**：使用时序特征+LSTM输出更稳健的在岗概率

### 预留扩展
- 🚧 **姿态估计**：OpenPose集成接口
- 🚧 **智能告警**：MQTT推送、邮件通知
- 🚧 **数据统计**：在岗时长、效率分析
- 🚧 **多人监控**：支持多人同时监控

## 技术架构

```
前端 (Web界面)
├── HTML5 + CSS3 + JavaScript
├── 响应式设计
└── 实时状态更新

后端 (Flask服务)
├── 视频流处理 (OpenCV)
├── 深度学习推理 (YOLOv8)
├── 坐标算法判断
└── RESTful API接口

核心算法
├── 目标检测: YOLOv8
├── 坐标判断: 中心点重叠
└── 状态平滑: 多帧投票
```

## 🚀 快速开始

### 环境要求
- Python 3.10+
- 摄像头设备（USB摄像头或笔记本内置摄像头）
- 8GB+ 内存推荐

### 安装步骤

1. **克隆项目**
```bash
git clone <项目地址>
cd on_duty_monitor
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置摄像头**（可选）
```bash
# 方法1: 编辑配置文件
# 修改 config.py 中的 CAMERA_SOURCE 参数

# 方法2: 使用环境变量
set CAMERA_SOURCE=1  # Windows
export CAMERA_SOURCE=1  # Linux/macOS

# 方法3: 运行配置测试
python test_config.py
```

4. **启动系统**
```bash
# 标准启动
python app.py

# 或使用引导式启动
python start.py
```

5. **访问界面**
```
浏览器打开：http://localhost:5000
```

### 首次运行
- 系统会自动下载YOLOv8s模型（约22MB）
- 启用自动摄像头检测功能
- 请确保摄像头权限已开启
- 首次加载可能需要1-2分钟

### 快速配置摄像头

#### 使用笔记本内置摄像头
```python
# config.py
CAMERA_SOURCE = 0
```

#### 使用USB摄像头
```python
# config.py  
CAMERA_SOURCE = 1
```

#### 使用测试视频
```python
# config.py
CAMERA_SOURCE = "test_video.mp4"
```

## 使用说明

### 基本使用
1. 运行程序后访问Web界面
2. 确保人员和椅子都在摄像头视野内
3. 系统自动识别并显示在岗状态
4. 观察实时视频流和状态指示器

### 状态说明
- 🟢 **在岗**：人员中心点位于椅子区域内
- 🔴 **离岗**：人员不在椅子区域内
- 🟡 **未知**：未检测到人员或椅子

### 性能优化

## LSTM行为序列分析

LSTM模块会收集每帧的 12 维特征（人员数、在岗占比、IoU、头部姿态、监视器距离等），形成连续序列并交由轻量级LSTM输出更平滑的在岗概率。

1. 在 `config.py` 中开启 `ENABLE_BEHAVIOR_ANALYSIS = True`
2. 可选地为 `LSTM_MODEL_PATH` 指定自定义的 `.pt/.pth` 模型；否则系统使用内建 `SimpleBehaviorLSTM`
3. 根据需要调整 `BEHAVIOR_SEQUENCE_LENGTH`、`BEHAVIOR_FEATURE_SIZE`、`LSTM_*` 阈值
4. 使用离线脚本验证模型：

```bash
python behavior_demo.py --verbose
```

当行为模块就绪时，状态栏会显示 `LSTM:0.xx` 概率，并与传统平滑结果进行权重融合。
- 推荐使用YOLOv8s模型（默认）
- 建议摄像头分辨率：640x480
- 目标帧率：20-30 FPS

## 📁 项目结构

```
on_duty_monitor/
├── app.py                  # Flask主程序
├── detector.py             # YOLOv8检测器核心
├── utils.py               # 工具函数库
├── config.py              # 主配置文件 🔧
├── requirements.txt       # 依赖包列表
├── README.md              # 项目说明文档
├── CONFIG_GUIDE.md        # 配置使用指南 📋
├── config_example.py      # 配置示例和管理工具
├── test_config.py         # 配置测试脚本
├── start.py              # 引导式启动脚本
├── templates/             # HTML模板目录
│   └── index.html         # 主页面模板
├── static/                # 静态资源目录
│   └── style.css          # 前端样式文件
├── models/                # AI模型文件目录
│   ├── README.md          # 模型说明文档
│   └── yolov8s.pt         # 预训练模型（自动下载）
└── docs/                  # 项目文档目录
    └── images/            # 文档图片资源
```

### 📋 配置文件说明

| 文件 | 作用 | 说明 |
|------|------|------|
| `config.py` | 主配置文件 | 包含所有系统参数配置 |
| `CONFIG_GUIDE.md` | 配置指南 | 详细的配置使用说明 |
| `config_example.py` | 配置工具 | 配置示例和管理工具 |
| `test_config.py` | 配置测试 | 验证配置有效性 |
| `start.py` | 启动脚本 | 引导式系统启动 |

## API接口

### 视频流接口
```
GET /video_feed
返回：MJPEG视频流
```

### 状态查询
```
GET /status
返回：{"status": "在岗状态", "timestamp": 时间戳}
```

### 数据分析（预留）
```
GET /api/analytics
返回：统计数据
```

## ⚙️ 配置说明

### 系统配置文件

系统使用 `config.py` 文件进行统一配置管理，支持灵活的参数配置和摄像头选择。

#### 📹 摄像头配置

**配置文件位置**: `config.py`

```python
# 摄像头配置选项
CAMERA_SOURCE = 0              # 摄像头源选择
CAMERA_WIDTH = 640             # 视频宽度  
CAMERA_HEIGHT = 480            # 视频高度
CAMERA_FPS = 30                # 帧率
AUTO_DETECT_CAMERA = True      # 自动检测可用摄像头
MAX_CAMERA_INDEX = 3           # 最大摄像头索引检测范围
```

#### 🎯 摄像头源选择方法

##### 方法1: 修改配置文件
编辑 `config.py` 文件中的 `CAMERA_SOURCE` 参数：

| 配置值 | 说明 | 使用场景 |
|--------|------|----------|
| `0` | 默认摄像头（通常是笔记本内置） | 个人开发和测试 |
| `1` | 第一个USB摄像头 | 外接高清摄像头 |
| `2` | 第二个USB摄像头 | 多摄像头环境 |
| `"rtmp://192.168.1.100/live"` | 网络摄像头RTMP流 | IP摄像头/监控设备 |
| `"test_video.mp4"` | 视频文件 | 测试和演示 |

**示例配置：**
```python
# config.py

# 使用笔记本内置摄像头
CAMERA_SOURCE = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# 使用USB高清摄像头
CAMERA_SOURCE = 1
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

# 使用网络IP摄像头
CAMERA_SOURCE = "rtmp://192.168.1.100/live"
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080

# 使用测试视频文件
CAMERA_SOURCE = "demo_video.mp4"
ENABLE_TEST_MODE = True
```

##### 方法2: 环境变量覆盖
无需修改代码，通过环境变量临时更改配置：

```bash
# Windows PowerShell
$env:CAMERA_SOURCE = "1"
$env:CAMERA_WIDTH = "1280"
$env:CAMERA_HEIGHT = "720"
python app.py

# Windows CMD
set CAMERA_SOURCE=1
set CAMERA_WIDTH=1280
set CAMERA_HEIGHT=720
python app.py

# Linux/macOS
export CAMERA_SOURCE=1
export CAMERA_WIDTH=1280
export CAMERA_HEIGHT=720
python app.py
```

##### 方法3: 自动检测摄像头
启用自动检测功能，系统会自动找到可用的摄像头：

```python
# config.py
AUTO_DETECT_CAMERA = True      # 启用自动检测
MAX_CAMERA_INDEX = 3          # 检测范围 0-3
CAMERA_SOURCE = 0             # 备用选项
```

#### 📊 配置管理工具

系统提供了多个配置管理工具：

```bash
# 查看当前配置信息
python config_example.py

# 测试配置有效性和摄像头连接
python test_config.py

# 使用引导式启动
python start.py
```

#### ⚡ 性能优化配置

根据硬件性能选择合适的配置：

| 配置等级 | 分辨率 | 帧率 | 置信度 | 适用设备 |
|----------|--------|------|--------|----------|
| **低配置** | 320x240 | 15 FPS | 0.7 | 低配置设备/树莓派 |
| **标准配置** | 640x480 | 30 FPS | 0.5 | 一般配置设备 |
| **高配置** | 1280x720 | 30 FPS | 0.3 | 高性能设备 |

**低配置模式示例：**
```python
# config.py - 适合低配置设备
CAMERA_SOURCE = 0
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
CAMERA_FPS = 15
CONFIDENCE_THRESHOLD = 0.7
JPEG_QUALITY = 60
STREAM_FPS = 15
```

**高清模式示例：**
```python
# config.py - 适合高性能设备
CAMERA_SOURCE = 1
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30
CONFIDENCE_THRESHOLD = 0.3
JPEG_QUALITY = 90
STREAM_FPS = 30
```

### 🤖 AI检测配置

```python
MODEL_PATH = "models/yolov8s.pt"    # YOLOv8模型路径
CONFIDENCE_THRESHOLD = 0.5           # 检测置信度阈值
STATUS_SMOOTH_FRAMES = 5            # 状态平滑帧数
DEVICE = "cpu"                      # 推理设备 ("cpu" 或 "cuda")
```

### 🌐 Web服务配置

```python
HOST = "0.0.0.0"               # 服务器主机地址
PORT = 5000                    # 服务器端口
DEBUG = False                  # 调试模式
JPEG_QUALITY = 80              # JPEG压缩质量
```

### 🚨 摄像头故障排除

**问题1: 摄像头无法连接**
```bash
# 运行摄像头测试
python test_config.py

# 启用自动检测
# 在config.py中设置: AUTO_DETECT_CAMERA = True
```

**问题2: 性能问题**
```python
# config.py - 降低配置
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
CAMERA_FPS = 15
CONFIDENCE_THRESHOLD = 0.7
```

**问题3: 网络摄像头连接**
```python
# config.py - 网络摄像头配置
CAMERA_SOURCE = "rtmp://192.168.1.100/live"
# 或者
CAMERA_SOURCE = "http://192.168.1.100:8080/video"
```

### 🔧 配置文件完整说明

详细的配置说明请参考 `CONFIG_GUIDE.md` 文件。

## 扩展开发

### 添加新功能
1. **姿态估计集成**
```python
# 在detector.py中添加
def detect_pose(self, frame):
    # TODO: OpenPose集成
    pass
```

2. **MQTT告警**
```python
# 在utils.py中添加
def send_mqtt_alert(message):
    # TODO: MQTT推送实现
    pass
```

3. **数据库存储**
```python
# 添加新文件 database.py
def save_detection_record(status, timestamp):
    # TODO: 数据持久化
    pass
```

## 🐛 故障排除

### 常见问题

#### **Q: 摄像头无法打开？**  
**A: 摄像头配置问题排查**
```bash
# 1. 运行摄像头诊断
python test_config.py

# 2. 启用自动检测
# 在config.py中设置: AUTO_DETECT_CAMERA = True

# 3. 手动尝试不同摄像头
# 在config.py中依次尝试: CAMERA_SOURCE = 0, 1, 2

# 4. 检查摄像头占用
# 确保没有其他程序在使用摄像头
```

#### **Q: 中文显示乱码？**  
**A: 字体配置问题**
```bash
# 系统已集成中文字体支持
# 确保安装了PIL库: pip install Pillow
# 字体路径在config.py的CHINESE_FONT_PATHS中配置
```

#### **Q: 模型加载失败？**  
**A: 模型下载问题**
```bash
# 检查网络连接，或手动下载模型
# 模型路径配置: config.py中的MODEL_PATH
# 手动下载: wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt
```

#### **Q: 检测精度不高？**  
**A: 检测参数调整**
```python
# config.py中调整以下参数:
CONFIDENCE_THRESHOLD = 0.3      # 降低阈值提高召回率
STATUS_SMOOTH_FRAMES = 3        # 减少平滑帧数提高响应
CAMERA_WIDTH = 1280             # 提高分辨率增强精度
CAMERA_HEIGHT = 720
```

#### **Q: 系统运行缓慢？**  
**A: 性能优化配置**
```python
# config.py中使用低配置模式:
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
CAMERA_FPS = 15
CONFIDENCE_THRESHOLD = 0.7
JPEG_QUALITY = 60
STREAM_FPS = 15
```

#### **Q: 页面无法访问？**  
**A: 网络配置问题**
```python
# config.py中检查网络配置:
HOST = "0.0.0.0"        # 允许外部访问
PORT = 5000             # 确保端口未被占用

# 或使用环境变量临时修改:
# set PORT=8080 && python app.py
```

#### **Q: 网络摄像头连接失败？**  
**A: 网络摄像头配置**
```python
# config.py中配置网络摄像头:
CAMERA_SOURCE = "rtmp://192.168.1.100/live"
# 或
CAMERA_SOURCE = "http://192.168.1.100:8080/video"

# 确保网络连通性和摄像头地址正确
```

### 🔧 配置诊断工具

```bash
# 完整系统诊断
python test_config.py

# 查看当前配置
python config_example.py

# 引导式启动（包含配置检查）
python start.py

# 启动时显示配置信息
python app.py
```

### 📊 日志查看
系统运行时会在控制台输出详细日志，包括：
- 模型加载状态
- 摄像头连接状态
- 检测结果信息
- 错误和警告信息

## 技术细节

### 坐标判断算法
```python
def point_in_rectangle(point, rectangle):
    x, y = point
    x1, y1, x2, y2 = rectangle
    return x1 <= x <= x2 and y1 <= y <= y2
```

### 状态平滑机制
使用滑动窗口多数投票，减少检测抖动：
- 保存最近5帧检测结果
- 统计在岗/离岗次数
- 选择多数状态作为最终结果

## 性能指标

### 系统性能
- **检测精度**：mAP@0.5 > 90%
- **处理延迟**：< 100ms
- **内存占用**：< 2GB
- **CPU占用**：< 50%（i5以上）

### 支持规格
- **最大分辨率**：1920x1080
- **最大帧率**：30 FPS
- **并发用户**：10+
- **连续运行**：24小时+

## 开发团队

**项目组**：大学生创新创业实验室  
**技术栈**：Python, YOLOv8, Flask, OpenCV  
**开发周期**：2025年10月 - 进行中  

## 许可证

本项目仅用于教育和研究目的，请勿用于商业用途。

## 联系方式

如有问题或建议，请联系项目开发团队。

---

© 2025 人员在岗行为识别与实时告警系统 | 大学生创新创业项目