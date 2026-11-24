"""Streamlit screens for adding, viewing, and updating crop records."""

from datetime import date

import streamlit as st

from farmerlly.crop_catalog import CROPS, crop_label, growth_stages
from farmerlly.database import add_crop_record, get_crop_records, update_crop_record
from farmerlly.i18n import translate, translate_mapping


COPY = {
    "English": {
        "title": "My crops",
        "intro": "Track each planting separately. Add another record for each field or planting date.",
        "add": "Add a crop",
        "crop": "Crop",
        "other_crop": "Enter crop name",
        "variety": "Variety",
        "no_variety": "Not selected",
        "other_variety": "Other / enter manually",
        "enter_variety": "Enter variety name (optional)",
        "planting_date": "Sowing or planting date",
        "growth_stage": "Current growth stage",
        "progress": "Crop progress (%)",
        "progress_help": "Your estimate of this crop's progress.",
        "save_crop": "Save crop",
        "update_crop": "Save changes",
        "list_title": "Crop records",
        "no_records": "No crop records yet. Use the form above to add your first crop.",
        "profile_needed": "Register your farmer profile before adding crop records.",
        "crop_name_error": "Enter a crop name before saving.",
        "saved": "Crop record added.",
        "updated": "Crop details updated.",
        "date_label": "Sown / planted",
        "variety_label": "Variety",
        "stage_label": "Growth stage",
        "details": "Edit crop details",
        "active_count": "Crop records",
        "catalog_note": "Starter variety choices are from TNAU references and may not suit every region. Check local recommendations.",
        "source": "TNAU source",
        "unnamed": "New crop",
        "empty_overview": "No crops have been added yet. Open My crops to create a crop record.",
    },
    "தமிழ்": {
        "title": "என் பயிர்கள்",
        "intro": "ஒவ்வொரு நடவையும் தனித்தனியாகப் பதிவு செய்யுங்கள். வேறு வயல் அல்லது நடவு நாளுக்கு புதிய பதிவைச் சேர்க்கவும்.",
        "add": "பயிரைச் சேர்க்கவும்",
        "crop": "பயிர்",
        "other_crop": "பயிரின் பெயரை உள்ளிடவும்",
        "variety": "ரகம்",
        "no_variety": "தேர்வு செய்யவில்லை",
        "other_variety": "மற்றது / கைமுறையாக உள்ளிடவும்",
        "enter_variety": "ரகத்தின் பெயரை உள்ளிடவும் (விருப்பம்)",
        "planting_date": "விதைத்த அல்லது நட்ட நாள்",
        "growth_stage": "தற்போதைய வளர்ச்சி நிலை",
        "progress": "பயிர் முன்னேற்றம் (%)",
        "progress_help": "இந்தப் பயிரின் முன்னேற்றம் குறித்த உங்கள் மதிப்பீடு.",
        "save_crop": "பயிரைப் பதிவு செய்யவும்",
        "update_crop": "மாற்றங்களைச் சேமிக்கவும்",
        "list_title": "பயிர் பதிவுகள்",
        "no_records": "இன்னும் பயிர் பதிவுகள் இல்லை. மேலே உள்ள படிவத்தில் முதல் பயிரைச் சேர்க்கவும்.",
        "profile_needed": "பயிர்களைச் சேர்ப்பதற்கு முன் விவசாயி விவரத்தைப் பதிவு செய்யவும்.",
        "crop_name_error": "சேமிப்பதற்கு முன் பயிரின் பெயரை உள்ளிடவும்.",
        "saved": "பயிர் பதிவு சேர்க்கப்பட்டது.",
        "updated": "பயிர் விவரங்கள் புதுப்பிக்கப்பட்டன.",
        "date_label": "விதைத்த / நட்ட நாள்",
        "variety_label": "ரகம்",
        "stage_label": "வளர்ச்சி நிலை",
        "details": "பயிர் விவரங்களைத் திருத்தவும்",
        "active_count": "பயிர் பதிவுகள்",
        "catalog_note": "தொடக்க ரகத் தேர்வுகள் TNAU ஆதாரங்களிலிருந்து எடுக்கப்பட்டவை; எல்லா இடங்களுக்கும் பொருந்தாது. உள்ளூர் பரிந்துரையைச் சரிபார்க்கவும்.",
        "source": "TNAU ஆதாரம்",
        "unnamed": "புதிய பயிர்",
        "empty_overview": "இன்னும் பயிர்கள் சேர்க்கப்படவில்லை. புதிய பயிர் பதிவுக்கு ‘என் பயிர்கள்’ பகுதிக்குச் செல்லவும்.",
    },
}


def _text(language: str, key: str) -> str:
    return COPY.get(language, translate_mapping(COPY["English"], language))[key]


def _stage_options(crop_code: str, language: str) -> tuple[list[str], dict[str, str]]:
    stages = growth_stages(crop_code)
    codes = [stage[0] for stage in stages]
    labels = {
        stage[0]: translate(stage[1], language)
        for stage in stages
    }
    return codes, labels


def _crop_record_name(record: dict, language: str) -> str:
    if record["crop_code"] == "other":
        return record["crop_name"]
    return crop_label(record["crop_code"], language)


