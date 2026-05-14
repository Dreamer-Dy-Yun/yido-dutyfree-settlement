###########################################
# Module name : cust_zip_processor.py
# Module class : ZipProcessor
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.03.03
# Updated at : 2026.03.03
# Supported by : -
# Note :
#        - ZIP 전체는 Path(파일) 기준으로 처리하여 메모리 사용을 줄임.
#        - ZIP 내부 개별 파일은 청크(기본 1MB) 단위로 읽고, 해시는 hashlib.update(chunk)로 누적 계산.
#        - set_hash_as_file_name=True 인 경우 임시 파일로 먼저 저장 후 해시 파일명으로 rename.
#        - Zip은 순차처리가 불가(스트리밍 불가)하므로, 바이트로 받지 않고 Path로만 받아 처리.
############################################


import hashlib
import os
import uuid
import zipfile
from pathlib import Path
from typing import Self, Any

class ZipProcessor:
    _CHUNK_SIZE: int = 1024 * 1024  # 1MB


    def __init__(self, zip_path: Path):
        self._zip_path: Path = Path(zip_path)
        self._meta_data: dict[Path, dict[str, Any]] = {}
        self._saved_paths: list[Path] = []
        self._dir_dest_root: Path = Path()
        self._dir_dest_sub: Path | None = None


    @property
    def saved_meta(self) -> dict[Path, dict[str, Any]]:
        """
        저장된 파일 메타데이터 반환
        - 파일 경로 : Path
        - 파일 메타데이터 : dict[str, Any]
        - 파일 메타데이터 종류 : hash, ext, name, relative_path
        """
        return self._meta_data

    @property
    def saved_full_paths_only(self) -> list[Path]:
        return [path for path in self._meta_data.keys()]

    @property
    def saved_relative_paths_only(self) -> list[Path]:
        return [meta_data["relative_path"] for meta_data in self._meta_data.values()]


    def exists(self) -> bool:
        """
        ZIP 파일 존재 여부 확인
        - 존재 시 True, 존재하지 않으면 False
        """
        return self._zip_path.exists()
    

    def delete(self) -> None:
        """
        ZIP 파일 삭제
        - 반환값 없음
        """
        if self._zip_path.exists():
            self._zip_path.unlink()
        return None

    def to_files(
        self,
        dir_dest_root: Path,
        dir_dest_sub: Path | None = None,
        allowed_extensions: list[str] = [""],
        ignore_inner_directory: bool = True,
        set_hash_as_file_name: bool = False,
    ) -> Self:
        """
        서버에서 받은 ZIP 바이너리를 실제 파일들로 저장용. .
        - ZIP 내부 디렉터리 구조 무시/유지 여부에 따라 파일 저장 위치 결정.
        - 허용된 확장자의 파일만 저장 (기본값 [""] 일 때는 모든 파일 허용).
        - allowed_extensions는 확장자 리스트로 지정.
        - 확장자는 대소문자 구분 없이 비교
        - 파일명.lower().endswith(allowed_extensions)로 비교.
        """
        # TODO : 시간있을 때 리팩토링. 잘게 나눌 것
        try : 
        # 이전 실행 결과 초기화
            self._meta_data = {}

            self._dir_dest_root = dir_dest_root
            self._dir_dest_sub = dir_dest_sub
            dir_target: Path = Path()
            file_name: str = ""
            file_ext: str = ""
            file_hash: str = ""
            path_temp: Path = Path()

            dir_destination: Path = dir_dest_root / dir_dest_sub if dir_dest_sub else dir_dest_root

            allowed_ext: tuple[str, ...] = tuple(ext.lower() for ext in allowed_extensions)

            with zipfile.ZipFile(self._zip_path, "r") as zip_file:
                for info in zip_file.infolist():
                    
                    if info.is_dir():
                        # 디렉토리는 대상외
                        continue
                    if not info.filename.lower().endswith(allowed_ext):
                        # 허용된 확장자가 아니면 대상외
                        continue

                    # ZIP 안의 경로를 그대로 살려서 저장
                    if ignore_inner_directory:
                        dir_target = dir_destination
                    else:
                        dir_target = dir_destination / Path(info.filename).parent

                    dir_target.mkdir(parents=True, exist_ok=True)

                    with zip_file.open(info, "r") as src:
                        file_ext = Path(info.filename).suffix
                        original_file_name = Path(info.filename).name
                        path_temp = dir_target / f".tmp_{uuid.uuid4().hex}"
                        hasher = hashlib.sha256()

                        with path_temp.open("wb") as dst:
                            while True:
                                chunk = src.read(self._CHUNK_SIZE)
                                if not chunk:
                                    break
                                hasher.update(chunk)
                                dst.write(chunk)

                        file_hash = hasher.hexdigest()
                        if set_hash_as_file_name:
                            file_name = f"{file_hash}{file_ext}"
                        else:
                            file_name = original_file_name

                        final_path = dir_target / file_name
                        os.replace(path_temp, final_path)

                        temp_dict: dict[str, Any] = {}
                        temp_dict["relative_path"] = final_path.relative_to(self._dir_dest_root)
                        temp_dict["hash"] = file_hash
                        temp_dict["ext"] = file_ext
                        temp_dict["name"] = file_name
                        self._meta_data[final_path] = temp_dict

            return self
        except Exception :
            raise
        finally:
            if path_temp.exists():
                path_temp.unlink()
# ---------------------------------------------------------------------------
# TEST CODE
# ---------------------------------------------------------------------------


if __name__ == "__main__":

    # 1) 로컬 ZIP 파일 경로 
    ZIP_PATH = Path(r"C:\Users\Dev-Env\Desktop\TEST\aaa.zip")

    # 2) 압축을 풀 대상 폴더 (원하는 위치로 바꿔서 사용)
    OUTPUT_ROOT = Path(r"C:\Users\Dev-Env\Desktop\TEST\t")

    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"ZIP 파일이 없습니다: {ZIP_PATH}")

    ZipProcessor(ZIP_PATH).to_files(
        dir_dest_root=OUTPUT_ROOT,
        # allowed_extensions=[".jpg", ".jpeg", ".png"],
        ignore_inner_directory=True,
    )
    print(f"압축 해제 완료: {OUTPUT_ROOT}")
