import telebot
from telebot import types
import sqlite3

from io import BytesIO
from PIL import Image
from pyzbar.pyzbar import decode
import re
from requests import exceptions as requestEx
from private import KEY
from utils import *


bot = telebot.TeleBot(KEY)

markup = types.ReplyKeyboardMarkup()
start = types.KeyboardButton("/start")
help = types.KeyboardButton("/help")
sum_current_month = types.KeyboardButton("/sum")
sum_last_month = types.KeyboardButton("/last_sum")
average_month = types.KeyboardButton("/avg")
average_month_per_day = types.KeyboardButton("/avg_per_day")
all_in_month = types.KeyboardButton("/all_in_month")
all_in_last_month = types.KeyboardButton("/last_month")
markup.add(help,
           sum_current_month,
           sum_last_month,
           average_month,
           average_month_per_day,
           all_in_month,
           all_in_last_month)


@bot.message_handler(commands=['start'])
def start(message) -> None:
    text = "Отправь фото чека с QR кодом или сумму покупки, я запишу ｡^‿^｡"
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(commands=['help'])
def help(message) -> None:
    text = "Команды бота:\n" \
           "/sum: Сумма покупок за текущий месяц\n" \
           "/last_sum: Сумма покупок за прошлый месяц\n" \
           "/avg: Средняя сумма покупки за этот месяц\n" \
           "/avg_per_day: Средняя сумма покупок в день\n" \
           "/all_in_month: Все покупки за этот месяц\n" \
           "/last_month Все покупки за прошлый месяц\n" \
           "Вы можете вывести функции sum avg all за определённый промежуток указав" \
           " сначала дату начала отсчёта, дату конца отчёта и название функции:\n" \
           "год месяц день год месяц день {sum, avg, all}"
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(content_types=['photo'])
def db_save(message) -> None:
    try:
        photo_id = message.photo[-1].file_id
        photo_file = bot.get_file(photo_id)
        photo_bytes = bot.download_file(photo_file.file_path)

        stream = BytesIO(photo_bytes)
        image = Image.open(stream).convert("RGBA")
        stream.close()
        data = decode(image)

        date = str(data[0][0]).split("&")[0].replace("b't=", "").split("T")
        coast = str(data[0][0]).split("&")[1].replace("s=", "")
        time = [date[1][:2], date[1][2:]]
        date = [date[0][:4], date[0][4:6], date[0][6:8]]

        db = sqlite3.connect("cost_accounting_base.db")
        sql = db.cursor()
        sql.execute(f"""INSERT INTO cost_accounting
                        VALUES
                            ({message.from_user.id}, datetime('{date[0]}-{date[1]}-{date[2]} 
                            {time[0]}:{time[1]}'), {coast});""")
        db.commit()
        db.close()
        bot.send_message(message.chat.id, "Покупка сохранена:\n"
                                          f"Время: {date[0]}-{date[1]}-{date[2]} {time[0]}:{time[1]}\n"
                                          f"Цена: {coast}", reply_markup=markup)
    except Exception as error:
        bot.send_message(message.chat.id, "Я не понял (╯︵╰,)", reply_markup=markup)
        print(error)


@bot.message_handler(commands=['sum'])
def sum_current_month(message) -> None:
    year, month, days = get_date()

    db = sqlite3.connect("cost_accounting_base.db")
    sql = db.cursor()
    sql_result = sql.execute(f"""SELECT SUM(cost)
                        FROM cost_accounting
                        WHERE telegram_id = {message.from_user.id} AND (date BETWEEN datetime('{year}-{month}-01') AND
                         datetime('{year}-{month}-{days}'))""")

    bot.send_message(message.chat.id, fetchone_sql(sql_result.fetchone()), reply_markup=markup)
    db.close()


@bot.message_handler(commands=['last_sum'])
def all_in_last_month(message) -> None:
    year, month, days = get_date()

    if month == "01":
        month = "12"
        year = str(int(year) - 1)
        days = "31"
    else:
        month = "0" + str(int(month) - 1)

    days = monthrange(int(year), int(month))[1]

    db = sqlite3.connect("cost_accounting_base.db")
    sql = db.cursor()
    sql_result = sql.execute(f"""SELECT SUM(cost)
                        FROM cost_accounting
                        WHERE telegram_id = {message.from_user.id} AND (date BETWEEN datetime('{year}-{month}-01') AND
                         datetime('{year}-{month}-{days}'))""")

    bot.send_message(message.chat.id, fetchone_sql(sql_result.fetchone()), reply_markup=markup)
    db.close()


@bot.message_handler(commands=['avg'])
def average_month(message) -> None:
    year, month, days = get_date()

    db = sqlite3.connect("cost_accounting_base.db")
    sql = db.cursor()
    sql_result = sql.execute(f"""SELECT AVG(cost)
                        FROM cost_accounting
                        WHERE telegram_id = {message.from_user.id} AND (date BETWEEN datetime('{year}-{month}-01') AND
                         datetime('{year}-{month}-{days}'))""")

    bot.send_message(message.chat.id, fetchone_sql(sql_result.fetchone()), reply_markup=markup)
    db.close()


