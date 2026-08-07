import re
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.services.firebase_service import firebase_service
from app.bot.states import WaterState
from app.bot.keyboards import get_main_menu_keyboard, get_water_quick_keyboard
from app.utils.formatting import make_progress_bar

router = Router(name="water_router")


@router.message(Command("water"))
@router.message(Command("air"))
async def cmd_water(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        match = re.search(r"(\d+)", args[1])
        if match:
            amount = int(match.group(1))
            await firebase_service.log_water(message.from_user.id, amount)
            summary = await firebase_service.get_daily_summary(message.from_user.id)
            pbar = make_progress_bar(summary.total_water_ml, summary.target_water_ml, length=10)

            await message.answer(
                "💧 *PENCATATAN AIR MINUM*\n\n"
                f"Ditambahkan: `+{amount:,}` ml\n"
                f"Total Hari Ini: `{summary.total_water_ml:,}` / `{summary.target_water_ml:,}` ml\n"
                f"{pbar}\n\n"
                "_Tetap terhidrasi untuk metabolisme dan fungsi otot maksimal!_",
                reply_markup=get_water_quick_keyboard(),
                parse_mode="Markdown"
            )
            return

    summary = await firebase_service.get_daily_summary(message.from_user.id)
    pbar = make_progress_bar(summary.total_water_ml, summary.target_water_ml, length=10)
    await message.answer(
        "💧 *ASUPAN AIR PUTIH HARI INI*\n\n"
        f"Tercatat: `{summary.total_water_ml:,}` / `{summary.target_water_ml:,}` ml\n"
        f"{pbar}\n\n"
        "Klik tombol cepat untuk menambah konsumsi air:",
        reply_markup=get_water_quick_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("water:add:"))
async def cb_water_add(callback: CallbackQuery):
    amount = int(callback.data.split(":")[2])
    await firebase_service.log_water(callback.from_user.id, amount)
    summary = await firebase_service.get_daily_summary(callback.from_user.id)
    pbar = make_progress_bar(summary.total_water_ml, summary.target_water_ml, length=10)

    await callback.message.edit_text(
        "💧 *ASUPAN AIR PUTIH TERBARU*\n\n"
        f"Ditambahkan: `+{amount:,}` ml\n"
        f"Total Saat Ini: `{summary.total_water_ml:,}` / `{summary.target_water_ml:,}` ml\n"
        f"{pbar}\n\n"
        "Pilih lagi untuk menambah:",
        reply_markup=get_water_quick_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer(f"+{amount} ml")


@router.callback_query(F.data == "nav:water")
async def cb_nav_water(callback: CallbackQuery):
    summary = await firebase_service.get_daily_summary(callback.from_user.id)
    pbar = make_progress_bar(summary.total_water_ml, summary.target_water_ml, length=10)

    await callback.message.edit_text(
        "💧 *PEMANTAUAN HIDRASI AIR*\n\n"
        f"Status Hari Ini: `{summary.total_water_ml:,}` / `{summary.target_water_ml:,}` ml\n"
        f"{pbar}\n\n"
        "Gunakan tombol cepat di bawah:",
        reply_markup=get_water_quick_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()
