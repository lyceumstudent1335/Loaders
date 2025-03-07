from flask import app, Flask, render_template, request, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from re import match
from datetime import datetime
import telebot
from threading import Thread
from dotenv import load_dotenv
import os
from json import loads
from subprocess import run
from waitress import serve

load_dotenv()

API_TOKEN = os.environ.get("API_TOKEN")
LOADER_HOUR_PRICE = int(os.environ.get("LOADER_HOUR_PRICE"))
bot = telebot.TeleBot(API_TOKEN)

class Base(DeclarativeBase): pass


db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///orders.db"
db.init_app(app)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[int] = mapped_column(unique=True)
    order_id: Mapped[int] = mapped_column(unique=True)
    processing: Mapped[bool]


with app.app_context():
    db.create_all()


def phone_to_int(phone: str) -> int:
    return int(''.join(filter(lambda s: s.isdigit(), phone)))


def new_order(first_name, last_name, address, loaders_count, phone_contact, timestamp):
    load_dotenv()
    admins = loads(os.environ.get("admins"))

    date = datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    for user_id in admins:
        bot.send_message(user_id, f"""Новый заказ📦
#{timestamp}
----------
Дата и время: {date}
Имя: {first_name}
Фамилия: {last_name}
Адрес: {address}
Кол-во грузчиков: {loaders_count}
Телефон: +{phone_contact}
""")


@app.route('/', methods=['GET'])
def home():
    if 'uid' in request.cookies.keys():
        q = db.session.query(Order).where(Order.order_id == int(request.cookies.get('uid'))).first()
        if q is not None and q.processing == True:
            return render_template("index.html", price=LOADER_HOUR_PRICE, processing_order=True, gen_id=request.cookies.get('uid'))
    return render_template("index.html", price=LOADER_HOUR_PRICE, processing_order=False)


@app.route('/order', methods=['POST'])
def order():
    if tuple(request.form.keys()) == ('first_name', 'last_name', 'address', 'loaders_count', 'phone_contact'):
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        address = request.form.get('address')
        loaders_count = request.form.get('loaders_count')
        phone_contact = request.form.get('phone_contact')

        if match("([А-Яа-я]+)", first_name) and match("([А-Яа-я]+)", last_name) and match("^[1-9]\d*$", loaders_count) and match("^\+7\s\(\d{3}\)\s\d{3}-\d{2}-\d{2}$", phone_contact):
            if 'uid' in request.cookies.keys():
                q = db.session.query(Order).where(Order.order_id == int(request.cookies.get('uid'))).first()
                if q is not None and q.processing == True:
                    return render_template("info.html", gen_id=request.cookies.get('uid'))
            
            phone_contact = phone_to_int(phone_contact)
            q = db.session.query(Order).where(Order.phone == phone_contact).first()
            if q is None:
                timestamp = int(datetime.now().timestamp())
                order = Order(
                    phone=phone_contact,
                    order_id=timestamp,
                    processing=True
                )
                db.session.add(order)
                db.session.commit()
                new_order(first_name, last_name, address, loaders_count, phone_contact, timestamp)
                response = make_response(render_template("success.html", gen_id=timestamp))
                response.set_cookie('uid', str(timestamp))
                return response
            else:
                if q.processing:
                    timestamp = q.order_id
                    response = make_response(render_template("info.html", gen_id=timestamp))
                    response.set_cookie('uid', str(timestamp))
                    return response
                else:
                    timestamp = int(datetime.now().timestamp())
                    q.order_id = timestamp
                    q.processing = True
                    db.session.commit()
                    new_order(first_name, last_name, address, loaders_count, phone_contact, timestamp)
                    response = make_response(render_template("success.html", gen_id=timestamp))
                    response.set_cookie('uid', str(timestamp))
                    return response
                
    return render_template("wrong.html")


if __name__ == "__main__":
    Thread(target=run, args=(["python3.10", "bot.py"],)).start()
    serve(app, host="127.0.0.1", port=8080)
