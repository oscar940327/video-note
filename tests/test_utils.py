from concurrent.futures import ThreadPoolExecutor
import json

from videonote.utils import write_json


def test_concurrent_json_writes_use_unique_temporary_files(tmp_path):
    path = tmp_path / "job.json"

    def write(index: int) -> None:
        write_json(path, {"index": index, "payload": "x" * 1000})

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(write, range(80)))

    result = json.loads(path.read_text(encoding="utf-8"))
    assert result["index"] in range(80)
    assert not list(tmp_path.glob("*.tmp"))
