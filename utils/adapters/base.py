from abc import ABC, abstractmethod
import pandas as pd

class BaseIngestionAdapter(ABC):
    @abstractmethod
    def to_dataframe(self) -> pd.DataFrame:
        raise NotImplementedError
    def validate(self) -> bool:
        return True
    @property
    def source_description(self) -> str:
        return self.__class__.__name__
