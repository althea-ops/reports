FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System toolchain: Python for the report scripts, LibreOffice (Impress) for the
# PPTX -> PDF export step in scripts/build_report.py, plus git/curl for tooling.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        python3-pip \
        libreoffice-impress \
        libreoffice-core \
        fonts-dejavu-core \
        git \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Use an isolated virtualenv so `pip install` works on Ubuntu 24.04
# (PEP 668 externally-managed) without --break-system-packages.
RUN python3 -m venv /opt/venv \
    && chown -R ubuntu:ubuntu /opt/venv
ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

USER ubuntu
