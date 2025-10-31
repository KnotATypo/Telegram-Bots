## Setup .env
### Template
```dotenv
BOT_API_URL=

EXPIRY_BOT_TOKEN=
EXPIRY_BOT_SECRET=

TOOLS_BOT_TOKEN=
TOOLS_BOT_SECRET=
```
### Description
- `BOT_API_URL`: The base URL for the bot API. This will be https://api.telegram.org if you're using the cloud API, otherwise it will be your local instance such as http://localhost:8081.
- `*_BOT_TOKEN`: The API TOKEN for the given bot. This is obtained from BotFather through `/mybots` > Select your bot > API Token.
- `*_BOT_SECRET`: The API secret for the given bot. This is set by you when you create the webhook for your bot (instructions below).