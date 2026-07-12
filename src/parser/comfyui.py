"""ComfyUI PNG Metadata Parser

ComfyUI 将 workflow JSON 嵌入 PNG 的 tEXt 块中，key 为 "workflow"。
同时部分工具（如 ComfyUI Manager）会附加 "prompt" 块。

解析策略:
1. 读 PNG chunks → 提取 "workflow" JSON
2. 从 workflow 中提取 CLIPTextEncode 节点的 prompt/negative
3. 从 workflow 中提取 CheckpointLoader 节点的 model
4. 从 workflow 中提取 LoraLoader 节点的 LoRA
5. 从 workflow 中提取 KSampler 节点的参数

参考: https://github.com/comfyanonymous/ComfyUI
"""
import json, struct, os
from pathlib import Path
from typing import Optional
from .base import BaseParser, Generation, LoraRef


class ComfyUIParser(BaseParser):
    """ComfyUI PNG 元数据解析器"""

    def can_parse(self, file_path: str) -> bool:
        if not file_path.lower().endswith('.png'):
            return False
        try:
            data = self._read_png_chunks(file_path)
            return 'workflow' in data or 'prompt' in data
        except Exception:
            return False

    def parse(self, file_path: str) -> Generation:
        gen = Generation(
            image_path=str(Path(file_path).resolve()),
            source_tool="ComfyUI",
        )

        chunks = self._read_png_chunks(file_path)
        workflow_raw = chunks.get('workflow', '') or chunks.get('prompt', '')

        if not workflow_raw:
            raise ValueError(f"No ComfyUI workflow found in {file_path}")

        workflow = json.loads(workflow_raw)

        # ComfyUI prompt format: {"nodes": [...], ...} or direct dict with node IDs
        nodes = self._get_nodes(workflow)

        # Extract prompt / negative
        gen.prompt, gen.negative = self._extract_texts(nodes)

        # Extract model
        gen.model_name, gen.model_hash = self._extract_model(nodes)

        # Extract LoRAs
        gen.loras = self._extract_loras(nodes)

        # Extract KSampler params
        self._extract_sampler_params(nodes, gen)

        # Store raw
        gen.workflow_json = workflow_raw

        return gen

    # ---- Internal ----

    @staticmethod
    def _read_png_chunks(file_path: str) -> dict:
        """读取 PNG 文本块"""
        chunks = {}
        with open(file_path, 'rb') as f:
            # Skip PNG signature (8 bytes)
            f.read(8)
            while True:
                length_bytes = f.read(4)
                if len(length_bytes) < 4:
                    break
                length = struct.unpack('>I', length_bytes)[0]
                chunk_type = f.read(4).decode('ascii', errors='ignore')
                data = f.read(length)
                f.read(4)  # CRC

                if chunk_type in ('tEXt', 'iTXt', 'zTXt'):
                    # Read key-value text chunk
                    null_idx = data.index(0)
                    key = data[:null_idx].decode('latin-1')
                    value = data[null_idx+1:].decode('latin-1')
                    chunks[key] = value
        return chunks

    @staticmethod
    def _get_nodes(workflow: dict) -> dict:
        """兼容 ComfyUI prompt 格式和直接 workflow 格式"""
        # ComfyUI prompt API format: { "output": {...}, ... } with node IDs
        # Workflow API format: { "nodes": [...], "links": [...] }
        if 'nodes' in workflow:
            return {str(n['id']): n for n in workflow['nodes']}
        # Strip output/status keys
        nodes = {}
        for k, v in workflow.items():
            if isinstance(v, dict) and 'inputs' in v:
                nodes[k] = v
        return nodes

    @staticmethod
    def _extract_texts(nodes: dict) -> tuple:
        """提取 CLIPTextEncode 节点的 prompt 和 negative"""
        prompt = ''
        negative = ''

        for node_id, node in nodes.items():
            class_type = node.get('class_type', '')
            inputs = node.get('inputs', {})

            if class_type == 'CLIPTextEncode':
                text = inputs.get('text', '').strip()
                title = node.get('_meta', {}).get('title', '').lower()

                if 'neg' in title or 'negative' in title:
                    negative = text
                elif not prompt or 'pos' in title:
                    prompt = text
                elif not prompt:
                    prompt = text  # first CLIPTextEncode = positive

        return prompt, negative

    @staticmethod
    def _extract_model(nodes: dict) -> tuple:
        """提取 CheckpointLoader 节点的 model"""
        for node in nodes.values():
            class_type = node.get('class_type', '')
            if 'CheckpointLoader' in class_type or 'ModelLoader' in class_type:
                inputs = node.get('inputs', {})
                ckpt = inputs.get('ckpt_name', '')
                name = Path(ckpt).stem if ckpt else ''
                return name, ''
        return '', ''

    @staticmethod
    def _extract_loras(nodes: dict) -> list:
        """提取所有 LoraLoader 节点"""
        loras = []
        for node in nodes.values():
            class_type = node.get('class_type', '')
            if 'LoraLoader' in class_type:
                inputs = node.get('inputs', {})
                name = inputs.get('lora_name', '')
                strength = inputs.get('strength_model', 0)
                loras.append(LoraRef(
                    name=Path(name).stem if name else '',
                    weight=round(float(strength), 2),
                ))
        return loras

    @staticmethod
    def _extract_sampler_params(nodes: dict, gen: Generation):
        """提取 KSampler / SamplerCustom 参数"""
        for node in nodes.values():
            class_type = node.get('class_type', '')
            if 'KSampler' in class_type or class_type == 'SamplerCustom':
                inputs = node.get('inputs', {})
                gen.seed = inputs.get('seed', -1)
                gen.cfg = float(inputs.get('cfg', 0))
                gen.sampler = inputs.get('sampler_name', '')
                gen.steps = inputs.get('steps', 0)
                break
