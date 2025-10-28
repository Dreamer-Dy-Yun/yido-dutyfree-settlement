# CURSOR가 작성

import subprocess
import time
import sys
import psutil
import os


class DockerManager:
    def __init__(self):
        self.docker_desktop_process = "Docker Desktop.exe"
        self.docker_engine_process = "com.docker.backend.exe"
    
    def is_docker_desktop_running(self):
        """Docker Desktop이 실행 중인지 확인"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == self.docker_desktop_process:
                    return True
            return False
        except Exception as e:
            print(f"프로세스 확인 중 오류: {e}")
            return False
    
    def is_docker_engine_ready(self):
        """Docker Engine이 준비되었는지 확인"""
        try:
            result = subprocess.run(
                ["docker", "info"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def start_docker_desktop(self, headless=False):
        """Docker Desktop 실행
        
        Args:
            headless (bool): True면 UI 없이 백그라운드에서만 실행
        """
        try:
            # Windows 기본 설치 경로
            docker_paths = [
                r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
                r"C:\Program Files (x86)\Docker\Docker\Docker Desktop.exe",
                os.path.expanduser(r"~\AppData\Local\Docker\Docker Desktop.exe")
            ]
            
            docker_path = None
            for path in docker_paths:
                if os.path.exists(path):
                    docker_path = path
                    break
            
            if not docker_path:
                print("Docker Desktop 실행 파일을 찾을 수 없습니다.")
                return False
            
            # 실행 명령어 구성
            cmd = [docker_path]
            
            if headless:
                # UI 없이 백그라운드에서만 실행
                cmd.extend(["--quiet", "--hide-window"])
                print("Docker Desktop을 백그라운드에서 실행하는 중...")
            else:
                print("Docker Desktop을 실행하는 중...")
            
            # 백그라운드에서 실행
            if headless:
                # UI를 숨기고 백그라운드에서 실행
                subprocess.Popen(
                    cmd, 
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                subprocess.Popen(cmd, shell=True)
            
            return True
            
        except Exception as e:
            print(f"Docker Desktop 실행 중 오류: {e}")
            return False
    
    def start_docker_headless(self):
        """Docker Desktop을 UI 없이 백그라운드에서만 실행"""
        return self.start_docker_desktop(headless=True)
    
    def is_docker_desktop_ui_visible(self):
        """Docker Desktop UI가 보이는지 확인"""
        try:
            import win32gui
            import win32con
            
            def enum_window_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if "Docker Desktop" in window_title:
                        windows.append((hwnd, window_title))
                return True
            
            windows = []
            win32gui.EnumWindows(enum_window_callback, windows)
            
            return len(windows) > 0
            
        except ImportError:
            print("win32gui 모듈이 필요합니다: pip install pywin32")
            return None
        except Exception as e:
            print(f"UI 확인 중 오류: {e}")
            return None
    
    def hide_docker_desktop_ui(self):
        """Docker Desktop UI 숨기기"""
        try:
            import win32gui
            import win32con
            
            def enum_window_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if "Docker Desktop" in window_title:
                        windows.append(hwnd)
                return True
            
            windows = []
            win32gui.EnumWindows(enum_window_callback, windows)
            
            hidden_count = 0
            for hwnd in windows:
                win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                hidden_count += 1
            
            if hidden_count > 0:
                print(f"{hidden_count}개의 Docker Desktop 창을 숨겼습니다.")
                return True
            else:
                print("숨길 Docker Desktop 창을 찾을 수 없습니다.")
                return False
                
        except ImportError:
            print("win32gui 모듈이 필요합니다: pip install pywin32")
            return False
        except Exception as e:
            print(f"UI 숨기기 중 오류: {e}")
            return False
    
    def wait_for_docker_ready(self, timeout=120):
        """Docker Engine이 준비될 때까지 대기"""
        print("Docker Engine이 준비될 때까지 대기 중...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_docker_engine_ready():
                print("Docker Engine이 준비되었습니다!")
                return True
            
            print(".", end="", flush=True)
            time.sleep(5)
        
        print(f"\n{timeout}초 대기 후에도 Docker Engine이 준비되지 않았습니다.")
        return False
    
    def ensure_docker_running(self, headless=False):
        """Docker Desktop이 실행되도록 보장
        
        Args:
            headless (bool): True면 UI 없이 백그라운드에서만 실행
        """
        if self.is_docker_desktop_running():
            print("Docker Desktop이 이미 실행 중입니다.")
            if self.is_docker_engine_ready():
                print("Docker Engine도 준비되었습니다.")
                return True
            else:
                print("Docker Engine이 아직 준비되지 않았습니다. 대기 중...")
                return self.wait_for_docker_ready()
        else:
            print("Docker Desktop이 실행되지 않았습니다.")
            if self.start_docker_desktop(headless=headless):
                return self.wait_for_docker_ready()
            return False
    
    def run_container(self, image_name, container_name=None, ports=None, volumes=None, 
                     environment=None, detach=True, remove=False):
        """Docker 컨테이너 실행"""
        if not self.ensure_docker_running():
            print("Docker를 실행할 수 없습니다.")
            return False
        
        cmd = ["docker", "run"]
        
        if detach:
            cmd.append("-d")
        
        if remove:
            cmd.append("--rm")
        
        if container_name:
            cmd.extend(["--name", container_name])
        
        if ports:
            for port_mapping in ports:
                cmd.extend(["-p", port_mapping])
        
        if volumes:
            for volume_mapping in volumes:
                cmd.extend(["-v", volume_mapping])
        
        if environment:
            for env_var in environment:
                cmd.extend(["-e", env_var])
        
        cmd.append(image_name)
        
        try:
            print(f"컨테이너 실행 중: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"컨테이너가 성공적으로 실행되었습니다.")
                if detach:
                    print(f"컨테이너 ID: {result.stdout.strip()}")
                return True
            else:
                print(f"컨테이너 실행 실패: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"컨테이너 실행 중 오류: {e}")
            return False
    
    def list_containers(self, all_containers=True, format_output=False):
        """실행 중인 컨테이너 목록 조회"""
        if not self.is_docker_engine_ready():
            print("Docker Engine이 실행되지 않았습니다.")
            return []
        
        cmd = ["docker", "ps"]
        if all_containers:
            cmd.append("-a")
        
        if format_output:
            # JSON 형태로 출력
            cmd.extend(["--format", "table {{.ID}}\\t{{.Names}}\\t{{.Image}}\\t{{.Status}}\\t{{.Ports}}"])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"컨테이너 목록 조회 실패: {result.stderr}")
                return ""
        except Exception as e:
            print(f"컨테이너 목록 조회 중 오류: {e}")
            return ""
    
    def find_containers_by_image(self, image_name):
        """특정 이미지로 실행된 컨테이너들 찾기"""
        if not self.is_docker_engine_ready():
            print("Docker Engine이 실행되지 않았습니다.")
            return []
        
        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"ancestor={image_name}", "--format", "{{.ID}} {{.Names}}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(' ', 1)
                        if len(parts) == 2:
                            containers.append({
                                'id': parts[0],
                                'name': parts[1]
                            })
                return containers
            else:
                print(f"컨테이너 검색 실패: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"컨테이너 검색 중 오류: {e}")
            return []
    
    def find_container_by_name(self, container_name):
        """이름으로 컨테이너 찾기"""
        if not self.is_docker_engine_ready():
            print("Docker Engine이 실행되지 않았습니다.")
            return None
        
        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.ID}} {{.Names}} {{.Status}}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                line = result.stdout.strip().split('\n')[0]
                parts = line.split(' ', 2)
                if len(parts) >= 3:
                    return {
                        'id': parts[0],
                        'name': parts[1],
                        'status': parts[2]
                    }
            return None
                
        except Exception as e:
            print(f"컨테이너 검색 중 오류: {e}")
            return None
    
    def stop_containers_by_image(self, image_name):
        """특정 이미지로 실행된 모든 컨테이너 중지"""
        containers = self.find_containers_by_image(image_name)
        
        if not containers:
            print(f"'{image_name}' 이미지로 실행된 컨테이너를 찾을 수 없습니다.")
            return False
        
        success_count = 0
        for container in containers:
            print(f"컨테이너 '{container['name']}' ({container['id'][:12]}) 중지 중...")
            if self.stop_container(container['id']):
                success_count += 1
        
        print(f"{success_count}/{len(containers)}개 컨테이너가 중지되었습니다.")
        return success_count == len(containers)
    
    def start_all_containers(self):
        """모든 중지된 컨테이너 시작"""
        if not self.is_docker_engine_ready():
            print("Docker Engine이 실행되지 않았습니다.")
            return False
        
        try:
            # 중지된 모든 컨테이너 ID 가져오기
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", "status=exited", "-q"], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                container_ids = result.stdout.strip().split('\n')
                container_ids = [cid for cid in container_ids if cid]  # 빈 문자열 제거
                
                if not container_ids:
                    print("시작할 중지된 컨테이너가 없습니다.")
                    return True
                
                # 모든 중지된 컨테이너 시작
                start_result = subprocess.run(
                    ["docker", "start"] + container_ids,
                    capture_output=True,
                    text=True
                )
                
                if start_result.returncode == 0:
                    print(f"{len(container_ids)}개의 컨테이너가 시작되었습니다.")
                    return True
                else:
                    print(f"컨테이너 시작 실패: {start_result.stderr}")
                    return False
            else:
                print(f"컨테이너 목록 조회 실패: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"모든 컨테이너 시작 중 오류: {e}")
            return False
    
    def restart_all_containers(self):
        """모든 컨테이너 재시작"""
        if not self.is_docker_engine_ready():
            print("Docker Engine이 실행되지 않았습니다.")
            return False
        
        try:
            # 모든 컨테이너 ID 가져오기 (실행 중 + 중지됨)
            result = subprocess.run(
                ["docker", "ps", "-a", "-q"], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                container_ids = result.stdout.strip().split('\n')
                container_ids = [cid for cid in container_ids if cid]  # 빈 문자열 제거
                
                if not container_ids:
                    print("재시작할 컨테이너가 없습니다.")
                    return True
                
                # 모든 컨테이너 재시작
                restart_result = subprocess.run(
                    ["docker", "restart"] + container_ids,
                    capture_output=True,
                    text=True
                )
                
                if restart_result.returncode == 0:
                    print(f"{len(container_ids)}개의 컨테이너가 재시작되었습니다.")
                    return True
                else:
                    print(f"컨테이너 재시작 실패: {restart_result.stderr}")
                    return False
            else:
                print(f"컨테이너 목록 조회 실패: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"모든 컨테이너 재시작 중 오류: {e}")
            return False
    
    def get_container_status_summary(self):
        """컨테이너 상태 요약 정보"""
        if not self.is_docker_engine_ready():
            print("Docker Engine이 실행되지 않았습니다.")
            return None
        
        try:
            # 모든 컨테이너 상태별 개수 조회
            result = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{.Status}}"], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                statuses = result.stdout.strip().split('\n')
                status_count = {
                    'running': 0,
                    'exited': 0,
                    'created': 0,
                    'paused': 0,
                    'other': 0
                }
                
                for status in statuses:
                    if status:
                        if 'Up' in status:
                            status_count['running'] += 1
                        elif 'Exited' in status:
                            status_count['exited'] += 1
                        elif 'Created' in status:
                            status_count['created'] += 1
                        elif 'Paused' in status:
                            status_count['paused'] += 1
                        else:
                            status_count['other'] += 1
                
                return status_count
            else:
                print(f"상태 조회 실패: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"상태 조회 중 오류: {e}")
            return None
    
    def stop_container(self, container_name_or_id):
        """컨테이너 중지"""
        if not self.is_docker_engine_ready():
            print("Docker Engine이 실행되지 않았습니다.")
            return False
        
        try:
            result = subprocess.run(
                ["docker", "stop", container_name_or_id], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                print(f"컨테이너 '{container_name_or_id}'가 중지되었습니다.")
                return True
            else:
                print(f"컨테이너 중지 실패: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"컨테이너 중지 중 오류: {e}")
            return False
    
    def kill_container(self, container_name_or_id):
        """컨테이너 강제 종료"""
        if not self.is_docker_engine_ready():
            print("Docker Engine이 실행되지 않았습니다.")
            return False
        
        try:
            result = subprocess.run(
                ["docker", "kill", container_name_or_id], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                print(f"컨테이너 '{container_name_or_id}'가 강제 종료되었습니다.")
                return True
            else:
                print(f"컨테이너 강제 종료 실패: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"컨테이너 강제 종료 중 오류: {e}")
            return False
    
    def force_stop_docker_desktop(self):
        """Docker Desktop 강제 종료"""
        try:
            # Docker Desktop 프로세스 강제 종료
            processes_to_kill = [
                "Docker Desktop.exe",
                "com.docker.backend.exe",
                "dockerd.exe",
                "docker.exe"
            ]
            
            killed_any = False
            for proc_name in processes_to_kill:
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'] == proc_name:
                        try:
                            proc.kill()
                            print(f"{proc_name} 프로세스를 강제 종료했습니다.")
                            killed_any = True
                        except Exception as e:
                            print(f"{proc_name} 종료 실패: {e}")
            
            if killed_any:
                print("Docker Desktop이 강제 종료되었습니다.")
                return True
            else:
                print("종료할 Docker 프로세스를 찾을 수 없습니다.")
                return False
                
        except Exception as e:
            print(f"Docker Desktop 강제 종료 중 오류: {e}")
            return False
    
    def stop_all_containers(self):
        """모든 컨테이너 중지"""
        if not self.is_docker_engine_ready():
            print("Docker Engine이 실행되지 않았습니다.")
            return False
        
        try:
            # 실행 중인 모든 컨테이너 ID 가져오기
            result = subprocess.run(
                ["docker", "ps", "-q"], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                container_ids = result.stdout.strip().split('\n')
                container_ids = [cid for cid in container_ids if cid]  # 빈 문자열 제거
                
                if not container_ids:
                    print("실행 중인 컨테이너가 없습니다.")
                    return True
                
                # 모든 컨테이너 중지
                stop_result = subprocess.run(
                    ["docker", "stop"] + container_ids,
                    capture_output=True,
                    text=True
                )
                
                if stop_result.returncode == 0:
                    print(f"{len(container_ids)}개의 컨테이너가 중지되었습니다.")
                    return True
                else:
                    print(f"컨테이너 중지 실패: {stop_result.stderr}")
                    return False
            else:
                print(f"컨테이너 목록 조회 실패: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"모든 컨테이너 중지 중 오류: {e}")
            return False
    
    def kill_all_containers(self):
        """모든 컨테이너 강제 종료"""
        if not self.is_docker_engine_ready():
            print("Docker Engine이 실행되지 않았습니다.")
            return False
        
        try:
            # 실행 중인 모든 컨테이너 ID 가져오기
            result = subprocess.run(
                ["docker", "ps", "-q"], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                container_ids = result.stdout.strip().split('\n')
                container_ids = [cid for cid in container_ids if cid]  # 빈 문자열 제거
                
                if not container_ids:
                    print("실행 중인 컨테이너가 없습니다.")
                    return True
                
                # 모든 컨테이너 강제 종료
                kill_result = subprocess.run(
                    ["docker", "kill"] + container_ids,
                    capture_output=True,
                    text=True
                )
                
                if kill_result.returncode == 0:
                    print(f"{len(container_ids)}개의 컨테이너가 강제 종료되었습니다.")
                    return True
                else:
                    print(f"컨테이너 강제 종료 실패: {kill_result.stderr}")
                    return False
            else:
                print(f"컨테이너 목록 조회 실패: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"모든 컨테이너 강제 종료 중 오류: {e}")
            return False


def main():
    """사용 예제"""
    docker_manager = DockerManager()
    
    # Docker Desktop 실행 확인 및 실행
    if docker_manager.ensure_docker_running():
        print("Docker가 성공적으로 실행되었습니다!")
        
        # 예제: nginx 컨테이너 실행
        success = docker_manager.run_container(
            image_name="nginx:latest",
            container_name="my-nginx",
            ports=["8080:80"],
            detach=True,
            remove=True
        )
        
        if success:
            print("nginx 컨테이너가 실행되었습니다.")
            print("http://localhost:8080 에서 확인할 수 있습니다.")
            
            # 실행 중인 컨테이너 목록 출력
            print("\n현재 실행 중인 컨테이너:")
            print(docker_manager.list_containers(all_containers=False))
            
    else:
        print("Docker 실행에 실패했습니다.")


if __name__ == "__main__":
    main()