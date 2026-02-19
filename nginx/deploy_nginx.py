#!/usr/bin/env python3
"""
Nginx 설정 파일 생성 스크립트
환경 변수를 사용하여 Nginx 설정 파일을 동적으로 생성
"""

import os
import re
import sys
import subprocess
from pathlib import Path


def load_env_file(env_file: Path) -> dict:
    """환경 변수 파일 로드"""
    env_vars = {}
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 주석이나 빈 줄 무시
                if not line or line.startswith('#'):
                    continue
                # KEY=VALUE 형식 파싱
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


def substitute_variables(template: str, env_vars: dict) -> str:
    """템플릿에서 환경 변수 치환"""
    result = template
    
    # %{VAR:-default}% 형식 처리
    def replace_with_default(match):
        var_expr = match.group(1)
        if ':-' in var_expr:
            var_name, default = var_expr.split(':-', 1)
            return env_vars.get(var_name, default)
        else:
            return env_vars.get(var_expr, '')
    
    # %{VAR}% 또는 %{VAR:-default}% 형식 치환
    result = re.sub(r'%\{([^}]+)\}%', replace_with_default, result)
    
    return result


def main():
    """메인 함수"""
    # 스크립트가 있는 디렉토리
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # 환경 변수 파일 로드
    env_file = script_dir / "nginx.env"
    env_vars = {}
    
    if env_file.exists():
        env_vars = load_env_file(env_file)
        # 환경 변수를 os.environ에도 설정
        for key, value in env_vars.items():
            os.environ[key] = value
    else:
        print("경고: nginx.env 파일이 없습니다. 기본값을 사용합니다.")
        print("nginx.env.example을 참고하여 nginx.env 파일을 생성하세요.")
    
    # 템플릿 파일 읽기
    template_file = script_dir / "nginx.conf.template"
    if not template_file.exists():
        print("오류: nginx.conf.template 파일을 찾을 수 없습니다.")
        exit(1)
    
    with open(template_file, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # 환경 변수 치환
    result = substitute_variables(template, env_vars)
    
    # 생성된 설정 파일 저장
    output_file = script_dir / "nginx.conf.generated"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"Nginx 설정 파일이 생성되었습니다: {output_file}")
    print()
    
    # 자동 적용 옵션 확인
    auto_apply = '--apply' in sys.argv or '-a' in sys.argv
    
    if auto_apply:
        apply_nginx_config(output_file, env_vars.get('NGINX_PROJECT_NAME', 'your-project'))
    else:
        print("다음 명령어로 Nginx 설정을 적용하세요:")
        print("  sudo cp nginx.conf.generated /etc/nginx/sites-available/your-project.conf")
        print("  sudo ln -s /etc/nginx/sites-available/your-project.conf /etc/nginx/sites-enabled/")
        print("  sudo nginx -t  # 설정 파일 검증")
        print("  sudo systemctl reload nginx  # Nginx 재시작")
        print()
        print("또는 자동 적용하려면:")
        print("  python deploy_nginx.py --apply")


def apply_nginx_config(config_file: Path, project_name: str = "your-project"):
    """Nginx 설정 파일을 자동으로 적용"""
    if os.name == 'nt':  # Windows
        print("경고: Windows에서는 Nginx 자동 적용을 지원하지 않습니다.")
        print("생성된 설정 파일을 수동으로 Nginx에 적용하세요.")
        return
    
    nginx_available = Path(f"/etc/nginx/sites-available/{project_name}.conf")
    nginx_enabled = Path(f"/etc/nginx/sites-enabled/{project_name}.conf")
    
    try:
        # 설정 파일 복사
        print(f"Nginx 설정 파일을 적용하는 중...")
        subprocess.run(
            ['sudo', 'cp', str(config_file), str(nginx_available)],
            check=True
        )
        print(f"  ✓ {nginx_available}에 복사 완료")
        
        # 심볼릭 링크 생성 (기존 링크가 있으면 제거)
        if nginx_enabled.exists() or nginx_enabled.is_symlink():
            subprocess.run(['sudo', 'rm', '-f', str(nginx_enabled)], check=False)
        
        subprocess.run(
            ['sudo', 'ln', '-s', str(nginx_available), str(nginx_enabled)],
            check=True
        )
        print(f"  ✓ {nginx_enabled} 심볼릭 링크 생성 완료")
        
        # Nginx 설정 검증
        print("Nginx 설정 파일 검증 중...")
        result = subprocess.run(['sudo', 'nginx', '-t'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✓ Nginx 설정 파일 검증 성공")
            
            # Nginx 재시작
            print("Nginx 재시작 중...")
            subprocess.run(['sudo', 'systemctl', 'reload', 'nginx'], check=True)
            print("  ✓ Nginx 재시작 완료")
            print()
            print("Nginx 설정이 성공적으로 적용되었습니다!")
        else:
            print("  ✗ Nginx 설정 파일 검증 실패:")
            print(result.stderr)
            print()
            print("설정 파일을 수정한 후 다시 시도하세요.")
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print(f"오류: Nginx 설정 적용 중 문제가 발생했습니다: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("오류: Nginx가 설치되어 있지 않거나 sudo 명령어를 사용할 수 없습니다.")
        print("수동으로 설정 파일을 적용하세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
