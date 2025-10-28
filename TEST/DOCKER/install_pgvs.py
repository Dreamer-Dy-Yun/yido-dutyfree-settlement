#!/usr/bin/env python3
"""
PGVS Server 자동 설치 및 실행 스크립트
"""

import subprocess
import time
import os
from docker_manager import DockerManager

class PGVSInstaller:
    def __init__(self):
        self.docker_manager = DockerManager()
        self.image_name = "pgvs-server:latest"
        self.container_name = "pgvs-server"
        
    def build_pgvs_image(self):
        """PGVS Server 이미지 빌드"""
        print("=== PGVS Server 이미지 빌드 ===")
        
        try:
            # Dockerfile이 있는지 확인
            if not os.path.exists("Dockerfile.pgvs"):
                print("Dockerfile.pgvs가 없습니다. 기본 PostgreSQL 이미지를 사용합니다.")
                return True
            
            # 이미지 빌드
            cmd = ["docker", "build", "-f", "Dockerfile.pgvs", "-t", self.image_name, "."]
            print(f"빌드 명령: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                print("✅ PGVS Server 이미지가 성공적으로 빌드되었습니다.")
                return True
            else:
                print(f"❌ 이미지 빌드 실패: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"이미지 빌드 중 오류: {e}")
            return False
    
    def pull_postgres_image(self):
        """PostgreSQL 이미지 다운로드"""
        print("=== PostgreSQL 이미지 다운로드 ===")
        
        try:
            cmd = ["docker", "pull", "postgres:15"]
            print("PostgreSQL 15 이미지를 다운로드하는 중...")
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                print("✅ PostgreSQL 이미지가 성공적으로 다운로드되었습니다.")
                return True
            else:
                print(f"❌ 이미지 다운로드 실패: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"이미지 다운로드 중 오류: {e}")
            return False
    
    def run_pgvs_server(self):
        """PGVS Server 컨테이너 실행"""
        print("=== PGVS Server 실행 ===")
        
        # Docker Desktop 실행 확인
        if not self.docker_manager.ensure_docker_running():
            print("Docker 실행에 실패했습니다.")
            return False
        
        # 기존 컨테이너가 있는지 확인하고 제거
        existing_container = self.docker_manager.find_container_by_name(self.container_name)
        if existing_container:
            print(f"기존 컨테이너 '{self.container_name}'를 제거합니다...")
            self.docker_manager.kill_container(self.container_name)
            subprocess.run(["docker", "rm", self.container_name], capture_output=True, encoding='utf-8')
        
        # 컨테이너 실행
        success = self.docker_manager.run_container(
            image_name="postgres:15",  # 기본 PostgreSQL 이미지 사용
            container_name=self.container_name,
            ports=["5432:5432"],
            environment=[
                "POSTGRES_DB=pgvs",
                "POSTGRES_USER=pgvs_user", 
                "POSTGRES_PASSWORD=pgvs_password"
            ],
            detach=True
        )
        
        if success:
            print("✅ PGVS Server가 성공적으로 실행되었습니다!")
            print("\n=== 연결 정보 ===")
            print("Host: localhost")
            print("Port: 5432")
            print("Database: pgvs")
            print("Username: pgvs_user")
            print("Password: pgvs_password")
            print("\n=== 컨테이너 상태 ===")
            print(self.docker_manager.list_containers(all_containers=False, format_output=True))
            return True
        else:
            print("❌ PGVS Server 실행에 실패했습니다.")
            return False
    
    def install_pgadmin(self):
        """PgAdmin4 설치 및 실행"""
        print("\n=== PgAdmin4 설치 ===")
        
        success = self.docker_manager.run_container(
            image_name="dpage/pgadmin4:latest",
            container_name="pgadmin4",
            ports=["5050:80"],
            environment=[
                "PGADMIN_DEFAULT_EMAIL=admin@admin.com",
                "PGADMIN_DEFAULT_PASSWORD=admin"
            ],
            detach=True
        )
        
        if success:
            print("✅ PgAdmin4가 성공적으로 실행되었습니다!")
            print("\n=== PgAdmin4 연결 정보 ===")
            print("URL: http://localhost:5050")
            print("Email: admin@admin.com")
            print("Password: admin")
            return True
        else:
            print("❌ PgAdmin4 실행에 실패했습니다.")
            return False
    
    def test_connection(self):
        """데이터베이스 연결 테스트"""
        print("\n=== 연결 테스트 ===")
        
        try:
            # 컨테이너가 실행 중인지 확인
            result = subprocess.run(
                ["docker", "exec", self.container_name, "pg_isready", "-U", "pgvs_user", "-d", "pgvs"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ PGVS Server에 성공적으로 연결되었습니다!")
                return True
            else:
                print("❌ 연결 테스트 실패. 서버가 아직 시작 중일 수 있습니다.")
                return False
                
        except Exception as e:
            print(f"연결 테스트 중 오류: {e}")
            return False
    
    def install_complete_environment(self):
        """완전한 PGVS 개발 환경 설치"""
        print("🐳 PGVS 개발 환경 자동 설치")
        print("=" * 50)
        
        # 1. PostgreSQL 이미지 다운로드
        if not self.pull_postgres_image():
            return False
        
        # 2. PGVS Server 실행
        if not self.run_pgvs_server():
            return False
        
        # 3. 잠시 대기 (서버 시작 시간)
        print("\n서버 시작을 기다리는 중...")
        time.sleep(10)
        
        # 4. 연결 테스트
        if not self.test_connection():
            print("연결 테스트 실패했지만 계속 진행합니다...")
        
        # 5. PgAdmin4 설치 (선택사항)
        install_pgadmin = input("\nPgAdmin4도 설치하시겠습니까? (y/N): ")
        if install_pgadmin.lower() == 'y':
            self.install_pgadmin()
        
        print("\n✅ PGVS 개발 환경 설치가 완료되었습니다!")
        return True

def main():
    """메인 함수"""
    installer = PGVSInstaller()
    
    print("PGVS Server 자동 설치 도구")
    print("=" * 30)
    print("1. PGVS Server만 설치")
    print("2. 완전한 개발 환경 설치 (Server + PgAdmin)")
    print("3. 연결 테스트")
    print("4. 컨테이너 상태 확인")
    
    choice = input("\n선택하세요 (1-4): ")
    
    if choice == "1":
        installer.run_pgvs_server()
    elif choice == "2":
        installer.install_complete_environment()
    elif choice == "3":
        installer.test_connection()
    elif choice == "4":
        print(installer.docker_manager.list_containers(all_containers=True, format_output=True))
    else:
        print("잘못된 선택입니다.")

if __name__ == "__main__":
    main() 