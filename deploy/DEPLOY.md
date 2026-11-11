# Deploy runbook (dtm-ai.uz, single VPS)

## 1. VPS
Ubuntu 24.04, 4 GB RAM+. `apt install docker.io docker-compose-v2 ufw`; `ufw allow 22,80,443/tcp && ufw enable`. Create a non-root deploy user in the `docker` group.

## 2. DNS
A records (TTL 300) to the VPS IPv4 (add matching AAAA only if the VPS has IPv6 and ufw allows it):

| Name | Type | Value | Serves |
|---|---|---|---|
| `dtm-ai.uz` | A | VPS IP | landing (web) |
| `app.dtm-ai.uz` | A | VPS IP | learner app + Mini App `/tg` (web) |
| `api.dtm-ai.uz` | A | VPS IP | API, `/tg/webhook`, `/billing/click/*` |
| `admin.dtm-ai.uz` | A | VPS IP | admin panel |

Wait until all four resolve (`dig +short app.dtm-ai.uz`) before issuing certificates.

## 3. Config
`git clone` the repo (or copy `deploy/`), `cp .env.sample .env`, fill secrets (`openssl rand -hex 32` for JWT). `docker login ghcr.io`.

## 4. First certificates
nginx needs certs to start, so issue them standalone once (ports 80/443 free):
```
docker compose -f docker-compose.prod.yaml run --rm -p 80:80 --entrypoint certbot certbot certonly --standalone \
  -d dtm-ai.uz -d app.dtm-ai.uz -d admin.dtm-ai.uz -d api.dtm-ai.uz --email you@dtm-ai.uz --agree-tos
```
One SAN cert named `dtm-ai.uz` is used by all sites. The `certbot` service renews via webroot every 12 h; `docker compose exec edge nginx -s reload` after renewal (cron weekly).

## 5. Start
```
docker compose -f docker-compose.prod.yaml --env-file .env pull
docker compose -f docker-compose.prod.yaml --env-file .env up -d
```
`migrate` (one-shot, `alembic upgrade heads` then the insert-only exam-info seed, which never overwrites admin edits) runs before api/worker/scheduler; `bot-webhook-setup` (one-shot) registers the Telegram webhook, commands and menu button once the api is healthy, so step 6 is only needed for manual repair. Bot updates are served by the api (`/tg/webhook`); there is no separate bot process. Check `curl https://api.dtm-ai.uz/healthz`.

Images (built by `deploy.yml`): `ghcr.io/aliakseych/dtmai-{api,web,admin}:${IMAGE_TAG}`. Local build: `docker build -t dtmai-api apps/api`; `docker build -f apps/web/Dockerfile --build-arg NEXT_PUBLIC_API_URL=https://api.dtm-ai.uz --build-arg NEXT_PUBLIC_TG_BOT=<bot> -t dtmai-web .` (admin likewise).

## 6. Telegram
Automated by `bot-webhook-setup`; manual equivalent:
```
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -d url=https://api.dtm-ai.uz/tg/webhook -d secret_token=$TELEGRAM_WEBHOOK_SECRET \
  -d 'allowed_updates=["message","callback_query"]'
```
BotFather: `/setdomain` -> `app.dtm-ai.uz` (Login Widget); `/mybots` -> Bot Settings -> Menu Button / Configure Mini App -> URL `https://app.dtm-ai.uz/tg`.

## 7. Click (cabinet merchant.click.uz)
- Prepare URL: `https://api.dtm-ai.uz/billing/click/prepare`
- Complete URL: `https://api.dtm-ai.uz/billing/click/complete`
- Put service_id / merchant_id / merchant_user_id / secret_key in `.env`. Requests are verified with the md5 `sign_string`.

## 8. First admin
1. Register at `https://app.dtm-ai.uz/register` and verify the email code.
2. Promote that user (from `deploy/`):
```
docker compose -f docker-compose.prod.yaml exec postgres psql -U dtmai -d dtmai \
  -c "UPDATE identity.users SET roles = '{student,admin}' WHERE email = 'you@example.com';"
```
3. Log out/in (roles are in the JWT), then open `https://admin.dtm-ai.uz`. Further admins/editors are managed in the admin panel.

## 9. Backups
Daily cron on host:
```
docker compose -f docker-compose.prod.yaml exec -T postgres pg_dump -U dtmai -Fc dtmai > /backups/dtmai-$(date +%F).dump
```
Keep 14 days; copy off-host (rclone to S3). RustFS: back up the `dtmai_s3` volume (`docker run --rm -v dtmai_s3:/d -v /backups:/b alpine tar czf /b/s3-$(date +%F).tgz -C /d .`). Restore: `pg_restore -U dtmai -d dtmai --clean`. Test restore monthly.

## 10. GitHub Actions deploy
`ci.yml` (PR/main): api `uv sync` + pytest, web/admin `bun install` + lint + build, OpenAPI drift check (`bun run gen:api` then `git diff --exit-code`).
`deploy.yml` (tag `v*`): builds and pushes `ghcr.io/aliakseych/dtmai-{api,web,admin}:<tag>` (+ `latest`), then over SSH sets `IMAGE_TAG` in `.env`, `pull`, `run --rm migrate`, `up -d`. Release: `git tag v1.2.3 && git push origin v1.2.3`.

Create a GitHub environment `production` with:

| Kind | Name | Value |
|---|---|---|
| secret | `DEPLOY_HOST` | VPS hostname/IP |
| secret | `DEPLOY_USER` | deploy user (in `docker` group) |
| secret | `DEPLOY_SSH_KEY` | private key (ed25519) whose public key is in the user's `authorized_keys` |
| secret | `DEPLOY_PORT` | SSH port, usually `22` |
| secret | `DEPLOY_HOST_FINGERPRINT` | `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` SHA256 value |
| secret | `DEPLOY_PATH` | directory on the VPS holding `docker-compose.prod.yaml`, `nginx/`, `.env` (the `deploy/` folder) |
| variable | `NEXT_PUBLIC_API_URL` | `https://api.dtm-ai.uz` (baked into web/admin at build) |
| variable | `NEXT_PUBLIC_TG_BOT` | bot username without `@` |

GHCR packages must be pulled by the VPS: `docker login ghcr.io` with a PAT (`read:packages`) once, or make the packages public. Keep `deploy/` on the VPS in sync with the repo (`git pull`) when compose/nginx change.

## 11. Update / rollback
- Update: tag `vX.Y.Z` (automatic), or manually set `IMAGE_TAG=vX.Y.Z` in `.env` then `docker compose -f docker-compose.prod.yaml --env-file .env pull && docker compose -f docker-compose.prod.yaml --env-file .env run --rm migrate && docker compose -f docker-compose.prod.yaml --env-file .env up -d`.
- Rollback: take a backup (section 9), set `IMAGE_TAG` to the previous tag in `.env`, `pull && up -d`. Migrations are expand-only (see the `migrations` skill), so older images run on the newer schema; do NOT downgrade the DB unless a release note says so. If a migration itself broke data, restore the pre-release `pg_restore --clean` dump, then deploy the previous tag.
- Or re-run the `deploy` workflow on the previous tag (Actions -> deploy -> re-run).
