import json
import os
from datetime import datetime

from dotenv import load_dotenv

from src.utils import (get_cashback, get_cbr_exchange_rates, get_common_cards_info, get_path_from_json, get_stocks,
                       get_top_transactions, greetings, open_excel)

load_dotenv()

path_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def page_home(date_and_time: object) -> str:
    """Функция, которая принимает на вход строку с датой и временем в формате
    YYYY-MM-DD HH:MM:SS и возвращающую JSON-ответ со следующими данными:

    1. Приветствие в формате "???", где ??? — «Доброе утро» / «Добрый день» / «Добрый вечер» / «Доброй ночи» в
    зависимости от текущего времени.
    2. По каждой карте:
        последние 4 цифры карты;
        общая сумма расходов;
        кешбэк (1 рубль на каждые 100 рублей).
    3. Топ-5 транзакций по сумме платежа.
    4. Курс валют.
    5. Стоимость акций из S&P500."""

    my_path_from_xlsx = os.path.join(path_base, "operations.xlsx")
    operations_excel = open_excel(my_path_from_xlsx)

    path_to_json = get_path_from_json("user_settings.json")

    result = {
        "greeting": greetings(date_and_time),
        "cards": get_cashback(get_common_cards_info(operations_excel)),
        "top_transactions": get_top_transactions(operations_excel),
        "currency_rates": get_cbr_exchange_rates(path_to_json),
        "stock_prices": get_stocks(path_to_json),
    }
    json_output = json.dumps(
        result, indent=4, ensure_ascii=False
    )  # indent=4 для красивого форматирования, ensure_ascii=False для поддержки кириллицы
    return json_output


if __name__ == "__main__":
    now = datetime.now()
    print(page_home(now))
