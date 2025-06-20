from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode

from app.database import *
from app.keyboards import *

from aiogram.filters.logic import or_f

router = Router()

class AnswerStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_cat = State()
    waiting_for_cat_another = State()
    waiting_for_char = State()
    waiting_for_dur = State()
    waiting_for_since = State()
    waiting_for_till = State()
    waiting_for_exp = State()
    waiting_for_desc = State()
    waiting_for_cur = State()
    waiting_for_sal = State()
    waiting_for_del = State()
    waiting_for_goal = State()

class VacancyState(StatesGroup):
    descriptions = State()  # Словарь {message_id: описание}

@router.message(Command('start'))
async def cmd_menu(message: Message, state: FSMContext):
    await message.answer('👋')
    await message.answer('Привіт! Це Gigsy, платформа для пошуку та публікації роботи на парт-тайм (підробіток). \n\n'
                         'Тут все просто та швидко, давай розберемось на практиці!', reply_markup=s_menu_kb)
    await message.answer('Перший крок. Обери свою мету', reply_markup=emp_srch_kb)
    await create_analytics_db()
    await state.set_state(AnswerStates.waiting_for_goal)

@router.callback_query(F.data.in_({"emp", "srch"}))
async def cmd_emp_srch(callback: CallbackQuery):

    #await callback.message.answer(str(count))

    if callback.data == 'emp':
        count = await select_analytics_db("emp")
        await update_analytics_db("emp", int(count+1))
        await callback.message.answer('Супер! Для публікації вакансії оберіть пункт "💼 Опублікувати вакансію" в меню')
    if callback.data == 'srch':
        count = await select_analytics_db("srch")
        await update_analytics_db("srch", int(count+1))
        await callback.message.answer('Супер! Для пошуку вакансій обери пункт "🔎 Шукати роботу" в меню')

@router.message(F.text == "45345")
async def cmd_an(message: Message):
    emp_count = await select_analytics_db("emp")
    srch_count = await select_analytics_db("srch")
    emp_to_vac_count = await select_analytics_db("emp_to_vac")
    srch_to_filt_count = await select_analytics_db("srch_to_filt")
    emp_to_publ_count = await select_analytics_db("emp_to_publ")
    srch_to_fav_count = await select_analytics_db("srch_to_fav")
    await message.answer(f"Роботодавці: {emp_count} \n"
                         f"Шукачі: {srch_count} \n\n"
                         f"Роботодавці, що почали публікувати вакансію: {emp_to_vac_count} \n"
                         f"Шукачі, що почали шукати: {srch_to_filt_count} \n"
                         f"Роботодавці, що опублікували вакансію: {emp_to_publ_count} \n"
                         f"Шукачі, що зберегли вакансію: {srch_to_fav_count}")

@router.message(F.text == "ШУКАТИ")
async def send_filters(message: Message):
    user_id = message.from_user.id  # Получаем user_id из Telegram
    filters = await get_user_filters(user_id)  # Загружаем данные из БД

    if filters:
        salary = 0
        viewed = 0
        await rec_alg(viewed, user_id)

        while True:
            row = await send_rec(user_id)
            if row is None:
                await message.answer("Рекомендации закончились.")
                break

            # Отправляем пользователю данные из row
            await message.answer(f"<b>{row['Назва']}</b> \n\n"
                                 f"<b>💵 Заробітна плата:</b> {row['ЗП']}\n\n"
                                 f"<b>👨‍💻 Характер роботи:</b> {row['Характер']} \n"
                                 f"<b>🕐 Графік:</b> {row['З']} до {row['До']} \n"
                                 f"<b>📝 Опис: </b>{row['Опис'][:100]}",
                                 parse_mode="HTML", reply_markup=vac_kb("Розгорнути 🔽", "🤍"))
    else:
        await message.answer("❌ Фильтры не найдены.")

