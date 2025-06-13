import json
import os
from datetime import datetime
from unittest import mock
from unittest.mock import mock_open, patch

import pandas as pd
import pytest
import requests

import src.utils as utils
from src.utils import get_cbr_exchange_rates, get_stocks, get_top_transactions

# --- Тесты для функции get_path_from_json ---


def test_get_path_from_json():
    """Тест проверяет, что функция возвращает путь к файлу user_settings.json."""
    expected_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "user_settings.json")
    assert utils.get_path_from_json("user_settings.json") == expected_path


# --- Тесты для функции greetings ---


def test_greetings_morning():
    """Тест проверяет приветствие утром."""
    dt = datetime(2024, 1, 1, 8, 0, 0)
    assert utils.greetings(dt) == "Доброе утро"


def test_greetings_afternoon():
    """Тест проверяет приветствие днем."""
    dt = datetime(2024, 1, 1, 14, 0, 0)
    assert utils.greetings(dt) == "Добрый день"


def test_greetings_evening():
    """Тест проверяет приветствие вечером."""
    dt = datetime(2024, 1, 1, 19, 0, 0)
    assert utils.greetings(dt) == "Добрый вечер"


def test_greetings_night():
    """Тест проверяет приветствие ночью."""
    dt = datetime(2024, 1, 1, 2, 0, 0)
    assert utils.greetings(dt) == "Доброй ночи"


# --- Тесты для функции open_excel ---


@patch("pandas.read_excel")
def test_open_excel_success(mock_read_excel):
    """Тест проверяет успешное открытие и чтение excel-файла."""
    mock_read_excel.return_value = pd.DataFrame([{"col1": 1, "col2": "a"}])
    result = utils.open_excel("dummy_path.xlsx")
    assert result == [{"col1": 1, "col2": "a"}]


@patch("pandas.read_excel", side_effect=FileNotFoundError)
def test_open_excel_file_not_found(mock_read_excel):
    """Тест проверяет обработку ошибки FileNotFoundError."""
    result = utils.open_excel("nonexistent_file.xlsx")
    assert result is None


@patch("pandas.read_excel", side_effect=pd.errors.EmptyDataError)
def test_open_excel_empty_file(mock_read_excel):
    """Тест проверяет обработку пустого файла."""
    result = utils.open_excel("empty_file.xlsx")
    assert result is None


@patch("pandas.read_excel", side_effect=pd.errors.ParserError)
def test_open_excel_parser_error(mock_read_excel):
    """Тест проверяет обработку ошибки ParserError."""
    result = utils.open_excel("invalid_file.xlsx")
    assert result is None


@patch("pandas.read_excel", side_effect=Exception("Generic Error"))
def test_open_excel_generic_error(mock_read_excel):
    """Тест проверяет обработку общей ошибки."""
    result = utils.open_excel("some_file.xlsx")
    assert result is None


# --- Тесты для функции round_and_abs ---


def test_round_and_abs_positive():
    """Тест проверяет округление и взятие модуля для положительного числа."""
    assert utils.round_and_abs(3.14159) == 3.14


def test_round_and_abs_negative():
    """Тест проверяет округление и взятие модуля для отрицательного числа."""
    assert utils.round_and_abs(-2.71828) == 2.72


def test_round_and_abs_zero():
    """Тест проверяет округление и взятие модуля для нуля."""
    assert utils.round_and_abs(0) == 0.0


# --- Тесты для функции get_common_cards_info ---


def test_get_common_cards_info_empty_list():
    """Тест проверяет обработку пустого списка транзакций."""
    assert utils.get_common_cards_info([]) == []


def test_get_common_cards_info_single_card():
    """Тест проверяет обработку списка с одной картой."""
    transactions = [{"Номер карты": "1234", "Сумма операции": -100.0}]
    expected_result = [{"last_digits": "1234", "total_spent": 100.0}]
    assert utils.get_common_cards_info(transactions) == expected_result


def test_get_common_cards_info_multiple_cards():
    """Тест проверяет обработку списка с несколькими картами."""
    transactions = [
        {"Номер карты": "1234", "Сумма операции": -100.0},
        {"Номер карты": "5678", "Сумма операции": -200.0},
        {"Номер карты": "1234", "Сумма операции": -50.0},
    ]
    expected_result = [
        {"last_digits": "1234", "total_spent": 150.0},
        {"last_digits": "5678", "total_spent": 200.0},
    ]
    assert utils.get_common_cards_info(transactions) == expected_result


