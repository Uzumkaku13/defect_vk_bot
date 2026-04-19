from __future__ import annotations

from vkbottle.bot import Bot, Message

from config import VK_TOKEN
from keyboards.main_menu import BTN_FINISH, get_main_menu
from services.pdf_generator import build_pdf
from services.report_service import finalize_report, get_active_report, get_defects
from services.vk_docs import upload_doc_to_vk
from storage import clear_user_state


def register_defect_handlers(bot: Bot) -> None:
    @bot.on.message(text=BTN_FINISH)
    async def finish_report_handler(message: Message):
        report = get_active_report(message.from_id)
        if not report:
            await message.answer("Нет активного черновика.", keyboard=get_main_menu())
            return

        defects = get_defects(report["id"])
        if not defects:
            await message.answer("Список дефектов пуст. Добавьте хотя бы один дефект.", keyboard=get_main_menu())
            return

        try:
            pdf_path = build_pdf(report["id"])
            attachment = upload_doc_to_vk(VK_TOKEN, message.peer_id, str(pdf_path))
        except Exception as exc:
            await message.answer(
                f"Не удалось сформировать или отправить PDF: {exc}",
                keyboard=get_main_menu(),
            )
            return

        finalize_report(report["id"], str(pdf_path))
        clear_user_state(message.from_id)

        await message.answer(
            f"Готово. Дефектная ведомость {report.get('report_number', 'без номера')} сформирована и отправлена.",
            attachment=attachment,
            keyboard=get_main_menu(),
        )
