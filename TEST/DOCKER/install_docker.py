#!/usr/bin/env python3
"""
Docker Desktop 설치 도우미
Windows 환경에서 Docker Desktop 설치를 도와주는 스크립트
"""

import subprocess
import sys
import os
import webbrowser
import platform

def check_windows_version():
    """Windows 버전을 확인합니다."""
    print("=== Windows 버전 확인 ===")
    version = platform.version()
    print(f"Windows 버전: {version}")
    
    # Windows 10 1903 이상 또는 Windows 11 필요
    if int(platform.version().split('.')[0]) >= 10:
        print("✅ Windows 버전이 Docker Desktop을 지원합니다.")
        return True
    else:
        print("❌ Docker Desktop을 사용하려면 Windows 10 1903 이상이 필요합니다.")
        return False

def check_wsl():
    """WSL 설치 상태를 확인합니다."""
    print("\n=== WSL 설치 확인 ===")
    try:
        result = subprocess.run(
            "wsl --list --verbose", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            print("✅ WSL이 설치되어 있습니다.")
            print(result.stdout)
            return True
        else:
            print("❌ WSL이 설치되어 있지 않습니다.")
            return False
    except Exception as e:
        print(f"WSL 확인 중 오류 발생: {e}")
        return False

def install_wsl():
    """WSL을 설치합니다."""
    print("\n=== WSL 설치 ===")
    print("WSL을 설치하려면 관리자 권한이 필요합니다.")
    print("다음 단계를 따라주세요:")
    print("1. PowerShell을 관리자 권한으로 실행")
    print("2. 다음 명령어 실행: wsl --install")
    print("3. 시스템 재시작")
    print("4. WSL 초기 설정 완료")
    
    choice = input("\nWSL 설치 페이지를 열까요? (y/N): ")
    if choice.lower() == 'y':
        webbrowser.open("https://docs.microsoft.com/ko-kr/windows/wsl/install")

def download_docker_desktop():
    """Docker Desktop 다운로드 페이지를 엽니다."""
    print("\n=== Docker Desktop 다운로드 ===")
    print("Docker Desktop 다운로드 페이지를 엽니다...")
    
    try:
        webbrowser.open("https://www.docker.com/products/docker-desktop/")
        print("✅ 다운로드 페이지가 열렸습니다.")
        print("\n설치 단계:")
        print("1. 'Download for Windows' 버튼 클릭")
        print("2. 다운로드된 Docker Desktop Installer.exe 실행")
        print("3. 'Use WSL 2 instead of Hyper-V' 옵션 선택")
        print("4. 설치 완료 후 시스템 재시작")
        print("5. Docker Desktop 실행")
    except Exception as e:
        print(f"브라우저 열기 실패: {e}")
        print("수동으로 다음 URL을 방문하세요:")
        print("https://www.docker.com/products/docker-desktop/")

def check_docker_installation():
    """Docker 설치 상태를 확인합니다."""
    print("\n=== Docker 설치 확인 ===")
    try:
        result = subprocess.run(
            "docker --version", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Docker가 설치되어 있습니다: {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker가 설치되어 있지 않습니다.")
            return False
    except Exception as e:
        print(f"Docker 확인 중 오류 발생: {e}")
        return False

def test_docker():
    """Docker가 정상적으로 작동하는지 테스트합니다."""
    print("\n=== Docker 테스트 ===")
    try:
        result = subprocess.run(
            "docker run --rm hello-world", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            print("✅ Docker가 정상적으로 작동합니다!")
            print("테스트 결과:")
            print(result.stdout)
            return True
        else:
            print("❌ Docker 테스트에 실패했습니다.")
            print("오류:", result.stderr)
            return False
    except Exception as e:
        print(f"Docker 테스트 중 오류 발생: {e}")
        return False

def show_installation_guide():
    """설치 가이드를 표시합니다."""
    print("\n" + "="*60)
    print("🐳 Docker Desktop 설치 가이드")
    print("="*60)
    print()
    print("📋 필수 요구사항:")
    print("  • Windows 10 1903 이상 또는 Windows 11")
    print("  • WSL 2 (Windows Subsystem for Linux 2)")
    print("  • 가상화 기능 활성화 (BIOS에서)")
    print()
    print("🔧 설치 단계:")
    print("1. WSL 2 설치")
    print("   - PowerShell을 관리자 권한으로 실행")
    print("   - 명령어: wsl --install")
    print("   - 시스템 재시작")
    print()
    print("2. Docker Desktop 설치")
    print("   - https://www.docker.com/products/docker-desktop/ 방문")
    print("   - 'Download for Windows' 클릭")
    print("   - 설치 파일 실행")
    print("   - 'Use WSL 2 instead of Hyper-V' 선택")
    print()
    print("3. 설치 후 설정")
    print("   - 시스템 재시작")
    print("   - Docker Desktop 실행")
    print("   - 초기 설정 완료")
    print()
    print("✅ 설치 확인:")
    print("   - 명령어: docker --version")
    print("   - 테스트: docker run hello-world")
    print("="*60)

def main():
    """메인 함수"""
    print("🐳 Docker Desktop 설치 도우미")
    print("="*40)
    
    # Windows 버전 확인
    if not check_windows_version():
        return
    
    # WSL 확인
    if not check_wsl():
        print("\nWSL 설치가 필요합니다.")
        install_wsl()
        return
    
    # Docker 설치 확인
    if check_docker_installation():
        print("\nDocker가 이미 설치되어 있습니다!")
        test_docker()
    else:
        print("\nDocker Desktop을 설치해야 합니다.")
        download_docker_desktop()
    
    # 설치 가이드 표시
    show_installation_guide()

if __name__ == "__main__":
    main() 