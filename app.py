import streamlit as st
import requests
import re

st.set_page_config(layout="wide", page_title="Quran Viewer", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&display=swap');

    [data-testid="stToolbar"] {
        visibility: hidden;
        display: none;
    }
    
    /* (Valfritt) Döljer den färgade linjen högst upp */
    [data-testid="stDecoration"] {
        visibility: hidden;
        display: none;
    }
    
    .block-container {
        padding-top: 1rem !important; /* Standard är ofta runt 6rem */
        padding-bottom: 1rem !important;
    }
    
    .quran-text {
        font-family: 'Scheherazade New', serif !important;
    }
    
    .verse-number {
        font-family: 'Scheherazade New', serif !important;
        color: #00e1ff;
    }
    
    .stNumberInput input {
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

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

@st.cache_data
def fetch_verses(chapter_number):
    base_url = "https://api.quran.com/api/v4/verses/by_chapter/"
    url = f"{base_url}{chapter_number}?language=en&words=false&fields=text_uthmani&per_page=1000"
    
    try:
        response = requests.get(url)
        response.raise_for_status() 
        data = response.json()
        return [v['text_uthmani'] for v in data['verses']]
    except requests.exceptions.RequestException as e:
        st.error(f"Could not fetch data from API. Check your connection. Error: {e}")
        return []


text_size = st.sidebar.number_input("Font size (px)", 10, 150, 22, 1)
line_height = st.sidebar.number_input("Line height", 0.1, 3.5, 1.65, 0.05)
enable_madd_highlight = st.sidebar.checkbox("Highlight 'Madd'", value=True)
new_line = st.sidebar.checkbox("Verse on new line", value=False)

# NYTT: Checkbox för Marginaljustering (Justify)
justify_text = st.sidebar.checkbox("Justify text", value=True)

display_option = st.sidebar.radio(
    "Mode",
    options=["Full verse", "First N words", "Last word", "First and last word"],
    index=0
)

num_words_to_show = 1
if display_option == "First N words":
    num_words_to_show = st.sidebar.number_input("Words to show", 1, 100, 1)

with st.expander("Chapter & Verses", expanded=True):
    selected_chapter_name = st.select_slider("Select Chapter:", options=chapter_list)
    
    if selected_chapter_name:
        chapter_num = chapter_data.get(selected_chapter_name)
        all_verses = fetch_verses(chapter_num)
        
        if all_verses:
            max_verse = len(all_verses)
            
            col1, col2 = st.columns(2)
            with col1:
                start_verse = st.number_input("Start Verse", 1, max_verse, 1)
            with col2:
                end_verse = st.number_input("End Verse", 1, max_verse, max_verse)

            if start_verse > end_verse:
                st.error("Start verse cannot be greater than end verse.")
                filtered_verses = []
            else:
                filtered_verses = all_verses[start_verse - 1 : end_verse]
                current_verse_num = start_verse 
        else:
            filtered_verses = []
            st.warning("Could not fetch verses.")
    else:
        filtered_verses = []

text_alignment = "center"
if not new_line and justify_text:
    text_alignment = "justify"

if filtered_verses:
    all_html_content = ""
    for verse in filtered_verses:
        processed_verse = format_verse_display(verse, display_option, num_words_to_show)
        
        if enable_madd_highlight:
            processed_verse = highlight_madd_rules(processed_verse, "#FF00FF")

        verse_symbol = "۝"
        
        verse_number_html = f"""
        <span style="position: relative; display: inline-block; margin: 0px;">
            <span class="verse-number" style="font-size: 1.0em;">{verse_symbol}</span>
            <span class="verse-number" style="position: absolute; 
                          top: 50%; 
                          left: 50%; 
                          transform: translate(-50%, -50%); 
                          font-size: 0.45em; 
                          font-weight: bold;">{current_verse_num}</span>
        </span>
        """
        
        verse_html_part = f"{processed_verse} {verse_number_html}"

        if new_line:
            all_html_content += f"<p style='margin-bottom: 10px;'>{verse_html_part}</p>"
        else:
            all_html_content += f"{verse_html_part} "

        current_verse_num += 1
    
    st.markdown(
        f"""
        <div class="quran-text" style='text-align: {text_alignment}; font-size: {text_size}px; direction: rtl; line-height: {line_height}; margin-top: 20px;'>
            {all_html_content}
        </div>
        """,
        unsafe_allow_html=True
    )
