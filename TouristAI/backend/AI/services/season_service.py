from datetime import datetime

def get_current_season():

    month = datetime.now().month

    if month in [3, 4, 5]:
        return "Summer"

    elif month in [6, 7, 8, 9]:
        return "Monsoon"

    elif month in [10, 11]:
        return "Post Monsoon"

    else:
        return "Winter"