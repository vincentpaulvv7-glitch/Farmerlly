"""Extensible crop names, variety choices, and growth-stage labels."""

from farmerlly.i18n import translate


CROPS = {
    "rice": {
        "name": {"English": "Rice", "தமிழ்": "நெல்"},
        "varieties": ["ADT 43", "ADT 56", "CO 59", "BPT 5204", "IR 64"],
        "variety_source": "https://agritech.tnau.ac.in/agriculture/agri_cropproduction_cereals_rice_season.html",
        "stages": [
            ("nursery", "Nursery / seedling", "நாற்று வளர்ப்பு"),
            ("transplanting", "Transplanting", "நடவு"),
            ("tillering", "Tillering", "தூர் உருவாகுதல்"),
            ("panicle", "Panicle initiation", "கதிர் உருவாகுதல்"),
            ("flowering", "Flowering", "பூக்கும் நிலை"),
            ("grain_fill", "Grain filling", "மணி நிரம்புதல்"),
            ("maturity", "Maturity", "முதிர்ச்சி"),
            ("harvested", "Harvested", "அறுவடை முடிந்தது"),
        ],
    },
    "tomato": {
        "name": {"English": "Tomato", "தமிழ்": "தக்காளி"},
        "varieties": ["PKM 1", "CO 3 (Marutham)", "COTH 2", "TNAU Tomato Hybrid CO 3", "TNAU Tomato Hybrid CO 4"],
        "variety_source": "https://agritech.tnau.ac.in/horticulture/agri_seasonandvarieties_tomato.html",
        "stages": [
            ("nursery", "Nursery / seedling", "நாற்று வளர்ப்பு"),
            ("transplanting", "Transplanting", "நடவு"),
            ("vegetative", "Vegetative growth", "இலை மற்றும் தண்டு வளர்ச்சி"),
            ("flowering", "Flowering", "பூக்கும் நிலை"),
            ("fruit_set", "Fruit development", "காய் வளர்ச்சி"),
            ("harvested", "Harvesting", "அறுவடை"),
        ],
    },
    "banana": {
        "name": {"English": "Banana", "தமிழ்": "வாழை"},
        "varieties": ["Robusta", "Dwarf Cavendish", "Grand Naine", "Rasthali", "Poovan", "Nendran", "Red Banana", "Karpooravalli"],
        "variety_source": "https://agritech.tnau.ac.in/horticulture/horti_fruits_banana.html",
        "stages": [
            ("establishment", "Establishment", "நிலைநிறுத்தம்"),
            ("vegetative", "Vegetative growth", "இலை மற்றும் தண்டு வளர்ச்சி"),
            ("flowering", "Flowering", "பூக்கும் நிலை"),
            ("bunch", "Bunch development", "குலை வளர்ச்சி"),
            ("maturity", "Maturity", "முதிர்ச்சி"),
            ("harvested", "Harvested", "அறுவடை முடிந்தது"),
        ],
    },
    "maize": {"name": {"English": "Maize", "தமிழ்": "மக்காச்சோளம்"}, "varieties": [], "variety_source": None},
    "wheat": {"name": {"English": "Wheat", "தமிழ்": "கோதுமை"}, "varieties": [], "variety_source": None},
    "cotton": {"name": {"English": "Cotton", "தமிழ்": "பருத்தி"}, "varieties": [], "variety_source": None},
    "sugarcane": {"name": {"English": "Sugarcane", "தமிழ்": "கரும்பு"}, "varieties": [], "variety_source": None},
    "groundnut": {"name": {"English": "Groundnut", "தமிழ்": "நிலக்கடலை"}, "varieties": [], "variety_source": None},
    "millet": {"name": {"English": "Millet", "தமிழ்": "சிறுதானியம்"}, "varieties": [], "variety_source": None},
    "pulses": {"name": {"English": "Pulses", "தமிழ்": "பயறு வகைகள்"}, "varieties": [], "variety_source": None},
    "other": {"name": {"English": "Other crop", "தமிழ்": "மற்ற பயிர்"}, "varieties": [], "variety_source": None},
}


GENERAL_STAGES = [
    ("sowing", "Sowing / planting", "விதைத்தல் / நடவு"),
    ("establishment", "Germination / establishment", "முளைப்பு / நிலைநிறுத்தம்"),
    ("vegetative", "Vegetative growth", "இலை மற்றும் தண்டு வளர்ச்சி"),
    ("flowering", "Flowering", "பூக்கும் நிலை"),
    ("development", "Fruit / grain development", "காய் / மணி வளர்ச்சி"),
    ("maturity", "Maturity", "முதிர்ச்சி"),
    ("harvested", "Harvested", "அறுவடை முடிந்தது"),
]


def crop_label(crop_code: str, language: str) -> str:
    """Get a crop name in the selected UI language."""
    crop = CROPS.get(crop_code, CROPS["other"])
    return translate(crop["name"]["English"], language)


def growth_stages(crop_code: str) -> list[tuple[str, str, str]]:
    """Return crop-specific stages, or a simple general stage list."""
    return CROPS.get(crop_code, {}).get("stages", GENERAL_STAGES)
