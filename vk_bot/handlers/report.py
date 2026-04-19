from __future__ import annotations

from pathlib import Path

from vkbottle.bot import Bot, Message

from config import VK_TOKEN
from keyboards.main_menu import BTN_REPORTS, get_main_menu
from services.report_service import list_recent_reports
from services.vk_docs import upload_doc_to_vk


def build_reports_text(user_id: int) -> str:
    reports = list_recent_reports(user_id, limit=10)
    if not reports:
        return "У вас пока нет ведомостей."

    lines = ["Последние ведомости:"]
    for item in reports:
        number = item.get("report_number") or f"№ {item['id']}"
        lines.append(
            f"{number} | {item['status']} | {item.get('client_name') or '—'} | {item.get('equipment') or '—'}"
        )
    lines.append("")
    lines.append("Чтобы повторно получить готовый файл, отправьте: файл <номер_без_символа_№>")
    lines.append("Пример: файл 2026-0000001")
    return "\n".join(lines)


def send_saved_pdf_by_number(user_id: int, peer_id: int, number_text: str):
    reports = list_recent_reports(user_id, limit=200)
    normalized = number_text.strip().replace("№", "").strip()
    report = next(
        (
            r for r in reports
            if (r.get("report_number") or "").replace("№", "").strip() == normalized
            or str(r["id"]) == normalized
        ),
        None,
    )
    if not report:
        return None, "Ведомость не найдена."

    pdf_path = report.get("pdf_path")
    if not pdf_path or not Path(pdf_path).exists():
        return None, "PDF-файл не найден на диске."

    attachment = upload_doc_to_vk(VK_TOKEN, peer_id, pdf_path)
    return attachment, f"Файл по ведомости {report.get('report_number') or normalized}:"


def register_report_handlers(bot: Bot) -> None:
    @bot.on.message(text=BTN_REPORTS)
    async def show_reports(message: Message):
        await message.answer(build_reports_text(message.from_id), keyboard=get_main_menu())
