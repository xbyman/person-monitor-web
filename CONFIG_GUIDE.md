# 配置文件使用指南

## 📋 概述

本系统采用配置文件驱动的架构，所有主要参数都可以通过 `config.py` 文件进行配置，无需修改核心代码。

## 🗂️ 配置文件结构

```
on_duty_monitor/
├── config.py              # 主配置文件
├── config_example.py      # 配置示例和管理工具
├── test_config.py         # 配置测试脚本
└── start.py              # 启动脚本（展示配置使用）
```

## ⚙️ 主要配置选项

### 📹 摄像头配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `CAMERA_SOURCE` | int/str | 0 | 摄像头源选择 |
| `CAMERA_WIDTH` | int | 640 | 视频宽度 |
| `CAMERA_HEIGHT` | int | 480 | 视频高度 |
| `CAMERA_FPS` | int | 30 | 帧率 |
| `AUTO_DETECT_CAMERA` | bool | True | 自动检测摄像头 |
| `MAX_CAMERA_INDEX` | int | 3 | 检测摄像头范围 |

### 🤖 AI检测配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `MODEL_PATH` | str | "models/yolov8s.pt" | 模型文件路径 |
| `CONFIDENCE_THRESHOLD` | float | 0.5 | 检测置信度阈值 |
| `STATUS_SMOOTH_FRAMES` | int | 5 | 状态平滑帧数 |
| `DETECTION_HISTORY_LENGTH` | int | 5 | 检测历史长度 |

### 🌐 Web服务配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `HOST` | str | "0.0.0.0" | 服务器地址 |
| `PORT` | int | 5000 | 服务器端口 |
| `DEBUG` | bool | False | 调试模式 |
| `JPEG_QUALITY` | int | 80 | JPEG压缩质量 |

## 🔧 配置摄像头的方法

### 方法1: 直接修改配置文件

编辑 `config.py` 文件：

```python
# 使用默认摄像头（笔记本内置）
CAMERA_SOURCE = 0

# 使用USB摄像头
CAMERA_SOURCE = 1

# 使用网络摄像头
CAMERA_SOURCE = "rtmp://192.168.1.100/live"

# 使用视频文件
CAMERA_SOURCE = "test_video.mp4"

# 使用IP摄像头
CAMERA_SOURCE = "http://192.168.1.100:8080/video"
```

### 方法2: 环境变量覆盖

```bash
# Windows
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

### 方法3: 创建.env文件

创建 `.env` 文件：

```env
CAMERA_SOURCE=1
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720
CONFIDENCE_THRESHOLD=0.6
PORT=8080
DEBUG=true
```

然后在 `config.py` 中添加：

```python
from dotenv import load_dotenv
load_dotenv()  # 加载.env文件
```

## 📱 常用配置场景

### 场景1: 笔记本开发环境

```python
# config.py
CAMERA_SOURCE = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
AUTO_DETECT_CAMERA = True
DEBUG = True
PORT = 5000
```

### 场景2: 高清USB摄像头

```python
# config.py
CAMERA_SOURCE = 1
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30
CONFIDENCE_THRESHOLD = 0.4  # 高分辨率可降低阈值
JPEG_QUALITY = 90
```

### 场景3: 网络部署环境

```python
# config.py
CAMERA_SOURCE = "rtmp://192.168.1.100/live"
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080
HOST = "0.0.0.0"
PORT = 80
DEBUG = False
ENABLE_ALERT = True
```

### 场景4: 测试和演示

```python
# config.py
CAMERA_SOURCE = "demo_video.mp4"
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
ENABLE_TEST_MODE = True
SAVE_DEBUG_FRAMES = True
DEBUG = True
```

### 场景5: 低配置设备

```python
# config.py
CAMERA_SOURCE = 0
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
CAMERA_FPS = 15
CONFIDENCE_THRESHOLD = 0.7
JPEG_QUALITY = 60
STREAM_FPS = 15
```

## 🛠️ 配置管理工具

### 1. 查看当前配置

```bash
python config_example.py
```

### 2. 测试配置有效性

```bash
python test_config.py
```

### 3. 使用启动脚本

```bash
python start.py
```

## 🔍 配置验证

系统内置配置验证功能，会自动检查：

- 摄像头索引是否有效
- 置信度阈值是否在合理范围
- 端口号是否可用
- 分辨率和帧率是否合理

验证失败时会显示详细错误信息。

## 🚨 故障排除

### 问题1: 摄像头无法连接

**解决方案:**
1. 检查 `CAMERA_SOURCE` 设置
2. 启用 `AUTO_DETECT_CAMERA = True`
3. 运行 `python test_config.py` 检测可用摄像头

### 问题2: 系统性能差

**解决方案:**
1. 降低分辨率: `CAMERA_WIDTH = 320, CAMERA_HEIGHT = 240`
2. 降低帧率: `CAMERA_FPS = 15`
3. 提高置信度阈值: `CONFIDENCE_THRESHOLD = 0.7`
4. 降低JPEG质量: `JPEG_QUALITY = 60`

### 问题3: 端口被占用

**解决方案:**
1. 修改端口: `PORT = 8080`
2. 或使用环境变量: `export PORT=8080`

### 问题4: 中文显示问题

**解决方案:**
1. 确保安装了Pillow: `pip install Pillow`
2. 检查中文字体路径: 修改 `CHINESE_FONT_PATHS`

## 📚 配置参考

完整的配置参数列表请参考 `config.py` 文件中的注释说明。

## 🔄 配置更新

修改配置后需要重启系统才能生效：

```bash
# 停止当前运行的系统 (Ctrl+C)
# 然后重新启动
python app.py
```

## 💡 最佳实践

1. **备份配置**: 修改前备份原配置文件
2. **渐进式调整**: 一次只修改一个参数进行测试
3. **性能监控**: 关注系统资源使用情况
4. **环境隔离**: 不同环境使用不同的配置文件
5. **版本控制**: 将配置文件纳入版本控制管理