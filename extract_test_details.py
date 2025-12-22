#!/usr/bin/env python3
"""테스트 파일에서 실제 입력값과 예상 결과를 추출하는 스크립트"""

import ast
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any

def get_all_tests():
    """모든 테스트 목록 추출"""
    result = subprocess.run(
        ['python', '-m', 'pytest', '--collect-only', '-q'],
        capture_output=True,
        text=True
    )
    
    tests = []
    for line in result.stdout.split('\n'):
        if '::' in line and 'test_' in line and 'ERROR' not in line and 'collected' not in line:
            tests.append(line.strip())
    
    return tests

def classify_test(test_name: str) -> str:
    """테스트를 정상계/비정상계로 분류"""
    test_func = test_name.split('::')[-1].lower()
    
    abnormal_keywords = [
        'not_found', 'none', 'empty', 'invalid', 'error', 'fail', 
        'exception', 'raise', 'mismatch', 'missing', 'disconnected',
        'no_', 'without_', 'not_', 'wrong', 'bad', 'negative', 'fails',
        'not_a_', 'different_', 'type_error', 'out_of_range', 'below',
        'exceed', 'greater_than', 'less_than', 'unhandled', 'already_has',
        'ignore_error', 'ignore_errors'
    ]
    
    normal_keywords = [
        'success', 'basic', 'init', 'get_', 'set_', 'build', 
        'compute_', 'derive_', 'equals', 'same', 'valid', 'with_',
        'suggest_', 'columns_', 'serialized_', 'loop_', 'from_enum',
        'extract_', 'to_datetime', 'to_date', 'to_float', 'to_integer',
        'to_string', 'to_boolean', 'to_time', 'container', 'by_extension',
        'since', 'by_full_name', 'name', 'full_name', 'creation_time',
        'first', 'by_creation_time', 'by_name', 'compress', 'field',
        'datetime', 'value', 'recursive', 'entry', 'condition_and',
        'condition_or', 'condition_not', 'quantize', 'analyze', 'count_',
        'different_resolution', 'set_file_name', 'to_json_file', 'get_target',
        'get_dataframe', 'get_measured', 'get_spec_analyzer', 'connect_to',
        'get_latest_created', 'make_void', 'upsert_', 'get_instrument',
        'get_base_dir', 'get_model', 'get_spec', 'get_measured_data',
        'get_serial_nos', 'get_time_series', 'get_measured_data_size',
        'get_unparsed', 'get_process_info', 'get_list_unretrieved',
        'unlock_list', 'reset_locks', 'is_db_connected', 'truncate_',
        'get_external_defects', 'on_instrument', 'on_model', 'on_spec',
        'on_measured', 'on_process', 'save_parquet', 'normalize_datetime',
        'execute_query', 'batch_upsert', 'database_maker', 'get_uniqueness',
        'is_connected', 'close', 'is_datetime_in_range', 'is_timestamp_in_range',
        'filter_sourcefiles', 'check_if_file', 'file_transfer', 'download_',
        'run_command', 'context_manager'
    ]
    
    for keyword in abnormal_keywords:
        if keyword in test_func:
            return '비정상계'
    
    for keyword in normal_keywords:
        if keyword in test_func:
            return '정상계'
    
    return '정상계'

