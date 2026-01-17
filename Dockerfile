FROM python:3.14-slim

RUN apt update && apt install wget libsystemd-dev gcc pkg-config ffmpeg -y && apt clean && rm -rf /var/lib/apt/lists/*
RUN wget -qO- https://astral.sh/uv/install.sh | sh

RUN mkdir telegram-bots
WORKDIR /telegram-bots
COPY . .
RUN /root/.local/bin/uv sync

ENV PYTHONUNBUFFERED=1
EXPOSE 5000

ENTRYPOINT ["/root/.local/bin/uv", "run", "start-bots"]