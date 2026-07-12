"""Parser 抽象基类 — 所有工具接入此接口"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Optional
import json


@dataclass
class LoraRef:
    name: str = ""
    weight: float = 0.0


@dataclass
class Generation:
    """一次 AI 生成的标准记录

    所有 Parser 必须输出此对象，数据库/Parser/UI 之间不传递 dict。
    """
    image_path: str = ""

    # Prompt
    prompt: str = ""
    negative: str = ""

    # Model
    model_name: str = ""
    model_hash: str = ""

    # LoRA
    loras: list = field(default_factory=list)  # List[LoraRef]

    # Parameters
    seed: int = -1
    cfg: float = 0.0
    sampler: str = ""
    steps: int = 0

    # Dimensions
    width: int = 0
    height: int = 0

    # Raw metadata
    workflow_json: str = ""
    source_tool: str = ""
    parser_name: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["loras"] = [asdict(l) if hasattr(l, '__dataclass_fields__') else l for l in self.loras]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Generation":
        loras_raw = data.pop("loras", [])
        loras = [LoraRef(**l) if isinstance(l, dict) else l for l in loras_raw]
        return cls(**data, loras=loras)


class BaseParser(ABC):
    """Parser 基类

    规则:
    - 无状态: parse() 不修改 self
    - 不写数据库 / 不写 UI / 不写搜索
    - 输入 file_path → 输出 Generation
    """

    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """判断是否能解析"""
        ...

    @abstractmethod
    def parse(self, file_path: str) -> Generation:
        """解析并返回 Generation"""
        ...
