FROM python:3.13-alpine

WORKDIR /app

RUN apk add --no-cache git && pip install --no-cache-dir uv

# Install obs-python (includes BAC0, PyYAML)
ARG OBS_PYTHON_REF=main
RUN uv pip install --system "git+https://github.com/C4SBF/obs-python.git@${OBS_PYTHON_REF}"

# Install CLI
COPY pyproject.toml README.md /app/
COPY src/ /app/src/
RUN uv pip install --system --no-deps /app

ENV PYTHONUNBUFFERED=1
VOLUME /data
WORKDIR /data

ENTRYPOINT ["obs"]
CMD ["--help"]
