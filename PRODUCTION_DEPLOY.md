# Production Deploy & Postgres Connection Safety

This runbook covers running the backend under ASGI in production **without
exhausting the shared PostgreSQL cluster**. It exists because of the 2026-06-05
incident where the app leaked connections until the whole shared cluster hit
`max_connections` (`TooManyConnectionsError: sorry, too many clients already`)
and took down unrelated tenants.

There are three independent layers of protection. Apply **all three** — each one
catches what the others miss:

1. **App-level** — bounded SSE streams + explicit connection close (already in
   code; see `common/views/notification_views.py`).
2. **Server-level** — uvicorn worker recycling + graceful shutdown.
3. **Database-level** — a per-app role with a hard `CONNECTION LIMIT` (the
   non-negotiable safety net — it's the only layer that *guarantees* one app
   can never exhaust a shared cluster again).

---

## 1. Database role with a hard connection cap (do this first)

The app must connect as a **non-superuser** role (superusers bypass RLS — see
`RLS_SETUP.md`) that **also has a `CONNECTION LIMIT`**. The cap is what makes a
future leak fail *this app only*, instead of the whole cluster.

```sql
-- Run as a Postgres admin/superuser, once per cluster.

-- The application role. Non-superuser, NOBYPASSRLS, capped.
-- 3 uvicorn workers + a few Celery workers comfortably fit under 30.
ALTER ROLE bottlecrm WITH NOSUPERUSER NOBYPASSRLS CONNECTION LIMIT 30;

-- If the role doesn't exist yet:
-- CREATE ROLE bottlecrm LOGIN PASSWORD '...' NOSUPERUSER NOBYPASSRLS CONNECTION LIMIT 30;

-- The enterprise super-admin dashboard role (BYPASSRLS, separate alias in
-- crm_enterprise.settings DATABASES["superadmin"]). Cap it tightly — the
-- dashboard is low-traffic and this role's connections also count against
-- the cluster. It MUST keep BYPASSRLS but does NOT need to be superuser.
ALTER ROLE bottlecrm_superadmin WITH NOSUPERUSER BYPASSRLS CONNECTION LIMIT 5;
```

Sizing rule of thumb: `CONNECTION LIMIT` ≥ `(uvicorn workers × ~2) +
(celery workers × concurrency) + headroom`, and the **sum of all app caps on
the cluster** must stay below `max_connections` minus the
`superuser_reserved_connections` slots. With the app-level SSE fix in place,
steady-state usage is a small multiple of the worker count, not per-open-tab.

Verify the role is safe:

```bash
cd backend
uv run python manage.py manage_rls --verify-user   # asserts non-superuser
```

Watch live connection counts (run as admin):

```sql
SELECT usename, count(*) , max(backend_start)
FROM pg_stat_activity
GROUP BY usename
ORDER BY count(*) DESC;
```

---

## 2. uvicorn: worker recycling + graceful shutdown

Run the ASGI app (`crm.asgi:application`) with worker recycling so a slow leak
can never accumulate indefinitely, and a bounded graceful-shutdown so deploys
don't leave **orphaned workers** holding connections (the other half of the
incident — those required `kill -9`).

```bash
cd backend
uv run uvicorn crm.asgi:application \
    --host 0.0.0.0 --port 8000 \
    --workers 3 \
    --limit-max-requests 2000 \      # recycle each worker after N requests — caps any per-request leak
    --timeout-graceful-shutdown 30 \ # don't wait forever for SSE streams to drain on restart
    --timeout-keep-alive 10 \
    --proxy-headers --forwarded-allow-ips='*'   # behind nginx/ELB
```

Notes:
- `--limit-max-requests` makes uvicorn replace a worker after it has served N
  requests, closing all its DB connections on the way out. Pick a value that
  recycles roughly every 1–2 hours of traffic.
- `--timeout-graceful-shutdown 30` bounds how long a worker waits for in-flight
  requests (including SSE streams) before being force-killed. Combined with the
  app-level `MAX_STREAM_SECONDS = 300`, streams self-close well within this, so
  workers drain cleanly on deploy instead of orphaning.
