"""A basic Telegram bot implemented as a Steamship package that uses a few Tools to accomplish tasks."""
import logging
import uuid
from typing import Type, Optional, Dict, Any

from pydantic import Field
from steamship import Block, Tag
from steamship.invocable import Config, InvocableResponse, PackageService, post

from steamship.experimental.tools.generate_speech import GenerateSpeechTool
from steamship.experimental.transports import TelegramTransport
from steamship.experimental.transports.chat import ChatMessage, ChatTag
from steamship.experimental.transports.steamship_widget import SteamshipWidgetTransport


def is_valid_uuid(uuid_to_test: str, version=4) -> bool:
    """Check a string to see if it is actually a UUID."""
    lowered = uuid_to_test.lower()
    try:
        uuid_obj = uuid.UUID(lowered, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == lowered


class VoiceGenBotConfig(Config):
    """Config object containing required parameters to initialize a MyPackage instance."""

    bot_token: str = Field(description="The secret token for your Telegram bot")
    use_gpt4: bool = Field(
        False,
        description="If True, use GPT-4 instead of GPT-3.5 to generate responses. "
        "GPT-4 creates better responses at higher cost and with longer wait times.",
    )


class VoiceGenBot(PackageService):
    """Implements a basic Telegram Bot that provides a dalle command."""

    config: VoiceGenBotConfig

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.web_transport = SteamshipWidgetTransport()
        self.telegram_transport = TelegramTransport(bot_token=self.config.bot_token)
        self._known_tools = [
            GenerateSpeechTool(client=self.client)
        ]

    @classmethod
    def config_cls(cls) -> Type[Config]:
        """Return the Configuration class."""
        return VoiceGenBotConfig

    def instance_init(self):
        """This instance init method is called automatically when an instance of this package is created. It registers the URL of the instance as the Telegram webhook for messages."""
        webhook_url = self.context.invocable_url + 'telegram_respond'
        self.telegram_transport.instance_init(webhook_url=webhook_url)
        self.web_transport.instance_init()

    def _get_preempting_tool_response(self, chat_block: ChatMessage) -> Optional[ChatMessage]:
        """Create an output if one is warranted. Otherwise return None."""
        for tool in self._known_tools:
            if tool.should_preempt_agent(chat_block.text) > 0.8:
                prompt = tool.preempt_agent_prompt(chat_block.text)
                response_block = tool.run(prompt)
                if is_valid_uuid(response_block):
                    block = Block.get(self.client, _id=response_block)
                    # Turn it into a chat block
                    chat_block = ChatMessage(client=block.client, chat_id=chat_block.get_chat_id(), **block.dict())
                    return chat_block

        return None

    @post("info")
    def info(self) -> dict:
        """Endpoint returning information about this bot."""
        info = self.telegram_transport.info()
        logging.info(f"/info: {info}")
        return info

    @post("telegram_respond", public=True)
    def telegram_respond(self, update_id: int, message: dict, **kwargs) -> InvocableResponse[str]:
        """Endpoint implementing the Telegram WebHook contract. This is a PUBLIC endpoint since Telegram cannot pass a Bearer token."""
        input_block = self.telegram_transport.parse_inbound(payload=message)
        output_block = self._get_preempting_tool_response(input_block)
        logging.info(f"Output block tags: {output_block.tags}")
        if output_block:
            self.telegram_transport.send([output_block])

        return InvocableResponse(string="OK")

    @post("/answer", public=True)
    def answer(
            self, question: str, chat_session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        input_block = self.web_transport.parse_inbound(payload={
            "question": question,
            "chat_session_id": chat_session_id
        })
        output_block = self._get_preempting_tool_response(input_block)
        if output_block:
            logging.info(f"Output block tags: {output_block.tags}")
            # Return block format JSON
            output_dict = output_block.dict()
            output_dict["who"] = "bot"
            return output_dict
        else:
            return {}