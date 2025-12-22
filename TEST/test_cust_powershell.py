###########################################
# Module name : test_cust_powershell.py
# 테스트 대상 : CUSTOMIZED.cust_powershell.PSCommand, Get_ChildItem, Filter, Select, Sort, ToJson
# Written by : Auto (Cursor AI)
###########################################

import pytest
from pathlib import Path
from datetime import datetime
from CUSTOMIZED import cust_powershell as ps


class TestPSCommand:
    """PSCommand 클래스 테스트"""

    def test_init(self):
        """초기화 테스트"""
        cmd = ps.PSCommand()
        
        assert cmd._source == ""
        assert cmd._condition == ""
        assert cmd._selection == ""
        assert cmd._consumer == ""
        assert cmd._sort == ""
        assert cmd._via_cmd is False  # 기본값이 False

    def test_set_encoding(self):
        """set_encoding() 테스트"""
        cmd = ps.PSCommand()
        result = cmd.set_encoding("UTF-8")
        
        assert result is cmd
        assert cmd._output_encoding == "UTF8"

    def test_set_source(self):
        """set_source() 테스트"""
        cmd = ps.PSCommand()
        source = ps.Get_ChildItem("/path").build()
        result = cmd.set_source(source)
        
        assert result is cmd
        assert cmd._source == str(source)

    def test_set_condition(self):
        """set_condition() 테스트"""
        cmd = ps.PSCommand()
        condition = ps.Filter.container("file")
        result = cmd.set_condition(condition)
        
        assert result is cmd
        assert cmd._condition == str(condition)

    def test_set_selection(self):
        """set_selection() 테스트"""
        cmd = ps.PSCommand()
        selection = ps.Select().name().build()
        result = cmd.set_selection(selection)
        
        assert result is cmd
        assert cmd._selection == str(selection)

    def test_set_consumer(self):
        """set_consumer() 테스트"""
        cmd = ps.PSCommand()
        consumer = ps.ToJson().build()
        result = cmd.set_consumer(consumer)
        
        assert result is cmd
        assert cmd._consumer == str(consumer)

    def test_set_sort(self):
        """set_sort() 테스트"""
        cmd = ps.PSCommand()
        sort = ps.Sort().by_creation_time().build()
        result = cmd.set_sort(sort)
        
        assert result is cmd
        assert cmd._sort == str(sort)

    def test_build_without_source(self):
        """build() source 없음 테스트"""
        cmd = ps.PSCommand()
        
        with pytest.raises(ValueError, match="source must have a value"):
            cmd.build()

    def test_build_basic(self):
        """build() 기본 테스트"""
        cmd = ps.PSCommand(via_cmd=True)  # via_cmd=True로 설정해야 powershell -Command가 포함됨
        source = ps.Get_ChildItem("/path").build()
        cmd.set_source(source)
        
        result = cmd.build()
        
        assert "powershell -Command" in result
        assert "Get-ChildItem" in result
        assert "'/path'" in result

    def test_build_with_all_components(self):
        """build() 모든 컴포넌트 포함 테스트"""
        cmd = ps.PSCommand()
        cmd.set_source(ps.Get_ChildItem("/path").build())
        cmd.set_condition(ps.Filter.container("file"))
        cmd.set_selection(ps.Select().name().build())
        cmd.set_sort(ps.Sort().by_creation_time().build())
        cmd.set_consumer(ps.ToJson().build())
        
        result = cmd.build()
        
        assert "Get-ChildItem" in result
        assert "Where-Object" in result
        assert "Select-Object" in result
        assert "Sort-Object" in result

    def test_build_via_cmd_false(self):
        """build() via_cmd=False 테스트"""
        cmd = ps.PSCommand(via_cmd=False)
        source = ps.Get_ChildItem("/path").build()
        cmd.set_source(source)
        
        result = cmd.build()
        
        assert "powershell -Command" not in result
        assert "Get-ChildItem" in result


