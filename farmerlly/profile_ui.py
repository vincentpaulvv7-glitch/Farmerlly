"""Registration form and editor for the local farmer profile."""

import streamlit as st

from farmerlly.database import save_farmer_profile
from farmerlly.i18n import LANGUAGES, translate_mapping


COPY = {
    "English": {
        "new_title": "Register your farm",
        "edit_title": "Your farmer and farm profile",
        "intro": "Add your details once. You can return here and update them whenever they change.",
        "name": "Farmer name",
        "language": "Preferred language",
        "state": "State",
        "district": "District",
        "village": "Village or city",
        "size": "Farm size (acres)",
        "size_help": "Enter the total area of your farm in acres.",
        "soil": "Soil type",
        "other_soil": "Enter your soil type",
        "water": "Available water sources",
        "other_water": "Describe another water source",
        "crops": "Crops you grow",
        "crops_help": "Enter one or more crop names, separated by commas. Example: Rice, Tomato, Cotton.",
        "save": "Save farm profile",
        "saved": "Your farm profile has been saved.",
        "storage": "Your profile is saved on this device in a local SQLite database.",
        "fix": "Please correct the following before saving:",
        "name_error": "Enter a name with at least 2 characters.",
        "name_long": "Keep the name under 101 characters.",
        "state_error": "Enter your state.",
        "district_error": "Enter your district.",
        "village_error": "Enter your village or city.",
        "location_long": "Keep each location field under 101 characters.",
        "size_error": "Farm size must be greater than zero acres.",
        "soil_error": "Choose your soil type.",
        "other_soil_error": "Enter the soil type in the field provided.",
        "water_error": "Choose at least one available water source.",
        "other_water_error": "Describe the other water source you selected.",
        "crops_error": "Enter at least one crop name.",
        "crop_count_error": "Enter no more than 30 crop names.",
        "crop_long": "Keep each crop name under 61 characters.",
        "soil_options": ["Loamy", "Clay", "Sandy", "Silty", "Black soil", "Red soil", "Other"],
        "water_options": ["Borewell", "Open well", "Canal", "River", "Pond or lake", "Rainwater harvesting", "Other"],
    },
    "தமிழ்": {
        "new_title": "உங்கள் பண்ணையைப் பதிவு செய்யவும்",
        "edit_title": "உங்கள் விவசாயி மற்றும் பண்ணை விவரங்கள்",
        "intro": "உங்கள் விவரங்களை ஒருமுறை சேர்க்கவும். பின்னர் இங்கே வந்து அவற்றைத் திருத்தலாம்.",
        "name": "விவசாயியின் பெயர்",
        "language": "விருப்ப மொழி",
        "state": "மாநிலம்",
        "district": "மாவட்டம்",
        "village": "கிராமம் அல்லது நகரம்",
        "size": "பண்ணை பரப்பளவு (ஏக்கர்)",
        "size_help": "உங்கள் பண்ணையின் மொத்த பரப்பளவை ஏக்கரில் உள்ளிடவும்.",
        "soil": "மண் வகை",
        "other_soil": "மண் வகையை உள்ளிடவும்",
        "water": "கிடைக்கும் நீர் ஆதாரங்கள்",
        "other_water": "மற்ற நீர் ஆதாரத்தை விவரிக்கவும்",
        "crops": "நீங்கள் விளைவிக்கும் பயிர்கள்",
        "crops_help": "ஒன்று அல்லது அதற்கு மேற்பட்ட பயிர் பெயர்களை காற்புள்ளியால் பிரித்து எழுதவும். எடுத்துக்காட்டு: நெல், தக்காளி, பருத்தி.",
        "save": "பண்ணை விவரங்களைச் சேமிக்கவும்",
        "saved": "உங்கள் பண்ணை விவரங்கள் சேமிக்கப்பட்டன.",
        "storage": "உங்கள் விவரங்கள் இந்தச் சாதனத்தில் உள்ள SQLite தரவுத்தளத்தில் சேமிக்கப்படும்.",
        "fix": "சேமிப்பதற்கு முன் பின்வருவனவற்றைத் திருத்தவும்:",
        "name_error": "குறைந்தது 2 எழுத்துகளுடன் பெயரை உள்ளிடவும்.",
        "name_long": "பெயர் 100 எழுத்துகளுக்குள் இருக்க வேண்டும்.",
        "state_error": "மாநிலத்தை உள்ளிடவும்.",
        "district_error": "மாவட்டத்தை உள்ளிடவும்.",
        "village_error": "கிராமம் அல்லது நகரத்தை உள்ளிடவும்.",
        "location_long": "ஒவ்வொரு இட விவரமும் 100 எழுத்துகளுக்குள் இருக்க வேண்டும்.",
        "size_error": "பண்ணை பரப்பளவு பூஜ்ஜியத்தை விட அதிகமாக இருக்க வேண்டும்.",
        "soil_error": "மண் வகையைத் தேர்ந்தெடுக்கவும்.",
        "other_soil_error": "கொடுக்கப்பட்ட பெட்டியில் மண் வகையை உள்ளிடவும்.",
        "water_error": "குறைந்தது ஒரு நீர் ஆதாரத்தைத் தேர்ந்தெடுக்கவும்.",
        "other_water_error": "தேர்ந்தெடுத்த மற்ற நீர் ஆதாரத்தை விவரிக்கவும்.",
        "crops_error": "குறைந்தது ஒரு பயிர் பெயரையாவது உள்ளிடவும்.",
        "crop_count_error": "30 பயிர் பெயர்களுக்கு மேல் உள்ளிட வேண்டாம்.",
        "crop_long": "ஒவ்வொரு பயிர் பெயரும் 60 எழுத்துகளுக்குள் இருக்க வேண்டும்.",
        "soil_options": ["மணல் கலந்த மண்", "களிமண்", "மணல் மண்", "படிவு மண்", "கரிசல் மண்", "செம்மண்", "மற்றவை"],
        "water_options": ["ஆழ்துளைக் கிணறு", "திறந்தவெளிக் கிணறு", "கால்வாய்", "நதி", "குளம் அல்லது ஏரி", "மழைநீர் சேமிப்பு", "மற்றவை"],
    },
}


