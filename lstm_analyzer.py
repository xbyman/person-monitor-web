# -*- coding: utf-8 -*-
"""LSTM行为序列分析模块"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np
import torch
import torch.nn as nn


class SimpleBehaviorLSTM(nn.Module):
    """轻量级LSTM模型，支持单类别在岗概率预测"""

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 64,
        num_layers: int = 1,
        dropout: float = 0.0,
    ) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.head = nn.Sequential(
            nn.LayerNorm(hidden_size),
            nn.Linear(hidden_size, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # type: ignore[override]
        output, _ = self.lstm(x)
        last_hidden = output[:, -1, :]
        logits = self.head(last_hidden)
        return logits


@dataclass
class AnalyzerConfig:
    model_path: Optional[str]
    sequence_length: int
    feature_size: int
    device: str = "cpu"
    enable_logging: bool = True


class BehaviorAnalyzer:
    """封装LSTM推理流程，兼容TorchScript或state_dict格式"""

    def __init__(self, config: AnalyzerConfig) -> None:
        self.config = config
        requested = config.device or "cpu"
        if requested.startswith("cuda") and not torch.cuda.is_available():
            requested = "cpu"
        self.device = torch.device(requested)
        self.model = self._load_or_create_model()
        self.model.eval()

    def predict(self, sequence: Sequence[Sequence[float]]) -> float:
        """返回在岗概率 (0-1)"""
        tensor = self._to_tensor(sequence)
        with torch.no_grad():
            logits = self.model(tensor)
            if logits.dim() == 2 and logits.size(-1) > 1:
                probs = torch.softmax(logits, dim=-1)[..., 1]
            else:
                probs = torch.sigmoid(logits)
            return float(probs.squeeze().cpu().item())

    # ------------------------------------------------------------------
    def _to_tensor(self, sequence: Sequence[Sequence[float]]) -> torch.Tensor:
        arr = np.asarray(sequence, dtype=np.float32)
        if arr.shape != (self.config.sequence_length, self.config.feature_size):
            raise ValueError(
                "Feature sequence shape mismatch: expected "
                f"({self.config.sequence_length}, {self.config.feature_size}),"
                f" got {arr.shape}"
            )
        tensor = torch.from_numpy(arr).unsqueeze(0).to(self.device)
        return tensor

    def _load_or_create_model(self) -> nn.Module:
        model_path = self._resolve_model_path(self.config.model_path)
        if model_path:
            model = self._try_load_model(model_path)
            if model is not None:
                if self.config.enable_logging:
                    print(f"✓ 行为分析模型加载成功: {model_path}")
                return model
            if self.config.enable_logging:
                print(f"⚠️ 无法加载指定模型 {model_path}，将使用默认SimpleBehaviorLSTM")
        model = SimpleBehaviorLSTM(self.config.feature_size).to(self.device)
        return model

    def _try_load_model(self, model_path: str) -> Optional[nn.Module]:
        try:
            loaded = torch.jit.load(model_path, map_location=self.device)
            return loaded.to(self.device)
        except (RuntimeError, FileNotFoundError):
            pass
        try:
            obj = torch.load(model_path, map_location=self.device)
            if isinstance(obj, nn.Module):
                return obj.to(self.device)
            if isinstance(obj, dict):
                model = SimpleBehaviorLSTM(self.config.feature_size)
                model.load_state_dict(obj)
                return model.to(self.device)
        except FileNotFoundError:
            return None
        except Exception as exc:  # noqa: BLE001  # keep logging signal
            if self.config.enable_logging:
                print(f"⚠️ 无法反序列化模型: {exc}")
        return None

    def _resolve_model_path(self, model_path: Optional[str]) -> Optional[str]:
        if not model_path:
            return None
        if os.path.isdir(model_path):
            candidate = os.path.join(model_path, "behavior_lstm.pt")
            return candidate if os.path.exists(candidate) else None
        return model_path if os.path.exists(model_path) else None


def demo_prediction(sequence_length: int = 30, feature_size: int = 10) -> None:
    """CLI演示：使用随机数据测试LSTM推理流程"""

    config = AnalyzerConfig(
        model_path=None,
        sequence_length=sequence_length,
        feature_size=feature_size,
        device="cpu",
        enable_logging=True,
    )
    analyzer = BehaviorAnalyzer(config)

    on_duty_seq = np.clip(
        np.random.normal(loc=0.8, scale=0.05, size=(sequence_length, feature_size)),
        0.0,
        1.0,
    )
    off_duty_seq = np.clip(
        np.random.normal(loc=0.2, scale=0.05, size=(sequence_length, feature_size)),
        0.0,
        1.0,
    )

    on_prob = analyzer.predict(on_duty_seq)
    off_prob = analyzer.predict(off_duty_seq)

    print("模拟在岗序列概率:", f"{on_prob:.3f}")
    print("模拟离岗序列概率:", f"{off_prob:.3f}")


if __name__ == "__main__":
    demo_prediction()
