# 테스트 결과 문서

총 테스트 수: 199개 (정상계: 118개, 비정상계: 81개)

## 정상계 테스트

| 연번 | 대분류 | 중분류 | 소분류 | 기능설명 | 조작방법(입력) | 예상결과 | 실제결과 | 테스트수행자(1차) | 테스트 일시(1차) |
|------|--------|--------|--------|----------|----------------|----------|----------|-------------------|------------------|
| 1 | 정상계 | ANALYZER.accumulate_measured | MeasuredDataCollector | get dataframe target columns | collector.get_dataframe(target_columns=["measured", "model"]) | len(result.columns) == 2 | OK | OK | 2025-01-XX |
| 2 | 정상계 | ANALYZER.accumulate_measured | MeasuredDataCollector | get dataframe with data | pd.DataFrame({
            "measured": [1.0, 2.0, 3.0],
            "model": ["A", "A", "B"]
) | len(result) == 3 | OK | OK | 2025-01-XX |
| 3 | 정상계 | ANALYZER.accumulate_measured | MeasuredDataCollector | get measured column exists | pd.DataFrame({
            "measured": [1.0, 2.0, 3.0]
        }) | len(result) == 3 | OK | OK | 2025-01-XX |
| 4 | 정상계 | ANALYZER.accumulate_measured | MeasuredDataCollector | get spec analyzer data group by model | pd.DataFrame({
            "measured": [1.0, 2.0, 3.0, 4.0],
            "model": ["A", "A", ) | len(result) == 2 | OK | OK | 2025-01-XX |
| 5 | 정상계 | ANALYZER.accumulate_measured | MeasuredDataCollector | get spec analyzer data with data | pd.DataFrame({
            "measured": [1.0, 2.0, 3.0],
            "model": ["A", "A", "A"]
) | len(result) == 1 | OK | OK | 2025-01-XX |
| 6 | 정상계 | ANALYZER.accumulate_measured | MeasuredDataCollector | get success | pd.DataFrame({"measured": [1.0, 2.0, 3.0]}) | collector.directory == target_path | OK | OK | 2025-01-XX |
| 7 | 정상계 | ANALYZER.accumulate_measured | MeasuredDataCollector | get target folder list | Path("/base/path") | len(folder_list) == 3 | OK | OK | 2025-01-XX |
| 8 | 정상계 | ANALYZER.accumulate_measured | MeasuredDataCollector | get target folder list single date | Path("/base/path") | len(folder_list) == 1 | OK | OK | 2025-01-XX |
| 9 | 정상계 | ANALYZER.accumulate_measured | MeasuredDataCollector | init | date(2025, 1, 1) | collector.date_from == date(2025, 1, 1) | OK | OK | 2025-01-XX |
| 10 | 정상계 | ANALYZER.spec_analyzer | AnalyzedFileExporter | analyzed file exporter init | AnalyzedFileExporter(sample_analyzer, "test_model") | exporter.model == "test_model" | OK | OK | 2025-01-XX |
| 11 | 정상계 | ANALYZER.spec_analyzer | AnalyzedFileExporter | serialized meta data | AnalyzedFileExporter(sample_analyzer, "test_model") | isinstance(data, list) | OK | OK | 2025-01-XX |
| 12 | 정상계 | ANALYZER.spec_analyzer | AnalyzedFileExporter | serialized pmf data | AnalyzedFileExporter(sample_analyzer, "test_model") | isinstance(data, list) | OK | OK | 2025-01-XX |
| 13 | 정상계 | ANALYZER.spec_analyzer | AnalyzedFileExporter | serialized trend data | AnalyzedFileExporter(sample_analyzer, "test_model") | isinstance(data, dict) | OK | OK | 2025-01-XX |
| 14 | 정상계 | ANALYZER.spec_analyzer | AnalyzedFileExporter | serialized zero pmf data | AnalyzedFileExporter(sample_analyzer, "test_model") | isinstance(data, list) | OK | OK | 2025-01-XX |
| 15 | 정상계 | ANALYZER.spec_analyzer | AnalyzedFileExporter | to json file | AnalyzedFileExporter(sample_analyzer, "test_model") | len(files) == 1 | OK | OK | 2025-01-XX |
| 16 | 정상계 | ANALYZER.spec_analyzer | SpecAnalyzer | spec analyzer analyze | SpecAnalyzer(sample_spec, resolution=100) | result is analyzer | OK | OK | 2025-01-XX |
| 17 | 정상계 | ANALYZER.spec_analyzer | SpecAnalyzer | spec analyzer compute cpk | SpecAnalyzer(sample_spec, resolution=100) | analyzer.list_mu is not None | OK | OK | 2025-01-XX |
| 18 | 정상계 | ANALYZER.spec_analyzer | SpecAnalyzer | spec analyzer compute pmf | SpecAnalyzer(sample_spec, resolution=100) | analyzer.pmf is not None | OK | OK | 2025-01-XX |
| 19 | 정상계 | ANALYZER.spec_analyzer | SpecAnalyzer | spec analyzer count inspection outcomes | SpecAnalyzer(sample_spec, resolution=100) | analyzer.list_exceeded_usl is not None | OK | OK | 2025-01-XX |
| 20 | 정상계 | ANALYZER.spec_analyzer | SpecAnalyzer | spec analyzer init | SpecAnalyzer(sample_spec, resolution=100) | analyzer.spec is not None | OK | OK | 2025-01-XX |
| 21 | 정상계 | ANALYZER.spec_analyzer | SpecAnalyzer | spec analyzer quantize spec only | SpecAnalyzer(sample_spec, resolution=100) | analyzer.spec_quantized is not None | OK | OK | 2025-01-XX |
| 22 | 정상계 | ANALYZER.spec_analyzer | SpecAnalyzer | spec analyzer run | SpecAnalyzer(sample_spec, resolution=100) | analyzer.list_ucv is not None | OK | OK | 2025-01-XX |
| 23 | 정상계 | CUSTOMIZED.cust_converter | StringConverter | from enum with enum | TestEnum(Enum) | result == "value1" | OK | OK | 2025-01-XX |
| 24 | 정상계 | CUSTOMIZED.cust_converter | StringConverter | from enum with int enum | IntEnum(Enum) | result == 1 | OK | OK | 2025-01-XX |
| 25 | 정상계 | CUSTOMIZED.cust_converter | StringConverter | from enum with string | StringConverter.From.enum("test_string") | result == "test_string" | OK | OK | 2025-01-XX |
| 26 | 정상계 | CUSTOMIZED.cust_deco_error | parse_query_params | parse query params multiple params | test_func(date_from, date_to, resolution) | "date_from" in result | OK | OK | 2025-01-XX |
| 27 | 정상계 | CUSTOMIZED.cust_deco_error | parse_query_params | parse query params single param | parse_query_params(date_param=Parser.to_date) | isinstance(date_param, type(None)) or hasattr(date_param, 'year') | OK | OK | 2025-01-XX |
| 28 | 정상계 | CUSTOMIZED.cust_deco_retry | async_retry | async retry success after retries | async_retry(exceptions=(ValueError,) | result == "success" | OK | OK | 2025-01-XX |
| 29 | 정상계 | CUSTOMIZED.cust_deco_retry | async_retry | async retry success first attempt | async_retry(exceptions=(ValueError,) | result == "success" | OK | OK | 2025-01-XX |
| 30 | 정상계 | CUSTOMIZED.cust_deco_retry | async_retry_with_recovery | async retry with recovery success | async_retry_with_recovery(
            exceptions=(ValueError,) | result == "success" | OK | OK | 2025-01-XX |
| 31 | 정상계 | CUSTOMIZED.cust_deco_retry | async_retry_with_recovery | async retry with recovery with args | recovery_func(*args) | result == "success" | OK | OK | 2025-01-XX |
| 32 | 정상계 | CUSTOMIZED.cust_hasher | Hasher | equals same hash | tempfile.NamedTemporaryFile(mode='wb', delete=False) | hasher.equals(expected_hash) is True | OK | OK | 2025-01-XX |
| 33 | 정상계 | CUSTOMIZED.cust_hasher | Hasher | hash file large file | tempfile.NamedTemporaryFile(mode='wb', delete=False) | hasher.value == expected_hash | OK | OK | 2025-01-XX |
| 34 | 정상계 | CUSTOMIZED.cust_hasher | Hasher | hash file multiple calls | tempfile.NamedTemporaryFile(mode='wb', delete=False) | hash1 != hash2 | OK | OK | 2025-01-XX |
| 35 | 정상계 | CUSTOMIZED.cust_hasher | Hasher | hash file success | tempfile.NamedTemporaryFile(mode='wb', delete=False) | result is hasher | OK | OK | 2025-01-XX |
| 36 | 정상계 | CUSTOMIZED.cust_hasher | Hasher | hasher init | 정상 입력 | hasher._hashed_value == bytes() | OK | OK | 2025-01-XX |
| 37 | 정상계 | CUSTOMIZED.cust_hasher | Hasher | str representation | str(hasher) | isinstance(str_repr, str) | OK | OK | 2025-01-XX |
| 38 | 정상계 | CUSTOMIZED.cust_hasher | Hasher | value property | tempfile.NamedTemporaryFile(mode='wb', delete=False) | hasher.value == bytes() | OK | OK | 2025-01-XX |
| 39 | 정상계 | CUSTOMIZED.cust_iterator | iterator | loop basic | test_func(**kwargs) | call_count == 3 | OK | OK | 2025-01-XX |
| 40 | 정상계 | CUSTOMIZED.cust_iterator | iterator | loop function returns value | test_func(**kwargs) | result is None | OK | OK | 2025-01-XX |
| 41 | 정상계 | CUSTOMIZED.cust_iterator | iterator | loop with kwargs | test_func(**kwargs) | received_kwargs == {"key1": "value1", "key2": "value2"} | OK | OK | 2025-01-XX |
| 42 | 정상계 | CUSTOMIZED.cust_parser | Parser | extract numbers | Parser.extract_numbers("abc123def456") | Parser.extract_numbers("abc123def456") == "123456" | OK | OK | 2025-01-XX |
| 43 | 정상계 | CUSTOMIZED.cust_parser | Parser | ignore case | Parser.to_string("NONE", ignore_case=True) | Parser.to_string("NONE", ignore_case=True) is None | OK | OK | 2025-01-XX |
| 44 | 정상계 | CUSTOMIZED.cust_parser | Parser | to boolean basic | Parser.to_boolean("True") | Parser.to_boolean("True") is True | OK | OK | 2025-01-XX |
| 45 | 정상계 | CUSTOMIZED.cust_parser | Parser | to date basic | Parser.to_date("20250115") | result == date(2025, 1, 15) | OK | OK | 2025-01-XX |
| 46 | 정상계 | CUSTOMIZED.cust_parser | Parser | to datetime basic | Parser.to_datetime("20250115(120000) | result == datetime(2025, 1, 15, 12, 0, 0) | OK | OK | 2025-01-XX |
| 47 | 정상계 | CUSTOMIZED.cust_parser | Parser | to datetime extract numbers only | Parser.to_datetime("2025-01-15(12:00:00) | result == datetime(2025, 1, 15, 12, 0, 0) | OK | OK | 2025-01-XX |
| 48 | 정상계 | CUSTOMIZED.cust_parser | Parser | to datetime with format | Parser.to_datetime("2025-01-15 12:00:00", format_of_strdatetime="%Y-%m-%d %H:%M:%S", extract_number) | result == datetime(2025, 1, 15, 12, 0, 0) | OK | OK | 2025-01-XX |
| 49 | 정상계 | CUSTOMIZED.cust_parser | Parser | to float basic | Parser.to_float("123.45") | Parser.to_float("123.45") == 123.45 | OK | OK | 2025-01-XX |
| 50 | 정상계 | CUSTOMIZED.cust_parser | Parser | to integer basic | Parser.to_integer("123") | Parser.to_integer("123") == 123 | OK | OK | 2025-01-XX |
| 51 | 정상계 | CUSTOMIZED.cust_parser | Parser | to string basic | Parser.to_string("test") | Parser.to_string("test") == "test" | OK | OK | 2025-01-XX |
| 52 | 정상계 | CUSTOMIZED.cust_parser | Parser | to time basic | Parser.to_time("120000") | result == time(12, 0, 0) | OK | OK | 2025-01-XX |
| 53 | 정상계 | CUSTOMIZED.cust_parser | when.err | fallback success | test_func(x) | result == "one" | OK | OK | 2025-01-XX |
| 54 | 정상계 | CUSTOMIZED.cust_parser | when.err | return success | test_func(x) | result == 10 | OK | OK | 2025-01-XX |
| 55 | 정상계 | CUSTOMIZED.cust_powershell | Filter | by extension | ps.Filter.by_extension("csv") | isinstance(result, ps.ConditionExpr) | OK | OK | 2025-01-XX |
| 56 | 정상계 | CUSTOMIZED.cust_powershell | Filter | by full name | ps.Filter.by_full_name("/path/file.csv") | isinstance(result, ps.ConditionExpr) | OK | OK | 2025-01-XX |
| 57 | 정상계 | CUSTOMIZED.cust_powershell | Filter | condition and | ps.Filter.container("file") | isinstance(result, ps.ConditionExpr) | OK | OK | 2025-01-XX |
| 58 | 정상계 | CUSTOMIZED.cust_powershell | Filter | condition not | ps.Filter.container("file") | isinstance(result, ps.ConditionExpr) | OK | OK | 2025-01-XX |
| 59 | 정상계 | CUSTOMIZED.cust_powershell | Filter | condition or | ps.Filter.container("file") | isinstance(result, ps.ConditionExpr) | OK | OK | 2025-01-XX |
| 60 | 정상계 | CUSTOMIZED.cust_powershell | Filter | container directory | 정상 입력 | 정상 결과 | OK | OK | 2025-01-XX |
| 61 | 정상계 | CUSTOMIZED.cust_powershell | Filter | container file | 정상 입력 | 정상 결과 | OK | OK | 2025-01-XX |
| 62 | 정상계 | CUSTOMIZED.cust_powershell | Filter | since | datetime(2025, 1, 15, 10, 30, 0) | isinstance(result, ps.ConditionExpr) | OK | OK | 2025-01-XX |
| 63 | 정상계 | CUSTOMIZED.cust_powershell | Get_ChildItem | build | ps.Get_ChildItem("/path") | isinstance(result, ps.SourceExpr) | OK | OK | 2025-01-XX |
| 64 | 정상계 | CUSTOMIZED.cust_powershell | Get_ChildItem | entry | ps.Get_ChildItem("/path") | result is gci | OK | OK | 2025-01-XX |
| 65 | 정상계 | CUSTOMIZED.cust_powershell | Get_ChildItem | entry all | 정상 입력 | 정상 결과 | OK | OK | 2025-01-XX |
| 66 | 정상계 | CUSTOMIZED.cust_powershell | Get_ChildItem | init with list | ps.Get_ChildItem(["/path1", "/path2"]) | "'/path1'" in gci._target | OK | OK | 2025-01-XX |
| 67 | 정상계 | CUSTOMIZED.cust_powershell | Get_ChildItem | init with path | ps.Get_ChildItem(Path("/test/path") | "test" in gci._target and "path" in gci._target | OK | OK | 2025-01-XX |
| 68 | 정상계 | CUSTOMIZED.cust_powershell | Get_ChildItem | init with string | ps.Get_ChildItem("/test/path") | "'/test/path'" in gci._target | OK | OK | 2025-01-XX |
| 69 | 정상계 | CUSTOMIZED.cust_powershell | Get_ChildItem | recursive | ps.Get_ChildItem("/path") | result is gci | OK | OK | 2025-01-XX |
| 70 | 정상계 | CUSTOMIZED.cust_powershell | Get_ChildItem | recursive false | ps.Get_ChildItem("/path") | gci._recurse == "" | OK | OK | 2025-01-XX |
| 71 | 정상계 | CUSTOMIZED.cust_powershell | PSCommand | build basic | ps.PSCommand(via_cmd=True) | "powershell -Command" in result | OK | OK | 2025-01-XX |
| 72 | 정상계 | CUSTOMIZED.cust_powershell | PSCommand | build via cmd false | ps.PSCommand(via_cmd=False) | "powershell -Command" not in result | OK | OK | 2025-01-XX |
| 73 | 정상계 | CUSTOMIZED.cust_powershell | PSCommand | build with all components | cmd.set_source(ps.Get_ChildItem("/path") | "Get-ChildItem" in result | OK | OK | 2025-01-XX |
| 74 | 정상계 | CUSTOMIZED.cust_powershell | PSCommand | init | 정상 입력 | cmd._source == "" | OK | OK | 2025-01-XX |
| 75 | 정상계 | CUSTOMIZED.cust_powershell | PSCommand | set condition | ps.Filter.container("file") | result is cmd | OK | OK | 2025-01-XX |
| 76 | 정상계 | CUSTOMIZED.cust_powershell | PSCommand | set consumer | cmd.set_consumer(consumer) | result is cmd | OK | OK | 2025-01-XX |
| 77 | 정상계 | CUSTOMIZED.cust_powershell | PSCommand | set encoding | cmd.set_encoding("UTF-8") | result is cmd | OK | OK | 2025-01-XX |
| 78 | 정상계 | CUSTOMIZED.cust_powershell | PSCommand | set selection | cmd.set_selection(selection) | result is cmd | OK | OK | 2025-01-XX |
| 79 | 정상계 | CUSTOMIZED.cust_powershell | PSCommand | set sort | cmd.set_sort(sort) | result is cmd | OK | OK | 2025-01-XX |
| 80 | 정상계 | CUSTOMIZED.cust_powershell | PSCommand | set source | ps.Get_ChildItem("/path") | result is cmd | OK | OK | 2025-01-XX |
| 81 | 정상계 | CUSTOMIZED.cust_powershell | Select | build | ps.Get_ChildItem("/path") | isinstance(result, ps.SourceExpr) | OK | OK | 2025-01-XX |
| 82 | 정상계 | CUSTOMIZED.cust_powershell | Select | creation time | 정상 입력 | result is sel | OK | OK | 2025-01-XX |
| 83 | 정상계 | CUSTOMIZED.cust_powershell | Select | creation time with milliseconds | sel.creation_time(with_milliseconds=True) | result is sel | OK | OK | 2025-01-XX |
| 84 | 정상계 | CUSTOMIZED.cust_powershell | Select | first | sel.first(10) | result is sel | OK | OK | 2025-01-XX |
| 85 | 정상계 | CUSTOMIZED.cust_powershell | Select | full name | 정상 입력 | result is sel | OK | OK | 2025-01-XX |
| 86 | 정상계 | CUSTOMIZED.cust_powershell | Select | name | 정상 입력 | result is sel | OK | OK | 2025-01-XX |
| 87 | 정상계 | CUSTOMIZED.cust_powershell | Sort | build | ps.Get_ChildItem("/path") | isinstance(result, ps.SourceExpr) | OK | OK | 2025-01-XX |
| 88 | 정상계 | CUSTOMIZED.cust_powershell | Sort | by creation time | 정상 입력 | result is sort | OK | OK | 2025-01-XX |
| 89 | 정상계 | CUSTOMIZED.cust_powershell | Sort | by name | 정상 입력 | result is sort | OK | OK | 2025-01-XX |
| 90 | 정상계 | CUSTOMIZED.cust_powershell | ToJson | build | ps.Get_ChildItem("/path") | isinstance(result, ps.SourceExpr) | OK | OK | 2025-01-XX |
| 91 | 정상계 | CUSTOMIZED.cust_powershell | ToJson | build with compress | str(result) | "-Compress" in str(result) | OK | OK | 2025-01-XX |
| 92 | 정상계 | CUSTOMIZED.cust_powershell | ToJson | compress | 정상 입력 | result is to_json | OK | OK | 2025-01-XX |
| 93 | 정상계 | CUSTOMIZED.cust_powershell | Types | datetime | datetime(2025, 1, 15, 10, 30, 0) | isinstance(result, ps.ConditionExpr) | OK | OK | 2025-01-XX |
| 94 | 정상계 | CUSTOMIZED.cust_powershell | Types | field | ps.Types.field("Name") | isinstance(result, ps.ConditionExpr) | OK | OK | 2025-01-XX |
| 95 | 정상계 | CUSTOMIZED.cust_powershell | Types | value | ps.Types.value("test") | isinstance(result, ps.ConditionExpr) | OK | OK | 2025-01-XX |
| 96 | 정상계 | CUSTOMIZED.cust_retrier | Retrier | retry calls on retry callback | ValueError("Always fails") | on_retry_called is True | OK | OK | 2025-01-XX |
| 97 | 정상계 | CUSTOMIZED.cust_retrier | Retrier | retry delay increases exponentially | call_times.append(asyncio.get_event_loop() | 0.09 < first_interval < 0.15  # jitter 없이 약 0.1초 | OK | OK | 2025-01-XX |
| 98 | 정상계 | CUSTOMIZED.cust_retrier | Retrier | retry success on first attempt | Retrier.retry(success_func, attempts=3) | result == "success" | OK | OK | 2025-01-XX |
| 99 | 정상계 | CUSTOMIZED.cust_retrier | Retrier | retry with return value | Retrier.retry(return_number) | result == 42 | OK | OK | 2025-01-XX |
| 100 | 정상계 | CUSTOMIZED.cust_web_helper | Export | as excel dataframe | pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"]
        }) | isinstance(result, StreamingResponse) | OK | OK | 2025-01-XX |
| 101 | 정상계 | CUSTOMIZED.cust_web_helper | Export | as excel dict dataframes | pd.DataFrame({"col1": [1, 2, 3]}) | isinstance(result, StreamingResponse) | OK | OK | 2025-01-XX |
| 102 | 정상계 | CUSTOMIZED.cust_web_helper | _sheet_name_sanitizer | get basic | sanitizer.get("Sheet1") | result == "Sheet1" | OK | OK | 2025-01-XX |
| 103 | 정상계 | CUSTOMIZED.cust_web_helper | _sheet_name_sanitizer | get quotes | sanitizer.get("'Sheet1'") | result == "Sheet1" | OK | OK | 2025-01-XX |
| 104 | 정상계 | CUSTOMIZED.cust_web_helper | _sheet_name_sanitizer | set used sheet names | sanitizer.set_used_sheet_names(["Sheet1", "Sheet2"]) | result == "Sheet1_(1)" | OK | OK | 2025-01-XX |
| 105 | 정상계 | OPEN_SSH.ict_data_extractor | ICTDataExtractor | columns for measured | isinstance(result, set) | isinstance(result, set) | OK | OK | 2025-01-XX |
| 106 | 정상계 | OPEN_SSH.ict_data_extractor | ICTDataExtractor | columns for spec | isinstance(result, set) | isinstance(result, set) | OK | OK | 2025-01-XX |
| 107 | 정상계 | OPEN_SSH.ict_data_extractor | ICTDataExtractor | derive d spec | ICTDataExtractor.derive_d_spec(100.0, 50.0) | result == 25.0  # (100 - 50) / 2 | OK | OK | 2025-01-XX |
| 108 | 정상계 | OPEN_SSH.ict_data_extractor | ICTDataExtractor | derive lcv | ICTDataExtractor.derive_lcv(75.0, 25.0, adjustment_factor=10.0) | result == -175.0  # 75.0 - (25.0 * 10.0) | OK | OK | 2025-01-XX |
| 109 | 정상계 | OPEN_SSH.ict_data_extractor | ICTDataExtractor | derive u spec | ICTDataExtractor.derive_u_spec(100.0, 50.0) | result == 75.0  # (100 + 50) / 2 | OK | OK | 2025-01-XX |
| 110 | 정상계 | OPEN_SSH.ict_data_extractor | ICTDataExtractor | derive ucv | ICTDataExtractor.derive_ucv(75.0, 25.0, adjustment_factor=10.0) | result == 325.0  # 75.0 + (25.0 * 10.0) | OK | OK | 2025-01-XX |
| 111 | 정상계 | OPEN_SSH.ict_data_extractor | ICTDataExtractor | derive visual scale | ICTDataExtractor.derive_visual_scale(100.0, 0.0, scale_factor=10.0) | result == 0.1  # 10.0 / (100.0 - 0.0) | OK | OK | 2025-01-XX |
| 112 | 정상계 | OPEN_SSH.ict_data_extractor | ICTDataExtractor | get essential column indexes success | extractor._get_essential_column_indexes(df, essential_columns) | result == [0, 1, 2] | OK | OK | 2025-01-XX |
| 113 | 정상계 | OPEN_SSH.ict_data_extractor | ICTDataExtractor | get with mock file | Path("/test/path.csv") | result is extractor | OK | OK | 2025-01-XX |
| 114 | 정상계 | OPEN_SSH.ict_data_extractor | ICTDataExtractor | init | Path("") | extractor.data_path == Path("") | OK | OK | 2025-01-XX |
| 115 | 정상계 | OPEN_SSH.ict_data_extractor | ICTDataExtractor | suggest file name measured | datetime(2025, 1, 15, 10, 30, 0) | "inst1" in result | OK | OK | 2025-01-XX |
| 116 | 정상계 | OPEN_SSH.ict_data_extractor | ICTDataExtractor | suggest file name spec | datetime(2025, 1, 15, 10, 30, 0) | "inst1" in result | OK | OK | 2025-01-XX |
| 117 | 정상계 | Unknown | Unknown | TEST/test_sample.py::test_example_sum | 정상 입력 | result == 3 | OK | OK | 2025-01-XX |
| 118 | 정상계 | sample | ExampleClass | value is ten | pytest.main([__file__, "-v"]) | self.value == 10 | OK | OK | 2025-01-XX |

## 비정상계 테스트

| 연번 | 대분류 | 중분류 | 소분류 | 기능설명 | 조작방법(입력) | 예상결과 | 실제결과 | 테스트수행자(1차) | 테스트 일시(1차) |
|------|--------|--------|--------|----------|----------------|----------|----------|-------------------|------------------|
| 1 | 비정상계 | ANALYZER.accumulate_measured | MeasuredDataCollector | get dataframe empty | 정상 입력 | result.empty | OK | OK | 2025-01-XX |
| 2 | 비정상계 | ANALYZER.accumulate_measured | MeasuredDataCollector | get directory not found | Path("/non/existent/path") | 정상 결과 | OK | OK | 2025-01-XX |
| 3 | 비정상계 | ANALYZER.accumulate_measured | MeasuredDataCollector | get measured column not exists | pd.DataFrame({
            "other": [1.0, 2.0, 3.0]
        }) | result.empty | OK | OK | 2025-01-XX |
| 4 | 비정상계 | ANALYZER.accumulate_measured | MeasuredDataCollector | get no parquet files | Path("/test/path") | collector.raw_data.empty | OK | OK | 2025-01-XX |
| 5 | 비정상계 | ANALYZER.accumulate_measured | MeasuredDataCollector | get spec analyzer data empty | 정상 입력 | result == [] | OK | OK | 2025-01-XX |
| 6 | 비정상계 | ANALYZER.accumulate_measured | MeasuredDataCollector | get spec analyzer data no group | pd.DataFrame({
            "measured": [1.0, 2.0, 3.0]
        }) | len(result) == 1 | OK | OK | 2025-01-XX |
| 7 | 비정상계 | ANALYZER.accumulate_measured | MeasuredDataCollector | get target folder list empty dates | Path("/base/path") | folder_list == [] | OK | OK | 2025-01-XX |
| 8 | 비정상계 | ANALYZER.spec_analyzer | AnalyzedFileExporter | raise error if file name not set | AnalyzedFileExporter(sample_analyzer, "test_model") | 정상 결과 | OK | OK | 2025-01-XX |
| 9 | 비정상계 | ANALYZER.spec_analyzer | AnalyzedFileExporter | set file name without extension | AnalyzedFileExporter(sample_analyzer, "test_model") | result == exporter.file_name_without_extension | OK | OK | 2025-01-XX |
| 10 | 비정상계 | ANALYZER.spec_analyzer | SpecAnalyzer | spec analyzer analyze dimension mismatch | SpecAnalyzer(sample_spec, resolution=100) | 정상 결과 | OK | OK | 2025-01-XX |
| 11 | 비정상계 | ANALYZER.spec_analyzer | SpecAnalyzer | spec analyzer different resolution | SpecAnalyzer(sample_spec, resolution=200) | analyzer.resolution == 200 | OK | OK | 2025-01-XX |
| 12 | 비정상계 | CUSTOMIZED.cust_converter | StringConverter | from enum with different enums | StatusEnum(Enum) | 정상 결과 | OK | OK | 2025-01-XX |
| 13 | 비정상계 | CUSTOMIZED.cust_deco_error | handle_http_error | handle http error general exception | RuntimeError("internal error") | exc_info.value.status_code == 500 | OK | OK | 2025-01-XX |
| 14 | 비정상계 | CUSTOMIZED.cust_deco_error | handle_http_error | handle http error success | test_handle_http_error_value_error(self) | result == {"status": "success"} | OK | OK | 2025-01-XX |
| 15 | 비정상계 | CUSTOMIZED.cust_deco_error | handle_http_error | handle http error value error | ValueError("validation error") | exc_info.value.status_code == 422 | OK | OK | 2025-01-XX |
| 16 | 비정상계 | CUSTOMIZED.cust_deco_error | parse_query_params | parse query params invalid value | parse_query_params(date_param=Parser.to_date) | exc_info.value.status_code == 422 | OK | OK | 2025-01-XX |
| 17 | 비정상계 | CUSTOMIZED.cust_deco_error | parse_query_params | parse query params none value | parse_query_params(date_param=Parser.to_date) | result["date"] is None | OK | OK | 2025-01-XX |
| 18 | 비정상계 | CUSTOMIZED.cust_deco_retry | async_retry | async retry fails after max attempts | async_retry(exceptions=(ValueError,) | call_count == 3 | OK | OK | 2025-01-XX |
| 19 | 비정상계 | CUSTOMIZED.cust_deco_retry | async_retry | async retry ignores other exceptions | async_retry(exceptions=(ValueError,) | 정상 결과 | OK | OK | 2025-01-XX |
| 20 | 비정상계 | CUSTOMIZED.cust_deco_retry | async_retry_with_recovery | async retry with recovery no args | async_retry_with_recovery(
            exceptions=(ValueError,) | result == "success" | OK | OK | 2025-01-XX |
| 21 | 비정상계 | CUSTOMIZED.cust_hasher | Hasher | equals different hash | tempfile.NamedTemporaryFile(mode='wb', delete=False) | hasher.equals(different_hash) is False | OK | OK | 2025-01-XX |
| 22 | 비정상계 | CUSTOMIZED.cust_hasher | Hasher | equals empty hash | hasher.equals(bytes() | hasher.equals(bytes()) is True | OK | OK | 2025-01-XX |
| 23 | 비정상계 | CUSTOMIZED.cust_hasher | Hasher | equals type error | tempfile.NamedTemporaryFile(mode='wb', delete=False) | 정상 결과 | OK | OK | 2025-01-XX |
| 24 | 비정상계 | CUSTOMIZED.cust_hasher | Hasher | hash file empty file | tempfile.NamedTemporaryFile(mode='wb', delete=False) | hasher.value == expected_hash | OK | OK | 2025-01-XX |
| 25 | 비정상계 | CUSTOMIZED.cust_hasher | Hasher | hash file not a file | Path(tempfile.gettempdir() | 정상 결과 | OK | OK | 2025-01-XX |
| 26 | 비정상계 | CUSTOMIZED.cust_hasher | Hasher | hash file not a file ignore errors | Path(tempfile.gettempdir() | result is hasher | OK | OK | 2025-01-XX |
| 27 | 비정상계 | CUSTOMIZED.cust_hasher | Hasher | hash file not found | Path("/non/existent/file.txt") | result is hasher | OK | OK | 2025-01-XX |
| 28 | 비정상계 | CUSTOMIZED.cust_hasher | Hasher | hash file not found raise | Path("/non/existent/file.txt") | 정상 결과 | OK | OK | 2025-01-XX |
| 29 | 비정상계 | CUSTOMIZED.cust_iterator | iterator | loop empty list | test_func(**kwargs) | call_count == 0 | OK | OK | 2025-01-XX |
| 30 | 비정상계 | CUSTOMIZED.cust_parser | Parser | none values custom | Parser.to_string("N/A", none_values=["N/A"]) | Parser.to_string("N/A", none_values=["N/A"]) is None | OK | OK | 2025-01-XX |
| 31 | 비정상계 | CUSTOMIZED.cust_parser | Parser | to boolean none value | Parser.to_boolean(None) | Parser.to_boolean(None) is None | OK | OK | 2025-01-XX |
| 32 | 비정상계 | CUSTOMIZED.cust_parser | Parser | to date ignore error | Parser.to_date("invalid", ignore_error=True) | result is None | OK | OK | 2025-01-XX |
| 33 | 비정상계 | CUSTOMIZED.cust_parser | Parser | to date none value | Parser.to_date(None) | Parser.to_date(None) is None | OK | OK | 2025-01-XX |
| 34 | 비정상계 | CUSTOMIZED.cust_parser | Parser | to datetime ignore error | Parser.to_datetime("invalid", ignore_error=True) | result is None | OK | OK | 2025-01-XX |
| 35 | 비정상계 | CUSTOMIZED.cust_parser | Parser | to datetime none value | Parser.to_datetime(None) | Parser.to_datetime(None) is None | OK | OK | 2025-01-XX |
| 36 | 비정상계 | CUSTOMIZED.cust_parser | Parser | to float ignore error | Parser.to_float("invalid", ignore_error=True) | result is None | OK | OK | 2025-01-XX |
| 37 | 비정상계 | CUSTOMIZED.cust_parser | Parser | to float none value | Parser.to_float(None) | Parser.to_float(None) is None | OK | OK | 2025-01-XX |
| 38 | 비정상계 | CUSTOMIZED.cust_parser | Parser | to integer ignore error | Parser.to_integer("invalid", ignore_error=True) | result is None | OK | OK | 2025-01-XX |
| 39 | 비정상계 | CUSTOMIZED.cust_parser | Parser | to integer none value | Parser.to_integer(None) | Parser.to_integer(None) is None | OK | OK | 2025-01-XX |
| 40 | 비정상계 | CUSTOMIZED.cust_parser | Parser | to string none value | Parser.to_string(None) | Parser.to_string(None) is None | OK | OK | 2025-01-XX |
| 41 | 비정상계 | CUSTOMIZED.cust_parser | Parser | to time none value | Parser.to_time(None) | Parser.to_time(None) is None | OK | OK | 2025-01-XX |
| 42 | 비정상계 | CUSTOMIZED.cust_parser | when.err | fallback not in dict | test_func(x) | result == 2 | OK | OK | 2025-01-XX |
| 43 | 비정상계 | CUSTOMIZED.cust_parser | when.err | return exception | test_func(x) | result == "default" | OK | OK | 2025-01-XX |
| 44 | 비정상계 | CUSTOMIZED.cust_parser | when.err | return none default | test_func(x) | result is None | OK | OK | 2025-01-XX |
| 45 | 비정상계 | CUSTOMIZED.cust_powershell | PSCommand | build without source | pytest.raises(ValueError, match="source must have a value") | 정상 결과 | OK | OK | 2025-01-XX |
| 46 | 비정상계 | CUSTOMIZED.cust_retrier | Retrier | retry fails after max attempts | ValueError("Always fails") | on_retry_called is True | OK | OK | 2025-01-XX |
| 47 | 비정상계 | CUSTOMIZED.cust_retrier | Retrier | retry success after failures | ValueError("Temporary failure") | result == "success" | OK | OK | 2025-01-XX |
| 48 | 비정상계 | CUSTOMIZED.cust_retrier | Retrier | retry with exception type | ValueError("First error") | result == "success" | OK | OK | 2025-01-XX |
| 49 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | below custom value name | Raise.If.below(3.0, 5.0, "custom_name") | "custom_name" in str(e) | OK | OK | 2025-01-XX |
| 50 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | below default value name | pytest.raises(ValueError, match="◈Below Minimum◈") | 정상 결과 | OK | OK | 2025-01-XX |
| 51 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | below error message | Raise.If.below(3.0, 5.0, "my_value") | "my_value" in str(e) | OK | OK | 2025-01-XX |
| 52 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | below negative values | Raise.If.below(0.0, -5.0, "test_value") | result == 0.0 | OK | OK | 2025-01-XX |
| 53 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | below value equal minimum | Raise.If.below(5.0, 5.0, "test_value") | result == 5.0 | OK | OK | 2025-01-XX |
| 54 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | below value greater than minimum | Raise.If.below(10.0, 5.0, "test_value") | result == 10.0 | OK | OK | 2025-01-XX |
| 55 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | below value less than minimum | pytest.raises(ValueError, match="◈Below Minimum◈") | 정상 결과 | OK | OK | 2025-01-XX |
| 56 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | empty bool false | Raise.If.empty(False, "test_variable") | result is False | OK | OK | 2025-01-XX |
| 57 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | empty bool true | Raise.If.empty(True, "test_variable") | result is True | OK | OK | 2025-01-XX |
| 58 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | empty datetime | datetime(2025, 1, 15, 10, 0, 0) | result == dt | OK | OK | 2025-01-XX |
| 59 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | empty empty dict | pytest.raises(ValueError, match="◈Empty Value◈") | 정상 결과 | OK | OK | 2025-01-XX |
| 60 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | empty empty list | pytest.raises(ValueError, match="◈Empty Value◈") | 정상 결과 | OK | OK | 2025-01-XX |
| 61 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | empty empty set | pytest.raises(ValueError, match="◈Empty Value◈") | 정상 결과 | OK | OK | 2025-01-XX |
| 62 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | empty empty string | pytest.raises(ValueError, match="◈Empty Value◈") | 정상 결과 | OK | OK | 2025-01-XX |
| 63 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | empty none | pytest.raises(ValueError, match="◈None Value◈") | 정상 결과 | OK | OK | 2025-01-XX |
| 64 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | empty unhandled type | pytest.raises(ValueError, match="◈Unhandled type◈") | 정상 결과 | OK | OK | 2025-01-XX |
| 65 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | empty valid dict | Raise.If.empty({"key": "value"}, "test_variable") | result == {"key": "value"} | OK | OK | 2025-01-XX |
| 66 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | empty valid list | Raise.If.empty([1, 2, 3], "test_variable") | result == [1, 2, 3] | OK | OK | 2025-01-XX |
| 67 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | empty valid string | Raise.If.empty("valid string", "test_variable") | result == "valid string" | OK | OK | 2025-01-XX |
| 68 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | empty variable name | Raise.If.empty(None, "my_variable") | "my_variable" in str(e) | OK | OK | 2025-01-XX |
| 69 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | exceed error message | Raise.If.exceed(15.0, 10.0) | "15.0" in str(e) | OK | OK | 2025-01-XX |
| 70 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | exceed negative values | Raise.If.exceed(-5.0, 0.0) | result == -5.0 | OK | OK | 2025-01-XX |
| 71 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | exceed value equal maximum | Raise.If.exceed(10.0, 10.0) | result == 10.0 | OK | OK | 2025-01-XX |
| 72 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | exceed value greater than maximum | pytest.raises(ValueError, match="◈Exceeded value◈") | 정상 결과 | OK | OK | 2025-01-XX |
| 73 | 비정상계 | CUSTOMIZED.cust_validator | Raise.If | exceed value less than maximum | Raise.If.exceed(5.0, 10.0) | result == 5.0 | OK | OK | 2025-01-XX |
| 74 | 비정상계 | CUSTOMIZED.cust_web_helper | Export | as excel invalid type | pytest.raises(ValueError, match="Invalid DataFrame Type") | 정상 결과 | OK | OK | 2025-01-XX |
| 75 | 비정상계 | CUSTOMIZED.cust_web_helper | _sheet_name_sanitizer | get duplicate names | sanitizer.get("Sheet1") | result1 == "Sheet1" | OK | OK | 2025-01-XX |
| 76 | 비정상계 | CUSTOMIZED.cust_web_helper | _sheet_name_sanitizer | get empty string | sanitizer.get("") | result == "Sheet" | OK | OK | 2025-01-XX |
| 77 | 비정상계 | CUSTOMIZED.cust_web_helper | _sheet_name_sanitizer | get invalid chars | sanitizer.get("Sheet:1/2?3*4[5]6'7") | ":" not in result | OK | OK | 2025-01-XX |
| 78 | 비정상계 | CUSTOMIZED.cust_web_helper | _sheet_name_sanitizer | get max length | sanitizer.get(long_name) | len(result) <= 31 | OK | OK | 2025-01-XX |
| 79 | 비정상계 | CUSTOMIZED.cust_web_helper | _sheet_name_sanitizer | get whitespace | sanitizer.get("  Sheet1  ") | result == "Sheet1" | OK | OK | 2025-01-XX |
| 80 | 비정상계 | OPEN_SSH.ict_data_extractor | ICTDataExtractor | get already has data | pd.DataFrame({"col1": [1, 2, 3]}) | result is extractor | OK | OK | 2025-01-XX |
| 81 | 비정상계 | OPEN_SSH.ict_data_extractor | ICTDataExtractor | get essential column indexes missing column | pd.DataFrame({
            "index": [1, 2, 3],
            "Part_Name": ["part1", "part2", "p) | 정상 결과 | OK | OK | 2025-01-XX |
