###########################################
# Module name : cust_zip_processor.py
# Module class : ZipProcessor
# Written by : Yun Dae-young 
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.03.03
# Updated at : 2026.03.03
# Supported by : -
# Note : 
#        - 청킹은 하지 않음.
#            - 사유 : 파일 해시시, 어차피 해당 파일을 통째로 메모리에 올려야 하므로 파일 청킹이 의미 없음
#            - 청킹을 하려면 set_hash_as_file_name = false 일 때만 청킹을 해야 함.
#        - Zip은 순차처리가 불가(스트리밍 불가)하므로, 바이트로 받지 않고 Path로만 받아 처리.
############################################


import zipfile
from pathlib import Path
from typing import Self
from cust_hasher import Hasher

class ZipProcessor:


    def __init__(self, zip_path: Path):
        self._zip_path: Path = Path(zip_path)
        self._saved_paths: list[Path] = []
        self._dir_dest_root: Path = Path()
        self._dir_dest_sub: Path | None = None


    @property
    def saved_full_paths(self) -> list[Path]:
        return self._saved_paths

    @property
    def saved_relative_paths(self) -> list[Path]:
        return [path.relative_to(self._dir_dest_root) for path in self._saved_paths]


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

        self._dir_dest_root = dir_dest_root
        self._dir_dest_sub = dir_dest_sub
        dir_target: Path = Path()
        file_name: str = ""
        file_ext: str = ""
        file_hash: str = ""

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

                with zip_file.open(info, "r") as src :
                    raw_data : bytes = src.read()

                    if set_hash_as_file_name:
                        file_hash = Hasher().hash(raw_data).to_hex_string
                        file_ext = Path(info.filename).suffix
                        file_name = f"{file_hash}{file_ext}"
                    else:
                        file_name = Path(info.filename).name

                    with (dir_target / file_name).open("wb") as dst:
                        dst.write(raw_data)

                self._saved_paths.append(dir_target / file_name)

        return self

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
