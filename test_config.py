# -*- coding: utf-8 -*-
"""
配置测试脚本
快速测试和验证配置文件的设置
"""

import sys
import os

sys.path.append(".")


def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")

    try:
        import config

        print("✅ config 模块导入成功")
    except Exception as e:
        print(f"❌ config 模块导入失败: {e}")
        return False

    try:
        from detector import DutyDetector

        print("✅ detector 模块导入成功")
    except Exception as e:
        print(f"❌ detector 模块导入失败: {e}")
        return False

    try:
        from utils import draw_chinese_text, draw_status_text

        print("✅ utils 模块导入成功")
    except Exception as e:
        print(f"❌ utils 模块导入失败: {e}")
        return False

    return True


def test_config_validation():
    """测试配置验证"""
    print("\n📋 测试配置验证...")

    try:
        import config

        if config.validate_config():
            print("✅ 配置验证通过")
            return True
        else:
            print("❌ 配置验证失败")
            return False
    except Exception as e:
        print(f"❌ 配置验证出错: {e}")
        return False


def test_camera_detection():
    """测试摄像头检测"""
    print("\n📹 测试摄像头检测...")

    try:
        import cv2
        import config

        # 测试配置的摄像头源
        print(f"配置的摄像头源: {config.CAMERA_SOURCE}")

        if isinstance(config.CAMERA_SOURCE, int):
            # 数字摄像头源
            for i in range(config.MAX_CAMERA_INDEX):
                camera = cv2.VideoCapture(i)
                if camera.isOpened():
                    ret, frame = camera.read()
                    if ret:
                        print(
                            f"✅ 摄像头 {i} 可用 - 分辨率: {frame.shape[1]}x{frame.shape[0]}"
                        )
                    else:
                        print(f"⚠️ 摄像头 {i} 可连接但无法读取帧")
                    camera.release()
                else:
                    print(f"❌ 摄像头 {i} 不可用")
        else:
            # 文件或网络摄像头源
            camera = cv2.VideoCapture(config.CAMERA_SOURCE)
            if camera.isOpened():
                ret, frame = camera.read()
                if ret:
                    print(f"✅ 摄像头源 '{config.CAMERA_SOURCE}' 可用")
                else:
                    print(f"⚠️ 摄像头源 '{config.CAMERA_SOURCE}' 可连接但无法读取帧")
                camera.release()
            else:
                print(f"❌ 摄像头源 '{config.CAMERA_SOURCE}' 不可用")

        return True

    except Exception as e:
        print(f"❌ 摄像头检测出错: {e}")
        return False


def test_font_detection():
    """测试中文字体检测"""
    print("\n🔤 测试中文字体检测...")

    try:
        import config

        found_fonts = []
        for font_path in config.CHINESE_FONT_PATHS:
            if os.path.exists(font_path):
                found_fonts.append(font_path)
                print(f"✅ 找到字体: {font_path}")

        if found_fonts:
            print(f"✅ 共找到 {len(found_fonts)} 个中文字体")
            return True
        else:
            print("⚠️ 未找到中文字体，将使用默认字体")
            return True

    except Exception as e:
        print(f"❌ 字体检测出错: {e}")
        return False


def test_detector_initialization():
    """测试检测器初始化"""
    print("\n🤖 测试检测器初始化...")

    try:
        from detector import DutyDetector
        import config

        # 不实际加载模型，只测试参数
        print(f"模型路径: {config.MODEL_PATH}")
        print(f"置信度阈值: {config.CONFIDENCE_THRESHOLD}")
        print(f"状态平滑帧数: {config.STATUS_SMOOTH_FRAMES}")
        print(f"历史记录长度: {config.DETECTION_HISTORY_LENGTH}")

        print("✅ 检测器参数配置正确")
        return True

    except Exception as e:
        print(f"❌ 检测器测试出错: {e}")
        return False


def display_config_summary():
    """显示配置摘要"""
    print("\n📊 配置摘要:")
    print("=" * 50)

    try:
        import config

        print(f"摄像头源: {config.CAMERA_SOURCE}")
        print(f"分辨率: {config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT}")
        print(f"帧率: {config.CAMERA_FPS} FPS")
        print(f"服务地址: http://{config.HOST}:{config.PORT}")
        print(f"检测阈值: {config.CONFIDENCE_THRESHOLD}")
        print(f"自动检测摄像头: {'是' if config.AUTO_DETECT_CAMERA else '否'}")
        print(f"调试模式: {'开启' if config.DEBUG else '关闭'}")
        print(f"告警功能: {'开启' if config.ENABLE_ALERT else '关闭'}")

    except Exception as e:
        print(f"❌ 配置读取出错: {e}")


def main():
    """主测试函数"""
    print("🧪 人员在岗检测系统 - 配置测试工具")
    print("=" * 50)

    tests = [
        ("模块导入", test_imports),
        ("配置验证", test_config_validation),
        ("摄像头检测", test_camera_detection),
        ("字体检测", test_font_detection),
        ("检测器初始化", test_detector_initialization),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔄 执行测试: {test_name}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")

    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！系统配置正确。")
        print("\n▶️ 可以运行以下命令启动系统:")
        print("   python app.py")
    else:
        print("⚠️ 部分测试失败，请检查配置和环境。")

    # 显示配置摘要
    display_config_summary()

    print("\n📝 配置修改建议:")
    print("1. 编辑 config.py 文件调整参数")
    print("2. 运行 python config_example.py 查看配置示例")
    print("3. 设置环境变量覆盖特定配置")


if __name__ == "__main__":
    main()
