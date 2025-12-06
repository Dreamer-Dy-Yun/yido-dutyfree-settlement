###########################################
# Module name : cust_powershell.py 
# Module class : PSCommand, GetChildItem, Types, Filter, Select
# Written by : Yun Dae-young 
# Supported by : ChatGPT-5.1
# Instructed by : -
# Created at : 2025.11.14
# Updated at : 2025.11.16
# Note : ※ Customized PowerShell Command DSL (Python에서 없는것 같아서 만듦)
#        ※ MidcroSoft에서는 Cmdlet / Provider / ScriptBlock / Formatting / Output 로 구분된다고 하나 이걸로 구분하지는 않음
#        2025.11.16 : Select 추가. 클래스 명 변경(파워셀 명령어 구조 재확인으로 인한 변경)
#        2025.11.17 : Consumer, Sort 추가
#
############################################

from __future__ import annotations
from typing import Literal, TypeAlias
from datetime import datetime
from pathlib import Path


############################################
# PSCommand Expression Factory
############################################
class PSCommand:
    """
    PowerShell 명령 전체를 구성하는 클래스.
    """
    STR_PWSH: str = "powershell -Command"
    STR_WHERE: str = "Where-Object"
    STR_SELECT: str = "Select-Object"
    STR_SORT: str = "Sort-Object"
    STR_PIPE: str = "|"

    def __init__(self):
        self._source : SourceExpr | str = ""
        self._condition : ConditionExpr | str = ""
        self._selection : SelectExpr | str = ""
        self._consumer : ConsumerExpr | str = ""
        self._sort : SortExpr | str = ""

    def set_source(self, source: SourceExpr | str) -> PSCommand:
        if isinstance(source, SourceExpr) and not source.is_built():
            raise ValueError("source is not built")
        self._source = str(source)
        return self

    def set_condition(self, condition: ConditionExpr | str) -> PSCommand:
        if isinstance(condition, ConditionExpr) and not condition.is_built():
            raise ValueError("filter is not built")
        self._condition = str(condition)
        return self
    
    def set_selection(self, selection: SelectExpr | str) -> PSCommand:
        if isinstance(selection, SelectExpr) and not selection.is_built():
            raise ValueError("selection is not built")
        self._selection = str(selection)
        return self

    def set_consumer(self, consumer: ConsumerExpr | str) -> PSCommand:
        if isinstance(consumer, ConsumerExpr) and not consumer.is_built():
            raise ValueError("consumer is not built")
        self._consumer = str(consumer)
        return self

    def set_sort(self, sort: SortExpr | str) -> PSCommand:
        if isinstance(sort, SortExpr) and not sort.is_built():
            raise ValueError("sort is not built")
        self._sort = str(sort)
        return self

    def build(self) -> str:
        if not self._source:
            raise ValueError("source must have a value")

        str_source = str(self._source)
        str_condition = str(self._condition)
        str_selection = str(self._selection)

        cmds : list[str] = []
        cmds.append(str_source)  
        if self._condition:
            cmds.append(self.STR_PIPE)
            cmds.append(self.STR_WHERE)
            cmds.append(f"{{ {str_condition} }}")  
        if self._sort:
            cmds.append(self.STR_PIPE)
            cmds.append(self.STR_SORT)
            cmds.append(self._sort)
        if self._selection:
            cmds.append(self.STR_PIPE)
            cmds.append(self.STR_SELECT)
            cmds.append(str_selection)
        if self._consumer:
            cmds.append(self.STR_PIPE)
            cmds.append(self._consumer)
        cmd : str = self.STR_PWSH + " \"" + " ".join(cmd for cmd in cmds if cmd) + "\""
        return cmd


class _CmdletExpr:
    def __init__(self, cmd: str = "") -> None:
        self._cmd : str = cmd
        self._is_built : bool = False

    def is_built(self) -> bool:
        return self._is_built

    def build(self) -> None:
        raise NotImplementedError("Subclass must implement this method")

    def __str__(self) -> str:
        return self._cmd

############################################
# Source Expression Factory
############################################
class SourceExpr(_CmdletExpr):
    # 명령어 표현식 
    # classification 용도로 사용
    def __init__(self, cmd: str = ""):
        super().__init__(cmd)
        self._cmd = cmd

############################################
# Select Expression Factory
############################################
class SelectExpr(_CmdletExpr):
    # 필드 선택 표현식 
    # classification 용도로 사용
    def __init__(self, cmd: str = ""):
        super().__init__(cmd)
        self._cmd = cmd

