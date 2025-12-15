FROM mcr.microsoft.com/devcontainers/python:1-3.13-bookworm

ENV PYTHONUNBUFFERED 1

RUN pip install uv pytest==9.0.2 pytest-cov==7.0.0 pytest-mock==3.15.1

COPY requirements.txt /tmp/pip-tmp/
RUN uv pip install --no-cache --system -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp
