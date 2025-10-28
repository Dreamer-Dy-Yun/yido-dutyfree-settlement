# CURSOR가 작성

from docker_manager import DockerManager


def run_pgvs_server_container():
    """PGVS Server 컨테이너 실행 예제"""
    docker_manager = DockerManager()
    
    # Docker Desktop 실행 확인
    if not docker_manager.ensure_docker_running():
        print("Docker 실행에 실패했습니다.")
        return
    
    # PGVS Server 컨테이너 실행
    success = docker_manager.run_container(
        image_name="pgvs-builder:latest",
        container_name="pgvs-server",
        ports=["5432:5432"],
        detach=True
    )
    
    if success:
        print("PGVS Server 컨테이너가 실행되었습니다.")
        print("연결 정보:")
        print("  Host: localhost")
        print("  Port: 5432")
        print("  Container Name: pgvs-server")


def run_pgadmin_container():
    """PgAdmin4 컨테이너 실행 예제"""
    docker_manager = DockerManager()
    
    if not docker_manager.ensure_docker_running():
        print("Docker 실행에 실패했습니다.")
        return
    
    success = docker_manager.run_container(
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
        print("PgAdmin4 컨테이너가 실행되었습니다.")
        print("연결 정보:")
        print("  URL: http://localhost:5050")
        print("  Email: admin@admin.com")
        print("  Password: admin")


def run_both_containers():
    """PGVS Server와 PgAdmin4 컨테이너 모두 실행"""
    docker_manager = DockerManager()
    
    if not docker_manager.ensure_docker_running():
        print("Docker 실행에 실패했습니다.")
        return
    
    containers = [
        {
            "image_name": "pgvs-builder:latest",
            "container_name": "pgvs-server",
            "ports": ["5432:5432"],
            "description": "PGVS Server (PostgreSQL)"
        },
        {
            "image_name": "dpage/pgadmin4:latest",
            "container_name": "pgadmin4",
            "ports": ["5050:80"],
            "environment": [
                "PGADMIN_DEFAULT_EMAIL=admin@admin.com",
                "PGADMIN_DEFAULT_PASSWORD=admin"
            ],
            "description": "PgAdmin4 (Database Management)"
        }
    ]
    
    print("=== PGVS 개발 환경 시작 ===")
    
    for container in containers:
        print(f"\n{container['description']} 실행 중...")
        success = docker_manager.run_container(
            image_name=container["image_name"],
            container_name=container["container_name"],
            ports=container.get("ports"),
            environment=container.get("environment"),
            detach=True
        )
        
        if success:
            print(f"✅ {container['container_name']} 컨테이너 실행 성공")
        else:
            print(f"❌ {container['container_name']} 컨테이너 실행 실패")
    
    print("\n=== 연결 정보 ===")
    print("🗄️  PGVS Server:")
    print("   Host: localhost")
    print("   Port: 5432")
    print()
    print("🌐 PgAdmin4:")
    print("   URL: http://localhost:5050")
    print("   Email: admin@admin.com")
    print("   Password: admin")
    
    # 실행 중인 컨테이너 목록 출력
    print("\n=== 현재 실행 중인 컨테이너 ===")
    print(docker_manager.list_containers(all_containers=False, format_output=True))


def stop_all_containers():
    """모든 컨테이너 중지 예제"""
    docker_manager = DockerManager()
    
    if not docker_manager.is_docker_engine_ready():
        print("Docker Engine이 실행되지 않았습니다.")
        return
    
    # 방법 1: 개별 컨테이너 중지
    container_names = ["web-server", "database", "cache", "my-postgres", "my-redis", "my-nginx"]
    
    for name in container_names:
        print(f"{name} 컨테이너 중지 중...")
        docker_manager.stop_container(name)
    
    # 방법 2: 모든 컨테이너 한번에 중지
    # docker_manager.stop_all_containers()


def force_kill_containers():
    """컨테이너 강제 종료 예제"""
    docker_manager = DockerManager()
    
    if not docker_manager.is_docker_engine_ready():
        print("Docker Engine이 실행되지 않았습니다.")
        return
    
    print("=== 컨테이너 강제 종료 ===")
    
    # 방법 1: 특정 컨테이너 강제 종료
    container_names = ["web-server", "database", "cache"]
    
    for name in container_names:
        print(f"{name} 컨테이너 강제 종료 중...")
        docker_manager.kill_container(name)
    
    # 방법 2: 모든 컨테이너 강제 종료
    print("\n모든 컨테이너 강제 종료...")
    docker_manager.kill_all_containers()


def force_stop_docker():
    """Docker Desktop 강제 종료 예제"""
    docker_manager = DockerManager()
    
    print("=== Docker Desktop 강제 종료 ===")
    print("⚠️  주의: 모든 Docker 프로세스가 강제 종료됩니다.")
    
    confirm = input("계속하시겠습니까? (y/N): ")
    if confirm.lower() != 'y':
        print("취소되었습니다.")
        return
    
    # 모든 컨테이너 먼저 강제 종료
    if docker_manager.is_docker_engine_ready():
        print("먼저 모든 컨테이너를 강제 종료합니다...")
        docker_manager.kill_all_containers()
    
    # Docker Desktop 강제 종료
    docker_manager.force_stop_docker_desktop()


def start_docker_headless():
    """Docker Desktop을 UI 없이 백그라운드에서 실행"""
    docker_manager = DockerManager()
    
    print("=== Docker Desktop 백그라운드 실행 ===")
    
    if docker_manager.is_docker_desktop_running():
        print("Docker Desktop이 이미 실행 중입니다.")
        
        # UI가 보이는지 확인
        ui_visible = docker_manager.is_docker_desktop_ui_visible()
        if ui_visible is True:
            print("Docker Desktop UI가 현재 표시되어 있습니다.")
            hide_ui = input("UI를 숨기시겠습니까? (y/N): ")
            if hide_ui.lower() == 'y':
                docker_manager.hide_docker_desktop_ui()
        elif ui_visible is False:
            print("Docker Desktop이 이미 백그라운드에서 실행 중입니다.")
        
    else:
        print("Docker Desktop을 백그라운드에서 시작합니다...")
        success = docker_manager.ensure_docker_running(headless=True)
        
        if success:
            print("✅ Docker Desktop이 백그라운드에서 성공적으로 시작되었습니다.")
            print("시스템 트레이에서 Docker 아이콘을 확인할 수 있습니다.")
        else:
            print("❌ Docker Desktop 시작에 실패했습니다.")


def search_containers():
    """컨테이너 검색 예제"""
    docker_manager = DockerManager()
    
    if not docker_manager.is_docker_engine_ready():
        print("Docker Engine이 실행되지 않았습니다.")
        return
    
    print("=== 컨테이너 검색 ===")
    print("1. 이름으로 검색")
    print("2. 이미지로 검색")
    print("3. 전체 컨테이너 목록 (포맷)")
    
    choice = input("선택하세요 (1-3): ")
    
    if choice == "1":
        name = input("컨테이너 이름 입력: ")
        container = docker_manager.find_container_by_name(name)
        
        if container:
            print(f"✅ 컨테이너 발견:")
            print(f"  ID: {container['id']}")
            print(f"  이름: {container['name']}")
            print(f"  상태: {container['status']}")
        else:
            print(f"❌ '{name}' 이름의 컨테이너를 찾을 수 없습니다.")
    
    elif choice == "2":
        image = input("이미지 이름 입력 (예: nginx, postgres:15): ")
        containers = docker_manager.find_containers_by_image(image)
        
        if containers:
            print(f"✅ '{image}' 이미지로 실행된 컨테이너들:")
            for container in containers:
                print(f"  - {container['name']} ({container['id'][:12]})")
        else:
            print(f"❌ '{image}' 이미지로 실행된 컨테이너를 찾을 수 없습니다.")
    
    elif choice == "3":
        print("=== 전체 컨테이너 목록 ===")
        output = docker_manager.list_containers(all_containers=True, format_output=True)
        print(output)


def start_all_containers():
    """모든 중지된 컨테이너 시작"""
    docker_manager = DockerManager()
    
    if not docker_manager.is_docker_engine_ready():
        print("Docker Engine이 실행되지 않았습니다.")
        return
    
    print("=== 모든 컨테이너 시작 ===")
    
    # 현재 상태 요약 표시
    status_summary = docker_manager.get_container_status_summary()
    if status_summary:
        print("현재 컨테이너 상태:")
        print(f"  🟢 실행 중: {status_summary['running']}개")
        print(f"  🔴 중지됨: {status_summary['exited']}개")
        print(f"  🟡 생성됨: {status_summary['created']}개")
        print(f"  ⏸️  일시정지: {status_summary['paused']}개")
        print(f"  ⚪ 기타: {status_summary['other']}개")
        print()
        
        if status_summary['exited'] == 0:
            print("시작할 중지된 컨테이너가 없습니다.")
            return
        
        confirm = input(f"{status_summary['exited']}개의 중지된 컨테이너를 모두 시작하시겠습니까? (y/N): ")
        if confirm.lower() == 'y':
            success = docker_manager.start_all_containers()
            if success:
                print("✅ 모든 컨테이너가 성공적으로 시작되었습니다!")
            else:
                print("❌ 일부 컨테이너 시작에 실패했습니다.")
        else:
            print("취소되었습니다.")


def restart_all_containers():
    """모든 컨테이너 재시작"""
    docker_manager = DockerManager()
    
    if not docker_manager.is_docker_engine_ready():
        print("Docker Engine이 실행되지 않았습니다.")
        return
    
    print("=== 모든 컨테이너 재시작 ===")
    print("⚠️  주의: 모든 컨테이너가 재시작됩니다.")
    
    # 현재 상태 요약 표시
    status_summary = docker_manager.get_container_status_summary()
    if status_summary:
        total_containers = sum(status_summary.values())
        print(f"총 {total_containers}개의 컨테이너가 재시작됩니다.")
        print()
        
        if total_containers == 0:
            print("재시작할 컨테이너가 없습니다.")
            return
        
        confirm = input("정말로 모든 컨테이너를 재시작하시겠습니까? (y/N): ")
        if confirm.lower() == 'y':
            print("컨테이너들을 재시작하는 중...")
            success = docker_manager.restart_all_containers()
            if success:
                print("✅ 모든 컨테이너가 성공적으로 재시작되었습니다!")
            else:
                print("❌ 일부 컨테이너 재시작에 실패했습니다.")
        else:
            print("취소되었습니다.")


def show_container_status():
    """컨테이너 상태 요약 표시"""
    docker_manager = DockerManager()
    
    if not docker_manager.is_docker_engine_ready():
        print("Docker Engine이 실행되지 않았습니다.")
        return
    
    print("=== 컨테이너 상태 요약 ===")
    
    status_summary = docker_manager.get_container_status_summary()
    if status_summary:
        total = sum(status_summary.values())
        print(f"📊 총 {total}개의 컨테이너:")
        print(f"  🟢 실행 중: {status_summary['running']}개")
        print(f"  🔴 중지됨: {status_summary['exited']}개")
        print(f"  🟡 생성됨: {status_summary['created']}개")
        print(f"  ⏸️  일시정지: {status_summary['paused']}개")
        print(f"  ⚪ 기타: {status_summary['other']}개")
        print()
        
        # 상세 목록도 표시
        print("=== 상세 컨테이너 목록 ===")
        detailed_output = docker_manager.list_containers(all_containers=True, format_output=True)
        print(detailed_output)
    else:
        print("컨테이너 상태를 조회할 수 없습니다.")


def stop_by_image():
    """이미지별 컨테이너 중지 예제"""
    docker_manager = DockerManager()
    
    if not docker_manager.is_docker_engine_ready():
        print("Docker Engine이 실행되지 않았습니다.")
        return
    
    print("=== 이미지별 컨테이너 중지 ===")
    
    # 현재 실행 중인 이미지들 표시
    print("현재 실행 중인 컨테이너들:")
    containers_output = docker_manager.list_containers(all_containers=False, format_output=True)
    print(containers_output)
    
    image_name = input("\n중지할 이미지 이름 입력 (예: nginx, postgres): ")
    
    if image_name:
        confirm = input(f"'{image_name}' 이미지의 모든 컨테이너를 중지하시겠습니까? (y/N): ")
        if confirm.lower() == 'y':
            docker_manager.stop_containers_by_image(image_name)
        else:
            print("취소되었습니다.")


def manage_docker_ui():
    """Docker Desktop UI 관리"""
    docker_manager = DockerManager()
    
    if not docker_manager.is_docker_desktop_running():
        print("Docker Desktop이 실행되지 않았습니다.")
        return
    
    print("=== Docker Desktop UI 관리 ===")
    
    ui_visible = docker_manager.is_docker_desktop_ui_visible()
    
    if ui_visible is True:
        print("현재 Docker Desktop UI가 표시되어 있습니다.")
        print("1. UI 숨기기")
        print("2. 그대로 두기")
        
        choice = input("선택하세요 (1-2): ")
        if choice == "1":
            docker_manager.hide_docker_desktop_ui()
            
    elif ui_visible is False:
        print("현재 Docker Desktop이 백그라운드에서 실행 중입니다.")
        print("UI를 표시하려면 시스템 트레이의 Docker 아이콘을 클릭하세요.")
        
    else:
        print("UI 상태를 확인할 수 없습니다. (pywin32 모듈 필요)")


def emergency_shutdown():
    """비상 종료 - 모든 Docker 관련 프로세스 강제 종료"""
    docker_manager = DockerManager()
    
    print("🚨 비상 종료 모드 🚨")
    print("모든 Docker 컨테이너와 Docker Desktop이 강제 종료됩니다.")
    
    confirm = input("정말로 계속하시겠습니까? (y/N): ")
    if confirm.lower() != 'y':
        print("취소되었습니다.")
        return
    
    print("\n1단계: 모든 컨테이너 강제 종료...")
    if docker_manager.is_docker_engine_ready():
        docker_manager.kill_all_containers()
    else:
        print("Docker Engine이 응답하지 않습니다.")
    
    print("\n2단계: Docker Desktop 강제 종료...")
    docker_manager.force_stop_docker_desktop()
    
    print("\n✅ 비상 종료가 완료되었습니다.")


if __name__ == "__main__":
    print("🐳 PGVS Docker 관리 도구")
    print("=" * 45)
    print("📦 PGVS 컨테이너 실행:")
    print("1. PGVS Server 컨테이너 실행")
    print("2. PgAdmin4 컨테이너 실행")
    print("3. PGVS 개발환경 전체 실행 (Server + Admin)")
    print()
    print("🔍 컨테이너 관리:")
    print("4. 컨테이너 상태 요약")
    print("5. 컨테이너 검색")
    print("6. 모든 중지된 컨테이너 시작 🚀")
    print("7. 모든 컨테이너 재시작 🔄")
    print("8. 모든 컨테이너 중지")
    print("9. 이미지별 컨테이너 중지")
    print("10. 컨테이너 강제 종료")
    print()
    print("🖥️  Docker Desktop 관리:")
    print("11. Docker Desktop 강제 종료")
    print("12. Docker Desktop 백그라운드 실행")
    print("13. Docker UI 관리")
    print("14. 🚨 비상 종료 (모든 Docker 프로세스)")
    print("=" * 45)
    
    choice = input("선택하세요 (1-14): ")
    
    if choice == "1":
        run_pgvs_server_container()
    elif choice == "2":
        run_pgadmin_container()
    elif choice == "3":
        run_both_containers()
    elif choice == "4":
        show_container_status()
    elif choice == "5":
        search_containers()
    elif choice == "6":
        start_all_containers()
    elif choice == "7":
        restart_all_containers()
    elif choice == "8":
        stop_all_containers()
    elif choice == "9":
        stop_by_image()
    elif choice == "10":
        force_kill_containers()
    elif choice == "11":
        force_stop_docker()
    elif choice == "12":
        start_docker_headless()
    elif choice == "13":
        manage_docker_ui()
    elif choice == "14":
        emergency_shutdown()
    else:
        print("잘못된 선택입니다.")