############################################
# Condition Expression Factory
############################################
class ConditionExpr(_CmdletExpr):
    # 조건식 표현식
    # classification 용도로 사용
    # 비교 연산자 등 사용
    def __init__(self, cmd: str):
        super().__init__(cmd)

    def build(self) -> ConditionExpr:
        self._is_built = True
        return self

    def __and__(self, other: ConditionExpr) -> ConditionExpr:
        """ & (and) """
        return ConditionExpr(f"{self._cmd} -and {other._cmd}").build()

    def __or__(self, other: ConditionExpr) -> ConditionExpr:
        """ | (or) """
        return ConditionExpr(f"{self._cmd} -or {other._cmd}").build()

    def __invert__(self) -> ConditionExpr:
        """ ~ (not) """
        return ConditionExpr(f"-not {self._cmd}").build()

    def __ge__(self, other: ConditionExpr) -> ConditionExpr:
        """ >= (이상) """
        return ConditionExpr(f"{self._cmd} -ge {other._cmd}").build()

    def __gt__(self, other: ConditionExpr) -> ConditionExpr:
        """ > (초과) """
        return ConditionExpr(f"{self._cmd} -gt {other._cmd}").build()

    def __le__(self, other: ConditionExpr) -> ConditionExpr:
        """ <= (이하) """
        return ConditionExpr(f"{self._cmd} -le {other._cmd}").build()

    def __lt__(self, other: ConditionExpr) -> ConditionExpr:
        """ < (미만) """
        return ConditionExpr(f"{self._cmd} -lt {other._cmd}").build()

    def __eq__(self, other: ConditionExpr) -> ConditionExpr:
        """ == (같음) """
        return ConditionExpr(f"{self._cmd} -eq {other._cmd}").build()

    def __ne__(self, other: ConditionExpr) -> ConditionExpr:
        """ != (같지 않음) """
        return ConditionExpr(f"{self._cmd} -ne {other._cmd}").build()

    @staticmethod
    def brkt(expr: ConditionExpr) -> ConditionExpr:
        """ ( ) """
        return ConditionExpr(f"( {expr} )").build()

############################################
# Consumer Expression Factory
############################################
class ConsumerExpr(_CmdletExpr):
    # Consumer 표현식
    # classification 용도로 사용
    def __init__(self, cmd: str = ""):
        super().__init__(cmd)


############################################
# Sort Expression Factory
############################################
class SortExpr(_CmdletExpr):
    # Sort-Object 표현식
    # classification 용도로 사용
    def __init__(self, cmd: str = ""):
        super().__init__(cmd)


############################################
# GetChildItem Factory
############################################
class Get_ChildItem(SourceExpr):
    STR_CMD = "Get-ChildItem"

    RECURSE = {
        True: "-Recurse",
        False: "",
    }

    ENTRY_TYPE = {
        "all": "",
        "file": "-File",
        "directory": "-Directory",
    }

    def __init__(self, target: str | Path):
        super().__init__()
        self._target = f"'{target}'"
        self._recurse: str = ""
        self._type: str = ""

    def entry(self, type_: Literal["file", "directory", "all"]) -> Get_ChildItem:
        self._type = self.ENTRY_TYPE[type_]
        return self

    def recursive(self, recursive: bool = True) -> Get_ChildItem:
        self._recurse = self.RECURSE[recursive]
        return self

    def build(self) -> SourceExpr:
        cmds : list[str] = []
        cmds.append(self.STR_CMD)
        cmds.append(self._target)
        cmds.append(self._recurse)
        cmds.append(self._type)
        self._cmd = " ".join(cmd for cmd in cmds if cmd)
        self._is_built = True
        result = SourceExpr(self._cmd)
        result._is_built = True
        return result

############################################
# Types Factory
############################################
class Types(ConditionExpr):
    OBJ = "$_"
    TYPE_DATETIME = "[datetime]"
    STR_DATETIME = "%Y-%m-%d %H:%M:%S.%f"   #밀리초 포함 형식

    @staticmethod
    def field(field_name: str) -> ConditionExpr:
        return ConditionExpr(f"{Types.OBJ}.{field_name}").build()

    @staticmethod
    def datetime(datetime_value: datetime) -> ConditionExpr:
        str_datetime = datetime_value.strftime(Types.STR_DATETIME)
        return ConditionExpr(f"{Types.TYPE_DATETIME}'{str_datetime}'").build()

    @staticmethod
    def value(value: str) -> ConditionExpr:
        return ConditionExpr(f"'{value}'").build()


