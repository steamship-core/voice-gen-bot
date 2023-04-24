"""Run a local version of the bot."""
from steamship import Steamship
from utils import use_local_with_ngrok

from api import VoiceGenBot

BOT_TOKEN = ""

if __name__ == "__main__":
    client = Steamship()
    config = {
        "bot_token": "6122588092:AAEioCXNaLm6zH7dfi-pvGoxcU6BrgmQrX8",
        "use_gpt4": False,
    }
    use_local_with_ngrok(client, VoiceGenBot, config=config, port=8084)
