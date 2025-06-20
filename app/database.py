import aiosqlite
from aiogram import Bot
from config import TOKEN

bot = Bot(token=TOKEN)

# creation of table with users names and ids

async def create_name_db(name: str, telegram_id: int):
    async with aiosqlite.connect("users.db") as db:
        # Создаем таблицу filters, если она еще не существует
        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS filters (
                name TEXT,
                ID BIGINT,  
                Категорія TEXT,
                Характер роботи TEXT,
                Тривалість TEXT,
                З TEXT,
                До TEXT, 
                Рівень досвіду TEXT
            )
        """)
        await db.commit()

        query_check_filters = "SELECT 1 FROM filters WHERE ID = ?"

        cursor_filters = await db.execute(query_check_filters, (telegram_id,))
        result_filters = await cursor_filters.fetchone()

        if result_filters is None:
            query_insert = "INSERT INTO filters (name, ID) VALUES (?, ?)"
            await db.execute(query_insert, (name, telegram_id))
            await db.commit()
            print(f"Пользователь {name} с telegram_id {telegram_id} добавлен.")
        else:
            print(f"Пользователь с telegram_id {telegram_id} уже существует")

# creation of table with questions and answers
async def create_answers_db(telegram_id):
    table_name = f"answers_{telegram_id}"
    async with aiosqlite.connect("answers.db") as db:
        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                questions TEXT,
                answers TEXT
            )
        """)
        await db.commit()

# insert of questions and users answers
async def add_qa(telegram_id, question, answer):
    table_name = f"answers_{telegram_id}"
    async with aiosqlite.connect("answers.db") as db:
        await db.execute(
            f"INSERT INTO {table_name} (questions, answers) VALUES (?, ?)",
            (question, answer,)
        )
        await db.commit()

async def create_vac_db():
    async with aiosqlite.connect("vacancies.db") as db:
        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS vacancies (
                vac_id INTEGER PRIMARY KEY,
                ID BIGINT,
                Назва TEXT,
                Категорія TEXT,
                Валюта ЗП TEXT, 
                ЗП INT, 
                Характер роботи TEXT,
                Тривалість TEXT,
                З TEXT,
                До TEXT, 
                Рівень досвіду TEXT,
                Опис TEXT
            )
        """)
        await db.commit()

async def create_users_db():
    async with aiosqlite.connect("users.db") as db:
        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS filters (
                name TEXT,
                ID BIGINT, 
                Категорія TEXT,
                ЗП INT, 
                Характер роботи TEXT,
                Тривалість TEXT,
                З TEXT,
                До TEXT, 
                Рівень досвіду TEXT
            )
        """)
        await db.commit()

