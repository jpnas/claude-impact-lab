import json
from functools import lru_cache
from pathlib import Path
from typing import Any


DATA_FILE_PATH = Path(__file__).resolve().parents[1] / "data" / "mock_area.json"


@lru_cache(maxsize=1)
def load_area_data() -> dict[str, Any]:
    with DATA_FILE_PATH.open("r", encoding="utf-8") as data_file:
        loaded_data = json.load(data_file)

    return loaded_data
