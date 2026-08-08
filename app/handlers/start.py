from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards import get_main_menu_keyboard
from app.models.schemas import DietPreference, UserGoals, UserProfile
from app.services.firebase_service import firebase_service

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


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📖 *PANDUAN LENGKAP PERINTAH FITTRACK AI*\n\n"
        "🏠 *Umum:*\n"
        "• `/start` — Menu utama & onboarding\n"
        "• `/today` / `/dashboard` — Rangkuman nutrisi harian\n"
        "• `/week` / `/stats` — Laporan tren mingguan\n"
        "• `/profile` — Lihat data profil kamu\n"
        "• `/progress` — Evaluasi progres & daily score\n\n"
        "🍱 *Nutrisi & Makanan:*\n"
        "• `/food` / `/makan` — Menu pencatatan makanan\n"
        "• Kirim *Foto Makanan* — Analisis AI visual otomatis\n"
        "• Kirim *Foto Label* — OCR nilai gizi kemasan\n\n"
        "🏃 *Aktivitas:*\n"
        "• `/walk 6 km` — Jalan kaki & langkah\n"
        "• `/run 5 km 42m` — Lari & pace\n"
        "• `/badminton 2 matches` — Badminton (match/set)\n"
        "• `/skipping 800` — Lompat tali\n"
        "• `/workout 35m` — Latihan beban/bodyweight\n\n"
        "⚖️ *Lainnya:*\n"
        "• `/weight 74.5` — Catat timbangan\n"
        "• `/water 500` — Catat air minum (ml)\n"
        "• `/sleep 23:00 07:00` — Catat jam tidur\n"
        "• `/coach <pertanyaan>` — Tanya AI Coach"
    )
    await message.answer(text=help_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user = await firebase_service.get_user(message.from_user.id)
    if not user:
        user = await firebase_service.create_user(message.from_user.id)
    p = user.profile
    g = user.goals

    profile_text = (
        "👤 *PROFIL PENGGUNA FITTRACK*\n\n"
        f"• Usia: `{p.age}` tahun\n"
        f"• Tinggi: `{int(p.height_cm)}` cm | Berat: `{p.current_weight_kg}` kg\n"
        f"• Target Berat: `{p.target_weight_kg}` kg (Tujuan: `{g.goal_type.replace('_', ' ').title()}`)\n"
        f"• Target Kalori: `{g.daily_calories_target}` kcal/hari\n"
        f"• Target Protein: `{int(g.protein_target_min_g)}–{int(g.protein_target_max_g)}` g/hari\n"
        f"• Batas Added Sugar: `≤ {int(g.added_sugar_max_g)}` g/hari\n"
        f"• Target Air: `{g.water_target_ml:,}` ml/hari\n"
        f"• Fokus Otot: `{', '.join(p.main_muscle_focus)}`\n"
        f"• Preferensi Diet: `{p.diet_preference.food_style}`\n\n"
        "_Semua nilai profil dapat disesuaikan kapan saja._"
    )
    await message.answer(text=profile_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")


@router.message(Command("progress"))
async def cmd_progress(message: Message):
    user = await firebase_service.get_user(message.from_user.id)
    summary = await firebase_service.get_daily_summary(message.from_user.id)
    history = await firebase_service.get_weight_history(message.from_user.id, limit=3)
    curr_w = history[0].weight_kg if history else user.profile.current_weight_kg if user else 75.0
    start_w = user.profile.current_weight_kg if user else 75.0
    target_w = user.profile.target_weight_kg if user else 70.0

    rem_w = max(curr_w - target_w, 0.0)
    lost_w = round(start_w - curr_w, 2)

    progress_text = (
        "📈 *EVALUASI PROGRES REKOMPOSISI*\n\n"
        f"⚖️ *Berat:* `{curr_w}` kg (Turun `{lost_w:+.1f}` kg dari awal)\n"
        f"🎯 *Target:* `{target_w}` kg (Sisa `{round(rem_w, 1)}` kg)\n"
        f"⭐ *Daily Score Hari Ini:* `{summary.daily_score}` / 10.0\n"
        f"🔥 *Kalori Masuk:* `{summary.total_calories}` / `{summary.target_calories}` kcal\n"
        f"💪 *Protein:* `{summary.total_protein_g}` / `{int(summary.target_protein_min_g)}–{int(summary.target_protein_max_g)}` g\n"
        f"🍬 *Added Sugar:* `{summary.added_sugar_g}` / `{int(summary.added_sugar_max_g)}` g\n"
        f"💧 *Air:* `{summary.total_water_ml:,}` / `{summary.target_water_ml:,}` ml\n\n"
        "💡 _Konsistensi jangka panjang adalah kunci keberhasilan rekomposisi tubuh._"
    )
    await message.answer(text=progress_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
