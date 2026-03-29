import pandas as pd
from typing import Dict, Any

class ColumnTypeDetector:
    def __init__(self, df: pd.DataFrame):
        self.df = df
    def detect_all(self) -> Dict[str, Dict[str, Any]]:
        return {col: self._detect_column(col) for col in self.df.columns}
    def _detect_column(self, col: str) -> Dict[str, Any]:
        s = self.df[col]
        total = len(s)
        null_count = int(s.isna().sum())
        non_null = s.dropna()
        unique_count = int(non_null.nunique())
        unique_pct = unique_count / total if total else 0
        data_type = self._infer_data_type(s)
        meta = {
            "data_type": data_type,
            "semantic_type": self._infer_semantic_type(col, s, unique_pct),
            "null_count": null_count,
            "null_percentage": round(null_count / total * 100, 2) if total else 0,
            "unique_count": unique_count,
            "unique_percentage": round(unique_pct * 100, 2),
            "sample_values": non_null.head(10).tolist(),
            "top_values": {},
        }
        if data_type in ("integer", "float"):
            num = pd.to_numeric(non_null, errors="coerce").dropna()
            meta.update({"min_value": float(num.min()), "max_value": float(num.max()),
                         "mean_value": float(num.mean()), "std_value": float(num.std()),
                         "median_value": float(num.median())})
        if meta["semantic_type"] == "category":
            meta["top_values"] = {str(k): int(v) for k, v in non_null.value_counts().head(20).items()}
        return meta
    def _infer_data_type(self, s):
        d = str(s.dtype)
        if "int" in d: return "integer"
        if "float" in d: return "float"
        if "bool" in d: return "boolean"
        if "datetime" in d: return "datetime"
        return "string"
    def _infer_semantic_type(self, col, s, unique_pct):
        c = col.lower()
        if any(k in c for k in ["_id","id_"," id","key","uuid"]): return "id"
        if any(k in c for k in ["date","time","created","updated"]): return "ts"
        if any(k in c for k in ["price","cost","revenue","amount","salary"]): return "currency"
        if any(k in c for k in ["pct","percent","rate","ratio"]): return "pct"
        if any(k in c for k in ["lat","lon","country","city","region"]): return "geo"
        if s.dtype == object and unique_pct < 0.05: return "category"
        if str(s.dtype) in ("int64","float64"): return "numeric"
        return "unknown"
