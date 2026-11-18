#!/bin/sh
set -eu

# Runs once per 24 hours. Set SCMS_BACKUP_UTC_HOUR to coordinate the first run.
hour="${SCMS_BACKUP_UTC_HOUR:-2}"
while true; do
  now_hour="$(date -u +%H)"
  if [ "$now_hour" = "$hour" ]; then
    python /opt/scms-backups/backup_sqlite.py
    sleep 3600
  else
    sleep 300
  fi
done
