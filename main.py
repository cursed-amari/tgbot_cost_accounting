from io import BytesIO
import os

import telebot
from telebot import types

from PIL import Image
from pyzbar.pyzbar import decode
import sqlite3
from datetime import datetime
from calendar import monthrange
from private import KEY

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
markup.add(start,
           help,
           sum_current_month,
           sum_last_month,
           average_month,
           average_month_per_day,
           all_in_month,
           all_in_last_month)


def get_date():
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%m")
    days = monthrange(int(year), int(month))[1]
    return [year, month, days]


@bot.message_handler(commands=['start'])
def start(message) -> None:
    text = "Отправь фото чека с QR кодом или сумму покупки, я запишу ｡^‿^｡"
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(commands=['help'])
def start(message) -> None:
    text = "Команды бота:\n" \
           "/sum: Сумма покупок за текущий месяц\n" \
           "/last_sum: Сумма покупок за прошлый месяц\n" \
           "/avg: Средняя сумма покупки за этот месяц\n" \
           "/avg_per_day: Средняя сумма покупок в день\n" \
           "/all_in_month: Все покупки за этот месяц\n" \
           "/last_month Все покупки за прошлый месяц"
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
                            (datetime('{date[0]}-{date[1]}-{date[2]} {time[0]}:{time[1]}'), {coast});""")
        db.commit()
        db.close()
        bot.send_message(message.chat.id, "Покупка сохранена:\n"
                                          f"Время: {date[0]}-{date[1]}-{date[2]} {time[0]}:{time[1]}\n"
                                          f"Цена: {coast}", reply_markup=markup)
    except Exception:
        bot.send_message(message.chat.id, "Я не понял (╯︵╰,)", reply_markup=markup)


@bot.message_handler(commands=['sum'])
def sum_current_month(message) -> None:
    year, month, days = get_date()

    db = sqlite3.connect("cost_accounting_base.db")
    sql = db.cursor()
    sql_result = sql.execute(f"""SELECT SUM(cost)
                        FROM cost_accounting
                        WHERE date BETWEEN datetime('{year}-{month}-01') AND datetime('{year}-{month}-{days}')""")

    text = sql_result.fetchone()

    if text[0] is None:
        text = "Покупок не было"
    else:
        text = str(round(text[0], 2))

    bot.send_message(message.chat.id, text, reply_markup=markup)
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
                        WHERE date BETWEEN datetime('{year}-{month}-01') AND datetime('{year}-{month}-{days}')""")

    text = sql_result.fetchone()

    if text[0] is None:
        text = "Покупок не было"
    else:
        text = str(round(text[0], 2))

    bot.send_message(message.chat.id, text, reply_markup=markup)
    db.close()


@bot.message_handler(commands=['avg'])
def average_month(message) -> None:
    year, month, days = get_date()

    db = sqlite3.connect("cost_accounting_base.db")
    sql = db.cursor()
    sql_result = sql.execute(f"""SELECT AVG(cost)
                        FROM cost_accounting
                        WHERE date BETWEEN datetime('{year}-{month}-01') AND datetime('{year}-{month}-{days}')""")

    text = sql_result.fetchone()

    if text[0] is None:
        text = "Покупок не было"
    else:
        text = str(round(text[0], 2))

    bot.send_message(message.chat.id, text, reply_markup=markup)
    db.close()


@bot.message_handler(commands=['avg_per_day'])
def average_month_per_day(message) -> None:
    year, month, days = get_date()

    db = sqlite3.connect("cost_accounting_base.db")
    sql = db.cursor()
    sql_result = sql.execute(f"""SELECT AVG(sum_cost.sum)
                                 FROM (SELECT SUM(cost) AS sum
                                     FROM cost_accounting
                                     GROUP BY strftime('%m-%d', date)) AS sum_cost""")

    text = sql_result.fetchone()

    if text[0] is None:
        text = "Покупок не было"
    else:
        text = str(round(text[0], 2))

    bot.send_message(message.chat.id, text, reply_markup=markup)
    db.close()


@bot.message_handler(commands=['all_in_month'])
def all_in_month(message) -> None:
    year, month, days = get_date()

    db = sqlite3.connect("cost_accounting_base.db")
    sql = db.cursor()
    sql_result = sql.execute(f"""SELECT *
                        FROM cost_accounting
                        WHERE date BETWEEN datetime('{year}-{month}-01') AND datetime('{year}-{month}-{days}')
                        ORDER BY date DESC""")

    result = ""
    for i in sql_result.fetchall():
        result += i[0] + " " + str(i[1]) + "\n"

    if result == "":
        text = "Покупок не было"
    else:
        text = result

    bot.send_message(message.chat.id, text, reply_markup=markup)
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
                        WHERE date BETWEEN datetime('{year}-{month}-01') AND datetime('{year}-{month}-{days}')
                        ORDER BY date DESC""")

    result = ""
    for i in sql_result.fetchall():
        result += i[0] + " " + str(i[1]) + "\n"

    if result == "":
        text = "Покупок не было"

    bot.send_message(message.chat.id, text, reply_markup=markup)
    db.close()


@bot.message_handler(content_types=["text"])
def db_save_from_text(message) -> None:
    if message.text.isdigit():
        year, month, days = get_date()
        time = datetime.now().strftime("%H:%M").split(":")
        day = datetime.now().strftime("%d")

        db = sqlite3.connect("cost_accounting_base.db")
        sql = db.cursor()
        sql.execute(f"""INSERT INTO cost_accounting
                        VALUES
                            (datetime('{year}-{month}-{day} {time[0]}:{time[1]}'), {message.text});""")
        db.commit()
        db.close()

        bot.send_message(message.chat.id, "Покупка сохранена:\n"
                                          f"Время: {year}-{month}-{day} {time[0]}:{time[1]}\n"
                                          f"Цена: {message.text}", reply_markup=markup)


if __name__ == "__main__":
    bot.polling(none_stop=True)
