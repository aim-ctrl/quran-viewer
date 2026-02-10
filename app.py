import streamlit as st
import requests
import re

# --- Konfiguration ---
st.set_page_config(layout="wide", page_title="Quran Viewer", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&display=swap');
    .block-container { padding-top: 2rem !important; }
    .quran-text { font-family: 'Scheherazade New', serif !important; }
    .verse-number { font-family: 'Scheherazade New', serif !important; color: #00e1ff; }
    </style>
""", unsafe_allow_html=True)

# --- Logik för Session State (Färgregler) ---
if 'color_rules' not in st.session_state:
    st.session_state.color_rules = [] # Lista med dicts: {'range': '1-3', 'color': '#ff0000'}

def parse_verse_range(range_str):
    verses = set()
    if not range_str: return verses
    try:
        parts = range_str.replace(" ", "").split(",")
        for part in parts:
            if "-" in part:
                start, end = map(int, part.split("-"))
                verses.update(range(start, end + 1))
            else:
                verses.add(int(part))
    except: pass
    return verses

# --- Hjälpfunktioner ---
def highlight_madd_rules(text, color_hex="#FF00FF"):
    pattern = r"([\u0600-\u06FF][\u064B-\u0652\u0670]*\u0653)"
    replacement = f"<span style='color: {color_hex}; font-weight: bold;'>\\1</span>"
    return re.sub(pattern, replacement, text)

def format_verse_display(verse_text, display_mode, n_words=1):
    verse_text = re.sub(r"[\*|۞|۩]", "", verse_text)
    words = verse_text.split()
    if not words: return ""
    if display_mode == "Full verse": return " ".join(words)
    elif display_mode == "First N words": return " ".join(words[:n_words])
    elif display_mode == "Last word": return words[-1]
    elif display_mode == "First and last word":
        return f"{words[0]} - {words[-1]}" if len(words) >= 2 else words[0]
    return " ".join(words)

@st.cache_data
def fetch_verses(chapter_number):
    url = f"https://api.quran.com/api/v4/verses/by_chapter/{chapter_number}?language=en&words=false&fields=text_uthmani&per_page=1000"
    try:
        r = requests.get(url)
        return [v['text_uthmani'] for v in r.json()['verses']]
    except: return []

# --- Sidomeny ---
st.sidebar.header("Inställningar")
text_size = st.sidebar.number_input("Textstorlek", 10, 150, 28)
line_height = st.sidebar.number_input("Radavstånd", 0.5, 4.0, 2.0)
new_line = st.sidebar.checkbox("Ny rad per vers", value=False)
enable_madd = st.sidebar.checkbox("Visa Madd", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("Färgregler")

# Knappar för att hantera regler
col_btn1, col_btn2 = st.sidebar.columns(2)
if col_btn1.button("Lägg till färg"):
    st.session_state.color_rules.append({'range': '', 'color': '#FFD700'})
if col_btn2.button("Rensa alla") and st.session_state.color_rules:
    st.session_state.color_rules = []

# Visa inmatningsfält för varje regel
active_rules = []
for i, rule in enumerate(st.session_state.color_rules):
    with st.sidebar.expander(f"Regel {i+1}", expanded=True):
        r_range = st.text_input(f"Intervall (t.ex. 1-5, 8)", value=rule['range'], key=f"range_{i}")
        r_color = st.color_picker(f"Färg", value=rule['color'], key=f"color_{i}")
        st.session_state.color_rules[i] = {'range': r_range, 'color': r_color}
        if r_range:
            active_rules.append({'verses': parse_verse_range(r_range), 'color': r_color})

# --- Huvudvy ---
chapter_data = {"1. Al-Fatiha": 1, "2. Al-Baqarah": 2, "18. Al-Kahf": 18, "36. Ya-Sin": 36} # Fortsätt listan...
selected_chapter = st.select_slider("Välj Surah", options=list(chapter_data.keys()))
chapter_num = chapter_data[selected_chapter]
all_verses = fetch_verses(chapter_num)

if all_verses:
    max_v = len(all_verses)
    v_range = st.slider("Visa verser", 1, max_v, (1, max_v if max_v < 10 else 10))
    start_v, end_v = v_range
    
    display_mode = st.selectbox("Visningsläge", ["Full verse", "First N words", "Last word", "First and last word"])
    
    # Rendering
    all_html = ""
    for idx, text in enumerate(all_verses[start_v-1:end_v], start=start_v):
        processed = format_verse_display(text, display_mode)
        if enable_madd:
            processed = highlight_madd_rules(processed)
        
        # Kolla färgregler (senast tillagda regel har företräde)
        applied_color = ""
        for rule in active_rules:
            if idx in rule['verses']:
                applied_color = f"color: {rule['color']}; font-weight: bold;"
        
        verse_num_html = f"""
        <span style="position: relative; display: inline-block; direction: ltr;">
            <span class="verse-number" style="font-size: 0.9em;">۝</span>
            <span class="verse-number" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 0.4em; font-weight: bold;">{idx}</span>
        </span>
        """
        
        content = f"<span style='{applied_color}'>{processed}</span> {verse_num_html}"
        
        if new_line:
            all_html += f"<p style='margin-bottom: 15px;'>{content}</p>"
        else:
            all_html += f" {content} "

    st.markdown(f"""
        <div class="quran-text" style="text-align: justify; font-size: {text_size}px; direction: rtl; line-height: {line_height};">
            {all_html}
        </div>
    """, unsafe_allow_html=True)