############################################
# Filter Factory
############################################
# 이것 외에도 추가 예정. 현재는 파악이 덜 됨
class Filter(ConditionExpr):
    # WHERE-OBJECT
    DICT_TIMESTAMP_TYPE = {
        "creation": "CreationTime",
        "last_access": "LastAccessTime",
        "last_write": "LastWriteTime",
    }
    DICT_SELECT_TYPE = {
        "name": "Name ",
        "full_name": "FullName ",
        "extension": "Extension ",
        "length": "Length ",
        "creation_time": "CreationTime ",
        "last_access_time": "LastAccessTime ",
        "last_write_time": "LastWriteTime ",
    }
    TimestampType: TypeAlias = Literal["creation", "last_access", "last_write"]
    SelectType: TypeAlias = Literal["name", "full_name", "extension", "length", "creation_time", "last_access_time", "last_write_time"]

    def __init__(self, cmd: str):
        super().__init__(cmd)
        
    @staticmethod
    def by_extension(extension: str = "csv") -> ConditionExpr:
        ext = extension if extension.startswith('.') else f'.{extension}'
        return Types.field("Extension") == Types.value(ext)

    @staticmethod
    def since(datetime_since: datetime, timestamp_type: Filter.TimestampType = "creation") -> ConditionExpr:
        """ Greater than or equal (이상) """
        return Types.field(Filter.DICT_TIMESTAMP_TYPE[timestamp_type]) >= Types.datetime(datetime_since)

    @staticmethod
    def until(datetime_until: datetime, timestamp_type: Filter.TimestampType = "creation") -> ConditionExpr:
        """ Less than or equal (이하) """
        return Types.field(Filter.DICT_TIMESTAMP_TYPE[timestamp_type]) <= Types.datetime(datetime_until)

    @staticmethod
    def after(datetime_since: datetime, timestamp_type: Filter.TimestampType = "creation") -> ConditionExpr:
        """ Greater than (초과) """
        return Types.field(Filter.DICT_TIMESTAMP_TYPE[timestamp_type]) > Types.datetime(datetime_since)

    @staticmethod
    def before(datetime_until: datetime, timestamp_type: Filter.TimestampType = "creation") -> ConditionExpr:
        """ Less than (미만) """
        return Types.field(Filter.DICT_TIMESTAMP_TYPE[timestamp_type]) < Types.datetime(datetime_until)

    @staticmethod
    def between(datetime_since: datetime, datetime_until: datetime, timestamp_type: Filter.TimestampType = "creation") -> ConditionExpr:
        """ Between (datetime_since <= x <= datetime_until) """
        return Filter.since(datetime_since, timestamp_type) & Filter.until(datetime_until, timestamp_type)

    # @staticmethod
    # def matches(field_name: Filter.SelectType | str, pattern: str = r"\d{4}\\\d{2}\\\d{2}$") -> ConditionExpr:
    #     """ matches (리팩토링 필요) """
    #     return ConditionExpr(f"{{ $_.{Filter.DICT_SELECT_TYPE[field_name]} -match '{pattern}' }}").build()


############################################
# Sort-Object Factory
############################################
class Sort(SortExpr):

    OrderType: TypeAlias = Literal["asc", "desc"]

    def __init__(self, cmd: str = ""):
        super().__init__(cmd)
        self._cmds : list[str] = []

    def by_property(self, property_name: str, descending: bool = False) -> Sort:
        temp_cmds : list[str] = []
        temp_cmds.append(f"-Property '{property_name}'")
        if descending:
            temp_cmds.append("-Descending") #명령어에 -Ascending 이 따로 없음
        self._cmds.append(" ".join(temp_cmds))
        return self
    
    def by_name(self, descending: bool = False) -> Sort:
        self.by_property("Name", descending)
        return self

    def by_full_name(self, descending: bool = False) -> Sort:
        self.by_property("FullName", descending)

    def by_extension(self, descending: bool = False) -> Sort:
        self.by_property("Extension", descending)
        return self

    def by_length(self, descending: bool = False) -> Sort:
        self.by_property("Length", descending)
        return self

    def by_creation_time(self, descending: bool = False) -> Sort:
        self.by_property("CreationTime", descending)
        return self

    def by_last_access_time(self, descending: bool = False) -> Sort:
        self.by_property("LastAccessTime", descending)
        return self

    def by_last_write_time(self, descending: bool = False) -> Sort:
        self.by_property("LastWriteTime", descending)
        return self

    def build(self) -> SelectExpr:
        self._cmd = " ".join(self._cmds)
        self._is_built = True
        return self