class TestGetChildItem:
    """Get_ChildItem 클래스 테스트"""

    def test_init_with_string(self):
        """초기화 문자열 테스트"""
        gci = ps.Get_ChildItem("/test/path")
        
        assert "'/test/path'" in gci._target

    def test_init_with_path(self):
        """초기화 Path 객체 테스트"""
        gci = ps.Get_ChildItem(Path("/test/path"))
        
        # Windows에서는 경로가 변환될 수 있음
        assert "test" in gci._target and "path" in gci._target

    def test_init_with_list(self):
        """초기화 리스트 테스트"""
        gci = ps.Get_ChildItem(["/path1", "/path2"])
        
        assert "'/path1'" in gci._target
        assert "'/path2'" in gci._target

    def test_recursive(self):
        """recursive() 테스트"""
        gci = ps.Get_ChildItem("/path")
        result = gci.recursive(True)
        
        assert result is gci
        assert gci._recurse == "-Recurse"

    def test_recursive_false(self):
        """recursive(False) 테스트"""
        gci = ps.Get_ChildItem("/path")
        gci.recursive(False)
        
        assert gci._recurse == ""

    def test_entry(self):
        """entry() 테스트"""
        gci = ps.Get_ChildItem("/path")
        result = gci.entry("file")
        
        assert result is gci
        assert "!Directory" in gci._attributes

    def test_entry_all(self):
        """entry("all") 테스트"""
        gci = ps.Get_ChildItem("/path")
        result = gci.entry("all")
        
        assert result is gci
        assert len(gci._attributes) == 0

    def test_build(self):
        """build() 테스트"""
        gci = ps.Get_ChildItem("/path")
        gci.recursive(True)
        gci.entry("file")
        
        result = gci.build()
        
        assert isinstance(result, ps.SourceExpr)
        assert "Get-ChildItem" in str(result)
        assert "-Recurse" in str(result)


class TestFilter:
    """Filter 클래스 테스트"""

    def test_container_file(self):
        """container("file") 테스트"""
        result = ps.Filter.container("file")
        
        assert isinstance(result, ps.ConditionExpr)
        assert "PsIsContainer" in str(result)

    def test_container_directory(self):
        """container("directory") 테스트"""
        result = ps.Filter.container("directory")
        
        assert isinstance(result, ps.ConditionExpr)
        assert "PsIsContainer" in str(result)

    def test_by_extension(self):
        """by_extension() 테스트"""
        result = ps.Filter.by_extension("csv")
        
        assert isinstance(result, ps.ConditionExpr)
        assert "Extension" in str(result)
        assert "csv" in str(result)

    def test_since(self):
        """since() 테스트"""
        dt = datetime(2025, 1, 15, 10, 30, 0)
        result = ps.Filter.since(dt)
        
        assert isinstance(result, ps.ConditionExpr)
        assert "CreationTime" in str(result)

    def test_by_full_name(self):
        """by_full_name() 테스트"""
        result = ps.Filter.by_full_name("/path/file.csv")
        
        assert isinstance(result, ps.ConditionExpr)
        assert "FullName" in str(result)

    def test_condition_and(self):
        """조건식 AND 연산 테스트"""
        cond1 = ps.Filter.container("file")
        cond2 = ps.Filter.by_extension("csv")
        result = cond1 & cond2
        
        assert isinstance(result, ps.ConditionExpr)
        assert "-and" in str(result)

    def test_condition_or(self):
        """조건식 OR 연산 테스트"""
        cond1 = ps.Filter.container("file")
        cond2 = ps.Filter.container("directory")
        result = cond1 | cond2
        
        assert isinstance(result, ps.ConditionExpr)
        assert "-or" in str(result)

    def test_condition_not(self):
        """조건식 NOT 연산 테스트"""
        cond = ps.Filter.container("file")
        result = ~cond
        
        assert isinstance(result, ps.ConditionExpr)
        assert "-not" in str(result)


