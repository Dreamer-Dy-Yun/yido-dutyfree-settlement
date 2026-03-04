import shutil
import tempfile
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from CUSTOMIZED.cust_hasher import Hasher
from CUSTOMIZED.cust_zip_processor import ZipProcessor


ZIP_PATH = Path(r"C:\Users\Dev-Env\Downloads\drive-download-20260304T074111Z-3-001.zip")
ALLOWED_EXT = [".jpg", ".jpeg", ".png", ".gif", ".webp"]


def main() -> None:
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"ZIP 파일이 없습니다: {ZIP_PATH}")

    temp_root = Path(tempfile.mkdtemp(prefix="yido_image_ocr_sim_"))
    try:
        # 1) upload_image_zip 단계 모사: 압축 해제 + hash/path 메타 구성
        processor = ZipProcessor(ZIP_PATH).to_files(
            dir_dest_root=temp_root,
            dir_dest_sub=Path("img"),
            allowed_extensions=ALLOWED_EXT,
            ignore_inner_directory=True,
            set_hash_as_file_name=True,
        )

        image_rows: list[dict[str, str | bool]] = []
        for _full_path, meta in processor.saved_meta.items():
            rel_path = meta.get("relative_path")
            file_hash = meta.get("hash")
            if not rel_path or not file_hash:
                continue
            image_rows.append(
                {
                    "hash": str(file_hash),
                    "path": str(rel_path).replace("\\", "/"),
                    "exists": True,
                    "is_processed": False,
                }
            )

        # drop_duplicates(subset=["hash"], keep="last") 동작 모사
        dedup_by_hash: dict[str, dict[str, str | bool]] = {}
        for row in image_rows:
            dedup_by_hash[str(row["hash"])] = row
        df_images_like = list(dedup_by_hash.values())
        image_hashes = list(dedup_by_hash.keys())

        # 2) run_image_ocr_background 단계 모사: path 기준 파일 재해시
        hash_mismatches: list[tuple[str, str, str]] = []
        missing_files: list[str] = []
        for row in df_images_like:
            hash_from_upload = str(row["hash"])
            rel_path = Path(str(row["path"]))
            full_path = temp_root / rel_path
            if not full_path.exists():
                missing_files.append(str(full_path))
                continue

            hash_from_file = Hasher().hash(full_path, ignore_errors=False).to_hex_string
            if hash_from_upload != hash_from_file:
                hash_mismatches.append((str(full_path), hash_from_upload, hash_from_file))

        # 3) 결과 출력
        print("=== Simulation Result ===")
        print(f"zip_path: {ZIP_PATH}")
        print(f"temp_root: {temp_root}")
        print(f"saved_meta_count: {len(processor.saved_meta)}")
        print(f"image_rows_count(before_dedup): {len(image_rows)}")
        print(f"image_rows_count(after_dedup): {len(df_images_like)}")
        print(f"image_hashes_count: {len(image_hashes)}")
        print(f"missing_files_count: {len(missing_files)}")
        print(f"hash_mismatch_count: {len(hash_mismatches)}")

        if missing_files:
            print("\n[Missing Files]")
            for p in missing_files[:10]:
                print(p)

        if hash_mismatches:
            print("\n[Hash Mismatches]")
            for p, h1, h2 in hash_mismatches[:10]:
                print(f"path={p}")
                print(f" upload_hash={h1}")
                print(f" file_hash  ={h2}")
        else:
            print("\n모사 결과: 업로드 단계 hash와 OCR 단계 파일 재해시 값이 모두 일치합니다.")
            print("=> 현재 에러(path NOT NULL)는 hash 불일치보다는 DB upsert payload(path 누락) 이슈일 가능성이 큽니다.")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
