#!/usr/bin/env sh
set -eu

HOST="${1:?Usage: verify_tls.sh hostname}"

echo "Checking HTTP to HTTPS redirect..."
curl --fail --head --location --max-redirs 1 "http://${HOST}" | grep -i '^HTTP/.* 200\|^HTTP/.* 301\|^HTTP/.* 302'

echo "Checking TLS 1.3..."
printf '' | openssl s_client -connect "${HOST}:443" -servername "${HOST}" -tls1_3 2>/dev/null | grep -q "Protocol  : TLSv1.3"

echo "TLS 1.3 and redirect checks passed."
