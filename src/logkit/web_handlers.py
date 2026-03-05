import os
import logging
import requests

from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

from requests.exceptions import (
    HTTPError,
    Timeout,
    RequestException,
    ConnectionError
)

from .handlers import Defaults


class TelegramHandler(logging.Handler):
    """Logging handler that sends records to Telegram chats.

    Chat IDs are resolved from bot update history for provided usernames.
    """

    def __init__(
        self,
        token: str,
        username: str | list[str],
        prefix: str = "",
        notify_levels: list[str] = ["INFO", "ERROR", "CRITICAL", "WARNING"],
        only_level: str | None = None,
    ) -> None:
        """Initialize Telegram handler configuration.

        Args:
            token: Telegram bot token.
            username: One username or a list of usernames to notify.
            prefix: Optional message prefix.
            notify_levels: Levels that should trigger active notifications.
            only_level: If set, send only records with this exact level name.

        Examples:
            >>> handler = TelegramHandler("BOT_TOKEN", ["username"])
        """
        super().__init__()
        self.setLevel(Defaults().level)
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{self.token}"

        self.unames = [username, ] if isinstance(username, str) else username
        self.chatid = self.get_chatids(self.unames)

        self.prefix = prefix
        self.notify_levels = notify_levels
        self.only_level = only_level
        self.host = os.uname()[1]


    def get_chatids(self, usernames: list[str]) -> list[int]:
        url = f"{self.base_url}/getUpdates"
        response = requests.get(url)

        assert response.status_code == 200, \
            f"Smth is off with Telegram handler, double check token"

        response_json = response.json()

        existed_chats = {}
        for update in response_json["result"]:
            if "message" in update:
                msg = update["message"]
                username = msg["from"].get("username")
                chat_id = msg["chat"]["id"]

                existed_chats[username] = chat_id

        for uname in usernames:
            assert uname in existed_chats.keys(), \
                f"{uname} does not have a chat history with bot"

        return [existed_chats[un] for un in usernames]


    def send_msg(self, text, disable_notification):
        if self.prefix != "":
            text = self.prefix + " " + text

        for cid in self.chatid:
            json_data = {
                "chat_id": cid,
                "text": text,
                "disable_notification": disable_notification,
                "link_preview_options": {
                    "is_disabled": True,
                },
            }
            try:
                response = requests.post(
                    f"{self.base_url}/sendMessage",
                    json=json_data,
                    timeout=10
                )
                response.raise_for_status()
            except (HTTPError, ConnectionError, Timeout, RequestException):
                # TODO Should i do smthing in case of error?
                pass

    def emit(self, record: logging.LogRecord) -> None:
        if self.only_level is None or (self.only_level == record.levelname):
            msg = self.format(record)
            app_name = getattr(record, "app_name", "<app_unknown>")
            disable_notify = True
            if record.levelname in self.notify_levels:
                disable_notify = False

            host_to_tag = self.host.replace("-", "_").replace("/", "_")
            app_to_tag = str(app_name).replace("-", "_").replace("/", "_").replace(".py", "")
            msg = f"{record.levelname}: {msg}\n" \
                  f"at: {self.host} (#{host_to_tag})\n" \
                  f"app: {app_name} (#{app_to_tag})\n"
            self.send_msg(msg, disable_notify)


# TBD: Seq Handler
#     seq_handler = SeqHandler(
#         application=application,
#         server_url="",
#         api_key="",
#         email_group=email_group,
#     )
# class SeqHandler(logging.Handler):
#     def __init__(
#         self,
#         application: str,
#         server_url: str,
#         api_key: str,
#         email_group: str | None = None
#     ) -> None:
#         super().__init__()
#         self.setLevel(logging.INFO)
#         self.server_url = server_url
#         self.api_key = api_key
#         self.email_group = email_group

#         self.application = application
#         self.host = os.uname()[1]

#     def emit(self, record: logging.LogRecord) -> None:
#         msg = self.format(record)
#         classname = record.name.replace("point_cloud_segm.", "").replace("point_cloud_segm", "")
#         classname = "<top-level-func>" if classname == "" else classname

#         url = f"{self.server_url}/api/events/raw?clef?apiKey={self.api_key}"
#         payload = {
#             "@t": datetime.fromtimestamp(record.created).isoformat(),
#             "@m": msg,
#             "@l": record.levelname,
#             "host": self.host,
#             "application": self.application,
#             "logger": record.name,
#             "pathname": record.pathname,
#             "class": classname,
#             "method": record.funcName,
#             "at_line": record.lineno,
#         }

#         if self.email_group is not None:
#             payload["email_group"] = self.email_group

#         if isinstance(record.args, dict):
#             payload = {**payload, **record.args}

#         try:
#             headers = {"Content-type": "application/vnd.serilog.clef"}
#             res = requests.post(url, json=payload, headers=headers)
#         except Exception as exc:
#             msg = f"Unable to send logs to Seq, stop to {type(exc)} - {exc}"
#             # TODO remove Seq handler from logger and keep logging using other.
#             print(msg)
