#!/usr/bin/env python3
"""Create an encrypted SQLite backup and prune expired archives.

The encryption passphrase is read only from SCMS_BACKUP_PASSPHRASE and is
provided to GnuPG through stdin, never written to a command line or log.
"""

import argparse
import os
import sqlite3
import subprocess
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path


def prune_expired(backup_dir: Path, retention_days: int, now: datetime) -> list[Path]:
    cutoff = now - timedelta(days=retention_days)
    deleted = []
    for archive in backup_dir.glob("scms-*.sqlite3.gpg"):
        modified = datetime.fromtimestamp(archive.stat().st_mtime, tz=UTC)
        if modified < cutoff:
            archive.unlink()
            deleted.append(archive)
    return deleted


def create_backup(source: Path, backup_dir: Path, retention_days: int) -> Path:
    passphrase = os.environ.get("SCMS_BACKUP_PASSPHRASE")
    if not passphrase:
        raise RuntimeError("SCMS_BACKUP_PASSPHRASE must be set in the deployment environment.")
    if not source.is_file():
        raise FileNotFoundError(f"SQLite database was not found: {source}")

    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    destination = backup_dir / f"scms-{timestamp}.sqlite3.gpg"

    with tempfile.TemporaryDirectory(prefix="scms-backup-") as temp_dir:
        snapshot = Path(temp_dir) / "scms.sqlite3"
        with sqlite3.connect(source) as live, sqlite3.connect(snapshot) as copied:
            live.backup(copied)
        subprocess.run(
            [
                "gpg", "--batch", "--yes", "--symmetric", "--cipher-algo", "AES256",
                "--pinentry-mode", "loopback", "--passphrase-fd", "0", "--output", str(destination), str(snapshot),
            ],
            input=passphrase + "\n", text=True, check=True,
        )

    prune_expired(backup_dir, retention_days, datetime.now(UTC))
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default=os.getenv("SCMS_DATABASE_PATH", "/app/data/db.sqlite3"))
    parser.add_argument("--backup-dir", default="/backups")
    parser.add_argument("--retention-days", type=int, default=365)
    args = parser.parse_args()
    archive = create_backup(Path(args.database), Path(args.backup_dir), args.retention_days)
    print(f"Created encrypted backup: {archive.name}")