def test_get_common_cards_info_missing_data():
    """Тест проверяет обработку транзакций с отсутствующими данными."""
    transactions = [
        {"Сумма операции": -100.0},
        {"Номер карты": "5678"},
    ]  # Отсутствует "Номер карты" и "Сумма операции"
    expected_result = [{"last_digits": "Unknown", "total_spent": 100.0}, {"last_digits": "5678", "total_spent": 0.0}]
    assert utils.get_common_cards_info(transactions) == expected_result


def test_get_common_cards_info_card_starts_with_asterisk():
    """Тест проверяет удаление звездочки в начале номера карты."""
    transactions = [{"Номер карты": "*1234", "Сумма операции": -100.0}]
    expected_result = [{"last_digits": "1234", "total_spent": 100.0}]
    assert utils.get_common_cards_info(transactions) == expected_result


def test_get_common_cards_info_invalid_data_types():
    """Тест проверяет обработку некорректных типов данных."""
    transactions = [{"Номер карты": 1234, "Сумма операции": "-100.0"}]
    expected_result = [{"last_digits": 1234, "total_spent": 0.0}]
    assert utils.get_common_cards_info(transactions) == expected_result


# --- Тесты для функции get_cashback ---


def test_get_cashback_empty_list():
    """Тест для пустого списка карт."""
    assert utils.get_cashback([]) == []


def test_get_cashback_single_card():
    """Тест для одной карты с суммой трат."""
    cards = [{"total_spent": 150.0}]
    expected = [{"total_spent": 150.0, "cashback": 1.5}]
    assert utils.get_cashback(cards) == expected


def test_get_cashback_multiple_cards():
    """Тест для нескольких карт с разными суммами трат."""
    cards = [{"total_spent": 100.0}, {"total_spent": 250.0}, {"total_spent": 0.0}]
    expected = [
        {"total_spent": 100.0, "cashback": 1.0},
        {"total_spent": 250.0, "cashback": 2.5},
        {"total_spent": 0.0, "cashback": 0.0},
    ]
    assert utils.get_cashback(cards) == expected


def test_get_cashback_missing_total_spent():
    """Тест для карты без поля 'total_spent'."""
    cards = [{"some_field": 100.0}]
    expected = [{"some_field": 100.0, "cashback": 0.0}]
    with patch("src.utils.logging.warning") as mock_warning:  # Проверка логирования warning
        assert utils.get_cashback(cards) == expected
        mock_warning.assert_called_once()


def test_get_cashback_invalid_total_spent_type():
    """Тест для карты с некорректным типом данных в 'total_spent'."""
    cards = [{"total_spent": "abc"}]
    expected = [{"total_spent": "abc", "cashback": 0.0}]
    with patch("src.utils.logging.error") as mock_error:  # Проверка логирования error
        assert utils.get_cashback(cards) == expected
        mock_error.assert_called_once()


def test_get_cashback_exception():
    """Тест для случая исключения при вычислении кэшбэка."""
    cards = [{"total_spent": float("inf")}]  # Вызовет ошибку при делении
    expected = [{"total_spent": float("inf"), "cashback": 0.0}]
    with patch("src.utils.logging.exception"):  # Проверка логирования exception
        assert utils.get_cashback(cards) == expected


def test_get_cashback_negative_total_spent():
    """Тест для карты с отрицательным значением 'total_spent'."""
    cards = [{"total_spent": -150.0}]
    expected = [{"total_spent": -150.0, "cashback": 1.5}]
    assert utils.get_cashback(cards) == expected


# --- Тесты для get_top_transactions ---


def test_get_top_transactions_empty_list():
    """Тест проверяет, что функция возвращает пустой список, если ей передан пустой список."""
    operations = []
    result = get_top_transactions(operations)
    assert result == [], "Функция должна возвращать пустой список для пустого входа"


def test_get_top_transactions_less_than_5():
    """Тест проверяет, что функция возвращает все транзакции, если их меньше 5."""
    operations = [
        {
            "Сумма операции с округлением": 100,
            "Дата платежа": "2023-10-26",
            "Сумма платежа": 100,
            "Категория": "A",
            "Описание": "Desc A",
        },
        {
            "Сумма операции с округлением": 50,
            "Дата платежа": "2023-10-27",
            "Сумма платежа": 50,
            "Категория": "B",
            "Описание": "Desc B",
        },
        {
            "Сумма операции с округлением": 25,
            "Дата платежа": "2023-10-28",
            "Сумма платежа": 25,
            "Категория": "C",
            "Описание": "Desc C",
        },
    ]
    expected_result = [
        {"date": "2023-10-26", "amount": 100, "category": "A", "description": "Desc A"},
        {"date": "2023-10-27", "amount": 50, "category": "B", "description": "Desc B"},
        {"date": "2023-10-28", "amount": 25, "category": "C", "description": "Desc C"},
    ]
    result = get_top_transactions(operations)
    assert result == expected_result, "Функция вернула неверный результат для списка < 5 элементов"