def get_module_class(test_name: str) -> Tuple[str, str]:
    """모듈/클래스 정보 추출"""
    match = re.match(r'TEST/(test_\w+\.py)::(\w+)::(test_\w+)', test_name)
    if not match:
        return None, None
    
    file_name, class_name, test_func = match.groups()
    
    module_map = {
        'test_cust_parser': 'CUSTOMIZED.cust_parser',
        'test_cust_powershell': 'CUSTOMIZED.cust_powershell',
        'test_cust_deco_error': 'CUSTOMIZED.cust_deco_error',
        'test_cust_deco_retry': 'CUSTOMIZED.cust_deco_retry',
        'test_cust_hasher': 'CUSTOMIZED.cust_hasher',
        'test_cust_validator': 'CUSTOMIZED.cust_validator',
        'test_cust_web_helper': 'CUSTOMIZED.cust_web_helper',
        'test_cust_converter': 'CUSTOMIZED.cust_converter',
        'test_cust_iterator': 'CUSTOMIZED.cust_iterator',
        'test_cruder_vector': 'DATABASE.cruder',
        'test_cruder_master': 'DATABASE.cruder',
        'test_cruder_measured': 'DATABASE.cruder',
        'test_cruder_process': 'DATABASE.cruder',
        'test_pg_manager': 'DATABASE.pg_manager',
        'test_router_similarity': 'WEB_SERVER.routers.router_similarity',
        'test_service_similarity': 'WEB_SERVER.services.service',
        'test_spec_analyzer': 'ANALYZER.spec_analyzer',
        'test_accumulate_measured': 'ANALYZER.accumulate_measured',
        'test_ict_data_extractor': 'OPEN_SSH.ict_data_extractor',
        'test_ssh_connector': 'OPEN_SSH.ssh_connector',
        'test_file_retriever': 'data_retriever',
        'test_data_archiver': 'data_archiver',
        'test_retrier': 'CUSTOMIZED.cust_retrier',
        'test_sample': 'sample'
    }
    
    file_base = file_name.replace('test_', '').replace('.py', '')
    module = module_map.get('test_' + file_base, file_base)
    
    class_map = {
        'TestParser': 'Parser',
        'TestWhenErr': 'when.err',
        'TestPSCommand': 'PSCommand',
        'TestGetChildItem': 'Get_ChildItem',
        'TestFilter': 'Filter',
        'TestSelect': 'Select',
        'TestSort': 'Sort',
        'TestToJson': 'ToJson',
        'TestTypes': 'Types',
        'TestHandleHttpError': 'handle_http_error',
        'TestParseQueryParams': 'parse_query_params',
        'TestAsyncRetry': 'async_retry',
        'TestAsyncRetryWithRecovery': 'async_retry_with_recovery',
        'TestHasher': 'Hasher',
        'TestRaiseIf': 'Raise.If',
        'TestExport': 'Export',
        'TestSheetNameSanitizer': '_sheet_name_sanitizer',
        'TestStringConverter': 'StringConverter',
        'TestIterator': 'iterator',
        'TestCRUDerVector': 'CRUDer',
        'TestCRUDerMaster': 'CRUDer',
        'TestCRUDerMeasured': 'CRUDer',
        'TestCRUDerProcess': 'CRUDer',
        'TestDataBaseMaker': 'DataBaseMaker',
        'TestPGDBManager': 'PGDBManager',
        'TestRouterSimilarity': 'router',
        'TestServiceSimilarity': 'service',
        'TestSpecAnalyzer': 'SpecAnalyzer',
        'TestAnalyzedFileExporter': 'AnalyzedFileExporter',
        'TestMeasuredDataCollector': 'MeasuredDataCollector',
        'TestICTDataExtractor': 'ICTDataExtractor',
        'TestOpenSSHConnector': 'OpenSSHConnector',
        'TestFileRetriever': 'FileRetriever',
        'TestDataArchiver': 'DataArchiver',
        'TestRetrier': 'Retrier',
        'TestExampleClass': 'ExampleClass'
    }
    
    class_name_short = class_map.get(class_name, class_name)
    
    return module, class_name_short

def extract_test_inputs_and_expected(file_path: str, test_func_name: str) -> Tuple[str, str]:
    """테스트 파일에서 실제 입력값과 예상 결과 추출"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # AST로 파싱
        tree = ast.parse(content)
        
        # 테스트 함수 찾기
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == test_func_name:
                # 함수 본문에서 assert 문과 호출 찾기
                inputs = []
                expected = []
                
                for stmt in node.body:
                    # 함수 호출에서 인자 추출
                    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                        inputs.append(ast.unparse(stmt.value))
                    
                    # assert 문에서 예상 결과 추출
                    if isinstance(stmt, ast.Assert):
                        expected.append(ast.unparse(stmt.test))
                    
                    # 할당문에서 입력값 추출
                    if isinstance(stmt, ast.Assign):
                        if isinstance(stmt.value, ast.Call):
                            inputs.append(ast.unparse(stmt.value))
                
                # 간단한 추출: 첫 번째 호출과 첫 번째 assert
                input_str = inputs[0] if inputs else "정상 입력"
                expected_str = expected[0] if expected else "정상 결과"
                
                return input_str[:100], expected_str[:100]  # 길이 제한
    except Exception as e:
        pass
    
    return "정상 입력", "정상 결과"

def get_function_name(test_name: str) -> str:
    """기능명 추출"""
    match = re.match(r'TEST/\w+\.py::\w+::(test_\w+)', test_name)
    if not match:
        return test_name
    
    func_name = match.group(1)
    func_name = func_name.replace('test_', '').replace('_', ' ')
    return func_name

def get_description(test_name: str) -> str:
    """기능 설명 생성"""
    return get_function_name(test_name)

def format_input_value(value: str) -> str:
    """입력값 포맷팅"""
    # 너무 길면 줄임
    if len(value) > 80:
        return value[:77] + "..."
    return value

def format_expected_result(value: str) -> str:
    """예상 결과 포맷팅"""
    if len(value) > 80:
        return value[:77] + "..."
    return value

if __name__ == '__main__':
    tests = get_all_tests()
    print(f"총 테스트 수: {len(tests)}")
    
    # 테스트 파일 경로 매핑
    test_file_map = {}
    for test in tests:
        match = re.match(r'TEST/(test_\w+\.py)::', test)
        if match:
            file_name = match.group(1)
            if file_name not in test_file_map:
                test_file_map[file_name] = []
            test_file_map[file_name].append(test)
    
    print(f"테스트 파일 수: {len(test_file_map)}")

