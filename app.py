import streamlit as st
import requests
import re

st.set_page_config(layout="wide", page_title="Quran Viewer", initial_sidebar_state="collapsed")

# --- 1. Styling och Typsnitt ---
st.markdown("""
    <style>
    @font-face {
        font-family: 'KFGQPC';
        src: url('https://cdn.jsdelivr.net/npm/kfgqpc-uthmanic-script-hafs-regular@1.0.0/arabic.otf') format('opentype');
    }

    .block-container {
        padding-top: 4rem !important;
        padding-bottom: 3rem !important;
    }
    
    .quran-text {
        font-family: 'KFGQPC', Arial, sans-serif !important;
    }
    
    /* NYTT: Snodde verse-symbol från första appen! */
    .verse-symbol {
        font-family: 'KFGQPC', Arial, sans-serif !important;
        color: #0394fc; 
        margin: 0 0px; 
    }
    
    .stNumberInput input {
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# NYTT: Funktionen för att omvandla vanliga siffror till arabiska siffror
def to_arabic_digits(num):
    western_to_arabic = str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')
    return str(num).translate(western_to_arabic)

def highlight_madd_rules(text, color_hex="#FF00FF"):
    pattern = r"([\u0600-\u06FF][\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]*[\u0653\u06E4]|\u0622[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]*)"
    replacement = f"<span style='color: {color_hex}; font-weight: bold;'>\\1</span>"
    return re.sub(pattern, replacement, text)

def format_verse_display(verse_text, display_mode, n_words=1):
    special_chars = ["*", "۞", "۩", "◌", "\u200c", "\u200d"]
    for char in special_chars:
        verse_text = verse_text.replace(char, "")
        
    waqf_marks = ['ۖ', 'ۗ', 'ۘ', 'ۙ', 'ۚ', 'ۛ', 'ۜ']
    for mark in waqf_marks:
        verse_text = verse_text.replace(" " + mark, mark)
        
    verse_text = " ".join(verse_text.split())
    words = verse_text.split()
    
    if not words:
        return ""

    if display_mode == "Full verse":
        return verse_text
    elif display_mode == "First N words":
        return " ".join(words[:n_words])
    elif display_mode == "Last word":
        return words[-1]
    elif display_mode == "First and last word":
        if len(words) >= 2:
            return f"{words[0]} - {words[-1]}"
        else:
            return words[0]
            
    return verse_text

chapter_data = {
    "1. Al-Fatiha": 1, "2. Al-Baqarah": 2, "3. Al-'Imran": 3, "4. An-Nisa": 4, "5. Al-Ma'idah": 5,
    "6. Al-An'am": 6, "7. Al-A'raf": 7, "8. Al-Anfal": 8, "9. At-Tawbah": 9, "10. Yunus": 10,
    "11. Hud": 11, "12. Yusuf": 12, "13. Ar-Ra'd": 13, "14. Ibrahim": 14, "15. Al-Hijr": 15,
    "16. An-Nahl": 16, "17. Al-Isra": 17, "18. Al-Kahf": 18, "19. Maryam": 19, "20. Ta-Ha": 20,
    "21. Al-Anbiya": 21, "22. Al-Hajj": 22, "23. Al-Mu'minun": 23, "24. An-Nur": 24, "25. Al-Furqan": 25,
    "26. Ash-Shu'ara": 26, "27. An-Naml": 27, "28. Al-Qasas": 28, "29. Al-'Ankabut": 29, "30. Ar-Rum": 30,
    "31. Luqman": 31, "32. As-Sajdah": 32, "33. Al-Ahzab": 33, "34. Saba": 34, "35. Fatir": 35,
    "36. Ya-Sin": 36, "37. As-Saffat": 37, "38. Sad": 38, "39. Az-Zumar": 39, "40. Ghafir": 40,
    "41. Fussilat": 41, "42. Ash-Shura": 42, "43. Az-Zukhruf": 43, "44. Ad-Dukhan": 44, "45. Al-Jathiyah": 45,
    "46. Al-Ahqaf": 46, "47. Muhammad": 47, "48. Al-Fath": 48, "49. Al-Hujurat": 49, "50. Qaf": 50,
    "51. Adh-Dhariyat": 51, "52. At-Tur": 52, "53. An-Najm": 53, "54. Al-Qamar": 54, "55. Ar-Rahman": 55,
    "56. Al-Waqi'ah": 56, "57. Al-Hadid": 57, "58. Al-Mujadila": 58, "59. Al-Hashr": 59, "60. Al-Mumtahanah": 60,
    "61. As-Saff": 61, "62. Al-Jumu'ah": 62, "63. Al-Munafiqun": 63, "64. At-Taghabun": 64, "65. At-Talaq": 65,
    "66. At-Tahrim": 66, "67. Al-Mulk": 67, "68. Al-Qalam": 68, "69. Al-Haqqah": 69, "70. Al-Ma'arij": 70,
    "71. Nuh": 71, "72. Al-Jinn": 72, "73. Al-Muzzammil": 73, "74. Al-Muddaththir": 74, "75. Al-Qiyamah": 75,
    "76. Al-Insan": 76, "77. Al-Mursalat": 77, "78. An-Naba": 78, "79. An-Nazi'at": 79, "80. 'Abasa": 80,
    "81. At-Takwir": 81, "82. Al-Infitar": 82, "83. Al-Mutaffifin": 83, "84. Al-Inshiqaq": 84, "85. Al-Buruj": 85,
    "86. At-Tariq": 86, "87. Al-A'la": 87, "88. Al-Ghashiyah": 88, "89. Al-Fajr": 89, "90. Al-Balad": 90,
    "91. Ash-Shams": 91, "92. Al-Layl": 92, "93. Ad-Duha": 93, "94. Ash-Sharh": 94, "95. At-Tin": 95,
    "96. Al-'Alaq": 96, "97. Al-Qadr": 97, "98. Al-Bayyinah": 98, "99. Az-Zalzalah": 99, "100. Al-'Adiyat": 100,
    "101. Al-Qari'ah": 101, "102. At-Takathur": 102, "103. Al-'Asr": 103, "104. Al-Humazah": 104, "105. Al-Fil": 105,
    "106. Quraysh": 106, "107. Al-Ma'un": 107, "108. Al-Kawthar": 108, "109. Al-Kafirun": 109, "110. An-Nasr": 110,
    "111. Al-Masad": 111, "112. Al-Ikhlas": 112, "113. Al-Falaq": 113, "114. An-Nas": 114
}

chapter_list = list(chapter_data.keys())

# --- 2. Datahämtning ---
@st.cache_data
def fetch_verses(chapter_number):
    url = f"http://api.alquran.cloud/v1/surah/{chapter_number}/quran-uthmani-hafs"
    
    try:
        response = requests.get(url)
        response.raise_for_status() 
        data = response.json()
        verses = []
        
        for ayah in data['data']['ayahs']:
            clean_text = ayah['text']
            
            if ayah['numberInSurah'] == 1 and chapter_number not in [1, 9]:
                if "بِس" in clean_text[:10] or "بسم" in clean_text[:10]:
                    parts = clean_text.split(" ", 4)
                    if len(parts) == 5:
                        clean_text = parts[-1]
                    else:
                        clean_text = clean_text.replace("بِسۡمِ ٱللَّهِ ٱلرَّحۡمَـٰنِ ٱلرَّحِيمِ ", "")
                        
            verses.append(clean_text)
            
        return verses
        
    except requests.exceptions.RequestException as e:
        st.error(f"Kunde inte hämta data från API. Kontrollera din anslutning. Fel: {e}")
        return []

# --- Sidebar Configuration ---

selected_chapter_name = st.sidebar.selectbox("Select Surah", chapter_list)
selected_chapter_number = chapter_data[selected_chapter_name]

text_size = st.sidebar.number_input("Font size (px)", 10, 150, 22, 1)
line_height = st.sidebar.number_input("Line height", 0.1, 3.5, 1.65, 0.05)
enable_madd_highlight = st.sidebar.checkbox("Highlight 'Madd'", value=False)
new_line = st.sidebar.checkbox("Verse on new line", value=True)
justify_text = st.sidebar.checkbox("Justify text", value=False)

display_option = st.sidebar.radio(
    "Mode",
    options=["Full verse", "First N words", "Last word", "First and last word"],
    index=0
)

num_words_to_show = 1
if display_option == "First N words":
    num_words_to_show = st.sidebar.number_input("Words to show", 1, 100, 1)

st.sidebar.markdown("---")
st.sidebar.markdown("### Färglägg Versintervall")

if 'highlight_ranges' not in st.session_state:
    st.session_state.highlight_ranges = []

col1, col2 = st.sidebar.columns(2)
with col1:
    range_start = st.number_input("Från vers", min_value=1, value=1, step=1)
with col2:
    range_end = st.number_input("Till vers", min_value=1, value=5, step=1)

range_color = st.sidebar.color_picker("Välj färg", "#FFD700")

if st.sidebar.button("Lägg till intervall"):
    st.session_state.highlight_ranges.append({
        'start': range_start,
        'end': range_end,
        'color': range_color
    })

if st.session_state.highlight_ranges:
    st.sidebar.markdown("#### Aktiva intervall:")
    ranges_to_keep = []
    for idx, r in enumerate(st.session_state.highlight_ranges):
        col_txt, col_btn = st.sidebar.columns([3, 1])
        with col_txt:
            st.markdown(f"**{r['start']} - {r['end']}**: <span style='color:{r['color']};'>⬤</span>", unsafe_allow_html=True)
        with col_btn:
            if not st.button("X", key=f"del_{idx}"):
                ranges_to_keep.append(r)
    
    st.session_state.highlight_ranges = ranges_to_keep

    if st.sidebar.button("Rensa alla intervall"):
        st.session_state.highlight_ranges = []

# --- Main Rendering Logic ---

verses = fetch_verses(selected_chapter_number)

if verses:
    justify_style = "text-align: justify;" if justify_text else "text-align: center;"
    
    container_html = f"<div class='quran-text' style='direction: rtl; {justify_style} font-size: {text_size}px; line-height: {line_height};'>"
    
    for idx, verse_text in enumerate(verses):
        verse_num = idx + 1
        
        current_text_color = "inherit" 
        for r in st.session_state.highlight_ranges:
            if r['start'] <= verse_num <= r['end']:
                current_text_color = r['color']
        
        processed_text = format_verse_display(verse_text, display_option, num_words_to_show)
        
        if enable_madd_highlight:
            processed_text = highlight_madd_rules(processed_text)
            
        # NYTT: Nu använder vi vår konverterade siffra och verse-symbol-klassen!
        arabic_num = to_arabic_digits(verse_num)
        verse_html = f"<span style='color: {current_text_color};'>{processed_text} <span class='verse-symbol'>{arabic_num}</span></span> "
        
        container_html += verse_html
        
        if new_line:
            container_html += "<br>"
            
    container_html += "</div>"
    
    st.markdown(container_html, unsafe_allow_html=True)
