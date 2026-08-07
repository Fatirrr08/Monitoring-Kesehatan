from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.services.firebase_service import firebase_service
from app.services.activity_service import activity_service
from app.bot.states import ActivityState
from app.bot.keyboards import get_main_menu_keyboard

router = Router(name="activity_router")


@router.message(Command("walk"))
async def cmd_walk(message: Message):
    args = message.text.split(maxsplit=1)
    args_text = args[1] if len(args) > 1 else "5 km"
    user = await firebase_service.get_user(message.from_user.id)
    weight = user.profile.current_weight_kg if user else 75.0

    act_log = activity_service.parse_activity_command("walk", args_text, message.from_user.id, weight)
    saved = await firebase_service.log_activity(act_log)

    await message.answer(
        f"🏃 *JALAN KAKI TERCATAT!*\n\n"
        f"📍 Jarak: `{saved.distance_km}` km\n"
        f"⏱️ Durasi: `{int(saved.duration_minutes)}` menit\n"
        f"👣 Langkah: ~`{saved.steps:,}` langkah\n"
        f"🔥 Kalori Terbakar: ~`{saved.estimated_calories}` kcal\n\n"
        "_Bagus sekali! Jalan kaki adalah cara efisien membakar lemak tanpa membebani pemulihan otot._",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.message(Command("run"))
async def cmd_run(message: Message):
    args = message.text.split(maxsplit=1)
    args_text = args[1] if len(args) > 1 else "5 km 35m"
    user = await firebase_service.get_user(message.from_user.id)
    weight = user.profile.current_weight_kg if user else 75.0

    act_log = activity_service.parse_activity_command("run", args_text, message.from_user.id, weight)
    saved = await firebase_service.log_activity(act_log)

    await message.answer(
        f"🏃💨 *LARI TERCATAT!*\n\n"
        f"📍 Jarak: `{saved.distance_km}` km\n"
        f"⏱️ Durasi: `{int(saved.duration_minutes)}` menit (Pace `{saved.pace_min_per_km}`'/km)\n"
        f"🔥 Kalori Terbakar: ~`{saved.estimated_calories}` kcal\n\n"
        "_Hebat! Pastikan minum air putih dan cukupi elektrolit setelah lari._",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.message(Command("skipping"))
async def cmd_skipping(message: Message):
    args = message.text.split(maxsplit=1)
    args_text = args[1] if len(args) > 1 else "500"
    user = await firebase_service.get_user(message.from_user.id)
    weight = user.profile.current_weight_kg if user else 75.0

    act_log = activity_service.parse_activity_command("skipping", args_text, message.from_user.id, weight)
    saved = await firebase_service.log_activity(act_log)

    await message.answer(
        f"🪢 *SKIPPING TERCATAT!*\n\n"
        f"🔢 Repetisi: `{saved.repetitions}` lompatan\n"
        f"⏱️ Estimasi Durasi: `{saved.duration_minutes}` menit\n"
        f"🔥 Kalori Terbakar: ~`{saved.estimated_calories}` kcal\n\n"
        "_Kardio intensitas tinggi yang hemat waktu!_",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.message(Command("workout"))
async def cmd_workout(message: Message):
    args = message.text.split(maxsplit=1)
    args_text = args[1] if len(args) > 1 else "30m"
    user = await firebase_service.get_user(message.from_user.id)
    weight = user.profile.current_weight_kg if user else 75.0

    act_log = activity_service.parse_activity_command("workout", args_text, message.from_user.id, weight)
    saved = await firebase_service.log_activity(act_log)

    await message.answer(
        f"🏋️ *HOME WORKOUT TERCATAT!*\n\n"
        f"📝 Fokus: `{saved.notes}`\n"
        f"⏱️ Durasi: `{int(saved.duration_minutes)}` menit\n"
        f"🔥 Kalori Terbakar: ~`{saved.estimated_calories}` kcal\n\n"
        "_Latihan beban/bodyweight sangat penting untuk menjaga dan membentuk massa otot saat fat loss!_",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "nav:activity")
async def cb_nav_activity(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🏃 *AKTIVITAS FISIK*\n\n"
        "Gunakan perintah cepat berikut kapan saja:\n"
        "• `/walk 6 km` — Catat jalan kaki\n"
        "• `/run 5 km 42m` — Catat lari & pace\n"
        "• `/skipping 800` — Catat lompat tali\n"
        "• `/workout 35m` — Catat latihan beban / home workout\n\n"
        "Atau kirim screenshot aplikasi lari (Strava/NRC) untuk deteksi otomatis.",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()
