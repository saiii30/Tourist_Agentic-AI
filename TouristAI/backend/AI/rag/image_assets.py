# backend/AI/rag/image_assets.py
RAG_IMAGE_URLS = {
    "Delhi": [
        "https://upload.wikimedia.org/wikipedia/commons/9/99/India_Gate_on_the_evening_of_77th_Independence_day.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/9/99/Red_Fort_in_Delhi_03-2016_img3.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/8/8d/Lotus_Temple_in_New_Delhi_03-2016.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/3/3c/Qutb_Minar_2022.jpg",
    ],
    "Rajasthan": [
        "https://upload.wikimedia.org/wikipedia/commons/0/09/Thar_Khuri.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/9/99/Mehrangarh_Fort_sanhita.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/5/5b/Hawa_Mahal_2011.jpg",
    ],
    "Uttar Pradesh": [
        "https://upload.wikimedia.org/wikipedia/commons/d/da/Taj-Mahal.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/e/e8/Varanasi_Ghats_-_Ganges.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/f/fc/Fatehpur_Sikri_Buland_Darwaza_2010.jpg",
    ],
    "Tamil Nadu": [
        "https://upload.wikimedia.org/wikipedia/commons/8/81/Brihadeeswarar_Temple_Tanjore_India.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/e/ea/Madurai_Meenakshi_Temple_West_Tower.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/a/a6/Nilgiri_Mountain_Railway_train%2C_India.jpg",
    ],
    "Madurai": [
        # Special:Redirect/file avoids brittle hash paths when Commons files move.
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/West_Tower_of_Madurai_Meenakshi_Temple.jpg?width=1000",
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/The_Court_Hall%2C_Thirumalai_Nayakkar_Mahal%2C_Madurai.jpg?width=1000",
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/Thirumalai_Nayakkar_Mahal%2C_Madurai.JPG?width=1000",
    ],
    "Meenakshi Amman Temple": [
        "https://upload.wikimedia.org/wikipedia/commons/e/ea/Madurai_Meenakshi_Temple_West_Tower.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/a/ae/Madurai_Meenakshi_Amman_Temple_Gopuram.jpg",
    ],
    "Thirumalai Nayakkar Palace": [
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/The_Court_Hall%2C_Thirumalai_Nayakkar_Mahal%2C_Madurai.jpg?width=1000",
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/Thirumalai_nayak_mahal.jpg?width=1000",
    ],
    "Kanniyakumari Tourist Spots": [
        "https://upload.wikimedia.org/wikipedia/commons/a/a4/Vivekananda_Rock_Memorial%2C_Kanyakumari.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/4/4e/Thiruvalluvar_Statue_at_Kanyakumari_beach.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/8/8d/Kanyakumari_sunrise.jpg",
    ],
    "Kanniyakumari": [
        "https://upload.wikimedia.org/wikipedia/commons/a/a4/Vivekananda_Rock_Memorial%2C_Kanyakumari.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/4/4e/Thiruvalluvar_Statue_at_Kanyakumari_beach.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/8/8d/Kanyakumari_sunrise.jpg",
    ],
    "Kanyakumari": [
        "https://upload.wikimedia.org/wikipedia/commons/a/a4/Vivekananda_Rock_Memorial%2C_Kanyakumari.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/4/4e/Thiruvalluvar_Statue_at_Kanyakumari_beach.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/8/8d/Kanyakumari_sunrise.jpg",
    ],
    "Ooty": [
        "https://upload.wikimedia.org/wikipedia/commons/a/a6/Nilgiri_Mountain_Railway_train%2C_India.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/9/91/Ooty_lake.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/3/3f/Ooty_Botanical_Gardens.jpg",
    ],
    "Ooty Lake and Boat House": [
        "https://upload.wikimedia.org/wikipedia/commons/9/91/Ooty_lake.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/a/a6/Nilgiri_Mountain_Railway_train%2C_India.jpg",
    ],
    "Kodaikanal": [
        "https://upload.wikimedia.org/wikipedia/commons/4/4f/Kodaikanal_lake.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/4/40/Kodaikanal_Coaker%27s_Walk.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/c/c4/Pillar_Rocks%2C_Kodaikanal.jpg",
    ],
}


def get_rag_image_urls(destination: str | None, city: str | None = None) -> list[str]:
    for key in [destination, city]:
        if key and key in RAG_IMAGE_URLS:
            return RAG_IMAGE_URLS[key]
    return []


def get_rag_image_url(destination: str | None, city: str | None = None) -> str | None:
    urls = get_rag_image_urls(destination, city)
    return urls[0] if urls else None
