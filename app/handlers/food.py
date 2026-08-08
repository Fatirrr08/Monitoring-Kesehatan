import uuid

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.ai.nutrition_analyzer import nutrition_analyzer
from app.ai.vision import vision_service
from app.bot.keyboards import (
    get_food_confirm_keyboard,
    get_main_menu_keyboard,
    get_quick_food_keyboard,
)
from app.bot.states import FoodState
from app.models.schemas import FoodLog, today_str
from app.services.firebase_service import firebase_service
from app.services.food_database import get_food_by_key, search_food

router = Router(name="food_router")

# Temporary cache for pending food confirmations
_pending_confirmations = {}


@router.message(Command("food"))
@router.message(Command("makan"))
async def cmd_food_menu(message: Message, state: FSMContext):
    """Show food logging options or parse text directly."""
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        # User typed e.g. "/makan dada ayam" or "/makan nasi goreng"
        query = args[1].strip()
        matched = search_food(query)
        if matched:
            item = matched[0]
            log = FoodLog(
                food_log_id=f"food_{today_str()}_{uuid.uuid4().hex[:6]}",
                telegram_user_id=message.from_user.id,
                food_name=item.name,
                portion=item.default_portion,
                calories=item.calories,
                protein_g=item.protein_g,
                carbs_g=item.carbs_g,
                fat_g=item.fat_g,
                total_sugar_g=item.total_sugar_g,
                added_sugar_g=item.added_sugar_g,
                fiber_g=item.fiber_g,
                sodium_mg=item.sodium_mg,
                confidence="high",
                source="preset",
                notes=item.notes,
            )
            await firebase_service.log_food(log)
            await message.answer(
                f"✅ *Berhasil Dicatat!*\n\n"
                f"🍽️ *{item.name}* ({item.default_portion})\n"
                f"🔥 Kalori: `{item.calories} kcal`\n"
                f"💪 Protein: `{item.protein_g} g` | 🍞 Karbo: `{item.carbs_g} g` | 🥑 Lemak: `{item.fat_g} g`\n"
                f"🍬 Added Sugar: `{item.added_sugar_g} g`",
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown"
            )
            return

    # Show prompt / quick picker
    await state.set_state(FoodState.waiting_food_text)
    await message.answer(
        "🍱 *CATAT MAKANAN*\n\n"
        "Silakan pilih menu cepat di bawah ini, atau *ketik nama makanan* (contoh: `nasi goreng`), "
        "atau *kirim foto makanan / label kemasan* langsung ke bot:",
        reply_markup=get_quick_food_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "nav:food")
async def cb_nav_food(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FoodState.waiting_food_text)
    await callback.message.edit_text(
        "🍱 *CATAT MAKANAN*\n\n"
        "Silakan pilih menu cepat di bawah ini, atau ketik nama makanan di chat:",
        reply_markup=get_quick_food_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "nav:food_photo")
async def cb_nav_food_photo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FoodState.waiting_food_photo)
    await callback.message.edit_text(
        "📸 *FOTO MAKANAN AI*\n\n"
        "Kirimkan foto makanan atau piring makanmu sekarang.\n"
        "AI kami akan menganalisis komponen makanan, estimasi porsi, kalori, dan makronutrisi.",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("quick_food:"))
