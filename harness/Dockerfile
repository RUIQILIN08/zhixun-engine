FROM docker.m.daocloud.io/library/python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /opt/contest-harness

COPY platform/sdk/contest-harness-sdk-1.0.2/pyproject.toml /opt/contest-harness/pyproject.toml
COPY platform/sdk/contest-harness-sdk-1.0.2/contest_harness /opt/contest-harness/contest_harness
RUN pip install --no-cache-dir -i "$PIP_INDEX_URL" /opt/contest-harness

COPY harness/requirements.txt /opt/app/requirements.txt
RUN pip install --no-cache-dir -i "$PIP_INDEX_URL" -r /opt/app/requirements.txt

COPY harness/app /app

WORKDIR /app

ENTRYPOINT ["python3", "/app/harness.py"]

