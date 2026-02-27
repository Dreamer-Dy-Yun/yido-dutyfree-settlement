import pandas as pd
from abc import ABC, abstractmethod
from typing import Self

class EdiProcessor(ABC):
    def __init__(self):
        self.original_data = None

    def set_original_data(self, df : pd.DataFrame) -> Self:
        self.original_data = df
        return self

    @abstractmethod
    def parse(self) -> pd.DataFrame:
        pass
