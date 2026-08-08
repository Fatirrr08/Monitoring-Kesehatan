from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.ai.coach import ai_coach_service
from app.bot.keyboards import get_main_menu_keyboard
from app.bot.states import CoachState

router = Router(name="coach_router")


@router.message(Command("coach"))
@router.message(Command("tanya"))
async def cmd_coach(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        user_query = args[1].strip()
        response_text = await ai_coach_service.get_coach_response(message.from_user.id, user_query)
        await message.answer(
            text=f"🤖 *AI COACH:*\n\n{response_text}",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        return

    await state.set_state(CoachState.chatting)
    await message.answer(
        "🤖 *AI COACH FITTRACK*\n\n"
        "Tanyakan apa saja seputar makanan, kalori, latihan, atau rencanamu hari ini secara santai.\n\n"
        "Contoh pertanyaan:\n"
        "• _\"aku boleh makan bakso sore ini?\"_\n"
        "• _\"hari ini proteinku kurang banyak gak?\"_\n"
        "• _\"aku boleh flexible meal hari ini?\"_\n"
        "• _\"besok enaknya latihan apa?\"_",
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "nav:coach")
async def cb_nav_coach(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CoachState.chatting)
    await callback.message.edit_text(
        "🤖 *AI COACH FITTRACK*\n\n"
        "Silakan ketik pertanyaan atau keluh kesahmu seputar nutrisi dan latihan di chat ini.\n"
        "AI Coach akan membaca data jurnal harianmu dari Firestore untuk memberikan saran yang pas dan santai!",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(CoachState.chatting)
async def process_coach_chat(message: Message, state: FSMContext):
    user_query = message.text.strip()
    response_text = await ai_coach_service.get_coach_response(message.from_user.id, user_query)
    await message.answer(
        text=f"🤖 *AI COACH:*\n\n{response_text}",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
