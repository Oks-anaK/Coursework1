import json
import os
from datetime import datetime
from unittest.mock import patch

import pytest
from dotenv import load_dotenv

# Импортируем тестируемую функцию (укажите правильный путь, если нужно)
from src.views import page_home  # Замените your_module

load_dotenv()

path_base = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)  # Путь к корню проекта (скорректировать, если нужно)


# Мокаем функции, чтобы тесты были изолированы
@pytest.fixture
def mock_functions():
    with (
        patch(
            "src.views.greetings", return_value="Доброе утро"
        ) as mock_greetings,  # Предполагаем, что в page_home вы обращаетесь к greetings просто по имени
        patch(
            "src.views.get_cashback", return_value=[{"card": "1234", "total_spent": 1000, "cashback": 10}]
        ) as mock_get_cashback,
        patch(
            "src.views.get_top_transactions", return_value=[{"amount": 100, "description": "Покупка 1"}]
        ) as mock_get_top_transactions,
        patch("src.views.get_cbr_exchange_rates", return_value={"USD": 75.0}) as mock_get_cbr_exchange_rates,
        patch("src.views.get_stocks", return_value={"AAPL": 150.0}) as mock_get_stocks,
        patch("src.views.open_excel") as mock_open_excel,
        patch("src.views.get_common_cards_info") as mock_get_common_cards_info,
        patch("src.views.get_path_from_json") as mock_get_path_from_json,
    ):
        yield (
            mock_greetings,
            mock_get_cashback,
            mock_get_top_transactions,
            mock_get_cbr_exchange_rates,
            mock_get_stocks,
            mock_open_excel,
            mock_get_common_cards_info,
            mock_get_path_from_json,
        )


def test_page_home_возвращает_json(mock_functions):
    """Проверяем, что функция page_home возвращает строку в формате JSON."""
    (
        mock_greetings,
        mock_get_cashback,
        mock_get_top_transactions,
        mock_get_cbr_exchange_rates,
        mock_get_stocks,
        mock_open_excel,
        mock_get_common_cards_info,
        mock_get_path_from_json,
    ) = mock_functions

    result = page_home(datetime.now())
    try:
        json.loads(result)
    except ValueError:
        pytest.fail("Результат не является JSON")


def test_page_home_содержит_правильные_ключи(mock_functions):
    """Проверяем, что JSON содержит ключи 'greeting', 'cards', 'top_transactions', 'currency_rates', 'stock_prices'."""
    (
        mock_greetings,
        mock_get_cashback,
        mock_get_top_transactions,
        mock_get_cbr_exchange_rates,
        mock_get_stocks,
        mock_open_excel,
        mock_get_common_cards_info,
        mock_get_path_from_json,
    ) = mock_functions

    result = page_home(datetime.now())
    data = json.loads(result)

    assert "greeting" in data
    assert "cards" in data
    assert "top_transactions" in data
    assert "currency_rates" in data
    assert "stock_prices" in data


def test_page_home_вызывает_функцию_greetings(mock_functions):
    """Проверяем, что функция page_home вызывает функцию greetings с переданной датой и временем."""
    (
        mock_greetings,
        mock_get_cashback,
        mock_get_top_transactions,
        mock_get_cbr_exchange_rates,
        mock_get_stocks,
        mock_open_excel,
        mock_get_common_cards_info,
        mock_get_path_from_json,
    ) = mock_functions

    now = datetime.now()
    page_home(now)
    mock_greetings.assert_called_once_with(now)


def test_page_home_вызывает_функции_данных(mock_functions):
    """Проверяем, что функция вызывает все функции для получения данных."""
    (
        mock_greetings,
        mock_get_cashback,
        mock_get_top_transactions,
        mock_get_cbr_exchange_rates,
        mock_get_stocks,
        mock_open_excel,
        mock_get_common_cards_info,
        mock_get_path_from_json,
    ) = mock_functions

    page_home(datetime.now())

    assert mock_get_cashback.called
    assert mock_get_top_transactions.called
    assert mock_get_cbr_exchange_rates.called
    assert mock_get_stocks.called
    assert mock_open_excel.called
    assert mock_get_common_cards_info.called
    assert mock_get_path_from_json.called


def test_page_home_корректно_передает_данные_в_json(mock_functions):
    """Проверяем, что в JSON передаются корректные данные, возвращаемые моками."""
    (
        mock_greetings,
        mock_get_cashback,
        mock_get_top_transactions,
        mock_get_cbr_exchange_rates,
        mock_get_stocks,
        mock_open_excel,
        mock_get_common_cards_info,
        mock_get_path_from_json,
    ) = mock_functions

    mock_greetings.return_value = "Тестовое приветствие"
    mock_get_cashback.return_value = [{"card": "5678", "total_spent": 2000, "cashback": 20}]
    mock_get_top_transactions.return_value = [{"amount": 200, "description": "Тестовая покупка"}]
    mock_get_cbr_exchange_rates.return_value = {"EUR": 85.0}
    mock_get_stocks.return_value = {"GOOG": 2500.0}

    result = page_home(datetime.now())
    data = json.loads(result)

    assert data["greeting"] == "Тестовое приветствие"
    assert data["cards"] == [{"card": "5678", "total_spent": 2000, "cashback": 20}]
    assert data["top_transactions"] == [{"amount": 200, "description": "Тестовая покупка"}]
    assert data["currency_rates"] == {"EUR": 85.0}
    assert data["stock_prices"] == {"GOOG": 2500.0}
