import pandas as pd
from sqlalchemy import create_engine, text
from .base import BaseIngestionAdapter

class SQLAdapter(BaseIngestionAdapter):
    MAX_ROWS = 1_000_000
    def __init__(self, connection_string: str, table_name: str = "", custom_query: str = ""):
        self.connection_string = connection_string
        self.table_name = table_name
        self.custom_query = custom_query
    def to_dataframe(self) -> pd.DataFrame:
        engine = create_engine(self.connection_string, pool_pre_ping=True)
        sql = self.custom_query if self.custom_query else f"SELECT * FROM {self.table_name} LIMIT {self.MAX_ROWS}"
        if not sql.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed.")
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn)