- Keep `--workers` modest and let the DB `CONNECTION LIMIT` be the real ceiling.
- `gunicorn -k uvicorn.workers.UvicornWorker` is a fine alternative; use
  `--max-requests 2000 --max-requests-jitter 200 --graceful-timeout 30` there.

---

## 3. systemd unit

`/etc/systemd/system/bottlecrm-api.service`:

```ini
[Unit]
Description=BottleCRM API (uvicorn/ASGI)
After=network.target

[Service]
Type=exec
User=bottlecrm
Group=bottlecrm
WorkingDirectory=/srv/bottlecrm/backend
EnvironmentFile=/srv/bottlecrm/backend/.env
# uv resolves the project venv automatically.
ExecStart=/usr/local/bin/uv run uvicorn crm.asgi:application \
    --host 127.0.0.1 --port 8000 \
    --workers 3 \
    --limit-max-requests 2000 \
    --timeout-graceful-shutdown 30 \
    --timeout-keep-alive 10 \
    --proxy-headers --forwarded-allow-ips='*'

# Graceful stop: SIGTERM lets workers finish draining; systemd force-kills
# after TimeoutStopSec, so a hung worker can't linger as an orphan.
KillSignal=SIGTERM
TimeoutStopSec=45
Restart=always
RestartSec=5

# Hardening (optional but recommended)
NoNewPrivileges=true
ProtectSystem=full
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Celery worker unit `/etc/systemd/system/bottlecrm-celery.service` (Celery keeps
its own persistent connections — bound concurrency so it stays under the role
cap):

```ini
[Unit]
Description=BottleCRM Celery worker
After=network.target redis.service

[Service]
Type=exec
User=bottlecrm
WorkingDirectory=/srv/bottlecrm/backend
EnvironmentFile=/srv/bottlecrm/backend/.env
ExecStart=/usr/local/bin/uv run celery -A crm worker \
    --loglevel=INFO --concurrency=4 --max-tasks-per-child=500
KillSignal=SIGTERM
TimeoutStopSec=60
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

`--max-tasks-per-child=500` recycles Celery child processes periodically, the
same idea as `--limit-max-requests` for the web tier.

Apply:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now bottlecrm-api bottlecrm-celery
sudo systemctl restart bottlecrm-api      # zero-orphan rolling restart
```

---

## 4. (Optional) pgbouncer — pooling in front of the cluster

On a shared cluster, putting **pgbouncer** between the app and Postgres caps
server-side connections regardless of how many clients the app opens. Use
**transaction** pooling (works with Django's autocommit; note RLS uses
`set_config(..., is_local=false)` at session scope, so verify the RLS context is
re-applied per checkout — the middleware sets and resets it every request, which
is compatible, but test tenant isolation under pgbouncer before rolling out).

`pgbouncer.ini`:

```ini
[databases]
crm_db = host=127.0.0.1 port=5432 dbname=crm_db

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 200
default_pool_size = 20          ; server-side conns per (user,db) — the real ceiling
reserve_pool_size = 5
server_idle_timeout = 60
```

Point the app at pgbouncer by setting `DBPORT=6432` (and `DBHOST=127.0.0.1`).
Keep the database-level `CONNECTION LIMIT` anyway — defense in depth.

---

## Post-deploy verification

```bash
# 1. App connects as a capped non-superuser
cd backend && uv run python manage.py manage_rls --verify-user

# 2. Connection count stays bounded under load (run as DB admin, watch over time)
watch -n 30 "psql -c \"SELECT count(*) FROM pg_stat_activity WHERE usename='bottlecrm'\""

# 3. SSE streams self-terminate: open the app, leave a tab on a page with the
#    notifications stream, confirm the connection count does NOT climb with
#    open-tab time (it should plateau, recycling ~every MAX_STREAM_SECONDS=300s).

# 4. Rolling restart leaves no orphans
sudo systemctl restart bottlecrm-api
ps -ef | grep '[u]vicorn'   # only the new master + 3 workers, no stragglers
```

If connections ever climb again: check `pg_stat_activity` for the `query` /
`state` / `backend_start` of the `bottlecrm` rows — long-idle (`idle` with old
`backend_start`) connections point back to a streaming/long-lived view holding a
connection; see `common/views/notification_views.py` for the pattern to follow
(close the request connection before a long-lived response, bound its lifetime).