async def create_analytics_db():
    async with aiosqlite.connect("analytics.db") as db:
        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS user_count (
                emp INT,
                srch INT, 
                emp_to_vac INT,
                srch_to_filt INT,
                emp_to_publ INT, 
                srch_to_fav INT
            )
        """)
        await db.commit()

async def select_analytics_db(column_name: str):
    # желательно убедиться, что column_name безопасен (не SQL-инъекция)
    allowed_columns = {"emp", "srch", "emp_to_vac", "srch_to_filt", "emp_to_publ", "srch_to_fav"}  # пример допустимых имён
    if column_name not in allowed_columns:
        raise ValueError("Недопустимое ім'я стовпця")

    async with aiosqlite.connect("analytics.db") as db:
        query = f"SELECT {column_name} FROM user_count LIMIT 1"
        async with db.execute(query) as cursor:
            row = await cursor.fetchone()

    return row[0] if row else None

async def update_analytics_db(field, value):
    async with aiosqlite.connect("analytics.db") as db:
        await db.execute(
            f"""UPDATE user_count
                SET {field} = ?""",
            (value, )
        )
        await db.commit()

async def insert_id(user_id):
    async with aiosqlite.connect("vacancies.db") as db:
        await db.execute("INSERT INTO vacancies (ID) VALUES (?)", (user_id,))
        await db.commit()

async def insert_searcher_id(user_id, name):
    async with aiosqlite.connect("users.db") as db:
        await db.execute("INSERT INTO filters (ID, name) VALUES (?, ?)", (user_id, name))
        await db.commit()

# Adding of new vacancy to th database. Employer enters "field" that represents column and "value" that represents
# data for cell
async def update_vacancy(field, user_id, value):
    async with aiosqlite.connect("vacancies.db") as db:
        await db.execute(
            f"""UPDATE vacancies 
                SET {field} = ? 
                WHERE ID = ? AND ("Опис" IS NULL)""",
            (value, user_id)
        )
        await db.commit()

async def update_filter(field, user_id, value):
    async with aiosqlite.connect("users.db") as db:
        await db.execute(f"UPDATE filters SET {field} = ? WHERE ID = ?", (value, user_id))
        await db.commit()

async def get_user_filters(user_id):
    # Столбцы, которые нужно извлечь
    columns = ["Категорія", "Характер роботи", "Тривалість роботи", "З", "До", "Рівень досвіду"]

    async with aiosqlite.connect("users.db") as db:
        async with db.execute(f"SELECT {', '.join(columns)} FROM filters WHERE ID = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()  # Получаем первую строку (предполагаем, что user_id уникален)

            if row:
                return dict(zip(columns, row))  # Преобразуем в словарь {название_столбца: значение}

    return None  # Если user_id не найден

async def rec_alg(viewed, telegram_id):

    filters = await get_user_filters(telegram_id)
    score = 0
    """Сравнивает вакансии с фильтрами и записывает подходящие в таблицу recommendations_{telegram_id}"""

    table_name = f"recommendations_{telegram_id}"

    print(f"🔄 [match_vacancies] Запущен поиск вакансий для {telegram_id} с фильтрами: {filters}")

    async with aiosqlite.connect("users.db") as user_db, aiosqlite.connect("vacancies.db") as vac_db:
        # Создаем таблицу рекомендаций (если ее нет)
        await user_db.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                viewed INTEGER,
                score INTEGER,
                Назва TEXT,
                Категорія TEXT,
                ЗП INT,
                Характер роботи TEXT,
                Тривалість роботи TEXT,
                З TEXT,
                До TEXT,
                Рівень досвіду TEXT,
                Опис TEXT
            )
        """)
        await user_db.commit()
        print(f"✅ [match_vacancies] Таблица {table_name} создана или уже существует.")

        vac_db.row_factory = aiosqlite.Row  # Делаем строки доступными по названию колонок
        async with vac_db.execute("SELECT * FROM vacancies") as cursor:
            async for row in cursor:
                row_dict = dict(row)  # Преобразуем строку в словарь
                if row_dict.get('Категорія') == filters.get('Категорія'):  # Защита от KeyError
                    score += 1
                    zp_value = row_dict.get('ЗП')
                    salary = None
                    if isinstance(zp_value, (int, float)):  # Проверка, что это число
                        if zp_value < 10000:
                            salary = 9999
                        elif 10000 <= zp_value < 40000:
                            salary = 39999
                        elif zp_value >= 40000:
                            salary = 40000
                    if salary == filters.get('ЗП'):
                        score += 1
                    if row_dict.get('Характер') == filters.get('Характер роботи'):
                        score += 1
                    if row_dict.get('Тривалість') == filters.get('Тривалість роботи'):
                        score += 1
                    if row_dict.get('З') == filters.get('З'):
                        score += 1
                    if row_dict.get('До') == filters.get('До'):
                        score += 1
                    if row_dict.get('Рівень') == filters.get('Рівень досвіду'):
                        score += 1
                    if score >= 2:
                        table_name = f"recommendations_{telegram_id}"
                        await user_db.execute(f"""INSERT INTO {table_name} (viewed, score, Назва, Категорія, ЗП, Характер, Тривалість, З, До, Рівень, Опис) 
                                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                              (viewed, score, row_dict.get('Назва'), row_dict.get('Категорія'),
                                               row_dict.get('ЗП'), row_dict.get('Характер'), row_dict.get('Тривалість'),
                                               row_dict.get('З'), row_dict.get('До'), row_dict.get('Рівень'),
                                               row_dict.get('Опис')))
                        await user_db.commit()

                    score = 0

async def send_rec(telegram_id):
    table_name = f"recommendations_{telegram_id}"
    async with aiosqlite.connect("users.db") as db:
        db.row_factory = aiosqlite.Row  # Позволяет обращаться к строкам как к словарям

        for score in range(6, 1, -1):  # Перебираем score от 6 до 2
            async with db.execute(f"SELECT * FROM {table_name} WHERE score = ? AND viewed = 0", (score,)) as cursor:
                row = await cursor.fetchone()  # Получаем первую строку с нужным score
                if row:
                    row_dict = dict(row)
                    # await db.execute(f"DELETE FROM {table_name} WHERE Опис = ?", (row_dict['Опис'],))
                    # await db.commit()  # Фиксируем изменения
                    await db.execute(f"UPDATE {table_name} SET viewed = 1 WHERE Опис = ?", (row_dict['Опис'],))
                    await db.commit()  # Фиксируем изменения
                    return row_dict  # Возвращаем строку, затем вызываем снова

                # Если больше нет строк с viewed = 0, очищаем таблицу
        async with db.execute(f"SELECT COUNT(*) FROM {table_name} WHERE viewed = 0") as cursor:
            count = await cursor.fetchone()
            if count[0] == 0:
                await db.execute(f"DELETE FROM {table_name}")  # Полностью очищаем таблицу
                await db.commit()

        return None  # Если записей больше нет

async def find_desc(telegram_id, short_description):
    async with aiosqlite.connect("vacancies.db") as db:
        db.row_factory = aiosqlite.Row

        # Ищем вхождение short_description в столбце Опис
        async with db.execute(f"SELECT * FROM vacancies WHERE Опис LIKE ?", (f"%{short_description}%",)) as cursor:
            row = await cursor.fetchone()
            if row:  # Проверяем, что row не None
                return dict(row)  # Преобразуем строку в словарь

    return None  # Если запись не найдена, возвращаем None

async def add_to_fav(telegram_id, row_dict: dict):
    async with aiosqlite.connect("users.db") as db:
        table_name = f"favorite_{telegram_id}"
        await db.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        viewed INTEGER,
                        Назва TEXT,
                        Категорія TEXT,
                        Характер роботи TEXT,
                        Тривалість роботи TEXT,
                        З TEXT,
                        До TEXT,
                        Рівень досвіду TEXT,
                        Опис TEXT
                    )
                """)
        await db.commit()

        viewed = 0

        await db.execute(f"""INSERT INTO {table_name} (viewed, Назва, Категорія, Характер, Тривалість, З, До, Рівень, Опис) 
                                                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                              (viewed, row_dict.get('Назва'), row_dict.get('Категорія'),
                               row_dict.get('Характер'), row_dict.get('Тривалість'),
                               row_dict.get('З'), row_dict.get('До'), row_dict.get('Рівень'),
                               row_dict.get('Опис')))
        await db.commit()

async def send_fav(telegram_id):
    async with aiosqlite.connect("users.db") as db:
        db.row_factory = aiosqlite.Row
        table_name = f"favorite_{telegram_id}"
        async with db.execute(f"SELECT * FROM {table_name} WHERE viewed = 0") as cursor:
            row = await cursor.fetchone()  # Получаем первую строчку с вьюд = 0
            if row:
                row_dict = dict(row)
                await db.execute(f"UPDATE {table_name} SET viewed = 1 WHERE Опис = ?", (row_dict['Опис'],))
                await db.commit()  # Фиксируем изменения
                return row_dict  # Возвращаем строку, затем вызываем снова

async def reset_viewed(telegram_id: int):
    async with aiosqlite.connect("users.db") as db:
        table_name = f"favorite_{telegram_id}"
        await db.execute(f"UPDATE {table_name} SET viewed = 0")
        await db.commit()

async def get_posted_vac(telegram_id):
    async with aiosqlite.connect("vacancies.db") as db:
        cursor = await db.execute("SELECT * FROM vacancies WHERE ID = ?", (telegram_id,))
        rows = await cursor.fetchall()
        await cursor.close()
        return rows

