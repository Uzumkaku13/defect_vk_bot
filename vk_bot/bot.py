from __future__ import annotations

import logging

from vkbottle.bot import Bot

from config import VK_TOKEN, LOG_LEVEL
from init_db import init_db
from handlers import (
    register_main_handlers,
    register_report_handlers,
    register_analytics_handlers,
    register_defect_handlers,
    register_photo_handlers,
    register_flow_handlers,
)


def main() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    init_db()
    bot = Bot(token=VK_TOKEN)

    register_main_handlers(bot)
    register_report_handlers(bot)
    register_analytics_handlers(bot)
    register_defect_handlers(bot)
    register_photo_handlers(bot)
    register_flow_handlers(bot)

    bot.run_forever()


if __name__ == "__main__":
    main()
