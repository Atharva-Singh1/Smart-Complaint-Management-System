import importlib.util
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path


MODULE_PATH = Path(__file__).parents[2] / "deploy" / "backups" / "backup_sqlite.py"
SPEC = importlib.util.spec_from_file_location("backup_sqlite", MODULE_PATH)
backup_sqlite = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backup_sqlite)


def test_prune_expired_removes_only_archives_older_than_retention(tmp_path):
    now = datetime(2026, 11, 18, tzinfo=UTC)
    old_archive = tmp_path / "scms-old.sqlite3.gpg"
    current_archive = tmp_path / "scms-current.sqlite3.gpg"
    unrelated_file = tmp_path / "notes.txt"
    for item in (old_archive, current_archive, unrelated_file):
        item.write_text("test")
    old_time = (now - timedelta(days=366)).timestamp()
    current_time = (now - timedelta(days=365)).timestamp()
    os.utime(old_archive, (old_time, old_time))
    os.utime(current_archive, (current_time, current_time))

    deleted = backup_sqlite.prune_expired(tmp_path, 365, now)

    assert deleted == [old_archive]
    assert not old_archive.exists()
    assert current_archive.exists()
    assert unrelated_file.exists()
