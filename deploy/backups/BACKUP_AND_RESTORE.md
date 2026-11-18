# Encrypted backup and restore procedure

Traceability: Issue #24 · SCMS-NF-005 · TC-OPS-02

## Deployment setup

1. On the deployment server, set a long random `SCMS_BACKUP_PASSPHRASE` in the
   uncommitted `.env` file or approved secret manager. Never commit it.
2. Start the backup profile with `docker compose -f docker-compose.tls.yml -f docker-compose.backup.yml up -d`.
3. The backup container creates an AES-256 GnuPG-encrypted SQLite archive every
   day and deletes archives older than 365 days.
4. Keep the Docker `backup_data` volume on encrypted server storage or copy its
   encrypted archives to the approved off-site storage location.

## Restore verification (staging only)

Run against a copy of a recent archive; never overwrite the production database:

```sh
docker compose -f docker-compose.tls.yml -f docker-compose.backup.yml run --rm backup \
  python /opt/scms-backups/restore_verify.py /backups/<archive>.sqlite3.gpg
```

The command validates SQLite integrity and fails when restore time reaches 30
minutes. QA records the archive date, elapsed time, and command result as
TC-OPS-02 evidence. Only verified operational evidence can satisfy the restore
and retention acceptance criteria.
