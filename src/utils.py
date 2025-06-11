import json
import logging
import math
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from pprint import pprint
from typing import Dict, List, Union

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

# Константы
DECIMAL_PLACES = 2

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

path_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_path_from_json(user_place_settings_json):
    """Пользовательская функция, которая получает путь к файлу json."""
    try:
        path_from_json = os.path.join(path_base, user_place_settings_json)
        return path_from_json
    except Exception as e:
        logging.error(f"Ошибка при получении пути к файлу json: {e}")
        return None


def greetings(date_time: datetime):
    """Выбирает приветствие в зависимости от времени дня."""
    if 5 <= date_time.hour < 12:
        return "Доброе утро"
    if 12 <= date_time.hour < 17:
        return "Добрый день"
    if 17 <= date_time.hour < 21:
        return "Добрый вечер"
    return "Доброй ночи"


def open_excel(path_from_xlsx: str) -> Union[List[Dict], None]:
    """Открывает excel-файл и считывает из него информацию."""
    try:
        df = pd.read_excel(path_from_xlsx)
        logging.info(f"Файл Excel успешно открыт: {path_from_xlsx}")
        return df.replace({float("nan"): None}).to_dict(orient="records")  # Замена NaN перед преобразованием
    except FileNotFoundError:
        logging.error(f"Ошибка: Файл не найден: {path_from_xlsx}")
        return None
    except pd.errors.EmptyDataError:
        logging.warning(f"Предупреждение: Файл {path_from_xlsx} пуст.")
        return None
    except pd.errors.ParserError:
        logging.error(f"Ошибка: Не удалось прочитать файл {path_from_xlsx}. Возможно, неверный формат.")
        return None
    except Exception as e:
        logging.exception(f"Ошибка: При открытии файла xlsx возникла ошибка: {e}")
        return None


def round_and_abs(value: float) -> float:
    """Округляет до двух знаков после запятой и берет модуль."""
    return math.fabs(round(value, DECIMAL_PLACES))


def get_common_cards_info(transactions_list: list[dict]) -> list[dict]:
    """Предоставляет общую информацию о картах."""
    cards = {}
    for transaction in transactions_list:
        try:
            last_digits = transaction.get("Номер карты", "Unknown")  # Безопасное получение
            total_spent = transaction.get("Сумма операции", 0.0)  # Безопасное получение

            if last_digits not in cards:
                cards[last_digits] = {"last_digits": last_digits, "total_spent": 0.0}
            cards[last_digits]["total_spent"] += total_spent
        except Exception as e:
            logging.error(f"Ошибка при обработке транзакции: {transaction}. Ошибка: {e}")
            # Можно решить продолжить обработку остальных транзакций или прервать.
            continue  # Продолжаем обработку остальных транзакций.
            # Если бы мы решили прервать, то делали бы raise

    result_list = []
    for card_data in cards.values():
        try:
            card_data["total_spent"] = math.fabs(round(card_data["total_spent"], 2))

            if isinstance(card_data["last_digits"], str) and card_data["last_digits"].startswith("*"):
                card_data["last_digits"] = card_data["last_digits"][1:]

            result_list.append(card_data)
        except Exception as e:
            logging.error(f"Ошибка при обработке card_data: {card_data}. Ошибка: {e}")
            continue  # Продолжаем обработку, если возможно

    return result_list


def get_cashback(unic_cards: List[Dict]) -> List[Dict]:
    """Вычисляет кэшбэк для каждой карты."""
    for card in unic_cards:
        try:
            total_spent = card.get("total_spent")
            if total_spent is None:
                logging.warning(f"Предупреждение: 'total_spent' отсутствует для карты: {card}")
                card["cashback"] = 0.0
                continue  # Перейти к следующей карте

            if math.isinf(total_spent):  # Добавлена проверка на бесконечность
                card["cashback"] = 0.0
            else:
                card["cashback"] = math.fabs(round(total_spent / 100, 2))
        except TypeError as e:
            logging.error(f"Ошибка: Неверный тип данных для 'total_spent' в карте: {card}. Ошибка: {e}")
            card["cashback"] = 0.0
        except Exception as e:
            logging.exception(f"Ошибка при вычислении кэшбэка для карты: {card}. Ошибка: {e}")
            card["cashback"] = 0.0
    return unic_cards