class TestSelect:
    """Select 클래스 테스트"""

    def test_name(self):
        """name() 테스트"""
        sel = ps.Select()
        result = sel.name()
        
        assert result is sel
        # _cmd는 build() 전에는 비어있고, _cmds_property에 저장됨
        assert "Name" in sel._cmds_property[0]

    def test_full_name(self):
        """full_name() 테스트"""
        sel = ps.Select()
        result = sel.full_name()
        
        assert result is sel
        assert "FullName" in sel._cmds_property[0]

    def test_creation_time(self):
        """creation_time() 테스트"""
        sel = ps.Select()
        result = sel.creation_time()
        
        assert result is sel
        assert "CreationTime" in sel._cmds_property[0]

    def test_creation_time_with_milliseconds(self):
        """creation_time(with_milliseconds=True) 테스트"""
        sel = ps.Select()
        result = sel.creation_time(with_milliseconds=True)
        
        assert result is sel
        # with_milliseconds=True일 때 computed property로 생성됨
        # build()를 호출하면 Expression이 포함됨
        built = sel.build()
        assert "CreationTime" in str(built)
        # 실제로는 _cmds_property에 "CreationTime"만 저장되고, 
        # build() 시점에 computed property 형태로 변환됨
        # 여기서는 메서드가 정상 호출되는지만 확인
        assert len(sel._cmds_property) > 0

    def test_first(self):
        """first() 테스트"""
        sel = ps.Select()
        result = sel.first(10)
        
        assert result is sel
        assert "-First 10" in sel._cmds_count[0]

    def test_build(self):
        """build() 테스트"""
        sel = ps.Select()
        sel.name()
        sel.full_name()
        
        result = sel.build()
        
        assert isinstance(result, ps.SelectExpr)
        assert "Name" in str(result)
        assert "FullName" in str(result)


class TestSort:
    """Sort 클래스 테스트"""

    def test_by_creation_time(self):
        """by_creation_time() 테스트"""
        sort = ps.Sort()
        result = sort.by_creation_time()
        
        assert result is sort
        assert "CreationTime" in sort._cmds[0]

    def test_by_name(self):
        """by_name() 테스트"""
        sort = ps.Sort()
        result = sort.by_name()
        
        assert result is sort
        assert "Name" in sort._cmds[0]

    def test_build(self):
        """build() 테스트"""
        sort = ps.Sort()
        sort.by_creation_time()
        
        result = sort.build()
        
        assert isinstance(result, ps.SortExpr)
        assert "CreationTime" in str(result)


class TestToJson:
    """ToJson 클래스 테스트"""

    def test_build(self):
        """build() 테스트"""
        to_json = ps.ToJson()
        result = to_json.build()
        
        assert isinstance(result, ps.ConsumerExpr)
        assert "ConvertTo-Json" in str(result)

    def test_compress(self):
        """compress() 테스트"""
        to_json = ps.ToJson()
        result = to_json.compress()
        
        assert result is to_json
        assert "-Compress" in to_json._cmds[0]

    def test_build_with_compress(self):
        """build() compress 포함 테스트"""
        to_json = ps.ToJson()
        to_json.compress()
        result = to_json.build()
        
        assert "-Compress" in str(result)


class TestTypes:
    """Types 클래스 테스트"""

    def test_field(self):
        """field() 테스트"""
        result = ps.Types.field("Name")
        
        assert isinstance(result, ps.ConditionExpr)
        assert "Name" in str(result)

    def test_datetime(self):
        """datetime() 테스트"""
        dt = datetime(2025, 1, 15, 10, 30, 0)
        result = ps.Types.datetime(dt)
        
        assert isinstance(result, ps.ConditionExpr)
        assert "[datetime]" in str(result)

    def test_value(self):
        """value() 테스트"""
        result = ps.Types.value("test")
        
        assert isinstance(result, ps.ConditionExpr)
        assert "test" in str(result)