def _variety_input(crop_code: str, language: str, key_prefix: str) -> str:
    words = COPY.get(language) or translate_mapping(COPY["English"], language)
    varieties = CROPS[crop_code]["varieties"]
    if varieties:
        variety_options = ["__none__", *varieties, "__other__"]
        selected_variety = st.selectbox(
            words["variety"],
            variety_options,
            format_func=lambda value: (
                words["no_variety"] if value == "__none__"
                else words["other_variety"] if value == "__other__"
                else value
            ),
            key=f"{key_prefix}_variety_choice",
        )
        if selected_variety == "__other__":
            return st.text_input(words["enter_variety"], key=f"{key_prefix}_variety_other").strip()
        return "" if selected_variety == "__none__" else selected_variety

    return st.text_input(words["enter_variety"], key=f"{key_prefix}_variety_text").strip()


def _render_record(record: dict, language: str) -> None:
    words = COPY.get(language) or translate_mapping(COPY["English"], language)
    crop_name = _crop_record_name(record, language)
    _, stage_labels = _stage_options(record["crop_code"], language)
    stage_name = stage_labels.get(record["growth_stage"], record["growth_stage"])
    planting_date = date.fromisoformat(record["planting_date"])

    with st.container(border=True):
        st.markdown(f"### {crop_name}")
        st.caption(f"{words['date_label']}: {planting_date.strftime('%d %b %Y')}")
        if record["variety"]:
            st.caption(f"{words['variety_label']}: {record['variety']}")
        st.caption(f"{words['stage_label']}: {stage_name}")
        st.progress(record["progress"] / 100, text=f"{record['progress']}%")

        with st.expander(words["details"]):
            stage_codes, stage_labels = _stage_options(record["crop_code"], language)
            current_stage_index = (
                stage_codes.index(record["growth_stage"])
                if record["growth_stage"] in stage_codes else 0
            )
            with st.form(f"edit_crop_{record['crop_id']}"):
                variety = st.text_input(
                    words["variety"], value=record["variety"],
                    key=f"edit_variety_{record['crop_id']}",
                )
                updated_date = st.date_input(
                    words["planting_date"], value=planting_date,
                    key=f"edit_date_{record['crop_id']}",
                )
                updated_stage = st.selectbox(
                    words["growth_stage"], stage_codes, index=current_stage_index,
                    format_func=stage_labels.get, key=f"edit_stage_{record['crop_id']}",
                )
                updated_progress = st.slider(
                    words["progress"], min_value=0, max_value=100,
                    value=int(record["progress"]), step=1,
                    key=f"edit_progress_{record['crop_id']}",
                )
                submitted = st.form_submit_button(words["update_crop"], type="primary")

            if submitted:
                update_crop_record(
                    record["crop_id"],
                    {
                        "variety": variety.strip(),
                        "planting_date": updated_date.isoformat(),
                        "growth_stage": updated_stage,
                        "progress": updated_progress,
                    },
                )
                st.session_state["crop_updated"] = True
                st.rerun()


def render_crop_management(language: str, profile: dict | None, compact: bool = False) -> None:
    """Render the crop overview or full crop registration and editing page."""
    words = COPY.get(language) or translate_mapping(COPY["English"], language)
    records = get_crop_records()
    st.subheader(words["title"])

    if compact:
        if not records:
            st.info(words["empty_overview"])
            return
        st.caption(f"{words['active_count']}: {len(records)}")
        columns = st.columns(min(3, len(records)))
        for index, record in enumerate(records):
            with columns[index % len(columns)].container(border=True):
                st.markdown(f"**{_crop_record_name(record, language)}**")
                st.caption(f"{words['stage_label']}: {_stage_options(record['crop_code'], language)[1].get(record['growth_stage'], record['growth_stage'])}")
                st.progress(record["progress"] / 100, text=f"{record['progress']}%")
        return

    st.caption(words["intro"])
    if st.session_state.pop("crop_added", False):
        st.success(words["saved"])
    if st.session_state.pop("crop_updated", False):
        st.success(words["updated"])

    if profile is None:
        st.info(words["profile_needed"])
    else:
        st.markdown(f"#### {words['add']}")
        crop_codes = list(CROPS)
        crop_code = st.selectbox(
            words["crop"], crop_codes,
            format_func=lambda code: crop_label(code, language),
            key="new_crop_code",
        )
        if crop_code == "other":
            crop_name = st.text_input(words["other_crop"], max_chars=80, key="new_crop_name").strip()
        else:
            crop_name = crop_label(crop_code, "English")

        variety = _variety_input(crop_code, language, "new_crop")
        variety_source = CROPS[crop_code].get("variety_source")
        if variety_source:
            st.caption(f"{words['catalog_note']} · [{words['source']}]({variety_source})")

        stage_codes, stage_labels = _stage_options(crop_code, language)
        with st.form("add_crop_form"):
            planting_date = st.date_input(words["planting_date"], value=date.today())
            growth_stage_code = st.selectbox(
                words["growth_stage"], stage_codes,
                format_func=stage_labels.get,
            )
            progress = st.slider(
                words["progress"], min_value=0, max_value=100,
                value=0, step=1, help=words["progress_help"],
            )
            submitted = st.form_submit_button(words["save_crop"], type="primary")

        if submitted:
            if not crop_name:
                st.error(words["crop_name_error"])
            else:
                add_crop_record(
                    {
                        "crop_code": crop_code,
                        "crop_name": crop_name,
                        "variety": variety,
                        "planting_date": planting_date.isoformat(),
                        "growth_stage": growth_stage_code,
                        "progress": progress,
                    }
                )
                st.session_state["crop_added"] = True
                st.rerun()

    st.divider()
    st.markdown(f"#### {words['list_title']} · {len(records)}")
    if not records:
        st.info(words["no_records"])
    else:
        for record in records:
            _render_record(record, language)
