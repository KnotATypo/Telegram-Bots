# Telegram Bots

This package contains a Flask app that hosts two Telegram bots: the "Expiry Bot" and the "Tools Bot". Detailed
information about each bot can be found in their respective directories.

## Setup

To use these Telegram bots, you will need to set up webhooks, meaning you will need a reachable HTTPS endpoint.

There are a bunch of ways to do this, such as using services
like [ngrok](https://ngrok.com), [localtunnel](https://localtunnel.app/) or deploying to a cloud service
like [AWS Lambda](https://aws.amazon.com/lambda/) or [Google Cloud Functions](https://cloud.google.com/functions).

Personally, I host my own domain with a reverse proxy to route requests in my local network to the bots. Either way,
setting up this HTTPS endpoint is outside the scope of this guide.

This setup guide assumes you have already created the Telegram bots using BotFather. If you haven't done so yet, please
navigate to [BotFather](https://t.me/botfather) on Telegram and create the bots you need with `/newbot`. You might also
find value in skimming through the [official tutorial](https://core.telegram.org/bots/tutorial).

### Local Bot API Instance [Optional]

The Telegram Bot API can be run locally if you want to avoid using the cloud-hosted version. The advantages of running a
local instance can be found in
the [official documentation](https://core.telegram.org/bots/api#using-a-local-bot-api-server). Personally, I have found
that some videos for the "Power meter" feature of the Tools Bot end up being too large for the cloud-hosted API to
handle, so I run a local instance to avoid the 20MB limit.

Instructions for building and running the local Bot API server can be found in
the [GitHub repository](https://github.com/tdlib/telegram-bot-api).

### Webhooks

To set up webhooks for your Telegram bots, you need to send a request to the Telegram Bot API to register the webhook
URL for each bot. If you're using a local Bot API instance, make sure to point the request to your local server.

```bash
curl https://api.telegram.org/bot<TOKEN>/setWebhook?url=<WEBHOOK_URL>/webhook&secret_token=<SECRET>
```

### .env

#### Template

```dotenv
BOT_API_URL=
DATABASE_PATH=

EXPIRY_BOT_TOKEN=
EXPIRY_BOT_SECRET=

TOOLS_BOT_TOKEN=
TOOLS_BOT_SECRET=
```

#### Description

- `BOT_API_URL`: The base URL for the bot API. This will be https://api.telegram.org if you're using the cloud API,
  otherwise it will be your local instance such as http://localhost:8081.
- `DATABASE_PATH`: The path to the SQLite database file used by bots that require persistent storage.
- `*_BOT_TOKEN`: The API TOKEN for the given bot. This is obtained from BotFather through `/mybots` > Select your bot >
  API Token.
- `*_BOT_SECRET`: The API secret for the given bot. This is set by you when you create the webhook for your bot (
  instructions above).

## Running the App

This package is run with [uv](https://docs.astral.sh/uv/). If you don't have it installed, you can follow the
appropriate instructions for your platform from
the [official documentation](https://docs.astral.sh/uv/getting-started/installation/).

Once you have uv installed, you can run the app from the root directory with the following command:

```bash
uv run start-bots
```
