import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


DEFAULT_AUDIT_PATH = os.getenv("RELAY_AUDIT_LOG_PATH", "/app/logs/relay_audit.log")


def write_audit(event: dict, path: Optional[str] = None) -> None:
    target_path = Path(path or DEFAULT_AUDIT_PATH)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    with target_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
