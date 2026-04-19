from __future__ import annotations

from vkbottle.bot import Bot, Message

from keyboards.main_menu import BTN_CANCEL, BTN_CONTINUE, BTN_NEW, get_main_menu
from services.report_service import (
    cancel_active_report,
    create_report,
    get_active_report,
    get_defects,
    get_next_state_for_report,
)
from states import States
from storage import clear_user_state, set_user_state

MAIN_MENU_TEXT = (
    "Главное меню:\n"
    "1) Новая ведомость\n"
    "2) Продолжить черновик\n"
    "3) Завершить и получить PDF\n"
    "4) Мои ведомости\n"
    "5) Статистика\n"
    "6) Отменить текущую"
)


def _prompt_for_state(state: str) -> str:
    if state == States.WAIT_CLIENT_NAME:
        return "Введите ФИО / название клиента:"
    if state == States.WAIT_CLIENT_PHONE:
        return "Введите телефон клиента:"
    if state == States.WAIT_OBJECT_NAME:
        return "Введите объект / место проведения ремонта:"
    if state == States.WAIT_EQUIPMENT:
        return "Введите технику / узел / агрегат:"
    if state == States.WAIT_COMMENT:
        return "Введите комментарий или краткое описание ситуации:"
    return (
        "Черновик восстановлен. Отправляйте дефекты по одному сообщению. "
        "Можно прикладывать фото. Когда закончите, нажмите "
        "«✅ Завершить и получить PDF»."
    )


def register_main_handlers(bot: Bot) -> None:
    @bot.on.message(text=["/start", "start", "старт", "меню"])
    async def start_handler(message: Message):
        await message.answer(MAIN_MENU_TEXT, keyboard=get_main_menu())

    @bot.on.message(text=BTN_NEW)
    async def new_report(message: Message):
        current = get_active_report(message.from_id)
        if current:
            next_state = get_next_state_for_report(current)
            defects = get_defects(current["id"])
            set_user_state(message.from_id, next_state, {"report_id": current["id"]})
            await message.answer(
                f"У вас уже есть незавершенный черновик {current.get('report_number') or ('№' + str(current['id']))}.\n"
                f"Заполнено: клиент={current.get('client_name') or '—'}, "
                f"объект={current.get('object_name') or '—'}, техника={current.get('equipment') or '—'}.\n"
                f"Дефектов: {len(defects)}.\n\n"
                f"{_prompt_for_state(next_state)}",
                keyboard=get_main_menu(),
            )
            return

        report_id = create_report(message.from_id)
        set_user_state(message.from_id, States.WAIT_CLIENT_NAME, {"report_id": report_id})
        await message.answer("Введите ФИО / название клиента:", keyboard=get_main_menu())

    @bot.on.message(text=BTN_CONTINUE)
    async def continue_draft(message: Message):
        report = get_active_report(message.from_id)
        if not report:
            await message.answer("Активного черновика нет. Нажмите «Новая ведомость».", keyboard=get_main_menu())
            return

        next_state = get_next_state_for_report(report)
        defects = get_defects(report["id"])
        set_user_state(message.from_id, next_state, {"report_id": report["id"]})
        await message.answer(
            "Черновик восстановлен.\n"
            f"{report.get('report_number') or ('№' + str(report['id']))}\n"
            f"Клиент: {report.get('client_name') or '—'}\n"
            f"Телефон: {report.get('client_phone') or '—'}\n"
            f"Объект: {report.get('object_name') or '—'}\n"
            f"Техника: {report.get('equipment') or '—'}\n"
            f"Комментарий: {report.get('comment') or '—'}\n"
            f"Дефектов: {len(defects)}\n\n"
            f"{_prompt_for_state(next_state)}",
            keyboard=get_main_menu(),
        )

    @bot.on.message(text=[BTN_CANCEL, "отмена", "/cancel"])
    async def cancel_current(message: Message):
        ok = cancel_active_report(message.from_id)
        clear_user_state(message.from_id)
        if ok:
            await message.answer("Текущий черновик удален.", keyboard=get_main_menu())
        else:
            await message.answer("Активного черновика нет.", keyboard=get_main_menu())
