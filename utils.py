from datetime import datetime
from calendar import monthrange


def get_date():
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%m")
    days = monthrange(int(year), int(month))[1]
    return [year, month, days]


def convert_date(date: str) -> list:
    str_result = []
    date = date.split(" ")
    date[5] = str(int(date[5]) + 1)
    for i in date:
        if len(i) == 1:
            str_result.append("0" + i)
        else:
            str_result.append(i)
    if type(date_validator(str_result)) == bool:
        return str_result
    else:
        return date_validator(str_result)


def date_validator(date: list) -> bool:
    year1 = int(date[0])
    month1 = int(date[1])
    day1 = int(date[2])
    year2 = int(date[3])
    month2 = int(date[4])
    day2 = int(date[5])

    error_dict = {1: "Ошибка 1 года",
                  2: "Ошибка 2 года",
                  3: "Ошибка 1 месяца",
                  4: "Ошибка 2 месяца",
                  5: "Ошибка 1 дня",
                  6: "Ошибка 2 дня"}

    error = 1

    if 2020 < year1 < 2500:
        error += 1
    else:
        return error_dict[error]

    if 2020 < year2 < 2500:
        error += 1
    else:
        return error_dict[error]

    if 0 < month1 < 13:
        error += 1
    else:
        return error_dict[error]

    if 0 < month2 < 13:
        error += 1
    else:
        return error_dict[error]

    if day1 <= monthrange(int(year1), int(month1))[1]:
        error += 1
    else:
        return error_dict[error]

    if day2 <= monthrange(int(year2), int(month2))[1]:
        error += 1
    else:
        return error_dict[error]

    return True


def fetchone_sql(sql_request) -> str:
    text = sql_request

    if text[0] is None:
        text = "Покупок не было"
    else:
        text = str(round(text[0], 2))
    return text


def fetchall_sql(sql_request) -> str:
    result = ""
    for i in sql_request:
        result += i[1] + " " + str(i[2]) + "\n"

    if result == "":
        text = "Покупок не было"
    else:
        text = result
    return text