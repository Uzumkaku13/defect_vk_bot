from __future__ import annotations

from pathlib import Path
from typing import Any

from vkbottle.bot import Bot, Message

from keyboards.main_menu import get_main_menu, is_menu_command
from services.media_service import download_image
from services.report_service import (
    add_defect,
    get_defects,
    update_report_client,
    update_report_comment,
    update_report_equipment,
    update_report_object,
)
from handlers.report import send_saved_pdf_by_number
from states import States
from storage import get_user_state, set_user_state


def _attachment_type_name(attachment: Any) -> str:
    value = getattr(attachment, "type", None)
    if isinstance(value, str):
        return value.lower()
    return str(value).lower()


def _extract_photo_url(message: Message) -> str | None:
    attachments = getattr(message, "attachments", None) or []
    for att in attachments:
        if _attachment_type_name(att) != "photo":
            continue
        photo = getattr(att, "photo", None)
        sizes = getattr(photo, "sizes", None) or []
        best_url = None
        best_area = -1
        for size in sizes:
            url = getattr(size, "url", None)
            width = int(getattr(size, "width", 0) or 0)
            height = int(getattr(size, "height", 0) or 0)
            area = width * height
            if url and area >= best_area:
                best_area = area
                best_url = url
        if best_url:
            return best_url
    return None


def register_flow_handlers(bot: Bot) -> None:
    @bot.on.message()
    async def universal_flow(message: Message):
        text = (message.text or "").strip()
        state, payload = get_user_state(message.from_id)
        report_id = payload.get("report_id")

        if state == States.IDLE:
            if text.lower().startswith("файл "):
                tail = text[5:].strip()
                if not tail.isdigit():
                    await message.answer("Укажите номер так: файл 12", keyboard=get_main_menu())
                    return
                try:
                    attachment, caption = send_saved_pdf_by_number(message.from_id, message.peer_id, tail)
                except Exception as exc:
                    await message.answer(f"Не удалось отправить файл: {exc}", keyboard=get_main_menu())
                    return
                if not attachment:
                    await message.answer(caption, keyboard=get_main_menu())
                    return
                await message.answer(caption, attachment=attachment, keyboard=get_main_menu())
            return

        if is_menu_command(text):
            return

        if not report_id:
            await message.answer("Активный черновик не найден. Нажмите «🆕 Новая ведомость».", keyboard=get_main_menu())
            return

        if state == States.WAIT_CLIENT_NAME:
            if not text:
                await message.answer("Введите ФИО или название компании.", keyboard=get_main_menu())
                return
            update_report_client(report_id, client_name=text)
            set_user_state(message.from_id, States.WAIT_CLIENT_PHONE, {"report_id": report_id})
            await message.answer("Введите телефон клиента:", keyboard=get_main_menu())
            return

        if state == States.WAIT_CLIENT_PHONE:
            if not text:
                await message.answer("Введите телефон клиента.", keyboard=get_main_menu())
                return
            update_report_client(report_id, client_phone=text)
            set_user_state(message.from_id, States.WAIT_OBJECT_NAME, {"report_id": report_id})
            await message.answer("Введите объект / место проведения ремонта:", keyboard=get_main_menu())
            return

        if state == States.WAIT_OBJECT_NAME:
            if not text:
                await message.answer("Введите объект / место проведения ремонта.", keyboard=get_main_menu())
                return
            update_report_object(report_id, text)
            set_user_state(message.from_id, States.WAIT_EQUIPMENT, {"report_id": report_id})
            await message.answer("Введите технику / узел / агрегат:", keyboard=get_main_menu())
            return

        if state == States.WAIT_EQUIPMENT:
            if not text:
                await message.answer("Введите технику / узел / агрегат.", keyboard=get_main_menu())
                return
            update_report_equipment(report_id, text)
            set_user_state(message.from_id, States.WAIT_COMMENT, {"report_id": report_id})
            await message.answer("Введите комментарий или краткое описание ситуации:", keyboard=get_main_menu())
            return

        if state == States.WAIT_COMMENT:
            if not text:
                await message.answer("Введите комментарий или краткое описание ситуации.", keyboard=get_main_menu())
                return
            update_report_comment(report_id, text)
            set_user_state(message.from_id, States.WAIT_DEFECT, {"report_id": report_id})
            await message.answer(
                "Теперь отправляйте дефекты по одному сообщению. "
                "Можно добавить фото вместе с текстом. "
                "Когда список закончится, нажмите «✅ Завершить и получить PDF».",
                keyboard=get_main_menu(),
            )
            return

        if state == States.WAIT_DEFECT:
            photo_url = _extract_photo_url(message)
            photo_path = None
            if photo_url:
                try:
                    photo_path = download_image(photo_url, prefix=f"report_{report_id}")
                except Exception:
                    photo_path = None

            description = text or ("Фото дефекта" if photo_url else "")
            if not description:
                await message.answer(
                    "Отправьте текст дефекта или фото дефекта.",
                    keyboard=get_main_menu(),
                )
                return

            defect_id = add_defect(report_id, description, photo_url=photo_url, photo_path=photo_path)
            defects = get_defects(report_id)

            suffix = ""
            if photo_path and Path(photo_path).exists():
                suffix = " Фото сохранено для вставки в PDF."
            elif photo_url:
                suffix = " Фото обнаружено, но сохранить локально не удалось."

            await message.answer(
                f"Дефект #{defect_id} добавлен. Всего дефектов: {len(defects)}.{suffix}",
                keyboard=get_main_menu(),
            )
            return
