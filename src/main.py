import os
from datetime import datetime
from typing import Optional

import pandas as pd

from src.reports import spending_by_category
from src.services import search_by_description_or_category
from src.utils import open_excel
from src.views import page_home

path_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main_func(
    date_and_time: object,
    string_for_search: str,
    path_to_trans: str,
    transactions: pd.DataFrame,
    category: str,
    date_str: Optional[str] = None,
):
    result_page_home = page_home(date_and_time)
    result_search_by_description_or_category = search_by_description_or_category(string_for_search, path_to_trans)
    result_spending_by_category = spending_by_category(transactions, category, date_str)
    return result_page_home, result_spending_by_category, result_search_by_description_or_category


if __name__ == "__main__":
    my_path_from_xlsx = os.path.join(path_base, "operations.xlsx")
    operations_excel = open_excel(my_path_from_xlsx)
    df_operations_excel = pd.DataFrame(operations_excel)

    now = datetime.now()

    print(main_func(now, "Красота", my_path_from_xlsx, df_operations_excel, "Каршеринг", "2021-12-31"))
