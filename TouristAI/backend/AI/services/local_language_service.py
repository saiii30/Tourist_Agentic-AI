import os
from typing import Dict, List

import httpx


LANGUAGES = {
    "en": {"name": "English", "speech": "en-IN"},
    "ta": {"name": "Tamil", "speech": "ta-IN"},
    "hi": {"name": "Hindi", "speech": "hi-IN"},
    "te": {"name": "Telugu", "speech": "te-IN"},
    "ml": {"name": "Malayalam", "speech": "ml-IN"},
    "kn": {"name": "Kannada", "speech": "kn-IN"},
    "mr": {"name": "Marathi", "speech": "mr-IN"},
    "bn": {"name": "Bengali", "speech": "bn-IN"},
}

SCRIPT_RANGES = {
    "bn": (0x0980, 0x09FF), "hi": (0x0900, 0x097F), "mr": (0x0900, 0x097F),
    "ta": (0x0B80, 0x0BFF), "te": (0x0C00, 0x0C7F), "kn": (0x0C80, 0x0CFF),
    "ml": (0x0D00, 0x0D7F),
}


def detect_language(text: str) -> str:
    counts = {code: 0 for code in SCRIPT_RANGES}
    for character in text:
        point = ord(character)
        for code, (start, end) in SCRIPT_RANGES.items():
            if start <= point <= end:
                counts[code] += 1
    detected = max(counts, key=counts.get)
    return detected if counts[detected] else "en"


PHRASES: List[Dict[str, str]] = [
    {"id": "taxi-station", "category": "Taxi", "en": "Please take me to the railway station.", "ta": "தயவுசெய்து என்னை ரயில் நிலையத்திற்கு அழைத்துச் செல்லுங்கள்.", "hi": "कृपया मुझे रेलवे स्टेशन ले चलिए।"},
    {"id": "taxi-fare", "category": "Taxi", "en": "How much will the fare be?", "ta": "கட்டணம் எவ்வளவு ஆகும்?", "hi": "किराया कितना होगा?"},
    {"id": "food-veg", "category": "Restaurant", "en": "I would like vegetarian food.", "ta": "எனக்கு சைவ உணவு வேண்டும்.", "hi": "मुझे शाकाहारी खाना चाहिए।"},
    {"id": "food-allergy", "category": "Restaurant", "en": "I have a food allergy. Please check the ingredients.", "ta": "எனக்கு உணவு ஒவ்வாமை உள்ளது. தயவுசெய்து பொருட்களைச் சரிபார்க்கவும்.", "hi": "मुझे खाने से एलर्जी है। कृपया सामग्री जाँच लें।"},
    {"id": "hotel-checkin", "category": "Hotel", "en": "I have a reservation. I would like to check in.", "ta": "எனக்கு முன்பதிவு உள்ளது. நான் செக்-இன் செய்ய விரும்புகிறேன்.", "hi": "मेरी बुकिंग है। मैं चेक-इन करना चाहता/चाहती हूँ।"},
    {"id": "shopping-price", "category": "Shopping", "en": "How much does this cost?", "ta": "இது எவ்வளவு விலை?", "hi": "इसकी कीमत कितनी है?"},
    {"id": "emergency-hospital", "category": "Emergency", "en": "I need a hospital. Please call an ambulance.", "ta": "எனக்கு மருத்துவமனை தேவை. தயவுசெய்து ஆம்புலன்ஸை அழைக்கவும்.", "hi": "मुझे अस्पताल जाना है। कृपया एम्बुलेंस बुलाइए।"},
    {"id": "emergency-police", "category": "Emergency", "en": "Please call the police. The emergency number is 112.", "ta": "தயவுசெய்து காவல்துறையை அழைக்கவும். அவசர எண் 112.", "hi": "कृपया पुलिस को बुलाइए। आपातकालीन नंबर 112 है।"},
    {"id": "direction-help", "category": "Directions", "en": "Can you show me this place on the map?", "ta": "இந்த இடத்தை வரைபடத்தில் காட்ட முடியுமா?", "hi": "क्या आप मुझे यह जगह नक्शे पर दिखा सकते हैं?"},
]

