from __future__ import annotations

from vkbottle import Keyboard, KeyboardButtonColor, Text

BTN_NEW = "🆕 Новая ведомость"
BTN_CONTINUE = "📂 Продолжить черновик"
BTN_FINISH = "✅ Завершить и получить PDF"
BTN_REPORTS = "📜 Мои ведомости"
BTN_STATS = "📊 Статистика"
BTN_CANCEL = "❌ Отменить текущую"

MENU_COMMANDS = {
    BTN_NEW,
    BTN_CONTINUE,
    BTN_FINISH,
    BTN_REPORTS,
    BTN_STATS,
    BTN_CANCEL,
    "новая ведомость",
    "продолжить черновик",
    "завершить и получить pdf",
    "мои ведомости",
    "статистика",
    "отменить текущую",
    "отмена",
    "/cancel",
    "/start",
    "start",
    "старт",
    "меню",
}


def normalize_command(text: str | None) -> str:
    return (text or "").strip().lower()


def is_menu_command(text: str | None) -> bool:
    return normalize_command(text) in {cmd.lower() for cmd in MENU_COMMANDS}


def get_main_menu() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text(BTN_NEW), color=KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Text(BTN_CONTINUE), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text(BTN_FINISH), color=KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Text(BTN_REPORTS), color=KeyboardButtonColor.SECONDARY)
    kb.add(Text(BTN_STATS), color=KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Text(BTN_CANCEL), color=KeyboardButtonColor.NEGATIVE)
    return kb.get_json()
