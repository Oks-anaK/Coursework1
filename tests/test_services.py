import json
from unittest.mock import patch

import pytest

from src.services import search_by_description_or_category

# Определяем путь к фиктивному файлу Excel для тестов
TEST_EXCEL_PATH = "test_data.xlsx"


# Фиктивные данные, которые будут возвращаться open_excel
TEST_DATA = [
    {"Описание": "Покупка продуктов в магазине Ашан", "Категория": "Продукты"},
    {"Описание": "Оплата интернета Ростелеком", "Категория": "Интернет"},
    {"Описание": "Пополнение счета телефона", "Категория": "Связь"},
    {"Описание": "Покупка билетов в кино", "Категория": "Развлечения"},
    {"Описание": None, "Категория": "Транспорт"},  # Добавляем строку с None в описании
]


@pytest.fixture
def mock_open_excel():
    """Фикстура для мокирования функции open_excel."""
    with patch("src.services.open_excel") as mock:
        mock.return_value = TEST_DATA
        yield mock


def test_search_by_description_found(mock_open_excel):
    """Тест, проверяющий, что функция находит транзакции по описанию."""
    result = search_by_description_or_category("Ашан", TEST_EXCEL_PATH)
    expected = json.dumps([TEST_DATA[0]], ensure_ascii=False, indent=4)
    assert result == expected, "Функция не нашла транзакцию по описанию"


def test_search_by_category_found(mock_open_excel):
    """Тест, проверяющий, что функция находит транзакции по категории."""
    result = search_by_description_or_category("Интернет", TEST_EXCEL_PATH)
    expected = json.dumps([TEST_DATA[1]], ensure_ascii=False, indent=4)
    assert result == expected, "Функция не нашла транзакцию по категории"


def test_search_not_found(mock_open_excel):
    """Тест, проверяющий, что функция возвращает пустой список, если ничего не найдено."""
    result = search_by_description_or_category("Несуществующий запрос", TEST_EXCEL_PATH)
    expected = json.dumps([], ensure_ascii=False, indent=4)
    assert result == expected, "Функция вернула результат, когда ничего не должно было найти"


def test_search_empty_string(mock_open_excel):
    """Тест, проверяющий, что функция ищет все данные, если передана пустая строка"""
    result = search_by_description_or_category("", TEST_EXCEL_PATH)
    expected = json.dumps(TEST_DATA, ensure_ascii=False, indent=4)
    assert result == expected, "Функция вернула результат, когда ничего не должно было найти"


def test_search_with_none_description(mock_open_excel):
    """Тест, проверяющий, что функция корректно обрабатывает None в поле описания."""
    result = search_by_description_or_category("Транспорт", TEST_EXCEL_PATH)
    expected = json.dumps([TEST_DATA[4]], ensure_ascii=False, indent=4)  # Последняя запись с None в описании
    assert result == expected, "Функция не обработала None в описании"


def test_search_with_case_insensitive(mock_open_excel):
    """Тест, проверяющий, что поиск не чувствителен к регистру."""
    result = search_by_description_or_category("ашАн", TEST_EXCEL_PATH)
    expected = json.dumps([TEST_DATA[0]], ensure_ascii=False, indent=4)
    assert result == expected, "Поиск чувствителен к регистру"


def test_open_excel_error():
    """Тест, проверяющий обработку ошибки при открытии excel файла."""
    # Мокируем open_excel так, чтобы он возвращал None (имитируем ошибку чтения файла)
    with patch("src.utils.open_excel", return_value=None):
        result = search_by_description_or_category("test", "dummy_path")
        assert (
            "Ошибка: Не удалось загрузить данные из Excel файла." in result
        ), "Функция не вернула сообщение об ошибке при проблеме с чтением файла"
