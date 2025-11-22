# -*- coding: utf-8 -*-
"""行为序列分析离线演示脚本"""

import argparse
import numpy as np

import config
from lstm_analyzer import AnalyzerConfig, BehaviorAnalyzer


def build_sequence(sequence_length, feature_size, baseline, noise=0.05):
    seq = np.clip(
        np.random.normal(
            loc=baseline, scale=noise, size=(sequence_length, feature_size)
        ),
        0.0,
        1.0,
    )
    return seq


def main():
    parser = argparse.ArgumentParser(description="LSTM行为分析演示")
    parser.add_argument("--device", default=config.DEVICE, help="推理设备，如cpu/cuda")
    parser.add_argument(
        "--model",
        default=config.LSTM_MODEL_PATH,
        help="自定义LSTM模型路径 (可选)",
    )
    parser.add_argument(
        "--sequence-length",
        type=int,
        default=config.BEHAVIOR_SEQUENCE_LENGTH,
        help="序列长度",
    )
    parser.add_argument(
        "--feature-size",
        type=int,
        default=config.BEHAVIOR_FEATURE_SIZE,
        help="特征维度",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="输出加载信息",
    )
    args = parser.parse_args()

    analyzer = BehaviorAnalyzer(
        AnalyzerConfig(
            model_path=args.model,
            sequence_length=args.sequence_length,
            feature_size=args.feature_size,
            device=args.device,
            enable_logging=args.verbose,
        )
    )

    on_duty_seq = build_sequence(args.sequence_length, args.feature_size, baseline=0.8)
    off_duty_seq = build_sequence(args.sequence_length, args.feature_size, baseline=0.2)

    on_prob = analyzer.predict(on_duty_seq)
    off_prob = analyzer.predict(off_duty_seq)

    print("=========================================")
    print("LSTM行为分析离线演示")
    print("=========================================")
    print(f"模型路径: {args.model}")
    print(f"序列长度: {args.sequence_length}")
    print(f"特征维度: {args.feature_size}")
    print("-----------------------------------------")
    print(f"模拟在岗序列概率 : {on_prob:.3f}")
    print(f"模拟离岗序列概率 : {off_prob:.3f}")
    print("-----------------------------------------")
    if on_prob > off_prob:
        print("结果: LSTM 可以区分不同序列，集成准备就绪 ✅")
    else:
        print("结果: 建议检查或训练自定义LSTM模型 ⚠️")


if __name__ == "__main__":
    main()
