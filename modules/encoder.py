"""Encode and split passages with the original MiniLM model's quantized export."""

import os
from pathlib import Path
import platform
import time

from huggingface_hub import hf_hub_download
import numpy as np
import onnxruntime as ort
from requests.exceptions import ChunkedEncodingError, ConnectionError, Timeout
from tokenizers import Tokenizer


MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MODEL_REVISION = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
MAX_TOKENS = 128
WINDOW_OVERLAP = 24
WEIGHTS = {
    "arm64": "model_qint8_arm64.onnx",
    "aarch64": "model_qint8_arm64.onnx",
    "amd64": "model_quint8_avx2.onnx",
    "x86_64": "model_quint8_avx2.onnx",
}


def model_files(directory: str | None = None) -> tuple[Path, Path]:
    weights = WEIGHTS.get(platform.machine().lower())
    if weights is None:
        raise RuntimeError("RAG-LAW requires an ARM64 or x86-64 CPU.")
    if directory:
        root = Path(directory)
        return root / "tokenizer.json", root / weights

    def download(filename: str) -> Path:
        for attempt in range(3):
            try:
                return Path(hf_hub_download(MODEL_ID, filename, revision=MODEL_REVISION, token=False))
            except (ChunkedEncodingError, ConnectionError, Timeout):
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)

    return download("tokenizer.json"), download(f"onnx/{weights}")


class MiniLMEncoder:
    def __init__(self, directory: str | None = None):
        tokenizer_path, model_path = model_files(directory)
        self.weights = model_path.name
        self.tokenizer = Tokenizer.from_file(str(tokenizer_path))
        self.tokenizer.enable_truncation(max_length=MAX_TOKENS, stride=WINDOW_OVERLAP)
        self.tokenizer.enable_padding(
            pad_id=self.tokenizer.token_to_id("<pad>"),
            pad_token="<pad>",
        )

        options = ort.SessionOptions()
        options.intra_op_num_threads = min(os.cpu_count() or 1, 4)
        self.session = ort.InferenceSession(
            str(model_path),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )
        self.input_names = {item.name for item in self.session.get_inputs()}

    def passages(self, text: str):
        """Yield overlapping excerpts with offsets into the original article."""
        for paragraph in text.split("\n\n"):
            encoded = self.tokenizer.encode(paragraph)
            for segment in (encoded, *encoded.overflowing):
                offsets = [offset for offset in segment.offsets if offset[0] < offset[1]]
                if offsets:
                    yield paragraph[offsets[0][0]:offsets[-1][1]].strip()

    def encode(self, texts: list[str]) -> np.ndarray:
        """Mean-pool real tokens and normalize vectors for cosine search."""
        batches = []
        for start in range(0, len(texts), 32):
            tokens = self.tokenizer.encode_batch(texts[start:start + 32])
            attention = np.asarray([token.attention_mask for token in tokens], dtype=np.int64)
            inputs = {
                "input_ids": np.asarray([token.ids for token in tokens], dtype=np.int64),
                "attention_mask": attention,
                "token_type_ids": np.asarray([token.type_ids for token in tokens], dtype=np.int64),
            }
            token_vectors = self.session.run(
                None,
                {name: inputs[name] for name in self.input_names},
            )[0]
            mask = attention[..., None].astype(np.float32)
            pooled = (token_vectors * mask).sum(axis=1) / mask.sum(axis=1).clip(min=1)
            norms = np.linalg.norm(pooled, axis=1, keepdims=True).clip(min=1e-12)
            batches.append(pooled / norms)
        return np.ascontiguousarray(np.concatenate(batches), dtype=np.float32)