def get_cbr_exchange_rates(file_path: str) -> dict:
    """
    Получает курсы валют к рублю с использованием API ЦБ РФ.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            user_settings = json.load(f)
            currencies = user_settings.get("user_currencies")
            url = "http://www.cbr.ru/scripts/XML_daily.asp"

        if not url:
            logging.warning("URL отсутствует, запрос к ЦБ не выполняется.")
            return {}

        if not currencies:
            logging.warning("Список валют пуст, запрос к ЦБ не выполняется.")
            return {}

        response = requests.get(url)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        rates = {}
        for valute in root.findall("Valute"):
            char_code = valute.find("CharCode").text
            if char_code in currencies:
                value = float(valute.find("Value").text.replace(",", "."))
                nominal = int(valute.find("Nominal").text)
                rates[char_code] = round(value / nominal, DECIMAL_PLACES)

        return rates

    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при запросе данных: {e}")
        return {}
    except ET.ParseError as e:
        logging.error(f"Ошибка при парсинге XML: {e}")
        return {}
    except FileNotFoundError:
        logging.error(f"Файл не найден: {file_path}")
        return {}
    except Exception as e:
        logging.exception(f"Произошла непредвиденная ошибка: {e}")
        return {}


def get_top_transactions(operations):
    """Получает топ-5 транзакций."""
    sorted_operations = sorted(
        operations, key=lambda operation: operation["Сумма операции с округлением"], reverse=True
    )
    top_5 = sorted_operations[:5]
    top_5_edited = []
    for dct_transaction in top_5:
        date = dct_transaction.get("Дата платежа", "Unknown")
        amount = dct_transaction.get("Сумма платежа", 0.0)
        category_trans = dct_transaction.get("Категория", "Unknown")
        description = dct_transaction.get("Описание", "Unknown")
        top_5_edited.append({"date": date, "amount": amount, "category": category_trans, "description": description})

    return top_5_edited


def get_stocks(file_path: str) -> list:
    """Функция считывает JSON-файл и получает актуальные цены акций со
    стороннего сервиса."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            user_settings = json.load(f)
        stocks = user_settings.get("user_stocks")
        result = []

        for stock in stocks:
            api_twelve = os.getenv("MY_API_KEY_TWELVE")
            if not api_twelve:
                result.append({"stock": stock, "price": None})
                continue

            try:
                response = requests.get(f"https://api.twelvedata.com/price?symbol={stock}&apikey={api_twelve}")
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                data = response.json()
                price = data.get("price")
                result.append({"stock": stock, "price": price})
            except requests.exceptions.RequestException as e:
                logging.error(f"Ошибка при получении цены для {stock}: {e}")
                result.append({"stock": stock, "price": None})  # Append None on API error

        return result
    except FileNotFoundError:
        logging.error(f"Файл не найден: {file_path}")
        raise  # Re-raise FileNotFoundError
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка при чтении JSON: {e}")
        return []
    except Exception as e:
        logging.error(f"Ошибка при получении цен акций: {e}")
        return []


if __name__ == "__main__":
    #     now = datetime.now()
    #     print(greetings(now))
    #     my_path_from_xlsx = os.path.join(path_base, "operations.xlsx")
    #     operations_excel = open_excel(my_path_from_xlsx)
    #     pprint(operations_excel)
    # unic_cards = get_common_cards_info(operations_excel)
    # pprint(unic_cards)
    # pprint(get_cashback(unic_cards))
    my_place_settings_json = "user_settings.json"
    path_json = get_path_from_json(my_place_settings_json)
    # print(get_stocks(path_json))
    # print(get_currencies(path_json))
    # pprint(get_top_transactions(operations_excel))
    # exchange_rates = get_cbr_exchange_rates(path_json)
    # print(exchange_rates)
