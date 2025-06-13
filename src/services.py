import json
import os
from typing import Union

from src.utils import open_excel

path_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def search_by_description_or_category(string_for_search: str, path_to_trans: str) -> Union[str, str]:
    """
    Функция, которая принимает строку для поиска и возвращает JSON-ответ со списком словарей,
    содержащих запрос в описании или категории. Если возникла ошибка, возвращает сообщение об ошибке.

    :param string_for_search: Строка для поиска.
    :param path_to_trans: Путь к Excel файлу с данными.
    :return: JSON строка с результатами или сообщение об ошибке.
    """
    try:
        list_of_trans = open_excel(path_to_trans)

        if list_of_trans is None:
            return "Ошибка: Не удалось загрузить данные из Excel файла."

        pattern = string_for_search.lower()
        matches = [
            dct
            for dct in list_of_trans
            if (dct.get("Описание") and isinstance(dct["Описание"], str) and pattern in dct["Описание"].lower())
            or (dct.get("Категория") and isinstance(dct["Категория"], str) and pattern in dct["Категория"].lower())
        ]

        return json.dumps(matches, ensure_ascii=False, indent=4)

    except Exception as e:
        return f"Возникла ошибка при поиске по транзакциям: {e}."


# if __name__ == '__main__':
#     my_path_from_xlsx = os.path.join(path_base, "operations.xlsx")
#     print(search_by_description_or_category("Красота", my_path_from_xlsx))
