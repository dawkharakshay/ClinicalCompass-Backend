import json
from pathlib import Path

from app.main import app

docs_dir = Path(__file__).parent.parent / "docs/api"
docs_dir.mkdir(parents=True, exist_ok=True)

output_dir = docs_dir / "openapi.json"
output_dir.write_text(json.dumps(app.openapi(), indent=2))



