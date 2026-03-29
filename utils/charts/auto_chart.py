import pandas as pd
from typing import Dict, Any

class AutoChartEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.num = df.select_dtypes(include="number").columns.tolist()
        self.cat = df.select_dtypes(include=["object","category"]).columns.tolist()
        self.dt  = df.select_dtypes(include=["datetime"]).columns.tolist()
    def recommend_and_build(self) -> Dict[str, Any]:
        chart_type, x, y, reason = self._select()
        return {"chart_type": chart_type, "x_col": x, "y_col": y,
                "reasoning": reason, "plotly_config": self._build(chart_type, x, y)}
    def _select(self):
        if self.dt and self.num:
            return "line", self.dt[0], self.num[0], f"Time series: '{self.dt[0]}' over time."
        if len(self.num) >= 2:
            return "scatter", self.num[0], self.num[1], "Two numeric columns suggest a correlation view."
        if self.cat and self.num:
            n = self.df[self.cat[0]].nunique()
            t = "bar" if n <= 20 else "treemap"
            return t, self.cat[0], self.num[0], f"'{self.cat[0]}' ({n} values) grouped with '{self.num[0]}'."
        if self.num:
            return "histogram", self.num[0], None, f"Distribution of '{self.num[0]}'."
        return "table", None, None, "No chart applies — showing as table."
    def _build(self, ct, x, y):
        layout = {"paper_bgcolor":"rgba(0,0,0,0)","plot_bgcolor":"rgba(0,0,0,0)",
                  "font":{"family":"Inter, sans-serif","size":13}}
        df = self.df
        if ct == "bar":
            g = df.groupby(x)[y].sum().reset_index().sort_values(y, ascending=False)
            return {"data":[{"type":"bar","x":g[x].tolist(),"y":g[y].tolist(),"marker":{"color":"#7F77DD"}}],"layout":layout}
        if ct == "line":
            d = df.sort_values(x)
            return {"data":[{"type":"scatter","mode":"lines","x":d[x].astype(str).tolist(),"y":d[y].tolist()}],"layout":layout}
        if ct == "scatter":
            return {"data":[{"type":"scatter","mode":"markers","x":df[x].tolist(),"y":df[y].tolist(),"marker":{"color":"#1D9E75","opacity":0.6}}],"layout":layout}
        if ct == "histogram":
            return {"data":[{"type":"histogram","x":df[x].tolist(),"marker":{"color":"#7F77DD"}}],"layout":layout}
        return {}
