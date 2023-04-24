In the course of developing your own extensions to this bot, you will
likely want/need the ability to run the bot locally. Running locally
will enable use of the debugger (as well as tigher retry loops).

## Run locally

To run the bot locally, use the `tests/run_server.py` script. You will
need to supply your own the `botToken` in the script.

Once it is up and running, you can use Telegram to exchange messages with
the bot.

## NOTE

The `Reminder` tool will not work in local-mode operation. Your package
**must** be deployed to use the `Reminder` functionality appropriately.