import holidays
from datetime import date

india_holidays = holidays.India()


def is_holiday(check_date=None):

    if check_date is None:
        check_date = date.today()

    return check_date in india_holidays