import sqlite3

from PIL import Image, ImageDraw, ImageFont


def fetch_all_from_db():
    try:
        with sqlite3.connect("olympiad.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")  # Замените 'users' на название вашей таблицы
            rows = cursor.fetchall()  # Получаем все строки
            for row in rows:
                print(row)  # Печатаем каждую строку
    except Exception as e:
        print(f"Ошибка базы данных: {e}")

#fetch_all_from_db()

def init_db():
    with sqlite3.connect("olympiad.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                school_class INTEGER,
                class_letter TEXT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                payment_status INTEGER DEFAULT 0,
                score_1 INTEGER DEFAULT 0,
                score_2 INTEGER DEFAULT 0,
                score_3 INTEGER DEFAULT 0,
                test_date TEXT,
                certificate_path TEXT
            );
        """)
        conn.commit()

def update_db_payment_status(id):
    with sqlite3.connect("olympiad.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET score_1 = ?
            WHERE id = ?
        """, (0, id))
        conn.commit()

update_db_payment_status(1)

def generate_certificate(user_id, user_name):
    try:
        # Имя и фамилия
        full_name = user_name
        x_offset = 345
        y_offset = 305

        # Загружаем фото
        image = Image.open("static/certificate/certificate.jpg")

        # Создаём объект для рисования
        draw = ImageDraw.Draw(image)

        # Загружаем TTF-шрифт с поддержкой кириллицы
        font_path = "OpenSans-Medium.ttf"  # Положи сюда свой шрифт
        font_size = 50
        font = ImageFont.truetype(font_path, font_size)

        # Получаем размеры текста
        bbox = draw.textbbox((0, 0), full_name, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Позиция — с учётом смещений (x_offset, y_offset)
        x = x_offset
        y = y_offset

        # Нарисовать текст
        draw.text((x, y), full_name, font=font, fill=(0, 0, 0))

        # Сохраняем в certificate/1.jpg
        image.save(f"static/certificate/{user_id}/certificate.jpg")

        return f"static/certificate/{user_id}/certificate.jpg"
    except Exception as e:
        print(f"Ошибка генерации: {e}")
        return None

#generate_certificate(1, "Сағындықов Бақыт Ә")