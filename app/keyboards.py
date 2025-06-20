from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# --- USER STATES ---
# Словарь для хранения состояний кнопок по telegram_id
user_states = {}


# --- INLINE KEYBOARD FOR EACH USER ---
async def main_inline(telegram_id):
    keyboard = InlineKeyboardBuilder()
    for key, state in user_states[telegram_id].items():
        text = f'✅ {key}' if state else key
        keyboard.add(InlineKeyboardButton(text=text, callback_data=key))

    # Проверяем, была ли нажата кнопка "Інший варіант"
    another_selected = user_states[telegram_id].get("another_selected", False)
    another_text = "✅ Інший варіант" if another_selected else "Інший варіант"
    keyboard.add(InlineKeyboardButton(text=another_text, callback_data='another'))

    keyboard.add(InlineKeyboardButton(text="Далі", callback_data='next'))
    return keyboard.adjust(1).as_markup()


async def next_kb():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Далі", callback_data='next'))
    return keyboard.adjust(1).as_markup()

# Keyboards for every category of vacnacies
e_cat_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Готельно-ресторанний бізнес', callback_data='hr')],
    [InlineKeyboardButton(text='IT', callback_data='it')],
    [InlineKeyboardButton(text='Фінанси, банк', callback_data='fin')],
    [InlineKeyboardButton(text='Бухгалтерія, аудит', callback_data='bukh')],
    [InlineKeyboardButton(text='Свій варіант', callback_data='cat_an')]
])

e_char_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Онлайн', callback_data='on')],
    [InlineKeyboardButton(text='Офлайн', callback_data='of')]
])

e_dur_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Одноразова/проектна робота', callback_data='one_time')],
    [InlineKeyboardButton(text='1-3 місяці', callback_data='1-3')],
    [InlineKeyboardButton(text='3-6 місяців', callback_data='3-6')],
    [InlineKeyboardButton(text='>6 місяців', callback_data='>6')]
])

e_exp_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Без досвіду', callback_data='no_exp')],
    [InlineKeyboardButton(text='менше 6 місяців', callback_data='less_6')],
    [InlineKeyboardButton(text='більше 6 місяців', callback_data='more_6')],
    [InlineKeyboardButton(text='більше 1 року', callback_data='more_1')]
])

e_sal_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='В гривнях', callback_data='uah')],
    [InlineKeyboardButton(text='В доларах', callback_data='usd')]
])

s_cat_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Готельно-ресторанний бізнес', callback_data='s_hr')],
    [InlineKeyboardButton(text='IT', callback_data='s_it')],
    [InlineKeyboardButton(text='Фінанси, банк', callback_data='s_fin')],
    [InlineKeyboardButton(text='Бухгалтерія, аудит', callback_data='s_bukh')],
    [InlineKeyboardButton(text='Свій варіант', callback_data='s_cat_an')]
])

s_char_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Онлайн', callback_data='s_on')],
    [InlineKeyboardButton(text='Офлайн', callback_data='s_of')]
])

s_dur_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Одноразова/проектна робота', callback_data='s_one_time')],
    [InlineKeyboardButton(text='1-3 місяці', callback_data='s_1-3')],
    [InlineKeyboardButton(text='3-6 місяців', callback_data='s_3-6')],
    [InlineKeyboardButton(text='>6 місяців', callback_data='s_>6')]
])

s_exp_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Без досвіду', callback_data='s_no_exp')],
    [InlineKeyboardButton(text='менше 6 місяців', callback_data='s_less_6')],
    [InlineKeyboardButton(text='більше 6 місяців', callback_data='s_more_6')],
    [InlineKeyboardButton(text='більше 1 року', callback_data='s_more_1')]
])

s_sal_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='До 10 000 грн.', callback_data='s_less_10')],
    [InlineKeyboardButton(text='Від 10 000 до 40 000 грн.', callback_data='s_10-40')],
    [InlineKeyboardButton(text='більше 40 000 грн.', callback_data='s_more_40')]
])

search_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='ШУКАТИ')]],
                                resize_keyboard=True, input_field_placeholder='Выберите пункт меню')

def vac_kb(exp: str, fav: str):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text=exp, callback_data='vac_exp'))
    keyboard.add(InlineKeyboardButton(text=fav, callback_data='vac_fav'))
    return keyboard.adjust(1).as_markup()


s_menu_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🔎 Шукати роботу'),
     KeyboardButton(text='❤️ Збережені вакансії')],
    [KeyboardButton(text='💼 Опублікувати вакансію')]
],
    resize_keyboard=True)

trash_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🗑', callback_data='trash')]
])

yes_no_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Так', callback_data='yes')],
    [InlineKeyboardButton(text='Ні', callback_data='no')]
])

emp_srch_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Я шукаю роботу', callback_data='srch')],
    [InlineKeyboardButton(text='Я шукаю працівника', callback_data='emp')]
])
