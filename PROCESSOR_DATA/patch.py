###########################################
# Module name : patch.py
# Module functions : fix_invalid_datetime_in_xlsx_bytes
# Written by : ChatGPT-5.3
# Contact : Dreamer.Dy.Yun@Gmail.com
# Created at : 2026.03.02
# Updated at : 2026.03.02
# Supported by : -
# Note : 
#       ※ 내용 검토 되지 않음
############################################


import io
import re
import zipfile

_PATTERN = re.compile(r'(?<!\d)(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})(?!\d)')

def fix_invalid_datetime_in_xlsx_bytes(src_bytes: bytes) -> bytes:
    """
    Patch invalid datetime strings like:
      20250417T000000  ->  2025-04-17T00:00:00
    inside xl/worksheets/*.xml of an .xlsx (zip) binary.

    Returns patched .xlsx as bytes.
    """
    def repl(m: re.Match) -> str:
        y, mo, d, hh, mm, ss = m.groups()
        return f"{y}-{mo}-{d}T{hh}:{mm}:{ss}"

    src_buf = io.BytesIO(src_bytes)
    dst_buf = io.BytesIO()

    with zipfile.ZipFile(src_buf, "r") as zin, zipfile.ZipFile(dst_buf, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)

            if item.filename.startswith("xl/worksheets/") and item.filename.endswith(".xml"):
                try:
                    text = data.decode("utf-8")
                except UnicodeDecodeError:
                    # XML이 UTF-8이 아닐 가능성은 낮지만, 방어적으로 원본 유지
                    zout.writestr(item, data)
                    continue

                new_text, n = _PATTERN.subn(repl, text)
                # 로깅이 필요하면 여기서 n 사용
                zout.writestr(item, new_text.encode("utf-8"))
            else:
                # 그대로 복사
                zout.writestr(item, data)

    return dst_buf.getvalue()