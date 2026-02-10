import streamlit as st
import requests
import re

# --- Konfiguration och Styling ---
st.set_page_config(layout="wide", page_title="Quran Viewer", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&display=swap');
    .block-container { padding-top: 4rem !important; padding-bottom: 3rem !important; }
    .quran-text { font-family: 'Scheherazade New', serif !important; }
    .verse-number { font-family: 'Scheherazade New', serif !important; color: #00e1ff; }
    .stNumberInput input { text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- Hjälpfunktioner ---

def parse_verse_range(range_str):
    """Omvandlar strängar som '1, 3-5' till en lista med heltal [1, 3, 4, 5]"""
    verses = set()
    if not range_str:
        return verses
    try:
        parts = range_str.replace(" ", "").split(",")
        for part in parts:
            if "-" in part:
                start, end = map(int, part.split("-"))
                verses.update(range(start, end + 1))
            else:
                verses.add(int(part))
    except ValueError:
        pass # Ignorera felaktig formatering
    return verses

def highlight_madd_rules(text, color_hex="#FF00FF"):
    pattern = r"([\u0600-\u06FF][\u064B-\u0652\u0670]*\u0653)"
    replacement = f"<span style='color: {color_hex}; font-weight: bold;'>\\1</span>"
    return re.sub(pattern, replacement, text)

def format_verse_display(verse_text, display_mode, n_words=1):
    special_chars = ["*", "۞", "۩"]
    for char in special_chars:
        verse_text = verse_text.replace(char, "")
    verse_text = " ".join(verse_text.split())
    words = verse_text.split()
    if not words: return ""

    if display_mode == "Full verse": return verse_text
    elif display_mode == "First N words": return " ".join(words[:n_words])
    elif display_mode == "Last word": return words[-1]
    elif display_mode == "First and last word":
        return f"{words[0]} - {words[-1]}" if len(words) >= 2 else words[0]
    return verse_text

@st.cache_data
def fetch_verses(chapter_number):
    base_url = "https://api.quran.com/api/v4/verses/by_chapter/"
    url = f"{base_url}{chapter_number}?language=en&words=false&fields=text_uthmani&per_page=1000"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return [v['text_uthmani'] for v in data['verses']]
    except Exception as e:
        st.error(f"Error: {e}")
        return []

# --- Sidomeny / Kontroller ---
st.sidebar.header("Display Settings")
text_size = st.sidebar.number_input("Font size (px)", 10, 150, 22, 1)
line_height = st.sidebar.number_input("Line height", 0.1, 3.5, 1.65, 0.05)
enable_madd_highlight = st.sidebar.checkbox("Highlight 'Madd'", value=True)
new_line = st.sidebar.checkbox("Verse on new line", value=False)
justify_text = st.sidebar.checkbox("Justify text", value=True)

st.sidebar.markdown("---")
st.sidebar.header("Custom Verse Coloring")
# Nytt: Inmatning för vilka verser som ska färgas
target_verses_input = st.sidebar.text_input("Verse(s) to color (e.g. 1, 3-5)", "")
highlight_color = st.sidebar.color_picker("Pick a color", "#FFD700") # Standard Guld

target_verse_list = parse_verse_range(target_verses_input)

display_option = st.sidebar.radio(
    "Mode", options=["Full verse", "First N words", "Last word", "First and last word"], index=0
)

num_words_to_show = 1
if display_option == "First N words":
    num_words_to_show = st.sidebar.number_input("Words to show", 1, 100, 1)

# --- Huvudinnehåll ---
chapter_data = { "1. Al-Fatiha": 1, "2. Al-Baqarah": 2, "114. An-Nas": 114 } # (Håll listan komplett i din kod)
# ... (Lägg till alla kapitel här som i din originalkod)

with st.expander("Chapter & Verses", expanded=True):
    chapter_list = ["1. Al-Fatiha", "2. Al-Baqarah", "18. Al-Kahf", "36. Ya-Sin"] # Exempel, använd din fulla lista
    selected_chapter_name = st.selectbox("Select Chapter:", options=chapter_list)
    
    if selected_chapter_name:
        # Extrahera nummer från strängen manuellt om chapter_data saknas
        chapter_num = int(selected_chapter_name.split(".")[0])
        all_verses = fetch_verses(chapter_num)
        
        if all_verses:
            max_verse = len(all_verses)
            col1, col2 = st.columns(2)
            with col1: start_verse = st.number_input("Start Verse", 1, max_verse, 1)
            with col2: end_verse = st.number_input("End Verse", 1, max_verse, max_verse)

            if start_verse > end_verse:
                st.error("Start verse cannot be greater than end verse.")
                filtered_verses = []
            else:
                filtered_verses = all_verses[start_verse - 1 : end_verse]
                current_verse_num = start_verse 
        else:
            filtered_verses = []

# --- Rendering ---
text_alignment = "justify" if (not new_line and justify_text) else "center"

if filtered_verses:
    all_html_content = ""
    for verse in filtered_verses:
        processed_verse = format_verse_display(verse, display_option, num_words_to_show)
        
        if enable_madd_highlight:
            processed_verse = highlight_madd_rules(processed_verse, "#FF00FF")

        # LOGIK FÖR ANPASSAD FÄRG
        # Vi kollar om det aktuella versnumret finns i vår "target_verse_list"
        current_style = ""
        if current_verse_num in target_verse_list:
            current_style = f"color: {highlight_color}; font-weight: bold;"

        verse_symbol = "۝"
        verse_number_html = f"""
        <span style="position: relative; display: inline-block; margin: 0px; color: #00e1ff;">
            <span class="verse-number" style="font-size: 1.0em;">{verse_symbol}</span>
            <span class="verse-number" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 0.45em; font-weight: bold;">{current_verse_num}</span>
        </span>
        """
        
        # Applicera färgen på texten om den är vald
        verse_html_part = f"<span style='{current_style}'>{processed_verse}</span> {verse_number_html}"

        if new_line:
            all_html_content += f"<p style='margin-bottom: 10px;'>{verse_html_part}</p>"
        else:
            all_html_content += f"{verse_html_part} "

        current_verse_num += 1
    
    st.markdown(
        f"""<div class="quran-text" style='text-align: {text_alignment}; font-size: {text_size}px; direction: rtl; line-height: {line_height}; margin-top: 20px;'>
            {all_html_content}
        </div>""",
        unsafe_allow_html=True
    )