############################################
# Select Factory
############################################
class Select(SelectExpr):
    #  Select-Object 
    STR_PROPERTY = "-Property"

    def __init__(self, cmd: str = ""):
        super().__init__(cmd)
        self._cmds_property : list[str] = []
        self._set_cmds_property : set[str] = set()
        self._cmds_count : list[str] = []
        self._set_cmds_count : set[str] = set()


    def _add_cmd_property(self, cmd: str) -> None:
        # 중복 없는 순서 보장을 위한 함수
        if not cmd in self._set_cmds_property:
            self._cmds_property.append(cmd)
            self._set_cmds_property.add(cmd)

    
    def _add_cmd_count(self, cmd: str) -> None:
        # 중복 없는 순서 보장을 위한 함수
        if not cmd in self._set_cmds_count:
            self._cmds_count.append(cmd)
            self._set_cmds_count.add(cmd)


    @staticmethod
    def _computed_property(field_name: str, alias: str | None = None, script: str | None = None) -> str:
        if script is None:
            script = f"$_.{field_name}"
        if alias is not None:
            return f"@{{ Name='{alias}'; Expression={{ {script} }}}}"
        else:
            return field_name

    @staticmethod
    def _iso8601_o_timestamp(field_name: str, alias: str | None = None, apply_iso8601: bool = False) -> str:
        script : str | None = None
        if apply_iso8601:
            script = f"$_.{field_name}.ToString('O')"
        return Select._computed_property(field_name, alias, script=script)

    @staticmethod
    def _apply_alias(field_name: str, alias: str | None = None) -> str:
        return Select._computed_property(field_name, alias, None)

    def name(self, alias: str | None = None) -> Select:
        elem :str = Select._apply_alias("Name", alias)
        self._add_cmd_property(elem)
        return self
    
    def extension(self, alias: str | None = None) -> Select:
        elem :str = Select._apply_alias("Extension", alias)
        self._add_cmd_property(elem)
        return self
    
    def full_name(self, alias: str | None = None) -> Select:
        elem :str = Select._apply_alias("FullName", alias)
        self._add_cmd_property(elem)
        return self
    
    def length(self, alias: str | None = None) -> Select:
        elem :str = Select._apply_alias("Length", alias)
        self._add_cmd_property(elem)
        return self
    
    def creation_time(self, alias: str | None = None, with_milliseconds: bool = False) -> Select:
        elem = Select._iso8601_o_timestamp("CreationTime", alias, with_milliseconds)
        self._add_cmd_property(elem)
        return self
    
    def last_access_time(self, alias: str | None = None, with_milliseconds: bool = False) -> Select:
        elem = Select._iso8601_o_timestamp("LastAccessTime", alias, with_milliseconds)
        self._add_cmd_property(elem)
        return self
    
    def last_write_time(self, alias: str | None = None, with_milliseconds: bool = False) -> Select:
        elem = Select._iso8601_o_timestamp("LastWriteTime", alias, with_milliseconds)
        self._add_cmd_property(elem)
        return self

    def first(self, count: int) -> Select:
        # 처음 count개 출력
        self._add_cmd_count(f"-First {count}")
        return self
    
    def last(self, count: int) -> Select:
        # 마지막 count개 출력
        self._add_cmd_count(f"-Last {count}")
        return self
    
    def skip(self, count: int) -> Select:
        # 앞 count개 건너뛰고 나머지 출력
        self._add_cmd_count(f"-Skip {count}")
        return self
    
    def build(self) -> Select:
        self._cmd_property = self.STR_PROPERTY + " " + ", ".join(self._cmds_property)
        self._cmd_count = " ".join(self._cmds_count)
        self._cmd = self._cmd_property + " " + self._cmd_count
        self._is_built = True
        return self

############################################
# Consumer Expression Factory
############################################
class ToJson(ConsumerExpr):
    STR_CMD = "ConvertTo-Json"
    def __init__(self, cmd: str = ""):
        super().__init__(cmd)
        self._cmds : list[str] = []

    def compress(self) -> ConsumerExpr:
        self._cmds.append(f"-Compress")
        return self
    
    def depth(self, depth: int) -> ConsumerExpr:
        self._cmds.append(f"-Depth {depth}")
        return self

    def enums_as_strings(self) -> ConsumerExpr:
        self._cmds.append(f"-EnumsAsStrings")
        return self

    def as_array(self) -> ConsumerExpr:
        self._cmds.append(f"-AsArray")
        return self
    
    def build(self) -> ConsumerExpr:
        self._cmd = self.STR_CMD + " " + " ".join(self._cmds)
        self._is_built = True
        return self

############################################
# Test
############################################
if __name__ == "__main__":
    # Find
    find_cmd = Get_ChildItem(".").entry("file").build()

    # Time Expression
    # time_condi = Filter.since(datetime.now()) & Filter.until(datetime.now())
    time_condi = Filter.after(datetime.now()) & Filter.before(datetime.now())
    extension_condi = Filter.by_extension("csv")
    selection = Select().name().extension().full_name().length().creation_time(with_milliseconds=True).last_access_time(with_milliseconds=True).last_write_time(with_milliseconds=True).build()
    full_condi = extension_condi & ConditionExpr.brkt(time_condi)
    # Wrap
    full_cmd = PSCommand().set_source(find_cmd).set_condition(full_condi).set_selection(selection).build()
    print(full_cmd)
