###########################################
# Module name : base.py
# Module class : BaseRepository (기본 Repository 클래스)
# Written by : Cursor AI
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.12.03
# Updated at : 2025.12.03
# Instructed by : Yun Dae-young 
# Supported by : Chat GPT-4o / Cursor AI
# Note : 모든 Repository의 기본 클래스
############################################

from DATABASE.dbms import DBManager


class BaseRepository:
    """모든 Repository의 기본 클래스"""
    
    def __init__(self, db_manager: DBManager):
        self.db = db_manager