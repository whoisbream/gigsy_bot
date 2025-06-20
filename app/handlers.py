from aiogram import Router, Bot

from aiogram.filters import CommandStart, BaseFilter, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database import create_name_db, create_answers_db, add_qa, vac_name, vac_cat
from app.keyboards import main_inline, user_states, next_kb, type_kb
# --- ROUTER ---
router = Router()

# --- СПИСОК ВОПРОСОВ И ВАРИАНТОВ ОТВЕТОВ ---
questions_with_answers = [
    {
        "question": "Перед початком, обери варіант, який найкраще характеризує тебе \n\n "
                    "1. Підприємець \n"
                    "2. Працюю в компанії, але наймаю співробтників \n"
                    "3. Фрілансер/працюю на себе",
        "answers": ["1", "2", "3"],
        "single_choice": True,
    },
    {
        "question": "❓ Do you like Python?",
        "answers": ["Yes", "No"],
        "single_choice": True,  # Одиночный выбор
    },
    {
        "question": "❓ What fruits do you eat?",
        "answers": ["Apple", "Banana", "Orange"],
        "single_choice": False,  # Множественный выбор
    },
]


class AnswerStates(StatesGroup):
    waiting_for_answer = State()
    waiting_for_another = State()
    collecting_vac_data = State()

# --- CALLBACK FILTER ---
class CallbackFilter(BaseFilter):
    async def __call__(self, callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id in user_states and (callback.data in user_states[user_id] or callback.data in ["next", "another"]):
            return True
        return False

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    telegram_id = message.from_user.id

    # Получаем первый вопрос и его параметры
    first_question = questions_with_answers[0]
    question = first_question["question"]
    answers = first_question["answers"]
    single_choice = first_question["single_choice"]

    # Инициализируем состояние пользователя
    user_states[telegram_id] = {answer: False for answer in answers}
    await state.update_data(question_index=0, question=question, single_choice=single_choice)

    # Отправляем вопрос с кнопками
    await message.answer(question, reply_markup=await main_inline(telegram_id))
    await create_name_db(message.from_user.first_name, message.from_user.id)
    await create_answers_db(message.from_user.id)
    await state.set_state(AnswerStates.waiting_for_answer)

@router.callback_query(CallbackFilter())
async def cmd_change(callback: CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id

    # Получаем данные из состояния
    data = await state.get_data()
    question_index = data.get("question_index", 0)
    question = data.get("question", "No question found.")
    single_choice = data.get("single_choice", False)

    if callback.data == 'another':
        await callback.message.answer("Введіть свій варіант відповіді")
        await state.set_state(AnswerStates.waiting_for_another)

    if callback.data == 'next':
        # Сохраняем выбранные ответы
        selected_options = ", ".join(
            [key for key, state in user_states[telegram_id].items() if state]
        )
        print(f"Data saved for user {telegram_id}: Question: {question}, Answers: {selected_options}")
        await add_qa(telegram_id, question, selected_options)

        # Переход к следующему вопросу
        question_index += 1
        if question_index < len(questions_with_answers):
            next_question = questions_with_answers[question_index]
            question = next_question["question"]
            answers = next_question["answers"]
            single_choice = next_question["single_choice"]

            # Обновляем состояние кнопок для нового вопроса
            user_states[telegram_id] = {answer: False for answer in answers}
            await state.update_data(question_index=question_index, question=question, single_choice=single_choice)

            # Отправляем следующий вопрос
            await callback.message.answer(question, reply_markup=await main_inline(telegram_id))
        else:
            # Если вопросы закончились
            await callback.message.answer("No more questions. Thank you!")
            user_states.pop(telegram_id, None)
            await state.clear()
    else:
        # Обработка выбора для одиночного и множественного выбора
        if single_choice:
            # Если одиночный выбор, сбрасываем все остальные кнопки
            for key in user_states[telegram_id]:
                user_states[telegram_id][key] = False
            user_states[telegram_id][callback.data] = True
        else:
            # Если множественный выбор, переключаем только нажатую кнопку
            user_states[telegram_id][callback.data] = not user_states[telegram_id][callback.data]

        # Обновляем клавиатуру
        await callback.message.edit_reply_markup(reply_markup=await main_inline(telegram_id))

@router.message(AnswerStates.waiting_for_another)
async def handle_custom_answer(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    custom_answer = message.text.strip()

    # Получаем текущий вопрос из состояния
    data = await state.get_data()
    question = data.get("question", "No question found.")
    print(f"Data saved for user {telegram_id}: Question: {question}, Answer: {custom_answer}")
    await add_qa(telegram_id, question, custom_answer)

    await message.answer("Ваша відповідь прийнята!", reply_markup=await next_kb())

    # Возвращаем пользователя в состояние ожидания ответа
    await state.set_state(AnswerStates.waiting_for_answer)

@router.message(Command('vac'))
async def cmd_vac_db(message: Message, state: FSMContext):
    await message.answer('Введіть назву вакансії:')
    await state.set_state(AnswerStates.collecting_vac_data)
    await state.update_data(step="name")

@router.message(AnswerStates.collecting_vac_data)
async def vac_data(message: Message, state: FSMContext):
    data = await state.get_data()
    step = data.get("step")

    if step == "name":
        await state.update_data(name=message.text)
        await message.answer("Введіть категорію:", reply_markup=type_kb)
        await state.update_data(step="cat")
    elif step == "cat":
        await state.update_data(cat=message.text)

        user_data = await state.get_data()
        name = user_data.get("name")
        cat = user_data.get("cat")

        await vac_name(name, cat)

        await message.answer('Данные приняты!')