@router.callback_query(F.data.in_({"vac_fav", "vac_exp"}))
async def fav_toggle(callback: CallbackQuery):
    fav_state = callback.message.reply_markup.inline_keyboard[1][0].text
    exp_state = callback.message.reply_markup.inline_keyboard[0][0].text

    fav_text = fav_state  # По умолчанию остаётся неизменным
    exp_text = exp_state  # То же самое
    new_text = callback.message.text  # По умолчанию текст остаётся прежним

    row = await find_desc(callback.from_user.id, callback.message.text.split("📝 Опис: ")[1]) if "📝 Опис: " in callback.message.text else None

    if callback.data == "vac_fav":
        count = await select_analytics_db("srch_to_fav")
        await update_analytics_db("srch_to_fav", int(count + 1))
        fav_text = "❤️" if fav_state == "🤍" else "🤍"
        await add_to_fav(callback.from_user.id, row)

    if callback.data == "vac_exp":
        exp_text = "Згорнути 🔼" if exp_state == "Розгорнути 🔽" else "Розгорнути 🔽"

        if row:
            if exp_state == "Розгорнути 🔽":
                new_text = (
                    f"<b>{row['Назва']}</b> \n\n"
                    f"<b>💵 Заробітна плата:</b> {row['ЗП']}\n\n"
                    f"<b>⚙️ Категорія:</b> {row['Категорія']} \n"
                    f"<b>👨‍💻 Характер роботи:</b> {row['Характер']} \n"
                    f"<b>📅 Тривалість:</b> {row['Тривалість']} \n"
                    f"<b>🕐 Графік:</b> {row['З']} до {row['До']} \n"
                    f"<b>💼 Рівень досвіду:</b> {row['Рівень']} \n\n"
                    f"<b>📝 Опис: </b>{row['Опис']}"
                )
            else:
                new_text = (
                    f"<b>{row['Назва']}</b> \n\n"
                    f"<b>💵 Заробітна плата:</b> {row['ЗП']}\n\n"
                    f"<b>👨‍💻 Характер роботи:</b> {row['Характер']} \n"
                    f"<b>🕐 Графік:</b> {row['З']} до {row['До']} \n\n"
                    f"<b>📝 Опис: </b>{row['Опис'][:100]}"
                )

    # **Обновляем кнопки всегда**, даже если изменился только "🤍"
    await callback.message.edit_text(new_text, parse_mode="HTML", reply_markup=vac_kb(exp_text, fav_text))

    await callback.answer()

    # message_text = callback.message.text

@router.message(or_f(F.text == "❤️ Збережені вакансії", Command("fav")))
async def cmd_send_favs(message: Message):
    max_attempts = 5
    attempts = 0

    while attempts < max_attempts:
        # viewed = 0
            row = await send_fav(message.from_user.id)
            print(row)
            if row is None:
                await reset_viewed(message.from_user.id)
                await message.answer("Рекомендации закончились.")
                break

            # Отправляем пользователю данные из row
            await message.answer(f"<b>{row['Назва']}</b> \n\n"
                                          f"<b>👨‍💻 Характер роботи:</b> {row['Характер']} \n"
                                          f"<b>🕐 Графік:</b> {row['З']} до {row['До']} \n"
                                          f"<b>📝 Опис: </b>{row['Опис'][:100]}",
                                          parse_mode="HTML", reply_markup=vac_kb("Розгорнути 🔽", "🤍"))
    else:
        await message.answer("❌ Фильтры не найдены.")

# Adding of new vacancy by employer
@router.message(or_f(F.text == "💼 Опублікувати вакансію", Command("vac")))
async def cmd_vac_db(message: Message, state: FSMContext):
    #analytics
    count = await select_analytics_db("emp_to_vac")
    await update_analytics_db("emp_to_vac", int(count + 1))

    await create_vac_db()
    await insert_id(message.from_user.id)
    await message.answer("Введіть назву вакансії:")
    await state.set_state(AnswerStates.waiting_for_name)

@router.message(AnswerStates.waiting_for_name)
async def cmd_collect_name(message: Message, state: FSMContext):
    await update_vacancy("Назва", message.from_user.id, message.text)
    await message.answer("Введіть категорію:", reply_markup=e_cat_kb)
    await state.set_state(AnswerStates.waiting_for_cat)

