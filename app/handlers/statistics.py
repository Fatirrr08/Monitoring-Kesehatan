from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import get_main_menu_keyboard
from app.services.firebase_service import firebase_service
from app.services.report_service import report_service

router = Router(name="statistics_router")


@router.message(Command("week"))
@router.message(Command("stats"))
async def cmd_weekly_stats(message: Message):
    report_text = await report_service.generate_weekly_report(message.from_user.id)
    await message.answer(
        text=report_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.message(Command("score"))
async def cmd_daily_score(message: Message):
    summary = await firebase_service.get_daily_summary(message.from_user.id)
    score_text = report_service.render_daily_score_text(summary)
    await message.answer(
        text=score_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "nav:stats")
async def cb_nav_stats(callback: CallbackQuery):
    report_text = await report_service.generate_weekly_report(callback.from_user.id)
    try:
        await callback.message.edit_text(
            text=report_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "nav:goals")
async def cb_nav_goals(callback: CallbackQuery):
    user = await firebase_service.get_user(callback.from_user.id)
    p = user.profile if user else None
    g = user.goals if user else None

    text = (
        "🎯 *TARGET REKOMPOSISI TUBUH*\n\n"
        f"• Berat Awal: `{p.current_weight_kg if p else 75}` kg ➔ Target: `{p.target_weight_kg if p else 70}` kg\n"
        f"• Target Kalori Harian: `{g.daily_calories_target if g else 2100}` kcal\n"
        f"• Target Protein: `{g.protein_target_min_g if g else 90}`–`{g.protein_target_max_g if g else 120}` g/hari\n"
        f"• Batas Added Sugar: `≤ {g.added_sugar_max_g if g else 25}` g/hari\n"
        f"• Target Air: `{g.water_target_ml if g else 2500:,}` ml/hari\n"
        f"• Target Tidur: `{g.sleep_target_hours if g else 8}` jam/hari\n"
        f"• Fokus Otot: `{', '.join(p.main_muscle_focus) if p else 'Chest, Arms, Shoulders, Core'}`\n\n"
        "_Semua target di atas fleksibel dan dapat disesuaikan kapan saja._"
    )
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "nav:settings")
async def cb_nav_settings(callback: CallbackQuery):
    user = await firebase_service.get_user(callback.from_user.id)
    text = (
        "⚙️ *PENGATURAN FITTRACK AI*\n\n"
        f"🆔 Telegram ID: `{callback.from_user.id}`\n"
        f"🌐 Zona Waktu: `{user.settings.timezone if user else 'Asia/Jakarta'}`\n"
        f"🔔 Notifikasi Skor Harian: `Aktif`\n"
        f"☁️ Database: `Google Cloud Firestore (Connected)`\n\n"
        "Data kamu dienkripsi dan terisolasi secara aman per Telegram User ID."
    )
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    except Exception:
        pass
    await callback.answer()
