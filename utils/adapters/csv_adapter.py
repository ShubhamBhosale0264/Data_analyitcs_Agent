import pandas as pd
import chardet
from pathlib import Path
from .base import BaseIngestionAdapter

class CSVAdapter(BaseIngestionAdapter):
    CHUNK_THRESHOLD_BYTES = 50 * 1024 * 1024
    def __init__(self, file_path: str, sheet_name: str = 0):
        self.file_path = Path(file_path)
        self.sheet_name = sheet_name
    def to_dataframe(self) -> pd.DataFrame:
        if self.file_path.suffix.lower() in (".xlsx", ".xls", ".xlsm"):
            return pd.read_excel(self.file_path, sheet_name=self.sheet_name, engine="openpyxl")
        encoding = self._detect_encoding()
        if self.file_path.stat().st_size > self.CHUNK_THRESHOLD_BYTES:
            return pd.concat(pd.read_csv(self.file_path, encoding=encoding, chunksize=50_000, low_memory=False), ignore_index=True)
        return pd.read_csv(self.file_path, encoding=encoding, low_memory=False)
    def _detect_encoding(self) -> str:
        with open(self.file_path, "rb") as f:
            return chardet.detect(f.read(100_000)).get("encoding") or "utf-8"
