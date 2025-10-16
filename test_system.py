# -*- coding: utf-8 -*-
"""
系统启动和测试脚本
用于验证中文显示功能
"""

import cv2
import numpy as np
from utils import draw_chinese_text, draw_status_text


def test_chinese_display():
    """测试中文显示功能"""
    print("开始测试中文显示功能...")

    # 创建测试图像
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # 测试各种中文状态文字
    test_texts = [
        "在岗 (1/1人)",
        "离岗 (1人均不在座位)",
        "部分在岗 (1/2人)",
        "未检测到人员",
        "未检测到椅子",
        "系统初始化中...",
    ]

    for i, text in enumerate(test_texts):
        # 创建新的测试帧
        frame = test_frame.copy()

        # 使用中文绘制函数
        try:
            frame = draw_chinese_text(frame, text, (50, 50 + i * 40), 25, (0, 255, 0))
            print(f"✓ 成功绘制: {text}")
        except Exception as e:
            print(f"✗ 绘制失败: {text}, 错误: {e}")

    # 测试draw_status_text函数
    try:
        frame = test_frame.copy()
        frame = draw_status_text(frame, "在岗状态检测中...", "top-left")
        print("✓ draw_status_text 函数测试成功")
    except Exception as e:
        print(f"✗ draw_status_text 函数测试失败: {e}")

    print("中文显示功能测试完成!")


def test_system_imports():
    """测试系统导入"""
    print("测试系统模块导入...")

    try:
        from detector import DutyDetector

        print("✓ detector 模块导入成功")
    except Exception as e:
        print(f"✗ detector 模块导入失败: {e}")

    try:
        from utils import point_in_rectangle, calculate_overlap

        print("✓ utils 模块导入成功")
    except Exception as e:
        print(f"✗ utils 模块导入失败: {e}")

    try:
        import flask

        print("✓ Flask 可用")
    except Exception as e:
        print(f"✗ Flask 不可用: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("人员在岗行为识别系统 - 功能测试")
    print("=" * 50)

    # 测试导入
    test_system_imports()
    print()

    # 测试中文显示
    test_chinese_display()
    print()

    print("如果上述测试都通过，您可以运行 python app.py 启动完整系统")
    print("访问地址: http://localhost:5000")
