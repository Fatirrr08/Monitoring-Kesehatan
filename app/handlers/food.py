import uuid
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext

from app.services.firebase_service import firebase_service
from app.services.food_database import get_food_by_key, search_food
from app.ai.vision import vision_service
from app.ai.nutrition_analyzer import nutrition_analyzer
from app.bot.states import FoodState
from app.bot.keyboards import (
    get_main_menu_keyboard,
    get_food_confirm_keyboard,
    get_quick_food_keyboard,
)
from app.models.schemas import FoodLog, utc_now, today_str
from app.utils.logger import logger

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
    """Process uploaded food picture or nutrition label."""
    bot = message.bot
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    file_io = await bot.download_file(file_info.file_path)
    image_bytes = file_io.read()

    # Upload to Firebase Storage
    upload_res = await firebase_service.upload_food_image(
        telegram_user_id=message.from_user.id,
        image_bytes=image_bytes,
        file_extension="jpg",
    )

    # Check if user specifically requested label scanner or default to meal analysis
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
            "protein_g": label_res.get("protein_g", 6.0),
            "carbs_g": label_res.get("carbs_g", 18.0),
            "fat_g": label_res.get("fat_g", 5.0),
            "total_sugar_g": label_res.get("sugar_g", 8.0),
            "added_sugar_g": label_res.get("sugar_g", 8.0),
            "fiber_g": label_res.get("fiber_g", 0.0),
            "sodium_mg": label_res.get("sodium_mg", 125.0),
            "confidence": "high",
            "source": "nutrition_label_ocr",
            "storage_path": upload_res["storage_path"],
            "image_url": upload_res["image_url"],
        }
        await message.answer(
            text=card_text,
            reply_markup=get_food_confirm_keyboard(pending_id),
            parse_mode="Markdown"
        )
    else:
        # Standard food photo analysis
        analysis = await vision_service.analyze_food_image(image_bytes)
        card_text = vision_service.format_food_analysis_card(analysis)
        pending_id = uuid.uuid4().hex[:8]
        _pending_confirmations[pending_id] = {
            "telegram_user_id": message.from_user.id,
            "food_name": analysis.get("food_name", "Piring Seimbang"),
            "portion": analysis.get("portion", "1 porsi"),
            "calories": analysis.get("calories", 480),
            "protein_g": analysis.get("protein_g", 32.0),
            "carbs_g": analysis.get("carbs_g", 54.0),
            "fat_g": analysis.get("fat_g", 14.0),
            "total_sugar_g": analysis.get("total_sugar_g", 3.0),
            "added_sugar_g": analysis.get("added_sugar_g", 0.0),
            "fiber_g": analysis.get("fiber_g", 3.0),
            "sodium_mg": analysis.get("sodium_mg", 420.0),
            "confidence": analysis.get("confidence", "medium"),
            "source": "photo_ai",
            "storage_path": upload_res["storage_path"],
            "image_url": upload_res["image_url"],
            "items": analysis.get("items", []),
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
