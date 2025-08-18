from datetime import datetime
from typing import Union

from dateutil.relativedelta import relativedelta


def get_billing_cycle(output: str = "string") -> Union[str, datetime]:
    current_month = datetime.now() - relativedelta(months=1)
    if output == "string":
        return current_month.strftime("%Y-%m")
    return current_month
