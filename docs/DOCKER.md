---
title: Deploy TokenPak with Docker
rung: 2
audience: Developers deploying the source-built TokenPak container image.
updated: 2026-08-20
status: current
---

# Deploy TokenPak with Docker

This guide is for developers who want to build the TokenPak v1.24.0 image and
run its proxy from Docker on the host's loopback interface. The image's default
`tokenpak serve` command binds to loopback inside the container, so publishing
port 8766 alone does not make that listener reachable from the host.

## Prerequisites

- A checkout of the public TokenPak v1.24.0 tag.
- The `git`, `docker`, `curl`, and `openssl` commands.
- Docker Compose v2 if you want to use the optional Compose procedure.
- An unused host port 8766 and permission to run local containers.

## 1. Check out v1.24.0

Check out the released source:

```bash
git checkout v1.24.0
```

## 2. Build the image

Build the source checkout as `tokenpak:v1.24.0`:

```bash
docker build -t tokenpak:v1.24.0 .
```

The shipped Dockerfile uses Python 3.11. It does not declare a configurable
base-image build argument.

## 3. Create the proxy credential

Generate the Bearer credential that every non-localhost client must present:

```bash
export TOKENPAK_PROXY_AUTH_TOKEN="$(openssl rand -hex 32)"
```

Keep this shell open for the remaining steps.

## 4. Run a proxy reachable from the host

Bind the proxy to all interfaces *inside* the container, publish it only on the
host's loopback interface, and require a proxy credential:

```bash
docker run --rm -d --name tokenpak-proxy \
  -p 127.0.0.1:8766:8766 \
  -e TOKENPAK_BIND_ADDRESS=0.0.0.0 \
  -e TOKENPAK_PROXY_AUTH_TOKEN="$TOKENPAK_PROXY_AUTH_TOKEN" \
  tokenpak:v1.24.0 python -m tokenpak.proxy.server
```

The host-side loopback publish keeps the service off the LAN. Docker bridge
traffic is non-localhost traffic from the proxy's perspective, so the Bearer
credential is still required.

## 5. Verify the deployment

Call the host-published health endpoint with the credential from step 3:

```bash
curl -H "Authorization: Bearer $TOKENPAK_PROXY_AUTH_TOKEN" \
  http://127.0.0.1:8766/health
```

The deployment is ready when the response includes `"status": "ok"` and
`"version": "1.24.0"`.

## Optional custom configuration

Built-in defaults are used when `TOKENPAK_CONFIG` is omitted. To replace the
running container with one that mounts a specific configuration, first create
the host file, then stop the current container and pass the file's container
path explicitly:

```bash
test -f "$PWD/config/config.yaml"
docker stop tokenpak-proxy

docker run --rm -d --name tokenpak-proxy \
  -p 127.0.0.1:8766:8766 \
  -e TOKENPAK_BIND_ADDRESS=0.0.0.0 \
  -e TOKENPAK_PROXY_AUTH_TOKEN="$TOKENPAK_PROXY_AUTH_TOKEN" \
  -e TOKENPAK_CONFIG=/app/config/config.yaml \
  -v "$PWD/config/config.yaml:/app/config/config.yaml:ro" \
  tokenpak:v1.24.0 python -m tokenpak.proxy.server
```

Proxy authentication and provider authentication are separate. The
`Authorization: Bearer` value above authenticates a non-localhost client to
TokenPak and is stripped before forwarding. Configure provider credentials
separately through the client or the proxy's provider credential settings.

## Optional Docker Compose deployment

The repository's v1.24.0 `docker-compose.yml` is not an out-of-the-box
host-facing deployment recipe: it retains the container-loopback entrypoint
and requires `./config/config.yaml`. Do not use that file unchanged for host
access.

For a minimal host-loopback deployment, save this as `compose.host.yml`:

```yaml
services:
  tokenpak:
    image: tokenpak:v1.24.0
    container_name: tokenpak-proxy
    command: ["python", "-m", "tokenpak.proxy.server"]
    ports:
      - "127.0.0.1:8766:8766"
    environment:
      TOKENPAK_BIND_ADDRESS: "0.0.0.0"
      TOKENPAK_PROXY_AUTH_TOKEN: "${TOKENPAK_PROXY_AUTH_TOKEN:?set TOKENPAK_PROXY_AUTH_TOKEN}"
    restart: unless-stopped
```

Then stop any single-container deployment and start Compose with the credential
created in step 3:

```bash
docker stop tokenpak-proxy 2>/dev/null || true
docker compose -f compose.host.yml up -d
docker compose -f compose.host.yml ps
```

Add a read-only config mount and `TOKENPAK_CONFIG` only when the host file
actually exists, as shown in the single-container recipe.

## Health and diagnostics

Inspect the Dockerfile health check:

```bash
docker inspect --format '{{json .State.Health}}' tokenpak-proxy
```

Run a container-local check with Python. The slim image does not include
`curl`, and a request from container loopback does not require proxy auth:

```bash
docker exec tokenpak-proxy python -c \
  "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8766/health', timeout=5).read().decode())"
```

View process output through Docker rather than assuming an application log
path inside the image:

```bash
docker logs --tail 100 tokenpak-proxy
docker logs -f tokenpak-proxy
```

## Resource limits

Docker can apply CPU and memory limits without changing TokenPak. Replace the
running single-container deployment with the limited alternative:

```bash
docker stop tokenpak-proxy
docker run --rm -d --name tokenpak-proxy \
  --cpus 1 --memory 512m \
  -p 127.0.0.1:8766:8766 \
  -e TOKENPAK_BIND_ADDRESS=0.0.0.0 \
  -e TOKENPAK_PROXY_AUTH_TOKEN="$TOKENPAK_PROXY_AUTH_TOKEN" \
  tokenpak:v1.24.0 python -m tokenpak.proxy.server
```

## Stop or remove the container

The `--rm` single-container recipe removes the stopped container while keeping
the locally built image:

```bash
docker stop tokenpak-proxy
```

For the Compose recipe:

```bash
docker compose -f compose.host.yml down
```

## Deployment boundary

Kubernetes, public reverse proxies, and cloud container services require the
same two controls: a non-loopback bind inside the container and a configured
`TOKENPAK_PROXY_AUTH_TOKEN` presented by every non-localhost client. TokenPak
v1.24.0 does not ship a separately verified Kubernetes or cloud-service
manifest, so this guide does not present those platform-specific snippets as
copy-paste deployment recipes.

Never expose port 8766 publicly without proxy authentication and an external
TLS boundary.
