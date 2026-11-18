# TLS deployment and TC-SEC-01 verification

This configuration is deployment-ready; it is not proof that TLS is active until deployed with a valid certificate and domain.

1. Copy `.env.example` to `.env` on the server and set a unique `SCMS_SECRET_KEY` plus real domain in `SCMS_ALLOWED_HOSTS`.
2. Obtain a valid certificate and key for the domain. Put them at `deploy/certs/fullchain.pem` and `deploy/certs/privkey.pem`. Never commit them.
3. Run `docker compose -f docker-compose.tls.yml up --build -d` on the deployment server.
4. Aum runs `deploy/scripts/verify_tls.sh <domain>` and records the result for TC-SEC-01.

Expected evidence:

- `http://<domain>` redirects to `https://<domain>`.
- TLS handshake reports `TLSv1.3`.
- HTTPS response includes HSTS, `X-Content-Type-Options`, `X-Frame-Options`, and secure cookies.

Do not close Issue #25 until these checks have been run against the deployment.
