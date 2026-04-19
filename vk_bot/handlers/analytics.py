from __future__ import annotations

from vkbottle.bot import Bot, Message
from keyboards.main_menu import BTN_STATS, get_main_menu
from services.report_service import get_stats


def register_analytics_handlers(bot: Bot) -> None:
    @bot.on.message(text=BTN_STATS)
    async def show_stats(message: Message):
        stats = get_stats(message.from_id)
        await message.answer(
            "Статистика:\n"
            f"Всего ведомостей: {stats['total_reports']}\n"
            f"Завершено: {stats['done_reports']}\n"
            f"Черновиков: {stats['draft_reports']}\n"
            f"Всего дефектов: {stats['total_defects']}",
            keyboard=get_main_menu(),
        )
