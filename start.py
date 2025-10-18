# -*- coding: utf-8 -*-
"""
启动脚本 - 展示配置文件的使用
"""

import sys
import os


def print_banner():
    """打印启动横幅"""
    print("=" * 60)
    print("🤖 人员在岗行为识别与实时告警系统")
    print("=" * 60)
    print("📋 配置文件版本 - 支持灵活的参数配置")
    print("-" * 60)


def show_config_options():
    """显示配置选项说明"""
    print("\n🛠️ 配置选项说明:")
    print("\n📹 摄像头配置 (在 config.py 中修改):")
    print("   CAMERA_SOURCE = 0          # 默认摄像头")
    print("   CAMERA_SOURCE = 1          # USB摄像头")
    print("   CAMERA_SOURCE = 'rtmp://ip/live'  # 网络摄像头")
    print("   CAMERA_SOURCE = 'video.mp4'      # 视频文件")

    print("\n⚡ 性能配置:")
    print("   CAMERA_WIDTH = 640         # 分辨率宽度")
    print("   CAMERA_HEIGHT = 480        # 分辨率高度")
    print("   CAMERA_FPS = 30            # 帧率")
    print("   CONFIDENCE_THRESHOLD = 0.5 # 检测阈值")

    print("\n🌐 服务配置:")
    print("   HOST = '0.0.0.0'          # 服务器地址")
    print("   PORT = 5000               # 服务器端口")
    print("   DEBUG = False             # 调试模式")


def quick_config_guide():
    """快速配置指南"""
    print("\n🚀 快速配置指南:")
    print("\n1️⃣ 使用笔记本内置摄像头:")
    print("   在 config.py 中设置: CAMERA_SOURCE = 0")

    print("\n2️⃣ 使用USB摄像头:")
    print("   在 config.py 中设置: CAMERA_SOURCE = 1")

    print("\n3️⃣ 使用测试视频:")
    print("   在 config.py 中设置: CAMERA_SOURCE = 'test_video.mp4'")

    print("\n4️⃣ 修改分辨率:")
    print("   在 config.py 中设置: CAMERA_WIDTH = 1280, CAMERA_HEIGHT = 720")

    print("\n5️⃣ 修改服务端口:")
    print("   在 config.py 中设置: PORT = 8080")


def start_system():
    """启动系统"""
    try:
        # 导入配置
        import config

        print(f"\n📊 当前配置:")
        print(f"   摄像头源: {config.CAMERA_SOURCE}")
        print(f"   分辨率: {config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT}")
        print(f"   帧率: {config.CAMERA_FPS} FPS")
        print(f"   服务地址: http://{config.HOST}:{config.PORT}")
        print(f"   检测阈值: {config.CONFIDENCE_THRESHOLD}")
        print(f"   自动检测摄像头: {'开启' if config.AUTO_DETECT_CAMERA else '关闭'}")

        # 验证配置
        if not config.validate_config():
            print("\n❌ 配置验证失败，请检查 config.py 文件")
            return False

        print("\n✅ 配置验证通过")

        # 启动主程序
        print("\n🚀 启动系统...")
        print("-" * 60)

        # 导入并运行主程序
        import app

        # 主程序会在 if __name__ == '__main__' 中自动运行

    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断，系统已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n🔧 故障排除建议:")
        print("1. 检查 config.py 文件是否存在")
        print("2. 验证摄像头连接")
        print("3. 确认所需依赖已安装")
        print("4. 运行 python test_config.py 进行诊断")
        return False

    return True


def main():
    """主函数"""
    print_banner()

    # 检查参数
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            show_config_options()
            quick_config_guide()
            return
        elif sys.argv[1] in ["-c", "--config"]:
            show_config_options()
            return

    # 显示配置信息
    show_config_options()
    quick_config_guide()

    print("\n" + "=" * 60)
    input("按 Enter 键启动系统，或 Ctrl+C 退出...")

    # 启动系统
    start_system()


if __name__ == "__main__":
    main()
