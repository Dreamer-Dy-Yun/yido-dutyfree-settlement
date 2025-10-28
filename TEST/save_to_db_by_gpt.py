import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# DB 파일명
DB_PATH = 'sqlite:///test_data_by_gpt.db'
Base = declarative_base()

def get_sqlalchemy_type(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return Integer
    elif pd.api.types.is_float_dtype(dtype):
        return Float
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return DateTime
    else:
        return String

def create_dynamic_model(table_name, df):
    attrs = {'__tablename__': table_name, 'id': Column(Integer, primary_key=True, autoincrement=True)}
    for col in df.columns:
        col_type = get_sqlalchemy_type(df[col].dtype)
        attrs[col] = Column(col_type)
    return type(table_name, (Base,), attrs)

def save_df_to_db(df, table_name='csv_data'):
    engine = create_engine(DB_PATH, echo=False)
    DynamicModel = create_dynamic_model(table_name, df)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    # DataFrame을 dict로 변환 후 insert
    for _, row in df.iterrows():
        data = row.to_dict()
        obj = DynamicModel(**data)
        session.add(obj)
    session.commit()
    session.close()
    print(f"Saved {len(df)} rows to table '{table_name}' in DB.")

# 사용 예시 (reader.py에서 DataFrame을 import해서 사용)
if __name__ == '__main__':
    # 예시: reader.py에서 df를 import했다고 가정
    # from reader import df
    # save_df_to_db(df)
    pass 