SOIL_KEYS = ["Loamy", "Clay", "Sandy", "Silty", "Black soil", "Red soil", "Other"]
WATER_KEYS = ["Borewell", "Open well", "Canal", "River", "Pond or lake", "Rainwater harvesting", "Other"]
SOIL_DISPLAY = dict(zip(SOIL_KEYS, COPY["தமிழ்"]["soil_options"]))
WATER_DISPLAY = dict(zip(WATER_KEYS, COPY["தமிழ்"]["water_options"]))


def render_profile_page(language: str, profile: dict | None) -> None:
    """Show the registration form or the same form prefilled for editing."""
    words = COPY.get(language) or translate_mapping(COPY["English"], language)
    st.subheader(words["edit_title"] if profile else words["new_title"])
    st.caption(words["intro"])

    if st.session_state.pop("profile_saved", False):
        st.success(words["saved"])

    saved_soil = profile["soil_type"] if profile else "Loamy"
    soil_choice = saved_soil if saved_soil in SOIL_KEYS else "Other"
    saved_water = profile["water_sources"] if profile else []
    known_water = [item for item in WATER_KEYS if item in saved_water]
    other_water_saved = next(
        (item.removeprefix("Other: ") for item in saved_water if item.startswith("Other: ")),
        "",
    )
    if other_water_saved and "Other" not in known_water:
        known_water.append("Other")

    with st.form("farmer_profile_form"):
        name = st.text_input(words["name"], value=profile["farmer_name"] if profile else "", max_chars=100)
        preferred_language = st.selectbox(
            words["language"], LANGUAGES,
            index=LANGUAGES.index(profile["preferred_language"])
            if profile and profile["preferred_language"] in LANGUAGES else 0,
        )
        state_col, district_col = st.columns(2)
        with state_col:
            state = st.text_input(words["state"], value=profile["state"] if profile else "", max_chars=100)
        with district_col:
            district = st.text_input(words["district"], value=profile["district"] if profile else "", max_chars=100)
        village = st.text_input(words["village"], value=profile["village_or_city"] if profile else "", max_chars=100)
        farm_size = st.number_input(
            words["size"], min_value=0.0, value=float(profile["farm_size_acres"]) if profile else 0.0,
            step=0.1, help=words["size_help"],
        )

        soil_labels = words["soil_options"]
        soil_label = dict(zip(SOIL_KEYS, soil_labels))
        soil_choice = st.selectbox(words["soil"], SOIL_KEYS, index=SOIL_KEYS.index(soil_choice), format_func=soil_label.get)
        other_soil = ""
        if soil_choice == "Other":
            other_soil = st.text_input(
                words["other_soil"],
                value=saved_soil if saved_soil not in SOIL_KEYS else "",
                max_chars=100,
            )

        water_labels = dict(zip(WATER_KEYS, words["water_options"]))
        water_sources = st.multiselect(
            words["water"], WATER_KEYS, default=known_water, format_func=water_labels.get
        )
        other_water = ""
        if "Other" in water_sources:
            other_water = st.text_input(
                words["other_water"], value=other_water_saved, max_chars=100
            )

        crop_names = st.text_input(
            words["crops"],
            value=", ".join(profile["crops"]) if profile else "",
            help=words["crops_help"],
        )
        submitted = st.form_submit_button(words["save"], type="primary", width="stretch")

    if submitted:
        clean_name = " ".join(name.split())
        clean_state = " ".join(state.split())
        clean_district = " ".join(district.split())
        clean_village = " ".join(village.split())
        clean_crops = []
        seen_crops = set()
        for item in crop_names.split(","):
            crop = " ".join(item.split())
            if crop and crop.casefold() not in seen_crops:
                clean_crops.append(crop)
                seen_crops.add(crop.casefold())

        errors = []
        if len(clean_name) < 2:
            errors.append(words["name_error"])
        if len(clean_name) > 100:
            errors.append(words["name_long"])
        if not clean_state:
            errors.append(words["state_error"])
        if not clean_district:
            errors.append(words["district_error"])
        if not clean_village:
            errors.append(words["village_error"])
        if any(len(item) > 100 for item in (clean_state, clean_district, clean_village)):
            errors.append(words["location_long"])
        if farm_size <= 0:
            errors.append(words["size_error"])
        if soil_choice == "Other" and not other_soil.strip():
            errors.append(words["other_soil_error"])
        if not water_sources:
            errors.append(words["water_error"])
        if "Other" in water_sources and not other_water.strip():
            errors.append(words["other_water_error"])
        if not clean_crops:
            errors.append(words["crops_error"])
        if len(clean_crops) > 30:
            errors.append(words["crop_count_error"])
        if any(len(crop) > 60 for crop in clean_crops):
            errors.append(words["crop_long"])

        if errors:
            st.error(words["fix"])
            for message in errors:
                st.write(f"- {message}")
        else:
            selected_water = [item for item in water_sources if item != "Other"]
            if "Other" in water_sources:
                selected_water.append(f"Other: {' '.join(other_water.split())}")
            profile_data = {
                "farmer_name": clean_name,
                "preferred_language": preferred_language,
                "state": clean_state,
                "district": clean_district,
                "village_or_city": clean_village,
                "farm_size_acres": float(farm_size),
                "soil_type": " ".join(other_soil.split()) if soil_choice == "Other" else soil_choice,
                "water_sources": selected_water,
                "crops": clean_crops,
            }
            save_farmer_profile(profile_data)
            st.session_state["profile_saved"] = True
            st.session_state["_preferred_language_pending"] = preferred_language
            st.rerun()

    st.caption(words["storage"])
