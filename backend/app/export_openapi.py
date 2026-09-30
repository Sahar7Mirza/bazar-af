"""Write the OpenAPI schema to docs/api/openapi.json (run from backend/:  python -m app.export_openapi)."""
import json
from pathlib import Path

from app.main import app

out = Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n")
print(f"wrote {out} ({len(app.openapi()['paths'])} paths)")
