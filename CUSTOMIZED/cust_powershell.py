###########################################
# Module name : cust_powershell.py (ver.1.0.0)
# Module class : PSCommand, GetChildItem, Types, Filter, Select
# Written by : Yun Dae-young 
# Supported by : ChatGPT-5.1
# Instructed by : -
# Created at : 2025.11.14
# Updated at : 2025.11.16
# Note : ※ Customized PowerShell Command DSL (Python에서 없는것 같아서 만듦)
#        ※ MidcroSoft에서는 Cmdlet / Provider / ScriptBlock / Formatting / Output 로 구분된다고 하나 이걸로 구분하지는 않음
#        ※ 추가기능은 PowerShell 추가 학습함에 따라 수정/버전업 할 예정
#        ※ 버전업시에는 Get-ChildItem을 그대로 쓰는것이 아닌, Get.file(), Get.directory() 등으로 변경하고, 
#           그에 따라 허용된 명령어만 조합하는 방식으로 구현
#        2025.11.16 : Select 추가. 클래스 명 변경(파워셀 명령어 구조 재확인으로 인한 변경)
#        2025.11.17 : Consumer, Sort 추가
#        2025.11.21 : Get-ChildItem 수정 (Attributes로 변경)
#        2025.11.21 : is_built 제거
#        2025.11.28 : Encoding 추가
############################################

from __future__ import annotations
from typing import Literal, TypeAlias
from datetime import datetime
from pathlib import Path


############################################
# PSCommand Factory
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
    STR_OUTPUT_ENCODING: str = "[Console]::OutputEncoding = [System.Text.Encoding]::"

    ENCODING_TYPE = {
        "UTF-8": "UTF8",
        "Unicode": "Unicode",
        "BigEndianUnicode": "BigEndianUnicode",
        "UTF-32": "UTF32",
        "ASCII": "ASCII",
        "Default": "Default"
    }

    EncodingType: TypeAlias = Literal["UTF-8", "Unicode", "BigEndianUnicode", "UTF-32", "ASCII", "Default"]

    def __init__(self, via_cmd: bool = False):
        self._source : str = ""
        self._condition : str = ""
        self._selection : str = ""
        self._consumer : str = ""
        self._sort : str = ""
        self._via_cmd : bool = via_cmd
        self._output_encoding : str = "UTF8"

    def set_encoding(self, encoding: EncodingType = "UTF-8") -> PSCommand:
        self._output_encoding = self.ENCODING_TYPE[encoding]
        return self

    def set_source(self, source: SourceExpr | str) -> PSCommand:
        self._source = str(source)
        return self

    def set_condition(self, condition: ConditionExpr | str) -> PSCommand:
        self._condition = str(condition)
        return self
    
    def set_selection(self, selection: SelectExpr | str) -> PSCommand:
        self._selection = str(selection)
        return self

    def set_consumer(self, consumer: ConsumerExpr | str) -> PSCommand:
        self._consumer = str(consumer)
        return self

    def set_sort(self, sort: SortExpr | str) -> PSCommand:
        self._sort = str(sort)
        return self

    def build(self) -> str:
        if not self._source:
            raise ValueError("source must have a value")

        str_source = str(self._source)
        str_condition = str(self._condition)
        str_selection = str(self._selection)

        cmds : list[str] = []

        if self._output_encoding:
            cmds.append(self.STR_OUTPUT_ENCODING + self._output_encoding + "; ")

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
        cmd : str = " ".join(cmd for cmd in cmds if cmd)
        if self._via_cmd:
            cmd = cmd.replace('"', r'\"')
            cmd = f'{self.STR_PWSH} "{cmd}"'
        return cmd


