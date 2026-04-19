from __future__ import annotations

from vkbottle.bot import Bot, Message
from keyboards.main_menu import get_main_menu, is_menu_command
from services.report_service import (
    update_report_client,
    update_report_object,
    update_report_equipment,
    update_report_comment,
)
from storage import get_user_state, set_user_state
from states import States


def register_client_handlers(bot: Bot) -> None:
    @bot.on.message()
    async def client_flow(message: Message):
        state, payload = get_user_state(message.from_id)
        report_id = payload.get("report_id")
        text = (message.text or "").strip()

        if not report_id or not text or is_menu_command(text):
            return

        if state == States.WAIT_CLIENT_NAME:
            update_report_client(report_id, client_name=text)
            set_user_state(message.from_id, States.WAIT_CLIENT_PHONE, {"report_id": report_id})
            await message.answer("Введите телефон клиента:", keyboard=get_main_menu())
            return

        if state == States.WAIT_CLIENT_PHONE:
            update_report_client(report_id, client_phone=text)
            set_user_state(message.from_id, States.WAIT_OBJECT_NAME, {"report_id": report_id})
            await message.answer("Введите объект / место проведения ремонта:", keyboard=get_main_menu())
            return

        if state == States.WAIT_OBJECT_NAME:
            update_report_object(report_id, text)
            set_user_state(message.from_id, States.WAIT_EQUIPMENT, {"report_id": report_id})
            await message.answer("Введите технику / узел / агрегат:", keyboard=get_main_menu())
            return

        if state == States.WAIT_EQUIPMENT:
            update_report_equipment(report_id, text)
            set_user_state(message.from_id, States.WAIT_COMMENT, {"report_id": report_id})
            await message.answer("Введите комментарий или краткое описание ситуации:", keyboard=get_main_menu())
            return

        if state == States.WAIT_COMMENT:
            update_report_comment(report_id, text)
            set_user_state(message.from_id, States.WAIT_DEFECT, {"report_id": report_id})
            await message.answer(
                "Теперь отправляйте дефекты по одному сообщению.\n"
                "Когда список закончится, нажмите «✅ Завершить и получить PDF».",
                keyboard=get_main_menu(),
            )
            return
