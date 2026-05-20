# Nginx Infrastructure

This folder contains nginx configuration used by backend Docker Compose and optional host-level nginx deployment.

## Files

| Path | Responsibility |
| --- | --- |
| `compose.default.conf` | nginx config mounted by `docker-compose.yml` for local/backend Compose runtime. |
| `nginx.conf.template` | Host nginx template using `%{VAR}%` and `%{VAR:-default}%` placeholders. |
| `nginx.env.example` | Example environment file for host nginx deployment. |
| `nginx.env` | Local host nginx deployment environment file. Do not commit. |
| `deploy_nginx.py` | Optional helper that renders `nginx.conf.generated` and can apply it on Unix-like hosts. |
| `nginx.conf.generated` | Generated host nginx config. Do not commit. |

## Compose Usage

Run from the backend repository root:

```bash
docker compose config --quiet
docker compose up -d --build
```

`docker-compose.yml` mounts `./infra/nginx/compose.default.conf` and serves frontend static files from `../frontend/dist` by default.

## Host Nginx Usage

Create a local environment file:

```bash
cd infra/nginx
cp nginx.env.example nginx.env
```

Render a config file:

```bash
python deploy_nginx.py
```

Apply automatically on a supported Unix-like host:

```bash
python deploy_nginx.py --apply
```

`--apply` copies the generated config to `/etc/nginx/sites-available/`, links it into `/etc/nginx/sites-enabled/`, runs `nginx -t`, and reloads nginx. Windows does not support automatic apply.

## Generated Files

`nginx.env` and `nginx.conf.generated` are ignored by Git. Keep environment-specific domains, ports, and frontend paths out of committed files.