@bot.message_handler(commands=['avg_per_day'])
def average_month_per_day(message) -> None:
    db = sqlite3.connect("cost_accounting_base.db")
    sql = db.cursor()
    sql_result = sql.execute(f"""SELECT AVG(sum_cost.sum)
                                 FROM (SELECT SUM(cost) AS sum
                                     FROM cost_accounting
                                     WHERE telegram_id = {message.from_user.id}
                                     GROUP BY strftime('%m-%d', date)) AS sum_cost""")

    bot.send_message(message.chat.id, fetchone_sql(sql_result.fetchone()), reply_markup=markup)
    db.close()


@bot.message_handler(commands=['all_in_month'])
def all_in_month(message) -> None:
    year, month, days = get_date()

    db = sqlite3.connect("cost_accounting_base.db")
    sql = db.cursor()
    sql_result = sql.execute(f"""SELECT *
                        FROM cost_accounting
                        WHERE telegram_id = {message.from_user.id} AND (date BETWEEN datetime('{year}-{month}-01') AND
                         datetime('{year}-{month}-{days}'))
                        ORDER BY date DESC""")

    bot.send_message(message.chat.id, fetchall_sql(sql_result.fetchall()), reply_markup=markup)
    db.close()


@bot.message_handler(commands=['last_month'])
def all_in_last_month(message) -> None:
    year, month, days = get_date()

    if month == "01":
        month = "12"
        year = str(int(year) - 1)
        days = "31"
    else:
        month = "0" + str(int(month) - 1)

    days = monthrange(int(year), int(month))[1]

    db = sqlite3.connect("cost_accounting_base.db")
    sql = db.cursor()
    sql_result = sql.execute(f"""SELECT *
                        FROM cost_accounting
                        WHERE telegram_id = {message.from_user.id} AND (date BETWEEN datetime('{year}-{month}-01') AND
                         datetime('{year}-{month}-{days}'))
                        ORDER BY date DESC""")

    bot.send_message(message.chat.id, fetchall_sql(sql_result.fetchall()), reply_markup=markup)
    db.close()


@bot.message_handler(content_types=["text"])
def db_save_from_text(message) -> None:
    if re.search(r"^\d{4} \d{1,2} \d{1,2} \d{4} \d{1,2} \d{1,2} \w{3}", message.text):
        route(message)

    if message.text.isdigit():
        year, month, days = get_date()
        time = datetime.now().strftime("%H:%M:%S").split(":")
        day = datetime.now().strftime("%d")

        db = sqlite3.connect("cost_accounting_base.db")
        sql = db.cursor()
        sql.execute(f"""INSERT INTO cost_accounting
                        VALUES
                            ({message.from_user.id}, datetime('{year}-{month}-{day}
                            {time[0]}:{time[1]}:{time[2]}'), {message.text});""")
        db.commit()
        db.close()

        bot.send_message(message.chat.id, "Покупка сохранена:\n"
                                          f"Время: {year}-{month}-{day} {time[0]}:{time[1]}\n"
                                          f"Цена: {message.text}", reply_markup=markup)


def route(message) -> None:
    id = message.from_user.id
    chat = message.chat.id
    date = convert_date(message.text)
    if type(date) == str:
        bot.send_message(message.chat.id, date, reply_markup=markup)
    else:
        if date[6] in ("sum", "avg", "all"):
            if date[6] == "sum":
                sum_current_month_user_input(date, id, chat)
            elif date[6] == "avg":
                average_month_user_input(date, id, chat)
            elif date[6] == "all":
                all_in_month_user_input(date, id, chat)
        else:
            bot.send_message(message.chat.id, "Ошибка функции", reply_markup=markup)


def sum_current_month_user_input(date: list, id: int, chat: int) -> None:
    db = sqlite3.connect("cost_accounting_base.db")
    sql = db.cursor()
    sql_result = sql.execute(f"""SELECT SUM(cost)
                        FROM cost_accounting
                        WHERE telegram_id = {id} AND (date BETWEEN datetime('{date[0]}-{date[1]}-{date[2]}') AND 
                        datetime('{date[3]}-{date[4]}-{date[5]}'))""")

    bot.send_message(chat, fetchone_sql(sql_result.fetchone()), reply_markup=markup)
    db.close()


def average_month_user_input(date: list, id: int, chat: int) -> None:
    db = sqlite3.connect("cost_accounting_base.db")
    sql = db.cursor()
    sql_result = sql.execute(f"""SELECT AVG(cost)
                        FROM cost_accounting
                        WHERE telegram_id = {id} AND (date BETWEEN datetime('{date[0]}-{date[1]}-{date[2]}') 
                        AND datetime('{date[3]}-{date[4]}-{date[5]}'))""")

    bot.send_message(chat, fetchone_sql(sql_result.fetchone()), reply_markup=markup)
    db.close()


def all_in_month_user_input(date: list,id: int, chat: int) -> None:
    db = sqlite3.connect("cost_accounting_base.db")
    sql = db.cursor()
    sql_result = sql.execute(f"""SELECT *
                        FROM cost_accounting
                        WHERE telegram_id = {id} AND (date BETWEEN datetime('{date[0]}-{date[1]}-{date[2]}') 
                        AND datetime('{date[3]}-{date[4]}-{date[5]}'))
                        ORDER BY date DESC""")

    bot.send_message(chat, fetchall_sql(sql_result.fetchall()), reply_markup=markup)
    db.close()


if __name__ == "__main__":
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except requestEx as error:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {error}")
            continue