# Curated travel intents. Stored translations above remain the verified offline subset;
# these additional phrases use the translation model on demand and are cached by the client.
TRAVEL_PHRASES = {
    "Taxi": ["Please take me to this address.", "Please use the meter.", "Please stop here.", "Is this taxi available?", "How long will the journey take?", "Can I pay by UPI?", "Please drive slowly.", "Please wait for five minutes."],
    "Bus/Train": ["Where is the bus stop?", "Where is the railway station?", "Which platform should I use?", "Does this bus go to the city centre?", "When is the next train?", "Is this seat reserved?", "Where can I buy a ticket?", "Please tell me when we arrive."],
    "Hotel": ["I have a reservation.", "I would like to check in.", "What time is check-out?", "Is breakfast included?", "Please give me the Wi-Fi password.", "Could I have another towel?", "Is hot water available?", "Please store my luggage."],
    "Restaurant": ["I would like vegetarian food.", "Please make it less spicy.", "Does this contain nuts?", "I have a food allergy.", "May I see the menu?", "Please bring drinking water.", "Could I have the bill?", "Is this dish available?"],
    "Directions": ["Where is this place?", "Please show it on the map.", "Is it within walking distance?", "Should I turn left or right?", "How far is it from here?", "Where is the nearest restroom?", "Is this the correct road?", "Can you help me find my hotel?"],
    "Shopping": ["How much does this cost?", "Do you have a smaller size?", "Do you have another colour?", "Can I pay by card?", "Can I pay by UPI?", "Please give me a receipt.", "Is the price fixed?", "Where is the nearest market?"],
    "Emergency": ["Please call emergency services.", "Please call the police.", "I am lost.", "My phone has been stolen.", "I need help immediately.", "Please contact my family.", "There is a fire.", "The emergency number is 112."],
    "Medical": ["I need a doctor.", "Please call an ambulance.", "Where is the nearest hospital?", "I have a food allergy.", "I need my medicine.", "I am feeling dizzy.", "I have severe pain.", "Please tell the doctor my name."],
}

_existing_ids = {phrase["id"] for phrase in PHRASES}
for _category, _texts in TRAVEL_PHRASES.items():
    for _index, _text in enumerate(_texts, 1):
        _phrase_id = f"{_category.lower().replace('/', '-').replace(' ', '-')}-{_index}"
        if _phrase_id not in _existing_ids:
            PHRASES.append({"id": _phrase_id, "category": _category, "en": _text})


def phrasebook(source_language: str = "en", target_language: str = "ta") -> List[Dict[str, str]]:
    source = source_language if source_language in LANGUAGES else "en"
    target = target_language if target_language in LANGUAGES else "ta"
    return [
        {
            "id": phrase["id"],
            "category": phrase["category"],
            "source_text": phrase.get(source, phrase["en"]),
            "translated_text": phrase.get(target, ""),
            "verified": source in phrase and target in phrase,
        }
        for phrase in PHRASES
    ]


def _offline_match(text: str, source: str, target: str) -> str:
    normalized = " ".join(text.strip().lower().split()).rstrip(".!?")
    for phrase in PHRASES:
        candidate = " ".join(phrase.get(source, phrase["en"]).lower().split()).rstrip(".!?")
        if normalized == candidate:
            return phrase.get(target, "")
    return ""


async def translate(text: str, source_language: str, target_language: str) -> Dict[str, object]:
    source = detect_language(text) if source_language == "auto" else (source_language if source_language in LANGUAGES else "en")
    target = target_language if target_language in LANGUAGES else "ta"
    if source == target:
        return {"translated_text": text, "transliteration": text, "detected_language": source, "provider": "identity", "is_live": False}

    offline = _offline_match(text, source, target)
    if offline:
        return {"translated_text": offline, "transliteration": offline, "detected_language": source, "provider": "verified_phrasebook", "is_live": False}

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return {
            "translated_text": "",
            "provider": "unavailable",
            "is_live": False,
            "warning": "Live translation is unavailable. Choose a phrase from the offline phrasebook.",
        }

    source_name = LANGUAGES[source]["name"]
    target_name = LANGUAGES[target]["name"]
    prompt = (
        f"Translate the following travel conversation from {source_name} to {target_name}. "
        "Return exactly two lines. Line 1 is the translation. Line 2 is a simple Latin-script "
        "pronunciation of the translation. Preserve names, addresses, phone numbers, prices, URLs, "
        "booking IDs, train numbers and flight numbers exactly. Do not add labels or explanations.\n\n"
        f"Text: {text}"
    )
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "openai/gpt-oss-20b",
                    "temperature": 0,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            translated = lines[0] if lines else ""
            transliteration = lines[1] if len(lines) > 1 else translated
            return {"translated_text": translated, "transliteration": transliteration, "detected_language": source, "provider": "groq", "is_live": True}
    except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
        return {
            "translated_text": "",
            "provider": "unavailable",
            "is_live": False,
            "warning": f"Translation could not be completed: {type(exc).__name__}. Try an offline phrase instead.",
        }
