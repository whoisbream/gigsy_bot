from aiogram import Router, Bot, F
from aiogram.filters import CommandStart, BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from app.database import *
from app.keyboards import *
from aiogram.filters.logic import or_f

router = Router()

class AnswerStates(StatesGroup):
    s_waiting_for_cat = State()
    s_waiting_for_cat_another = State()
    s_waiting_for_char = State()
    s_waiting_for_dur = State()
    s_waiting_for_since = State()
    s_waiting_for_till = State()
    s_waiting_for_exp = State()
    s_waiting_for_sal = State()

@router.message(or_f(F.text == "🔎 Шукати роботу", Command("search")))
async def cmd_collect_name(message: Message, state: FSMContext):
    #analytics
    count = await select_analytics_db("srch_to_filt")
    await update_analytics_db("srch_to_filt", int(count + 1))

    await create_users_db()
    await insert_searcher_id(message.from_user.id, message.from_user.first_name)
    await message.answer("Оберіть категорію:", reply_markup=s_cat_kb)
    await state.set_state(AnswerStates.s_waiting_for_cat)

@router.callback_query(F.data.in_({"s_hr", "s_it", "s_fin", "s_bukh"}))
async def cmd_cat(callback: CallbackQuery, state: FSMContext):
    if callback.data == 's_hr':
        await update_filter("Категорія", callback.from_user.id, 'Готельно-ресторанний бізнес')
    if callback.data == 's_it':
        await update_filter("Категорія", callback.from_user.id, 'IT')
    if callback.data == 's_fin':
        await update_filter("Категорія", callback.from_user.id, 'Фінанси, банк')
    if callback.data == 's_bukh':
        await update_filter("Категорія", callback.from_user.id, 'Бухгалтерія, аудит')
    await callback.message.answer("Який характер роботи?", reply_markup=s_char_kb)
    await state.set_state(AnswerStates.s_waiting_for_char)

@router.callback_query(F.data == 's_cat_an')
async def cmd_cat_another(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Ваш варіант:")
    await state.set_state(AnswerStates.s_waiting_for_cat_another)

@router.message(AnswerStates.s_waiting_for_cat_another)
async def cmd_cat_another_text(message: Message, state: FSMContext):
    await update_filter("Категорія", message.from_user.id, message.text)
    await message.answer("Який характер роботи?", reply_markup=s_char_kb)
    await state.set_state(AnswerStates.s_waiting_for_char)

@router.callback_query(F.data.in_({"s_on", "s_of"}))
async def cmd_char(callback: CallbackQuery, state: FSMContext):
    if callback.data == 's_on':
        await update_filter("Характер", callback.from_user.id, "Онлайн")
    if callback.data == 's_of':
        await update_filter("Характер", callback.from_user.id, "Офлайн")
    await callback.message.answer("Яка тривалість роботи?", reply_markup=s_dur_kb)
    await state.set_state(AnswerStates.s_waiting_for_dur)

@router.callback_query(F.data.in_({"s_one_time", "s_1-3", "s_3-6", "s_>6"}))
async def cmd_dur(callback: CallbackQuery, state: FSMContext):
    if callback.data == 's_one_time':
        await update_filter("Тривалість", callback.from_user.id, 'Одноразова/проектна робота')
    if callback.data == 's_1-3':
        await update_filter("Тривалість", callback.from_user.id, '1-3 місяці')
    if callback.data == 's_3-6':
        await update_filter("Тривалість", callback.from_user.id, '3-6 місяців')
    if callback.data == 's_>6':
        await update_filter("Тривалість", callback.from_user.id, '>6 місяців')
    await callback.message.answer("З якої години? (просто число)")
    await state.set_state(AnswerStates.s_waiting_for_since)

@router.message(AnswerStates.s_waiting_for_since)
async def cmd_since(message: Message, state: FSMContext):
    await update_filter("З", message.from_user.id, message.text)
    await message.answer("До якої години? (просто число)")
    await state.set_state(AnswerStates.s_waiting_for_till)

@router.message(AnswerStates.s_waiting_for_till)
async def cmd_till(message: Message, state: FSMContext):
    await update_filter("До", message.from_user.id, message.text)
    await message.answer("Рівень досвіду", reply_markup=s_exp_kb)
    await state.set_state(AnswerStates.s_waiting_for_exp)

@router.callback_query(F.data.in_({"s_no_exp", "s_less_6", "s_more_6", "s_more_1"}))
async def cmd_exp(callback: CallbackQuery, state: FSMContext):
    if callback.data == 's_no_exp':
        await update_filter("Рівень", callback.from_user.id, 'Без досвіду')
    if callback.data == 's_less_6':
        await update_filter("Рівень", callback.from_user.id, 'менше 6 місяців')
    if callback.data == 's_more_6':
        await update_filter("Рівень", callback.from_user.id, 'більше 6 місяців')
    if callback.data == 's_more_1':
        await update_filter("Рівень", callback.from_user.id, 'більше 1 року')
    await callback.message.answer("Які ваші зарплатні очікування?", reply_markup=s_sal_kb)
    await state.set_state(AnswerStates.s_waiting_for_sal)

@router.callback_query(F.data.in_({"s_less_10", "s_10-40", "s_more_40"}))
async def cmd_s_sal(callback: CallbackQuery, state: FSMContext):
    if callback.data == 's_less_10':
        await update_filter("ЗП", callback.from_user.id, '9999')
    if callback.data == 's_10-40':
        await update_filter("ЗП", callback.from_user.id, '39999')
    if callback.data == 's_more_40':
        await update_filter("ЗП", callback.from_user.id, '40000')
    await callback.message.answer("Готово, ти крутий!", reply_markup=search_kb)
    await state.clear()