class _CmdletExpr:
    def __init__(self, cmd: str = "") -> None:
        self._cmd : str = cmd

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

    def __and__(self, other: ConditionExpr) -> ConditionExpr:
        """ & (and) """
        return ConditionExpr(f"{self._cmd} -and {other._cmd}")

    def __or__(self, other: ConditionExpr) -> ConditionExpr:
        """ | (or) """
        return ConditionExpr(f"{self._cmd} -or {other._cmd}")

    def __invert__(self) -> ConditionExpr:
        """ ~ (not) """
        return ConditionExpr(f"-not ({self._cmd})")

    def __ge__(self, other: ConditionExpr) -> ConditionExpr:
        """ >= (이상) """
        return ConditionExpr(f"{self._cmd} -ge {other._cmd}")

    def __gt__(self, other: ConditionExpr) -> ConditionExpr:
        """ > (초과) """
        return ConditionExpr(f"{self._cmd} -gt {other._cmd}")

    def __le__(self, other: ConditionExpr) -> ConditionExpr:
        """ <= (이하) """
        return ConditionExpr(f"{self._cmd} -le {other._cmd}")

    def __lt__(self, other: ConditionExpr) -> ConditionExpr:
        """ < (미만) """
        return ConditionExpr(f"{self._cmd} -lt {other._cmd}")

    def __eq__(self, other: ConditionExpr) -> ConditionExpr:
        """ == (같음) """
        return ConditionExpr(f"{self._cmd} -eq {other._cmd}")

    def __ne__(self, other: ConditionExpr) -> ConditionExpr:
        """ != (같지 않음) """
        return ConditionExpr(f"{self._cmd} -ne {other._cmd}")

    @staticmethod
    def brkt(expr: ConditionExpr) -> ConditionExpr:
        """ ( ) """
        return ConditionExpr(f"( {expr} )")


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
    STR_ATTRIBUTE = "-Attributes"

    RECURSE = {
        True: "-Recurse",
        False: "",
    }

    ATTRIBUTE_TYPE = {
        "all": "",
        "file": "!Directory",
        "directory": "Directory",
        "hidden": "Hidden",
        "read_only": "ReadOnly",
        "system": "System",
        "archive": "Archive",
        "compressed": "Compressed",
        "encrypted": "Encrypted",
        "offline": "Offline",
        "sparse": "SparseFile",
        "temporary": "Temporary",
    }
    
    AttributeType: TypeAlias = Literal["all", "file", "directory", "hidden", "read_only", "system", "archive", "compressed", "encrypted", "offline", "sparse", "temporary"]

    def __init__(self, target: str | Path | list[str | Path]):
        super().__init__()
        self._target : str = ""
        if isinstance(target, list):
            self._target = ", ".join(f"'{str(t)}'" for t in target)
        else:
            self._target = f"'{str(target)}'"
        self._recurse: str = ""
        self._attributes: list[str] = []

    def entry(self, type_: AttributeType) -> Get_ChildItem:
        """
          5.0 이상 대상.
          5.0 이하는 추후 통합 예정 => 현재는 Filter.container() 사용할 것
        """
        lower_cased_type : str = type_.lower()
        if lower_cased_type == "all":
            return self
        self._attributes.append(self.ATTRIBUTE_TYPE[lower_cased_type])
        return self

    def recursive(self, recursive: bool = True) -> Get_ChildItem:
        self._recurse = self.RECURSE[recursive]
        return self

    def build(self) -> SourceExpr:
        cmds : list[str] = []
        attribute : str = ""

        cmds.append(self.STR_CMD)
        cmds.append(self._target)
        cmds.append(self._recurse)
        if self._attributes:
            attribute = self.STR_ATTRIBUTE + " " + ", ".join(self._attributes)
            cmds.append(attribute)
        self._cmd = " ".join(cmd for cmd in cmds if cmd)
        return SourceExpr(self._cmd)

