import edi_processor
import pandas as pd
from typing import Self

class EdiLotte(edi_processor.EdiProcessor):

    def __init__(self):
        super().__init__()

    def set_original_data(self, df : pd.DataFrame) -> Self:
        self.original_data = df
        return self

    def parse(self) -> pd.DataFrame:
        pass