FROM node:20-bookworm

ARG STUDIAMATCH_UID=1000
ARG STUDIAMATCH_GID=1000

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PATH="/opt/venv/bin:${PATH}" \
    STUDIAMATCH_UID=${STUDIAMATCH_UID} \
    STUDIAMATCH_GID=${STUDIAMATCH_GID} \
    HOME=/home/studiamatch

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-venv \
        python3.11-dev \
        build-essential \
        libpq-dev \
        ca-certificates \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-pipeline.txt /tmp/requirements-pipeline.txt

RUN python3.11 --version \
    && python3.11 -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install "pip==25.2" \
    && /opt/venv/bin/python -m pip install --require-hashes -r /tmp/requirements-pipeline.txt \
    && /opt/venv/bin/python --version

RUN apt-get update \
    && /opt/venv/bin/python -m playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/node-staging/web
COPY web/package.json web/package-lock.json /opt/node-staging/web/

RUN cd /opt/node-staging/web \
    && npm ci \
    && sha256sum package.json package-lock.json > /opt/node-staging/web/manifests.sha256

RUN getent group "${STUDIAMATCH_GID}" >/dev/null 2>&1 || groupadd --gid "${STUDIAMATCH_GID}" studiamatch
RUN getent passwd "${STUDIAMATCH_UID}" >/dev/null 2>&1 || useradd --uid "${STUDIAMATCH_UID}" --gid "${STUDIAMATCH_GID}" --create-home --shell /bin/bash studiamatch
RUN if [ "${STUDIAMATCH_UID}" = "0" ] || [ "${STUDIAMATCH_GID}" = "0" ]; then echo "ERROR: STUDIAMATCH_UID/STUDIAMATCH_GID must not be 0 (root runtime is not allowed)" >&2; exit 1; fi
RUN chown -R "${STUDIAMATCH_UID}:${STUDIAMATCH_GID}" /opt/node-staging
RUN install -d -o "${STUDIAMATCH_UID}" -g "${STUDIAMATCH_GID}" /home/studiamatch \
    && mkdir -p /app/web \
    && cp -a /opt/node-staging/web/. /app/web/ \
    && printf 'STUDIAMATCH_UID=%s\nSTUDIAMATCH_GID=%s\n' "${STUDIAMATCH_UID}" "${STUDIAMATCH_GID}" > /app/web/node_modules/.studiamatch-node-deps.sha256 \
    && cat /opt/node-staging/web/manifests.sha256 >> /app/web/node_modules/.studiamatch-node-deps.sha256

COPY init-container.sh /usr/local/bin/studiamatch-bootstrap
RUN chmod 0755 /usr/local/bin/studiamatch-bootstrap

WORKDIR /app
EXPOSE 3000
USER ${STUDIAMATCH_UID}:${STUDIAMATCH_GID}
ENTRYPOINT ["/usr/local/bin/studiamatch-bootstrap"]
