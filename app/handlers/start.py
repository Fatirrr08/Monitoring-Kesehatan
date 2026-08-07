from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.services.firebase_service import firebase_service
from app.models.schemas import UserProfile, UserGoals, DietPreference
from app.bot.keyboards import get_main_menu_keyboard

router = Router(name="start_router")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command, initialize default user profile if new, and render main menu."""
    await state.clear()
    telegram_user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Check if user already exists or create with default profile
    existing_user = await firebase_service.get_user(telegram_user_id)
    if not existing_user:
        default_profile = UserProfile(
            age=20,
            gender="male",
            height_cm=175.0,
            current_weight_kg=75.0,
            target_weight_kg=70.0,
            activity_level="moderate",
            main_muscle_focus=["chest", "arms", "shoulders", "core"],
            preferred_exercises=["walking", "running", "skipping", "home workout"],
            diet_preference=DietPreference(
                reduce_added_sugar=True,
                food_style="normal affordable Indonesian food",
                no_extreme_dieting=True,
            )
        )
        default_goals = UserGoals(
            goal_type="recomposition",
            daily_calories_target=2100,
            protein_target_min_g=90.0,
            protein_target_max_g=120.0,
            added_sugar_max_g=25.0,
            water_target_ml=2500,
            sleep_target_hours=8.0,
        )
        existing_user = await firebase_service.create_user(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            profile=default_profile,
            goals=default_goals,
        )

    welcome_text = (
        f"👋 Halo, *{first_name or 'Sobat FitTrack'}*!\n\n"
        "Selamat datang di *FitTrack AI* — personal assistant kesehatan, nutrisi, berat badan, aktivitas, tidur, dan hidrasimu.\n\n"
        "🎯 *Profil & Target Aktif:*\n"
        f"• Usia: `{existing_user.profile.age}` thn | Tinggi: `{int(existing_user.profile.height_cm)}` cm\n"
        f"• Berat Saat Ini: `{existing_user.profile.current_weight_kg}` kg ➔ Target: `{existing_user.profile.target_weight_kg}` kg\n"
        "• Fokus Otot: `Chest, Arms, Shoulders, Core`\n"
        "• Target Protein: `90–120 g/hari`\n"
        "• Batas Added Sugar: `≤ 25 g/hari`\n"
        "• Prinsip: _Makanan lokal terjangkau, no extreme diet, no kelaparan!_\n\n"
        "Pilih menu di bawah ini atau ketik langsung perintah cepat (misal `/today`, `/walk 6 km`, `/weight 74.5`, `/water 500`):"
    )

    await message.answer(
        text=welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
