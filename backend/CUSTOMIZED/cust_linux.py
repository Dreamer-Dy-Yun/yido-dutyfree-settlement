###########################################
# Module name : cust_linux.py 
# Module class : LinuxCommand, Find
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2025.11.13
# Updated at : 2025.11.13
# Supported by : ChatGPT-5.1
# Note : 
#        ※ 미완성. GPT가 리눅스와 파워쉘 명령어 작성 방법을 섞어 알려줘서 일단 분리해서 남겨만 둠 아마 명령어 다시 손보아야 할 듯
#        2025.11.13 : 초기 작성
############################################

# 파워쉘(powershell) 명령어 작성 클래스


from typing import Literal
from datetime import datetime
from pathlib import Path

class LinuxCommand:
    STR_LINUX : str = "linux -Command "
    def __init__(self):
        self.cmds : list[str] = []
        self.cmd : str = ""
        self.conditions: list[str] = []
        self.cmd_chain: list[str] = []  

    def or_(self, *cmds: str) -> "LinuxCommand":
        self.cmd_chain.append(f"({ ' -o '.join(cmds) })")
        return self

    def and_(self, *cmds: str) -> "LinuxCommand":
        self.cmd_chain.append(f"({ ' -a '.join(cmds) })")
        return self

    def build(self) -> str:
        full_command = self.STR_POWERSHLL + " ".join(self.cmds)
        if self.cmd_chain:
            full_command += " | " + " | ".join(self.cmd_chain)
        return full_command


class Find(LinuxCommand):
    STR_FIND : str = "find"
    DAY_TYPE : dict = {
        "older": "+",
        "on": "",
        "within": "-",
    }
    def __init__(self, target_path: Path | str):
        super().__init__()
        self.target_path = f'"{target_path}"'
        self.file_type: str = ""  


    def type_(self, type: Literal["file", "directory"]) -> "Find":
        if type == "file":
            self.file_type = "-type f"
        elif type == "directory":
            self.file_type = "-type d"
        return self


    def newer_than_modified_time(self, datetime_anchor: datetime) -> "Find":
        """수정 시간 이후의 파일 검색 (YYYY-MM-DD HH:MM:SS)"""
        formatted_time = datetime_anchor.strftime('%Y-%m-%d %H:%M:%S')
        cmd = f'-newermt '
        cmd += f'"{formatted_time}"'
        self.conditions.append(cmd)
        return self


    def modified_days(self, days: int, type_: Literal["older", "on" , "within"] = "on") -> "Find":
        """
        수정일 기준으로 파일을 검색합니다. (days)
        type_: 
            "older" : 수정된 지 days보다 오래된 대상
            "on" : 수정된 지 days 인 대상
            "within" : 수정된 지 days 이내의 대상
        예 :
            작업일 : 2025-11-13 10:00:00
            days : 7
            대상 날짜 : x
            "older" : x < 2025-11-06 
            "on" : 2025-11-05 10:00:00 < x <= 2025-11-06 10:00:00
            "within" : 2025-11-06 10:00:00 <= x < 2025-11-14 10:00:00
        """
        cmd = f"-mtime "
        cmd += self.DAY_TYPE[type_]
        cmd += f"{days}"
        self.conditions.append(cmd)
        return self

    # 기타 추후 추가

    def build(self) -> str:
        self.cmds.append(self.STR_FIND)
        self.cmds.append(self.target_path)
        self.cmds.append(self.file_type) 
        self.cmds.extend(self.conditions)  
        return super().build()


# ------------------------------------------------------------------------------------------------
# 테스트 코드
if __name__ == "__main__":
    find = Find(".", datetime.now())
    subcmd = find.type_("file").newer_than_modified_time(datetime.now()).modified_days(7).build()
    print(subcmd)






# class Op_Time():
#     def modified(self, days: int, mode: Literal["after", "before"]):
#         if mode == "after":
#             return f"+{days}"
#         elif mode == "before":
#             return f"-{days}"


# class PowerShellCommand():
#     class Find():
#         def __init__(self, dir: str):
#             self.command : str = f"find {dir}"
#         class Files(Op_Time):
#             def __init__(self):
#                 self.command : str = " -type f"
#             def path(self, path: str):
#                 self.command += f" -path '{path}'"
#             def after(self, after: datetime):
#                 self.command += f" -newermt '{after.strftime('%Y-%m-%d %H:%M:%S')}'"
#             def before(self, before: datetime):
#                 self.command += f" -oldermt '{before.strftime('%Y-%m-%d %H:%M:%S')}'"
#             def get_command(self):
#                 return self.command
