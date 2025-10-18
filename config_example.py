# -*- coding: utf-8 -*-
"""
配置使用示例
演示如何通过修改config.py来配置不同的摄像头和参数
"""

import config


def show_current_config():
    """显示当前配置信息"""
    print("=" * 60)
    print("当前系统配置信息")
    print("=" * 60)

    print("📹 摄像头配置:")
    print(f"  摄像头源: {config.CAMERA_SOURCE}")
    print(f"  分辨率: {config.CAMERA_WIDTH} x {config.CAMERA_HEIGHT}")
    print(f"  帧率: {config.CAMERA_FPS} FPS")
    print(f"  自动检测: {'启用' if config.AUTO_DETECT_CAMERA else '关闭'}")
    print(f"  检测范围: 0-{config.MAX_CAMERA_INDEX}")

    print("\n🤖 AI检测配置:")
    print(f"  模型路径: {config.MODEL_PATH}")
    print(f"  置信度阈值: {config.CONFIDENCE_THRESHOLD}")
    print(f"  推理设备: {config.DEVICE}")
    print(f"  状态平滑帧数: {config.STATUS_SMOOTH_FRAMES}")

    print("\n🌐 Web服务配置:")
    print(f"  服务器地址: {config.HOST}:{config.PORT}")
    print(f"  调试模式: {'启用' if config.DEBUG else '关闭'}")
    print(f"  JPEG质量: {config.JPEG_QUALITY}%")
    print(f"  流输出帧率: {config.STREAM_FPS} FPS")

    print("\n🎨 显示配置:")
    print(f"  默认字体大小: {config.DEFAULT_FONT_SIZE}")
    print(f"  状态字体大小: {config.STATUS_FONT_SIZE}")
    print(f"  标签字体大小: {config.LABEL_FONT_SIZE}")

    print("\n🔔 告警配置:")
    print(f"  告警功能: {'启用' if config.ENABLE_ALERT else '关闭'}")
    print(f"  冷却时间: {config.ALERT_COOLDOWN}秒")
    print(f"  告警方式: {', '.join(config.ALERT_METHODS)}")

    print("=" * 60)


def demo_camera_configs():
    """演示不同的摄像头配置方案"""
    print("\n📱 摄像头配置方案示例:")
    print("-" * 40)

    configs = [
        {
            "name": "默认摄像头（笔记本内置）",
            "source": 0,
            "description": "适用于笔记本电脑内置摄像头",
        },
        {
            "name": "USB摄像头",
            "source": 1,
            "description": "外接USB摄像头，通常画质更好",
        },
        {
            "name": "高清摄像头",
            "source": 0,
            "width": 1280,
            "height": 720,
            "description": "使用高清分辨率，需要更好的硬件性能",
        },
        {
            "name": "网络摄像头 (RTMP)",
            "source": "rtmp://192.168.1.100/live",
            "description": "使用网络摄像头或IP摄像头",
        },
        {
            "name": "测试视频文件",
            "source": "test_video.mp4",
            "description": "用于测试和演示的视频文件",
        },
    ]

    for i, cfg in enumerate(configs, 1):
        print(f"{i}. {cfg['name']}")
        print(f"   配置: CAMERA_SOURCE = {cfg['source']}")
        if "width" in cfg:
            print(f"   分辨率: {cfg['width']}x{cfg['height']}")
        print(f"   说明: {cfg['description']}")
        print()


def demo_performance_configs():
    """演示不同性能配置"""
    print("⚡ 性能配置方案示例:")
    print("-" * 40)

    performance_configs = [
        {
            "name": "低配置模式",
            "camera_width": 320,
            "camera_height": 240,
            "camera_fps": 15,
            "confidence": 0.7,
            "description": "适用于低配置设备，优先保证流畅性",
        },
        {
            "name": "标准配置模式",
            "camera_width": 640,
            "camera_height": 480,
            "camera_fps": 30,
            "confidence": 0.5,
            "description": "平衡性能和质量的标准配置",
        },
        {
            "name": "高质量模式",
            "camera_width": 1280,
            "camera_height": 720,
            "camera_fps": 30,
            "confidence": 0.3,
            "description": "追求最高质量，需要高性能硬件",
        },
    ]

    for i, cfg in enumerate(performance_configs, 1):
        print(f"{i}. {cfg['name']}")
        print(f"   分辨率: {cfg['camera_width']}x{cfg['camera_height']}")
        print(f"   帧率: {cfg['camera_fps']} FPS")
        print(f"   置信度: {cfg['confidence']}")
        print(f"   说明: {cfg['description']}")
        print()


def create_custom_config_example():
    """创建自定义配置示例文件"""
    custom_config = '''# -*- coding: utf-8 -*-
"""
自定义配置示例
复制此文件为 custom_config.py 并修改相应参数
"""

# 摄像头配置示例
CAMERA_CONFIGS = {
    "laptop": {
        "CAMERA_SOURCE": 0,
        "CAMERA_WIDTH": 640,
        "CAMERA_HEIGHT": 480,
        "CAMERA_FPS": 30,
        "description": "笔记本内置摄像头"
    },
    
    "usb_hd": {
        "CAMERA_SOURCE": 1,
        "CAMERA_WIDTH": 1280,
        "CAMERA_HEIGHT": 720,
        "CAMERA_FPS": 30,
        "description": "USB高清摄像头"
    },
    
    "ip_camera": {
        "CAMERA_SOURCE": "rtmp://192.168.1.100/live",
        "CAMERA_WIDTH": 1920,
        "CAMERA_HEIGHT": 1080,
        "CAMERA_FPS": 25,
        "description": "网络IP摄像头"
    },
    
    "test_video": {
        "CAMERA_SOURCE": "demo_video.mp4",
        "CAMERA_WIDTH": 640,
        "CAMERA_HEIGHT": 480,
        "CAMERA_FPS": 30,
        "description": "测试视频文件"
    }
}

# 使用示例：
# 1. 在config.py中设置: CAMERA_SOURCE = CAMERA_CONFIGS["usb_hd"]["CAMERA_SOURCE"]
# 2. 或直接修改config.py中的相应参数

# 环境配置示例
ENVIRONMENT_CONFIGS = {
    "development": {
        "DEBUG": True,
        "LOG_LEVEL": "DEBUG",
        "ENABLE_DEBUG_MODE": True,
        "SAVE_DEBUG_FRAMES": True
    },
    
    "production": {
        "DEBUG": False,
        "LOG_LEVEL": "INFO",
        "ENABLE_DEBUG_MODE": False,
        "SAVE_DEBUG_FRAMES": False
    },
    
    "demo": {
        "DEBUG": False,
        "CAMERA_SOURCE": "demo_video.mp4",
        "ENABLE_TEST_MODE": True
    }
}
'''

    with open("custom_config_example.py", "w", encoding="utf-8") as f:
        f.write(custom_config)
    print("✅ 已创建自定义配置示例文件: custom_config_example.py")


def main():
    """主函数"""
    print("🛠️  人员在岗检测系统 - 配置管理工具")

    # 显示当前配置
    show_current_config()

    # 显示配置示例
    demo_camera_configs()
    demo_performance_configs()

    # 创建自定义配置示例
    create_custom_config_example()

    print("\n📝 配置修改说明:")
    print("1. 直接编辑 config.py 文件")
    print("2. 设置环境变量覆盖配置")
    print("3. 参考 custom_config_example.py 创建自定义配置")
    print("\n🔄 修改配置后重启系统生效:")
    print("   python app.py")


if __name__ == "__main__":
    main()
"""
    
    with open("config_manager.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ 已创建配置管理工具: config_manager.py")
"""
