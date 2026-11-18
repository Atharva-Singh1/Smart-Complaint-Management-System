#!/usr/bin/env python3
"""Decrypt a backup to an isolated staging path and validate SQLite integrity."""

import argparse
import os
import sqlite3
import subprocess
import time
from pathlib import Path


def verify_restore(archive: Path, staging_db: Path) -> float:
    passphrase = os.environ.get("SCMS_BACKUP_PASSPHRASE")
    if not passphrase:
        raise RuntimeError("SCMS_BACKUP_PASSPHRASE must be set in the deployment environment.")
    started = time.monotonic()
    staging_db.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["gpg", "--batch", "--yes", "--decrypt", "--pinentry-mode", "loopback", "--passphrase-fd", "0", "--output", str(staging_db), str(archive)],
        input=passphrase + "\n", text=True, check=True,
    )
    with sqlite3.connect(staging_db) as connection:
        result = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        raise RuntimeError(f"Staging restore integrity check failed: {result}")
    elapsed = time.monotonic() - started
    if elapsed >= 30 * 60:
        raise RuntimeError(f"Restore exceeded the 30-minute target ({elapsed:.1f} seconds).")
    return elapsed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--staging-db", type=Path, default=Path("/restore-verification/db.sqlite3"))
    args = parser.parse_args()
    seconds = verify_restore(args.archive, args.staging_db)
    print(f"Restore verification succeeded in {seconds:.1f} seconds.")
