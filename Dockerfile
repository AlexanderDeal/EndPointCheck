FROM python:3.14-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN groupadd --gid 10001 endpointcheck && useradd --uid 10001 --gid 10001 --no-create-home endpointcheck

FROM base AS demo-api
COPY demo_api /app/demo_api
USER 10001:10001
CMD ["python", "-m", "demo_api.server"]

FROM base AS inspector
COPY pyproject.toml /app/pyproject.toml
COPY endpointcheck /app/endpointcheck
RUN python -m pip install --no-cache-dir .
COPY demo /app/demo
USER 10001:10001
ENTRYPOINT ["endpointcheck"]
CMD ["check", "/app/demo/mixed.json"]
