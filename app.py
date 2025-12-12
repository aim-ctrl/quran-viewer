import streamlit as st
import requests
import streamlit.components.v1 as components
import re  # Importerar regex-biblioteket för textanalys

st.set_page_config(layout="wide", page_title="Quran Viewer")

# --- NY FUNKTION: Identifiera och färga Madd-regler ---
def highlight_madd_rules(text, color_hex="#FF00FF"):
    """
    Letar efter Uthmani 'Maddah'-tecknet (~) (Unicode \u0653) 
    och färgar bokstaven som bär det samt själva tecknet.
    """
    # Regex-förklaring:
    # ( ... )              = Gruppera det vi vill ersätta
    # [\u0600-\u06FF]      = Matchar en arabisk bas-bokstav
    # [\u064B-\u0652\u0670]* = Matchar 0 eller flera andra diakritiska tecken (vokaler, dagger alif etc) som kan finnas emellan
    # \u0653               = Matchar specifikt Maddah-tecknet (~)
    
    pattern = r"([\u0600-\u06FF][\u064B-\u0652\u0670]*\u0653)"
    
    # Ersätt matchningen med en span som har rätt färg
    replacement = f"<span style='color: {color_hex}; font-weight: bold;'>\\1</span>"
    
    return re.sub(pattern, replacement, text)

def highlight_text(text, search_term, color_hex):
    if search_term and color_hex:
        # Använd regex för exakt matchning av söktermen om det behövs, 
        # men enkel replace fungerar bra för hela ord/delar.
        replacement_tag = f"<span style='color: {color_hex}; font-weight: bold;'>{search_term}</span>"
        return text.replace(search_term, replacement_tag)
    return text

def format_verse_display(verse_text, display_mode, n_words=1):
    special_chars = ["*", "۞", "۩"]
    for char in special_chars:
        verse_text = verse_text.replace(char, "")
    
    # Normalisera mellanslag
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

st.sidebar.title("Settings")

st.sidebar.markdown("### Highlighting")
# Checkbox för Madd-regler
enable_madd_highlight = st.sidebar.checkbox("Highlight 'Madd'", value=True)

search_term = st.sidebar.text_input("Custom char/text to highlight:", value="")
color_hex = st.sidebar.color_picker("Select custom color:", value="#FF0000")
st.sidebar.markdown("---")

st.sidebar.markdown("### Display Mode")
display_option = st.sidebar.radio(
    "How should verses be displayed?",
    options=["Full verse", "First N words", "Last word", "First and last word"],
    index=0
)

num_words_to_show = 1
if display_option == "First N words":
    num_words_to_show = st.sidebar.number_input(
        "Number of words to show:", 
        min_value=1, 
        max_value=100, 
        value=1,
        step=1
    )

new_line = st.sidebar.checkbox("Show each verse on a new line", value=True)
st.sidebar.markdown("---")

st.sidebar.markdown("### Text Appearance")
text_size = st.sidebar.number_input(
    "Font size (px)",
    min_value=10, max_value=150, value=28, step=1
)

line_height = st.sidebar.number_input(
    "Line height",
    min_value=0.1, max_value=3.5, value=1.6, step=0.1
)
st.sidebar.markdown("---")

show_snapshot_view = st.sidebar.checkbox("📷 View in 16:9 Snapshot Mode", value=False)
st.sidebar.markdown("---")

selected_chapter_name = st.sidebar.selectbox("1. Select a Chapter:", chapter_list)

