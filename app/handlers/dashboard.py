from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.services.firebase_service import firebase_service
from app.services.nutrition_service import nutrition_service
from app.bot.keyboards import get_main_menu_keyboard

router = Router(name="dashboard_router")


@router.message(Command("today"))
@router.message(Command("dashboard"))
async def cmd_today(message: Message, state: FSMContext):
    """Handle /today command and show visual daily progress."""
    await state.clear()
    telegram_user_id = message.from_user.id
    summary = await firebase_service.get_daily_summary(telegram_user_id)
    text = nutrition_service.render_nutrition_summary_text(summary)

    await message.answer(
        text=text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "nav:dashboard")
async def cb_dashboard(callback: CallbackQuery, state: FSMContext):
    """Handle inline navigation to Dashboard."""
    await state.clear()
    telegram_user_id = callback.from_user.id
    summary = await firebase_service.get_daily_summary(telegram_user_id)
    text = nutrition_service.render_nutrition_summary_text(summary)

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.message.answer(
            text=text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    await callback.answer()
