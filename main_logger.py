from pathlib import Path
from CUSTOMIZED.cust_logger import set_logfile

project_root = Path(__file__).parent.parent
log_path = project_root / "logs" / "novas_ICT.log"
set_logfile(log_path)