if selected_chapter_name:
    chapter_num = chapter_data.get(selected_chapter_name)
    all_verses = fetch_verses(chapter_num)
    
    if all_verses:
        max_verse = len(all_verses)
        st.sidebar.markdown(f"**Chapter has {max_verse} verses.**")

        start_verse = st.sidebar.number_input("2. Start Verse:", 1, max_verse, 1)
        end_verse = st.sidebar.number_input("3. End Verse:", 1, max_verse, max_verse)

        if start_verse > end_verse:
            st.error("Start verse cannot be greater than end verse.")
        else:
            filtered_verses = all_verses[start_verse - 1 : end_verse]
            current_verse_num = start_verse 
            all_html_content = ""

            for verse in filtered_verses:
                # 1. Först formaterar vi texten (klipper ut ord, tar bort specialtecken)
                processed_verse = format_verse_display(verse, display_option, num_words_to_show)
                
                # 2. Sedan applicerar vi Madd-highlighting (Magenta) om valt
                # Vi gör detta INNAN den vanliga sök-highlightingen för att undvika krockar
                if enable_madd_highlight:
                    processed_verse = highlight_madd_rules(processed_verse, "#FF00FF")

                # 3. Sist applicerar vi användarens specifika sök-highlight
                processed_verse = highlight_text(processed_verse, search_term, color_hex)
                
                verse_symbol = "۝"
                verse_number_html = f"""
                <span style="position: relative; display: inline-block; margin: 0 5px;">
                    <span style="font-size: 1.0em; color: #00e1ff;">{verse_symbol}</span>
                    <span style="position: absolute; 
                                 top: 50%; 
                                 left: 50%; 
                                 transform: translate(-50%, -50%); 
                                 font-size: 0.45em; 
                                 color: #00d; 
                                 font-family: arial;
                                 font-weight: bold;">{current_verse_num}</span>
                </span>
                """
                
                verse_html_part = f"{processed_verse} {verse_number_html}"

                if new_line:
                    all_html_content += f"<p style='margin-bottom: 10px;'>{verse_html_part}</p>"
                else:
                    all_html_content += f"{verse_html_part} "

                current_verse_num += 1
            
            if show_snapshot_view:
                # HTML-koden för snapshot (samma som tidigare)
                html_code = f"""
                <!DOCTYPE html>
                <html lang="ar" dir="rtl">
                <head>
                    <meta charset="UTF-8">
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
                    <style>
                        body {{
                            font-family: arial; 
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            background-color: #f0f2f6;
                            margin: 0px;
                            padding: 0px;
                        }}
                        #capture-container {{
                            width: 800px;
                            height: 450px; 
                            background-color: white;
                            padding: 15px;
                            box-sizing: border-box;
                            border: 4px solid #190991;
                            text-align: center;
                            font-size: {text_size}px; 
                            line-height: {line_height};
                            overflow-y: auto; 
                            color: #000000;
                        }}
                        #capture-container::-webkit-scrollbar {{
                            width: 0px;
                        }}
                        button {{
                            margin-top: 20px;
                            padding: 10px 20px;
                            background-color: #ff4b4b;
                            color: white;
                            border: none;
                            border-radius: 5px;
                            cursor: pointer;
                            font-size: 16px;
                            font-weight: bold;
                        }}
                        button:hover {{
                            background-color: #ff2b2b;
                        }}
                    </style>
                </head>
                <body>
                    <div id="capture-container">
                        {all_html_content}
                    </div>
                    <button onclick="takeSnapshot()">💾 Save as JPEG</button>
                    <script>
                        function takeSnapshot() {{
                            const element = document.getElementById('capture-container');
                            html2canvas(element, {{
                                scale: 2, 
                                scrollY: -window.scrollY 
                            }}).then(canvas => {{
                                const link = document.createElement('a');
                                link.download = 'quran_verse_{chapter_num}_{start_verse}-{end_verse}.jpg';
                                link.href = canvas.toDataURL("image/jpeg", 0.9);
                                link.click();
                            }});
                        }}
                    </script>
                </body>
                </html>
                """
                st.info("Click the button below to save the frame as an image.")
                components.html(html_code, height=600, scrolling=False)

            else:
                st.markdown(
                    f"""
                    <div style='text-align: center; font-size: {text_size}px; direction: rtl; line-height: {line_height};'>
                        {all_html_content}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    else:
        st.warning("Could not fetch verses.")