def test_get_top_transactions_more_than_5():
    """Тест проверяет, что функция возвращает топ-5 транзакций."""
    operations = [
        {
            "Сумма операции с округлением": 100,
            "Дата платежа": "2023-10-26",
            "Сумма платежа": 100,
            "Категория": "A",
            "Описание": "Desc A",
        },
        {
            "Сумма операции с округлением": 50,
            "Дата платежа": "2023-10-27",
            "Сумма платежа": 50,
            "Категория": "B",
            "Описание": "Desc B",
        },
        {
            "Сумма операции с округлением": 25,
            "Дата платежа": "2023-10-28",
            "Сумма платежа": 25,
            "Категория": "C",
            "Описание": "Desc C",
        },
        {
            "Сумма операции с округлением": 12.5,
            "Дата платежа": "2023-10-29",
            "Сумма платежа": 12.5,
            "Категория": "D",
            "Описание": "Desc D",
        },
        {
            "Сумма операции с округлением": 6.25,
            "Дата платежа": "2023-10-30",
            "Сумма платежа": 6.25,
            "Категория": "E",
            "Описание": "Desc E",
        },
        {
            "Сумма операции с округлением": 3.125,
            "Дата платежа": "2023-10-31",
            "Сумма платежа": 3.125,
            "Категория": "F",
            "Описание": "Desc F",
        },
    ]
    expected_result = [
        {"date": "2023-10-26", "amount": 100, "category": "A", "description": "Desc A"},
        {"date": "2023-10-27", "amount": 50, "category": "B", "description": "Desc B"},
        {"date": "2023-10-28", "amount": 25, "category": "C", "description": "Desc C"},
        {"date": "2023-10-29", "amount": 12.5, "category": "D", "description": "Desc D"},
        {"date": "2023-10-30", "amount": 6.25, "category": "E", "description": "Desc E"},
    ]
    result = get_top_transactions(operations)
    assert result == expected_result, "Функция вернула неверный топ-5"


def test_get_top_transactions_missing_fields():
    """Тест проверяет, что функция корректно обрабатывает отсутствующие поля в транзакциях."""
    operations = [
        {"Сумма операции с округлением": 100},  # Отсутствуют другие поля
        {"Сумма операции с округлением": 50, "Дата платежа": "2023-10-27"},  # Отсутствует часть полей
    ]
    expected_result = [
        {"date": "Unknown", "amount": 0.0, "category": "Unknown", "description": "Unknown"},
        {"date": "2023-10-27", "amount": 0.0, "category": "Unknown", "description": "Unknown"},
    ]
    result = get_top_transactions(operations)
    assert result == expected_result, "Функция неверно обработала отсутствующие поля"


# --- Тесты для get_stocks ---


@patch.dict(os.environ, {"MY_API_KEY_TWELVE": "test_api_key"})
@patch("src.utils.requests.get")
def test_get_stocks_success(mock_get):
    """Тест проверяет успешное получение цен акций."""
    # Фиктивные настройки пользователя
    user_settings = {"user_stocks": ["AAPL", "GOOG"]}
    # Мокируем открытие файла
    with patch("builtins.open", mock_open(read_data=json.dumps(user_settings))):
        # Мокируем ответ API
        mock_response_aapl = mock.MagicMock()
        mock_response_aapl.status_code = 200
        mock_response_aapl.json.return_value = {"price": "150.00"}

        mock_response_goog = mock.MagicMock()
        mock_response_goog.status_code = 200
        mock_response_goog.json.return_value = {"price": "2700.00"}

        mock_get.side_effect = [mock_response_aapl, mock_response_goog]

        result = get_stocks("dummy_path.json")
        expected_result = [{"stock": "AAPL", "price": "150.00"}, {"stock": "GOOG", "price": "2700.00"}]
        assert result == expected_result, "Функция не вернула корректные цены акций"


@patch.dict(os.environ, {"MY_API_KEY_TWELVE": "test_api_key"})
@patch("src.utils.requests.get")
def test_get_stocks_api_error(mock_get):
    """Тест проверяет обработку ошибки при запросе к API."""
    user_settings = {"user_stocks": ["AAPL"]}
    with patch("builtins.open", mock_open(read_data=json.dumps(user_settings))):
        mock_get.side_effect = Exception("API Error")

        result = get_stocks("dummy_path.json")
        assert result == [], "Функция не вернула пустой список при ошибке API"