############################################
# Types Factory
############################################
class Types(ConditionExpr):
    OBJ = "$_"
    TYPE_DATETIME = "[datetime]"
    STR_DATETIME = "%Y-%m-%d %H:%M:%S.%f"   #밀리초 포함 형식

    @staticmethod
    def field(field_name: str) -> ConditionExpr:
        return ConditionExpr(f"{Types.OBJ}.{field_name}")

    @staticmethod
    def datetime(datetime_value: datetime) -> ConditionExpr:
        str_datetime = datetime_value.strftime(Types.STR_DATETIME)
        return ConditionExpr(f"{Types.TYPE_DATETIME}'{str_datetime}'")

    @staticmethod
    def value(value: str) -> ConditionExpr:
        return ConditionExpr(f"'{value}'")


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
        "is_container": "PsIsContainer",
        "name": "Name",
        "full_name": "FullName",
        "extension": "Extension",
        "length": "Length",
        "creation_time": "CreationTime",
        "last_access_time": "LastAccessTime",
        "last_write_time": "LastWriteTime",
    }
    
    DICT_CONTAINER_TYPE = {
        "file": "File",
        "directory": "Directory",
        "all": "",
    }

    TimestampType: TypeAlias = Literal["creation", "last_access", "last_write"]
    SelectType: TypeAlias = Literal["name", "full_name", "extension", "length", "creation_time", "last_access_time", "last_write_time"]
    ContainerType: TypeAlias = Literal["file", "directory"]

    def __init__(self, cmd: str):
        super().__init__(cmd)
    
    @staticmethod
    def container(kind: ContainerType = "file") -> ConditionExpr:
        """PowerShell 5.0이하는 파일/폴더 선택시 이걸 사용할 것"""
        if kind == "file":
            return ~ Types.field("PsIsContainer")
        elif kind == "directory":
            return Types.field("PsIsContainer")
        else:
            return ConditionExpr("")

    @staticmethod
    def by_name(name: str, wildcard_preposision: Literal["*", "?"] | None = None, wildcard_postposition: Literal["*", "?"] | None = None) -> ConditionExpr:
        str_name : str = name
        if wildcard_preposision:
            str_name = f"{wildcard_preposision}{str_name}"
        if wildcard_postposition:
            str_name = f"{str_name}{wildcard_postposition}"
        return Types.field("Name") == Types.value(str_name)

    @staticmethod
    def by_full_name(full_name: Path) -> ConditionExpr:
        return Types.field("FullName") == Types.value(str(full_name))

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
        return self

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

    def build(self) -> SortExpr:
        self._cmd = " ".join(self._cmds)
        return SortExpr(self._cmd)

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
    
    def build(self) -> SelectExpr:
        cmd_property : str = ""
        if self._cmds_property:
            cmd_property = self.STR_PROPERTY + " " + ", ".join(self._cmds_property)
        cmd_count : str = " ".join(self._cmds_count)
        return SelectExpr(f"{cmd_property} {cmd_count}".strip())

############################################
# Consumer Expression Factory
############################################
class ToJson(ConsumerExpr):
    STR_CMD = "ConvertTo-Json"
    def __init__(self, cmd: str = ""):
        super().__init__(cmd)
        self._cmds : list[str] = []

    def compress(self) -> ToJson:
        self._cmds.append(f"-Compress")
        return self
    
    def depth(self, depth: int) -> ToJson:
        self._cmds.append(f"-Depth {depth}")
        return self

    def enums_as_strings(self) -> ToJson:
        self._cmds.append(f"-EnumsAsStrings")
        return self

    def as_array(self) -> ToJson:
        self._cmds.append(f"-AsArray")
        return self
    
    def build(self) -> ConsumerExpr:
        self._cmd = self.STR_CMD + " " + " ".join(self._cmds)
        return ConsumerExpr(self._cmd)

############################################
# Test
############################################
if __name__ == "__main__":
    # Find

    dir_source_base = Path("D:\BLIZZARD")

    cmd_source = Get_ChildItem(dir_source_base).build() # 5.0 이상 대상.
    cmd_condition = Filter.container("directory")
    cmd_selection = Select().name().build()
    cmd_consumer = ToJson().compress().build()
    cmd = PSCommand().set_source(cmd_source).set_condition(cmd_condition).set_selection(cmd_selection).set_consumer(cmd_consumer).build()

    print(cmd)
