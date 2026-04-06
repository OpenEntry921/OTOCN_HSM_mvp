import json
from datetime import datetime


def write_audit(event: dict, path: str = "audit.log") -> None:
    record = {
        "ts": datetime.utcnow().isoformat(),
        **event
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
