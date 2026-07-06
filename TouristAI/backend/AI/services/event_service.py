from datetime import datetime


EVENTS = {

    "Goa": [
        ("Goa Carnival", 2, 15, 2, 20),
        ("Sunburn Festival", 12, 26, 12, 30)
    ],

    "Madurai": [
        ("Chithirai Festival", 4, 20, 5, 5)
    ],

    "Mysore": [
        ("Dasara", 10, 1, 10, 15)
    ]

}


def has_event(city):

    city = city.title()

    if city not in EVENTS:
        return False, ""

    today = datetime.now()

    for event in EVENTS[city]:

        name, sm, sd, em, ed = event

        start = datetime(today.year, sm, sd)

        end = datetime(today.year, em, ed)

        if start <= today <= end:
            return True, name

    return False, ""