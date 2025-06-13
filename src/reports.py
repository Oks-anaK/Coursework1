import json
import logging
import os
from datetime import date
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta

path_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования только для ошибок
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("spending_category_errors.log"), logging.StreamHandler()],
)
logger = logging.getLogger("spending_category")


def spending_by_category(transactions: pd.DataFrame, category: str, date_str: Optional[str] = None) -> str:
    """
    Рассчитывает траты по указанной категории за последние 3 месяца от указанной даты.

    Args:
        transactions: DataFrame с транзакциями
        category: Категория для фильтрации
        date_str: Строка с датой в формате YYYY-MM-DD (опционально)

    Returns:
        JSON строка с результатами расчета
    """
    try:
        # Проверка правильности формата даты
        if date_str:
            try:
                input_date = pd.to_datetime(date_str, dayfirst=True).date()
            except ValueError as e:
                logger.error(f"Ошибка преобразования даты '{date_str}': {e}")
                raise ValueError("Неверный формат даты. Ожидается YYYY-MM-DD.")
        else:
            input_date = date.today()

        # Рассчитываем дату 3 месяца назад
        start_date = input_date - relativedelta(months=3)

        # Преобразуем даты транзакций и фильтруем транзакции
        try:
            # Фильтруем транзакции по дате и категории
            filtered_transactions = transactions[
                (
                    pd.to_datetime(transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S", dayfirst=True).dt.date
                    >= start_date
                )
                & (
                    pd.to_datetime(transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S", dayfirst=True).dt.date
                    <= input_date
                )
                & (transactions["Категория"] == category)
            ]
        except Exception as e:
            logger.error(f"Ошибка при фильтрации транзакций: {e}")
            raise

        # Рассчитываем итоговые значения
        try:
            total_spending = round(filtered_transactions["Сумма операции с округлением"].sum(), 2)
            transaction_count = len(filtered_transactions)
        except Exception as e:
            logger.error(f"Ошибка при расчете итоговых значений: {e}")
            raise

        # Формируем результат
        result = {
            "category": category,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": input_date.strftime("%Y-%m-%d"),
            "total_spending": total_spending,
            "transaction_count": transaction_count,
        }

        # Преобразуем в JSON
        return json.dumps(result, ensure_ascii=False, indent=4)

    except Exception as e:
        # Логируем непредвиденные ошибки
        logger.error(f"Непредвиденная ошибка при расчете трат по категории '{category}': {e}")
        raise

    # if __name__ == "__main__":
    #     my_path_from_xlsx = os.path.join(path_base, "operations.xlsx")
    # operations_excel = open_excel(my_path_from_xlsx)


#     df_operations_excel = pd.DataFrame(operations_excel)
#
#     spended_trans = spending_by_category(df_operations_excel, "Каршеринг", "2021-12-31")
#     print(spended_trans)