@patch.dict(os.environ, {"MY_API_KEY_TWELVE": "test_api_key"})
@patch("src.utils.requests.get")
def test_get_stocks_json_error(mock_get):
    """Тест проверяет обработку случая, когда API возвращает некорректный JSON."""
    user_settings = {"user_stocks": ["AAPL"]}
    with patch("builtins.open", mock_open(read_data=json.dumps(user_settings))):
        mock_get.return_value.json.side_effect = json.JSONDecodeError("msg", "doc", 0)
        mock_get.return_value.raise_for_status.return_value = None
        result = get_stocks("dummy_path.json")
        assert result == [], "Функция не вернула пустой список при ошибке JSON"


@patch.dict(os.environ, {"MY_API_KEY_TWELVE": "test_api_key"})
@patch("src.utils.requests.get")
def test_get_stocks_missing_price(mock_get):
    """Тест проверяет, что функция корректно обрабатывает отсутствие цены в ответе API."""
    user_settings = {"user_stocks": ["AAPL"]}
    with patch("builtins.open", mock_open(read_data=json.dumps(user_settings))):
        mock_get.return_value.json.return_value = {}  # Ответ API без цены

        result = get_stocks("dummy_path.json")
        expected_result = [{"stock": "AAPL", "price": None}]  # Цена должна быть None
        assert result == expected_result, "Функция не обработала отсутствие цены"


def test_get_stocks_file_not_found():
    """Тест проверяет, что функция обрабатывает ошибку, если файл настроек не найден."""
    with pytest.raises(FileNotFoundError):
        get_stocks("non_existent_file.json")


@patch("src.utils.requests.get")
def test_get_stocks_no_api_key(mock_get):
    """Тест проверяет, что функция возвращает корректное значение при отсутствии API ключа."""
    user_settings = {"user_stocks": ["AAPL"]}
    with patch.dict(os.environ, {"MY_API_KEY_TWELVE": ""}):
        with patch("builtins.open", mock_open(read_data=json.dumps(user_settings))):
            result = get_stocks("dummy_path.json")
            expected_result = [{"stock": "AAPL", "price": None}]
            assert result == expected_result, "Функция должна возвращать None при отсутствии API ключа"


# --- Тесты для get_cbr_exchange_rates ---

# Пример успешного ответа от API с необходимыми отступами
MOCK_XML_RESPONSE = """<?xml version="1.0" encoding="windows-1251"?>
<ValCurs Date="01.01.2022" name="Foreign Currency Market">
    <Valute>
        <CharCode>USD</CharCode>
        <Value>75,50</Value>
        <Nominal>1</Nominal>
    </Valute>
    <Valute>
        <CharCode>EUR</CharCode>
        <Value>85,50</Value>
        <Nominal>1</Nominal>
    </Valute>
</ValCurs>
"""


def test_get_cbr_exchange_rates_success():
    """Тест успешного выполнения функции."""
    user_settings = {"user_currencies": ["USD", "EUR"]}

    with patch("builtins.open", mock_open(read_data=json.dumps(user_settings))), patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = MOCK_XML_RESPONSE.encode(
            "windows-1251"
        )  # Убедитесь, что используете правильную кодировку

        rates = get_cbr_exchange_rates("dummy_path.json")
        assert rates == {"USD": 75.5, "EUR": 85.5}


def test_file_not_found():
    """Тест, который проверяет вывод при отсутствии такого файла."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        rates = get_cbr_exchange_rates("dummy_path.json")
        assert rates == {}


def test_json_decode_error():
    """Тест, который проверяет вывод при несоответствии формата файла(json)."""
    with patch("builtins.open", mock_open(read_data="not a json")):
        rates = get_cbr_exchange_rates("dummy_path.json")
        assert rates == {}


def test_no_currencies():
    """Тест, который поверяет вывод при отсутствии входных валют."""
    user_settings = {"user_currencies": []}

    with patch("builtins.open", mock_open(read_data=json.dumps(user_settings))):
        rates = get_cbr_exchange_rates("dummy_path.json")
        assert rates == {}


def test_request_exception():
    """Тест, который проверяет вывод при возникновении исключения."""
    user_settings = {"user_currencies": ["USD"]}

    with patch("builtins.open", mock_open(read_data=json.dumps(user_settings))), patch(
        "requests.get", side_effect=requests.exceptions.RequestException
    ):
        rates = get_cbr_exchange_rates("dummy_path.json")
        assert rates == {}