async def cb_quick_food(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]
    item = get_food_by_key(key)
    if not item:
        await callback.answer("Menu tidak ditemukan.")
        return

    log = FoodLog(
        food_log_id=f"food_{today_str()}_{uuid.uuid4().hex[:6]}",
        telegram_user_id=callback.from_user.id,
        food_name=item.name,
        portion=item.default_portion,
        calories=item.calories,
        protein_g=item.protein_g,
        carbs_g=item.carbs_g,
        fat_g=item.fat_g,
        total_sugar_g=item.total_sugar_g,
        added_sugar_g=item.added_sugar_g,
        fiber_g=item.fiber_g,
        sodium_mg=item.sodium_mg,
        confidence="high",
        source="preset",
        notes=item.notes,
    )
    await firebase_service.log_food(log)
    await callback.message.edit_text(
        f"✅ *Tercatat ke Jurnal!*\n\n"
        f"🍽️ *{item.name}* ({item.default_portion})\n"
        f"🔥 Kalori: `{item.calories} kcal`\n"
        f"💪 Protein: `{item.protein_g} g` | 🍞 Karbo: `{item.carbs_g} g`\n"
        f"🍬 Added Sugar: `{item.added_sugar_g} g`",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer("Tercatat!")


@router.message(F.photo)
async def handle_food_photo(message: Message, state: FSMContext):
    """Process uploaded food picture or nutrition label with security validation."""
    bot = message.bot
    photo = message.photo[-1]

    # File size validation (limit 15MB)
    if photo.file_size and photo.file_size > 15 * 1024 * 1024:
        await message.answer("⚠️ Ukuran gambar terlalu besar. Maksimum 15 MB.")
        return

    file_info = await bot.get_file(photo.file_id)
    file_io = await bot.download_file(file_info.file_path)
    image_bytes = file_io.read()

    # Magic byte verification (JPEG, PNG, WebP)
    is_valid_image = (
        image_bytes.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n"))
        or (image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP")
    )
    if not is_valid_image:
        await message.answer("⚠️ Format file tidak didukung. Mohon kirimkan foto JPG, PNG, atau WebP.")
        return

    # Upload to Firebase Storage
    upload_res = await firebase_service.upload_food_image(
        telegram_user_id=message.from_user.id,
        image_bytes=image_bytes,
        file_extension="jpg",
    )

    current_state = await state.get_state()
    if current_state == FoodState.waiting_label_photo:
        user_doc = await firebase_service.get_user(message.from_user.id)
        label_res = await nutrition_analyzer.analyze_label(image_bytes, user_doc)
        card_text = nutrition_analyzer.format_label_card(label_res, user_doc)
        pending_id = uuid.uuid4().hex[:8]
        _pending_confirmations[pending_id] = {
            "telegram_user_id": message.from_user.id,
            "food_name": label_res.get("product_name", "Produk Kemasan"),
            "portion": label_res.get("serving_size", "1 sajian"),
            "calories": label_res.get("calories", 140),
            "calories_min": label_res.get("calories", 140),
            "calories_max": label_res.get("calories", 140),
            "protein_g": label_res.get("protein_g", 6.0),
            "carbs_g": label_res.get("carbs_g", 18.0),
            "fat_g": label_res.get("fat_g", 5.0),
            "total_sugar_g": label_res.get("sugar_g", 8.0),
            "added_sugar_g": label_res.get("sugar_g", 8.0),
            "fiber_g": label_res.get("fiber_g", 0.0),
            "sodium_mg": label_res.get("sodium_mg", 125.0),
            "confidence": 0.95,
            "source": "nutrition_label_ocr",
            "storage_path": upload_res["storage_path"],
            "image_url": upload_res["image_url"],
            "assumptions": ["Berdasarkan nilai gizi pada kemasan"],
        }
        await message.answer(
            text=card_text,
            reply_markup=get_food_confirm_keyboard(pending_id),
            parse_mode="Markdown"
        )
    else:
        # Structured visual AI estimation
        analysis = await vision_service.analyze_food_image(image_bytes)
        card_text = vision_service.format_food_analysis_card(analysis)
        pending_id = uuid.uuid4().hex[:8]
        _pending_confirmations[pending_id] = {
            "telegram_user_id": message.from_user.id,
            "food_name": analysis.food_name,
            "portion": analysis.portion,
            "calories": analysis.calories,
            "calories_min": analysis.calories_min,
            "calories_max": analysis.calories_max,
            "protein_g": analysis.protein_g,
            "carbs_g": analysis.carbs_g,
            "fat_g": analysis.fat_g,
            "total_sugar_g": analysis.total_sugar_g,
            "added_sugar_g": analysis.added_sugar_g,
            "fiber_g": analysis.fiber_g,
            "sodium_mg": analysis.sodium_mg,
            "confidence": analysis.overall_confidence,
            "source": "photo_ai",
            "storage_path": upload_res["storage_path"],
            "image_url": upload_res["image_url"],
            "assumptions": analysis.assumptions,
        }
        await message.answer(
            text=card_text,
            reply_markup=get_food_confirm_keyboard(pending_id),
            parse_mode="Markdown"
        )

    await state.clear()


@router.callback_query(F.data.startswith("food_confirm:"))
async def cb_food_confirm(callback: CallbackQuery):
    parts = callback.data.split(":")
    action = parts[1]
    pending_id = parts[2]

    if action == "cancel":
        _pending_confirmations.pop(pending_id, None)
        await callback.message.edit_text(
            "❌ *Pencatatan dibatalkan.*",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer("Dibatalkan")
        return

    data = _pending_confirmations.pop(pending_id, None)
    if not data:
        await callback.answer("Sesi konfirmasi telah kadaluarsa.")
        return

    if action == "save":
        saved_log = await firebase_service.save_food_analysis(callback.from_user.id, data)
        await callback.message.edit_text(
            f"✅ *Makanan Berhasil Dicatat ke Firestore!*\n\n"
            f"🍽️ *{saved_log.food_name}*\n"
            f"🔥 Kalori: `{saved_log.calories} kcal`\n"
            f"💪 Protein: `{saved_log.protein_g} g` | 🍞 Karbo: `{saved_log.carbs_g} g`\n"
            f"🍬 Added Sugar: `{saved_log.added_sugar_g} g`",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer("Tersimpan!")
    elif action == "edit":
        # Save baseline and prompt for manual note
        saved_log = await firebase_service.save_food_analysis(callback.from_user.id, data)
        await callback.message.edit_text(
            f"✏️ Makanan tercatat sebagai *{saved_log.food_name}*.\n"
            "Kamu bisa menyesuaikan porsi di log harian kapan saja.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()


@router.message(FoodState.waiting_food_text)
async def process_manual_food_text(message: Message, state: FSMContext):
    """Handle text input when user searches or types food name."""
    await state.clear()
    query = message.text.strip()
    matched = search_food(query)

    if matched:
        item = matched[0]
        log = FoodLog(
            food_log_id=f"food_{today_str()}_{uuid.uuid4().hex[:6]}",
            telegram_user_id=message.from_user.id,
            food_name=item.name,
            portion=item.default_portion,
            calories=item.calories,
            protein_g=item.protein_g,
            carbs_g=item.carbs_g,
            fat_g=item.fat_g,
            total_sugar_g=item.total_sugar_g,
            added_sugar_g=item.added_sugar_g,
            fiber_g=item.fiber_g,
            sodium_mg=item.sodium_mg,
            confidence="high",
            source="manual_text",
            notes=item.notes,
        )
        await firebase_service.log_food(log)
        await message.answer(
            f"✅ *Berhasil Dicatat!*\n\n"
            f"🍽️ *{item.name}* ({item.default_portion})\n"
            f"🔥 Kalori: `{item.calories} kcal`\n"
            f"💪 Protein: `{item.protein_g} g` | 🍞 Karbo: `{item.carbs_g} g`\n"
            f"🍬 Added Sugar: `{item.added_sugar_g} g`",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        # Fallback estimation
        log = FoodLog(
            food_log_id=f"food_{today_str()}_{uuid.uuid4().hex[:6]}",
            telegram_user_id=message.from_user.id,
            food_name=query.title(),
            portion="1 porsi standar",
            calories=350,
            protein_g=15.0,
            carbs_g=40.0,
            fat_g=12.0,
            total_sugar_g=2.0,
            added_sugar_g=1.0,
            confidence="medium",
            source="manual_text",
        )
        await firebase_service.log_food(log)
        await message.answer(
            f"✅ *Dicatat dengan Estimasi Wajar:*\n\n"
            f"🍽️ *{query.title()}*\n"
            f"🔥 Kalori: ~`350 kcal`\n"
            f"💪 Protein: ~`15 g` | 🍞 Karbo: ~`40 g`",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
