from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build Telegram Main Menu Inline Keyboard according to specification."""
    buttons = [
        [
            InlineKeyboardButton(text="🏠 Dashboard", callback_data="nav:dashboard"),
            InlineKeyboardButton(text="🍱 Catat Makanan", callback_data="nav:food"),
        ],
        [
            InlineKeyboardButton(text="📸 Foto Makanan", callback_data="nav:food_photo"),
            InlineKeyboardButton(text="🏃 Aktivitas", callback_data="nav:activity"),
        ],
        [
            InlineKeyboardButton(text="⚖️ Berat Badan", callback_data="nav:weight"),
            InlineKeyboardButton(text="😴 Tidur", callback_data="nav:sleep"),
        ],
        [
            InlineKeyboardButton(text="💧 Air", callback_data="nav:water"),
            InlineKeyboardButton(text="📊 Statistik", callback_data="nav:stats"),
        ],
        [
            InlineKeyboardButton(text="🎯 Target", callback_data="nav:goals"),
            InlineKeyboardButton(text="🤖 AI Coach", callback_data="nav:coach"),
        ],
        [
            InlineKeyboardButton(text="⚙️ Pengaturan", callback_data="nav:settings"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_food_confirm_keyboard(pending_id: str) -> InlineKeyboardMarkup:
    """Keyboard for food confirmation: ✅ Catat, ✏️ Edit, ❌ Batal."""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Catat", callback_data=f"food_confirm:save:{pending_id}"),
            InlineKeyboardButton(text="✏️ Edit Porsi", callback_data=f"food_confirm:edit:{pending_id}"),
            InlineKeyboardButton(text="❌ Batal", callback_data=f"food_confirm:cancel:{pending_id}"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_water_quick_keyboard() -> InlineKeyboardMarkup:
    """Quick increment buttons for water consumption."""
    buttons = [
        [
            InlineKeyboardButton(text="💧 +250 ml (Gelas)", callback_data="water:add:250"),
            InlineKeyboardButton(text="💧 +500 ml (Botol)", callback_data="water:add:500"),
        ],
        [
            InlineKeyboardButton(text="💧 +600 ml (Tumbler)", callback_data="water:add:600"),
            InlineKeyboardButton(text="💧 +1000 ml", callback_data="water:add:1000"),
        ],
        [
            InlineKeyboardButton(text="🔙 Menu Utama", callback_data="nav:dashboard")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_quick_food_keyboard() -> InlineKeyboardMarkup:
    """Indonesian staple presets for 1-click logging."""
    buttons = [
        [
            InlineKeyboardButton(text="🍚 Nasi + Dada Ayam", callback_data="quick_food:dada_ayam"),
            InlineKeyboardButton(text="🍳 Nasi + Telur", callback_data="quick_food:telur"),
        ],
        [
            InlineKeyboardButton(text="🍲 Sayur Sop", callback_data="quick_food:sayur_sop"),
            InlineKeyboardButton(text="🍢 Tempe / Tahu", callback_data="quick_food:tempe"),
        ],
        [
            InlineKeyboardButton(text="🍈 Jambu Biji Merah", callback_data="quick_food:jambu_merah"),
            InlineKeyboardButton(text="☕ Americano", callback_data="quick_food:americano"),
        ],
        [
            InlineKeyboardButton(text="🔙 Menu Utama", callback_data="nav:dashboard")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Menu Utama", callback_data="nav:dashboard")]
    ])
