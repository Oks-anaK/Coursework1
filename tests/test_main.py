from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from src.main import main_func


@pytest.fixture
def sample_dataframe():
    """Возвращает пример DataFrame."""
    data = {
        "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "amount": [100, 200, 150],
        "category": ["Food", "Travel", "Food"],
        "description": ["Grocery shopping", "Train ticket", "Restaurant"],
    }
    return pd.DataFrame(data)


def test_main_func(sample_dataframe):
    """Тестирует main_func, проверяя правильность вызовов и обработки результатов."""

    # Определяем тестовые значения
    now = datetime(2023, 1, 1)
    search_string = "Grocery"
    path_to_transactions = "dummy_path.xlsx"  # Неважно, если функция замокирована
    category = "Food"
    date_str = "2023-01-01"

    # Определяем фиктивные возвращаемые значения для замокированных функций
    mock_page_home_return = "Mocked page_home result"
    mock_search_return = pd.DataFrame({"description": ["Grocery shopping"]})
    mock_spending_return = 100.0

    # Используем patch для замены функций моками и отслеживания вызовов
    with patch("src.main.page_home", return_value=mock_page_home_return) as mock_page_home, patch(
        "src.main.search_by_description_or_category", return_value=mock_search_return
    ) as mock_search, patch("src.main.spending_by_category", return_value=mock_spending_return) as mock_spending:

        # Вызываем функцию main_func
        result_page_home, result_spending, result_search = main_func(
            now, search_string, path_to_transactions, sample_dataframe, category, date_str
        )

        # Проверяем, что функции были вызваны с правильными аргументами
        mock_page_home.assert_called_once_with(now)
        mock_search.assert_called_once_with(search_string, path_to_transactions)
        mock_spending.assert_called_once_with(sample_dataframe, category, date_str)

        # Проверяем, что main_func вернула правильные значения
        assert result_page_home == mock_page_home_return
        assert result_spending == mock_spending_return
        assert result_search is mock_search_return
