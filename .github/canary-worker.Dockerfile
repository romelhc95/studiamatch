FROM python:3.11-slim@sha256:db3ff2e1800a8581e2c48a27c3995339d47bdf046da21c7627accd3d51053a93

WORKDIR /app
RUN python -m pip install --no-cache-dir \
    beautifulsoup4==4.12.3 \
    PyPDF2==3.0.1 \
    python-dotenv==1.0.1 \
    regex==2024.11.6 \
    requests==2.32.3
COPY scripts ./scripts
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin canary
USER 10001:10001

ENTRYPOINT ["python"]
