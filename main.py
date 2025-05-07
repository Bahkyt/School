import os
import sqlite3

import qrcode
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, redirect, render_template, request, session, jsonify
from flask import send_file
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

min_score = 5

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

init_db()


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



@app.route('/', methods=["POST", "GET"])
def index():
    if request.method == "POST":
        login = request.form["login"]
        password = request.form["password"]

        if login == "admin@admin" and password == "admin":
            return redirect("/teacher")
        else:
            with sqlite3.connect("olympiad.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ?", (login,))
                user = cursor.fetchone()

                if user:
                    if user[6] == password:
                        session['user_id'] = user[0]
                        session['email'] = user[5]
                        return redirect("/payment")
                    else:
                        return "Неправильный пароль"
                else:
                    return "Пользователь не найден"
    else:
        return render_template("main_login.html")


@app.route('/registration', methods=["POST", "GET"])
def registration():
    if request.method == "POST":
        name = request.form["first_name"]
        last_name = request.form["last_name"]
        school_class = request.form["class"]
        school_class_letter = request.form["class_letter"]
        email = request.form["email"]
        password = request.form["password"]

        try:
            with sqlite3.connect("olympiad.db") as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (first_name, last_name, school_class, class_letter, email, password)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, last_name, school_class, school_class_letter, email, password))
                user_id = cursor.lastrowid
                folder_path = f"static/certificate/{user_id}"
                os.makedirs(folder_path, exist_ok=True)
                cursor.execute("""
                    UPDATE users SET certificate_path = ? WHERE id = ?
                """, (folder_path + '/', user_id))
                conn.commit()
            return redirect("/")
        except sqlite3.IntegrityError as e:
            if 'UNIQUE constraint failed: users.email' in str(e):
                return "Ошибка: Email уже используется!"
            else:
                return f"Ошибка при добавлении пользователя: {e}"
        except Exception as e:
            return f"Общая ошибка: {e}"


    else:
        return render_template("main_reg.html")


@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect('/')

    with sqlite3.connect("olympiad.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()


    if user[8] >= min_score:
        # блок кнопок test-1
        pass

    if user[9] >= min_score:
        # блок кнопок test-2
        pass

    if user[10] >= min_score:
        # блок кнопок test-3
        pass

    if user[7] == 1:
        return render_template("home.html", user=user)
    else:
        return redirect("/payment")



@app.route('/payment')
def payment():
    if 'user_id' not in session:
        return redirect('/')

    with sqlite3.connect("olympiad.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()

    if user[7] == 1:
        return redirect("/home")
    else:
        return render_template("payment.html", user=user)


@app.route("/profile/<id>")
def profile(id):
    if 'user_id' not in session:
        return redirect('/')

    with sqlite3.connect("olympiad.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()

        if not user:
            return "Пользователь не найден", 404

        total_score = user[8] + user[9] + user[10]
        max_score = 75
        status = "Не пройден"
        cert_path = None

        if total_score >= min_score * 3:
            status = "Пройден"
            cert_path = f"static/certificate/{user[0]}/certificate.jpg"
            if not os.path.exists(cert_path):
                generated_path = generate_certificate(user[0], f"{user[1]} {user[2]}")
                if generated_path:
                    cursor.execute("UPDATE users SET certificate_path=? WHERE id=?",
                                 (f"static/certificate/{user[0]}/", user[0]))
                    conn.commit()
                    print("Успешно")
                    cert_path = generated_path

        user_data = {
            'id': user[0],
            'full_name': f"{user[1]} {user[2]}",
            'class_info': f"{user[3]}{user[4]}",
            'email': user[5],
            'payment_status': "Оплачено" if user[7] else "Не оплачено",
            'scores': {
                'test1': user[8],
                'test2': user[9],
                'test3': user[10],
                'total': total_score,
                'max': max_score,
                'status': status
            },
            'certificate_path': f"/static/certificate/{id}/certificate.jpg"
        }

    return render_template('profile.html', user=user_data, min_score=min_score)

@app.route('/verify/<cert_id>')
def verify_certificate(cert_id):
    cert_path = f"static/certificate/{cert_id}/certificate.jpg"
    if os.path.exists(cert_path):
        with sqlite3.connect("olympiad.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT first_name, last_name FROM users WHERE id=?", (cert_id,))
            user = cursor.fetchone()

        if user:
            return render_template("verify.html",
                                   valid=True,
                                   name=f"{user[0]} {user[1]}",
                                   cert_id=cert_id)

    return render_template("verify.html", valid=False)


@app.route('/test_cert/<user_id>')
def test_cert(user_id):
    if not os.environ.get('DEBUG'):  # Доступно только в режиме разработки
        return "Not allowed", 403

    with sqlite3.connect("olympiad.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, last_name FROM users WHERE id=?", (user_id,))
        user = cursor.fetchone()

    if user:
        generate_certificate(user_id, f"{user[0]} {user[1]}", fake_mode=True)
        return redirect(f"/static/certificates/{user_id}/certificate.png")

    return "User not found", 404

@app.route('/print_certificate/<user_id>')
def print_certificate(user_id):
        cert_path = f"static/certificate/{user_id}/certificate.jpg"
        if os.path.exists(cert_path):
            return send_file(cert_path, mimetype='image/png')
        else:
            return "Сертификат не найден", 404


@app.route('/teacher')
def teacher_cabinet():
    try:
        with sqlite3.connect("olympiad.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
    except Exception as e:
        print(f"Ошибка базы данных: {e}")
    return render_template('Tcabinet.html', rows=rows)



@app.route('/teacher/<id>')
def teacher(id):
    with sqlite3.connect("olympiad.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (id,))
        user = cursor.fetchone()


    return render_template('detailed.html', user=user)


@app.route('/teacher/<int:id>/update', methods=['POST'])
def update_teacher_permission(id):
    data = request.get_json()
    permission_value = data.get('payment_status')

    if permission_value not in [0, 1]:
        return jsonify({'error': 'Неверное значение'}), 400

    with sqlite3.connect("olympiad.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET payment_status = ? WHERE id = ?", (permission_value, id))
        conn.commit()

    return '', 200


@app.route("/test/1")
def test():
    if 'user_id' not in session:
        return redirect('/')

    with sqlite3.connect("olympiad.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()

    return render_template("test_1.html", user=user, min_score=min_score)




@app.route("/receive_score", methods=["POST"])
def receive_score():
    if 'user_id' not in session:
        return "Unauthorized", 401

    data = request.get_json()
    score = data.get("score")

    if score is not None:
        try:
            with sqlite3.connect("olympiad.db") as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET score_1 = ?
                    WHERE id = ?
                """, (score, session['user_id']))
                conn.commit()
            return "", 204
        except Exception as e:
            print(f"Ошибка при обновлении балла: {e}")
            return "Ошибка при сохранении", 500
    else:
        return "Нет данных о балле", 400


@app.route("/update-pay")
def pay():
    id = session['user_id']
    with sqlite3.connect("olympiad.db") as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET payment_status = ?
            WHERE id = ?
        """, (1, id))


        cursor.execute("""
            UPDATE users
            SET score_1 = ?
            WHERE id = ?
        """, (0, id))

        cursor.execute("""
            UPDATE users
            SET score_2 = ?
            WHERE id = ?
        """, (10, id))

        cursor.execute("""
            UPDATE users
            SET score_3 = ?
            WHERE id = ?
        """, (10, id))

        conn.commit()

    return redirect("/home")



@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)