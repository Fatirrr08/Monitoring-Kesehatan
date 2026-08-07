from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.services.firebase_service import firebase_service
from app.services.sleep_service import sleep_service
from app.bot.states import SleepState
from app.bot.keyboards import get_main_menu_keyboard

router = Router(name="sleep_router")


@router.message(Command("sleep"))
async def cmd_sleep(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        log = sleep_service.evaluate_sleep(message.from_user.id, args[1])
        saved = await firebase_service.log_sleep(log)
        text = sleep_service.render_sleep_message(saved)
        await message.answer(
            text=text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        return

    await state.set_state(SleepState.waiting_sleep_input)
    await message.answer(
        "😴 *PENCATATAN TIDUR*\n\n"
        "Ketik jam tidur dan bangunmu (contoh: `23:30 07:30` atau `07:00 15:00` atau `8 jam`):",
        parse_mode="Markdown"
    )


@router.message(SleepState.waiting_sleep_input)
async def process_sleep_input(message: Message, state: FSMContext):
    await state.clear()
    log = sleep_service.evaluate_sleep(message.from_user.id, message.text)
    saved = await firebase_service.log_sleep(log)
    text = sleep_service.render_sleep_message(saved)
    await message.answer(
        text=text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "nav:sleep")
async def cb_nav_sleep(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "😴 *PELACAK TIDUR & PEMULIHAN*\n\n"
        "Tidur cukup 7–9 jam sangat krusial untuk sintesis protein dan pembakaran lemak.\n\n"
        "Gunakan perintah cepat:\n"
        "• `/sleep 23:00 07:00` (Jadwal malam reguler)\n"
        "• `/sleep 07:00 15:00` (Jadwal istirahat shift/siang)\n"
        "• `/sleep 8` (8 jam durasi total)",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()
