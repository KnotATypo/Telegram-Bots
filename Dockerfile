FROM uv:debian-slim

RUN apt update && apt install libsystemd-dev gcc pkg-config ffmpeg -y && apt clean && rm -rf /var/lib/apt/lists/*

RUN mkdir telegram-bots
WORKDIR /telegram-bots

COPY . .

ENTRYPOINT ["uv", "run", "start-bots"]