# Two-minute demonstration

Prerequisite: Docker with Compose and a running Linux-container daemon. No host
ports are published. Run from this repository in PowerShell. **Builds and container runs were verified with Docker 29.8.1, Compose 5.5.1
and container Python 3.14.8: mixed exits 1 twice, healthy exits 0.** First image download/build can take longer
than two minutes; the demonstration itself is short after building. Use the
project/name below only if they are not already used by unrelated work.

```powershell
docker compose -p endpointcheck-demo config --quiet
docker compose -p endpointcheck-demo build
docker compose -p endpointcheck-demo up --abort-on-container-exit --exit-code-from inspector
$mixedWrapperExit = $LASTEXITCODE
$inspectorId = docker compose -p endpointcheck-demo ps -aq inspector
docker inspect --format '{{.State.ExitCode}}' $inspectorId
docker compose -p endpointcheck-demo logs inspector
```

Expected inspector exit: **1**. The wrapper should propagate it; `docker inspect`
checks the actual inspector process independently. The report order is healthy,
slow, error, timeout; outcomes are healthy, slow, failed, timed out, and the
summary counts are one each. Timeout retains HTTP 200. Durations vary.

Repeat the mixed run, then run the healthy scenario:

```powershell
docker compose -p endpointcheck-demo up --force-recreate --abort-on-container-exit --exit-code-from inspector
$repeatWrapperExit = $LASTEXITCODE
$inspectorId = docker compose -p endpointcheck-demo ps -aq inspector
docker inspect --format '{{.State.ExitCode}}' $inspectorId
docker compose -p endpointcheck-demo up -d --wait demo-api
docker compose -p endpointcheck-demo run --name endpointcheck-demo-healthy inspector check /app/demo/all-healthy.json
$healthyWrapperExit = $LASTEXITCODE
docker inspect --format '{{.State.ExitCode}}' endpointcheck-demo-healthy
```

Expected healthy inspector exit: **0**, summary healthy=1, all other counts=0.
The fixed one-off name makes its exit inspectable; remove it before repeating.
Do not infer an inspector exit from a failed build/start wrapper.

Runtime verification observed Compose marking the API healthy before starting
inspector, and health-check completion timestamps preceded inspector start.
Live `docker top CONTAINER -eo uid,pid,args` showed UID 10001 for both processes.
The mixed API shutdown exited 137 when Compose stopped it; this is separate from
the inspector's expected exit 1. Graceful API SIGTERM handling is not implemented.

Cleanup only these demonstration resources:

```powershell
docker rm endpointcheck-demo-healthy
docker compose -p endpointcheck-demo down
```

This removes demonstration containers and network; built images/cache remain
available for later runs. No global prune or removal of unrelated resources.

Health checks use `/ready`; inspector starts after API health is observed.
Readiness is a startup check, not a guarantee the API remains available.
Services communicate using `demo-api:8000` on their Compose network; localhost
inside inspector would refer to inspector itself. Both processes run as UID
10001. The API is a controlled standard-library demonstration, not a production
server. Existing timeout and finite-response limitations still apply; see
[REQUIREMENTS.md](REQUIREMENTS.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

Locally verified fallback (no Docker required):

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_demo_api.py -s
```

These tests start ephemeral loopback servers, adapt only the demo hostname/port,
and capture real module CLI reports and process exit codes. They do not verify
container networking, image installation, Linux execution or Compose readiness.
