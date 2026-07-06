import re

from utils.query_parser import (
    resolve_destination,
    extract_intent,
)


BUDGET = {

    "budget": "Budget",
    "cheap": "Budget",
    "low budget": "Budget",

    "moderate": "Moderate",
    "medium": "Moderate",

    "luxury": "Luxury",
    "premium": "Luxury",

}


TRIP_TYPES = {

    "honeymoon": "Couple",
    "couple": "Couple",

    "family": "Family",
    "kids": "Family",
    "children": "Family",

    "solo": "Solo",

    "friends": "Friends",

    "business": "Business"

}


CATEGORIES = {

    "waterfall": "Waterfall",
    "falls": "Waterfall",

    "temple": "Temple",

    "beach": "Beach",

    "lake": "Lake",

    "hill station": "Hill Station",

    "trek": "Adventure",

    "adventure": "Adventure",

    "museum": "Museum",

    "park": "Park",

    "shopping": "Shopping",

    "food": "Food",

}


DISCOVER_KEYWORDS = {

    "discover",

    "places",

    "visit",

    "tourist",

    "explore",

    "things to do",

    "hidden",

    "waterfall",

    "temple",

    "near",

    "around"

}


def extract_days(question):

    m = re.search(r"(\d+)\s*(day|days|night|nights)", question.lower())

    if m:

        return int(m.group(1))

    return None


def extract_budget(question):

    q = question.lower()

    for k, v in BUDGET.items():

        if k in q:

            return v

    return None


def extract_trip_type(question):

    q = question.lower()

    for k, v in TRIP_TYPES.items():

        if k in q:

            return v

    return None


def extract_category(question):

    q = question.lower()

    for k, v in CATEGORIES.items():

        if k in q:

            return v

    return None


def parse_query(question):

    destination = resolve_destination(question)

    intent = extract_intent(question)

    return {

        "question": question,

        "destination":

            destination["name"]

            if destination else None,

        "destination_id":

            destination["id"]

            if destination else None,

        "matched_as":

            destination["match"]

            if destination else None,

        "days":

            extract_days(question),

        "budget":

            extract_budget(question),

        "trip_type":

            extract_trip_type(question),

        "category":

            extract_category(question),

        "intent":

            intent["intent"],

        "discover":

            any(

                k in question.lower()

                for k in DISCOVER_KEYWORDS

            ),

        "weather":

            "weather" in question.lower(),

        "hotel":

            "hotel" in question.lower()
            or "stay" in question.lower(),

        "food":

            "food" in question.lower()
            or "restaurant" in question.lower(),

        "calendar":

            "calendar" in question.lower()
            or "schedule" in question.lower(),

        "nearby":

            "near" in question.lower()
            or "around" in question.lower(),

    }