@router.callback_query(F.data.in_({"hr", "it", "fin", "bukh"}))
async def cmd_cat(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'hr':
        await update_vacancy("Категорія", callback.from_user.id, 'Готельно-ресторанний бізнес')
    if callback.data == 'it':
        await update_vacancy("Категорія", callback.from_user.id, 'IT')
    if callback.data == 'fin':
        await update_vacancy("Категорія", callback.from_user.id, 'Фінанси, банк')
    if callback.data == 'bukh':
        await update_vacancy("Категорія", callback.from_user.id, 'Бухгалтерія, аудит')
    await callback.message.answer("Який характер роботи?", reply_markup=e_char_kb)
    await state.set_state(AnswerStates.waiting_for_char)

@router.callback_query(F.data == "cat_an")
async def cmd_cat_another(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Ваш варіант:")
    await state.set_state(AnswerStates.waiting_for_cat_another)

@router.message(AnswerStates.waiting_for_cat_another)
async def cmd_cat_another_text(message: Message, state: FSMContext):
    await update_vacancy("Категорія", message.from_user.id, message.text)
    await message.answer("Який характер роботи?", reply_markup=e_char_kb)
    await state.set_state(AnswerStates.waiting_for_char)

@router.callback_query(F.data.in_({"on", "of"}))
async def cmd_char(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'on':
        await update_vacancy("Характер", callback.from_user.id, "Онлайн")
    if callback.data == 'of':
        await update_vacancy("Характер", callback.from_user.id, "Офлайн")
    await callback.message.answer("Яка тривалість роботи?", reply_markup=e_dur_kb)
    await state.set_state(AnswerStates.waiting_for_dur)

@router.callback_query(F.data.in_({"one_time", "1-3", "3-6", ">6"}))
async def cmd_dur(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'one_time':
        await update_vacancy("Тривалість", callback.from_user.id, 'Одноразова/проектна робота')
    if callback.data == '1-3':
        await update_vacancy("Тривалість", callback.from_user.id, '1-3 місяці')
    if callback.data == '3-6':
        await update_vacancy("Тривалість", callback.from_user.id, '3-6 місяців')
    if callback.data == '>6':
        await update_vacancy("Тривалість", callback.from_user.id, '>6 місяців')
    await callback.message.answer("З якого часу?")
    await state.set_state(AnswerStates.waiting_for_since)

@router.message(AnswerStates.waiting_for_since)
async def cmd_since(message: Message, state: FSMContext):
    await update_vacancy("З", message.from_user.id, message.text)
    await message.answer("До якого часу?")
    await state.set_state(AnswerStates.waiting_for_till)

@router.message(AnswerStates.waiting_for_till)
async def cmd_till(message: Message, state: FSMContext):
    await update_vacancy("До", message.from_user.id, message.text)
    await message.answer("Рівень досвіду", reply_markup=e_exp_kb)
    await state.set_state(AnswerStates.waiting_for_exp)

@router.callback_query(F.data.in_({"no_exp", "less_6", "more_6", "more_1"}))
async def cmd_exp(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'no_exp':
        await update_vacancy("Рівень", callback.from_user.id, 'Без досвіду')
    if callback.data == 'less_6':
        await update_vacancy("Рівень", callback.from_user.id, 'менше 6 місяців')
    if callback.data == 'more_6':
        await update_vacancy("Рівень", callback.from_user.id, 'більше 6 місяців')
    if callback.data == 'more_1':
        await update_vacancy("Рівень", callback.from_user.id, 'більше 1 року')
    await callback.message.answer("Оберіть валюту для вказання заробітної плати", reply_markup=e_sal_kb)
    await state.set_state(AnswerStates.waiting_for_cur)

@router.callback_query(F.data.in_({"usd", "uah"}))
async def cmd_cur(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'uah':
        await update_vacancy("Валюта", callback.from_user.id, 'UAH')
    if callback.data == 'usd':
        await update_vacancy("Валюта", callback.from_user.id, 'USD')
    await callback.message.answer("Введіть суму заробітної плати числом без пробілів")
    await state.set_state(AnswerStates.waiting_for_sal)

@router.message(AnswerStates.waiting_for_sal)
async def cmd_sal(message: Message, state: FSMContext):
    await update_vacancy("ЗП", message.from_user.id, message.text)
    await message.answer("Введіть опис вакансії не менше, ніж на 100 символів")
    await state.set_state(AnswerStates.waiting_for_desc)

@router.message(AnswerStates.waiting_for_desc)
async def cmd_desc(message: Message, state: FSMContext):
    if len(message.text) < 100:
        await message.answer("❌ Опис занадто короткий! Будь ласка, введи хоча б 100 символів.")
        return  # Не завершаем state, ждем правильный ввод

    await update_vacancy("Опис", message.from_user.id, message.text)
    await message.answer("✅ Готово! Ваша ваканся опублікована!")

    #analytics
    count = await select_analytics_db("emp_to_publ")
    await update_analytics_db("emp_to_publ", int(count + 1))

    await state.clear()

@router.message(Command("my_vac"))
async def cmd_my_vac_db(message: Message):
    vacancies = await get_posted_vac(message.from_user.id)

    if not vacancies:
        await message.answer("Вакансий не найдено.")
        return

    for vacancy in vacancies:
        text = (
            f"<b>{vacancy[1]}</b>\n\n"
            f"<b>💵 Заробітна плата:</b>{vacancy[4]}\n\n"
            f"<b>⚙️ Категорія:</b>{vacancy[2]}\n"
            f"<b>👨‍💻 Характер роботи:</b> {vacancy[5]}\n"
            f"<b>📅 Тривалість:</b>{vacancy[6]}\n"
            f"<b>🕐 Графік:</b> З {vacancy[7]} до {vacancy[8]}\n"
            f"<b>💼 Рівень досвіду:</b> {vacancy[9]}\n\n"
            f"<b>📝 Опис:</b>{vacancy[10]}"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=trash_kb)

@router.callback_query(F.data == 'trash')
async def cmd_del_conf(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Ви впевнені, що хочете видалити цю вакансію?', reply_markup=yes_no_kb)
    await state.set_state(AnswerStates.waiting_for_del)

