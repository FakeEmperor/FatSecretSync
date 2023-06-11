# FatSecret Sync Bot

Syncs food between users. 
Use case is that people might share the same or similar diet.
This allows one of them (or both) to share information about 
food entries and save time;

Provides a Telegram Bot to check on sync status and get summary
information quickly.

## Installation instructions

- Obtain necessary authentication credentials:
  - Obtain FatSecret API keys;
  - Obtain all participating users' access. See below how to do that;
  - Obtain Telegram Bot credentials using [@BotFather](https://t.me/BotFather);
- Start Telegram Bot.

  You can use Docker to start the telegram bot. This project provides a sample
  `docker-compose.yml` file. Please use instructions in `.env.example`  
  and create your personal `.env` file with all the credentials, 
  after which you can run `docker-compose up` and start the bot.

### Using Docker to start Telegram Bot

Telegram Bot stores authentication credentials in a file called `creds.yaml`.
This file should be persistent and mounted in Docker run command:

```bash
docker build . -t fatsecret-sync-bot:latest --progress=plain
docker run --name=fatsecret-sync-bot -v ./creds.yaml:/app/creds.yaml fatsecret-sync-bot:latest
```

As mentioned above, you can use `docker compose` to run the bot:

```bash
docker compose up
```

On successful run, you will see a log message:

```
Successfully logged in as @<BOT_USER> (https://t.me/<BOT_USER>)
```

### Obtaining User access using Telegram Bot

After starting Telegram Bot, you can use `/register` command to register a user.
The bot will send you a link to FatSecret App Authorization page, 
that you need to pass to the user in question.

It will prompt the user to give access to user data, and will give back a PIN code.
User must give the PIN code back and you need to paste it for the bot.

```plain
You: /register
Bot: 👼 Okay, let's add another user! Here's the link: https://fatsecret.com/auth/...
     Please keep in mind that the link expires in 30 minutes.
You: 0000
Bot: ✅ Great, registration finished and the user is checked!
<or>
Bot: ❌ Oh, no! PIN is incorrect or the link is expired. 
     Try again?
```

If there is an error during registration or User declined access, use `/cancel` 
command to start again or go back.

### Obtaining User access using CLI

It is almost the same process: the only difference is, obviously that is not 
being run in Telegram's context. You may use command-line tool to register the user:

```bash
fatsecret-sync authorize --save
```

Or, if using Docker:

```
docker build . -t fatsecret-sync-bot:latest --progress=plain
docker run --rm -it -v ./creds.yaml:/app/creds.yaml fatsecret-sync-bot:latest fatsecret-sync authorize --save
```

And follow instructions from command-line tool.


## Command-line help

```plain

```