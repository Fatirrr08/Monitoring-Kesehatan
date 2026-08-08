import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import get_main_menu_keyboard
from app.bot.states import WeightState
from app.services.firebase_service import firebase_service

router = Router(name="weight_router")


@router.message(Command("weight"))
async def cmd_weight(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        match = re.search(r"([\d\.]+)", args[1])
        if match:
            val = float(match.group(1))
            saved = await firebase_service.log_weight(message.from_user.id, val)
            rem = max(saved.weight_kg - saved.target_weight_kg, 0.0)

            diff_text = f"({saved.difference_from_previous_kg:+} kg dari sesi lalu)" if saved.difference_from_previous_kg is not None else ""

            await message.answer(
                "⚖️ *WEIGHT TRACKING*\n\n"
                f"Current:  `{saved.weight_kg}` kg {diff_text}\n"
                f"Starting: `{saved.starting_weight_kg}` kg\n"
                f"Target:   `{saved.target_weight_kg}` kg\n"
                f"Remaining: `{round(rem, 1)}` kg menuju target\n\n"
                "💡 *Catatan Santai:*\n"
                "_Fluktuasi berat harian (1–2 kg) sangat wajar akibat retensi air dan glikogen. "
                "Fokus pada tren mingguan dan komposisi tubuhmu!_",
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown"
            )
            return

    await state.set_state(WeightState.waiting_weight_input)
    await message.answer(
        "⚖️ *TIMBANGAN BERAT BADAN*\n\n"
        "Ketik berat badanmu saat ini (contoh: `74.5` atau gunakan command `/weight 74.5`):",
        parse_mode="Markdown"
    )


@router.message(WeightState.waiting_weight_input)
async def process_weight_input(message: Message, state: FSMContext):
    await state.clear()
    match = re.search(r"([\d\.]+)", message.text)
    if match:
        val = float(match.group(1))
        saved = await firebase_service.log_weight(message.from_user.id, val)
        rem = max(saved.weight_kg - saved.target_weight_kg, 0.0)
        diff_text = f"({saved.difference_from_previous_kg:+} kg)" if saved.difference_from_previous_kg is not None else ""

        await message.answer(
            "⚖️ *WEIGHT TRACKING*\n\n"
            f"Current:   `{saved.weight_kg}` kg {diff_text}\n"
            f"Starting:  `{saved.starting_weight_kg}` kg\n"
            f"Target:    `{saved.target_weight_kg}` kg\n"
            f"Remaining: `{round(rem, 1)}` kg\n\n"
            "💡 _Tren tubuhmu berada di jalur yang baik untuk rekomposisi._",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer("Format angka tidak valid. Silakan gunakan format `74.5`.")


@router.callback_query(F.data == "nav:weight")
async def cb_nav_weight(callback: CallbackQuery, state: FSMContext):
    user = await firebase_service.get_user(callback.from_user.id)
    history = await firebase_service.get_weight_history(callback.from_user.id, limit=5)
    current_w = user.profile.current_weight_kg if user else 75.0
    target_w = user.profile.target_weight_kg if user else 70.0
    rem = max(current_w - target_w, 0.0)

    hist_lines = []
    for h in history:
        hist_lines.append(f"• `{h.logged_date}`: `{h.weight_kg}` kg")
    hist_text = "\n".join(hist_lines) if hist_lines else "• Belum ada riwayat"

    await callback.message.edit_text(
        "⚖️ *STATUS BERAT BADAN*\n\n"
        f"Saat Ini: `{current_w}` kg\n"
        f"Target:   `{target_w}` kg (Sisa `{round(rem, 1)}` kg)\n\n"
        f"📜 *Riwayat Terbaru:*\n{hist_text}\n\n"
        "Ketik `/weight <angka>` (contoh `/weight 74.5`) untuk mencatat timbangan baru.",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()
