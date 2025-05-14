import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
import os
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Table, TableStyle, Spacer, PageBreak, Flowable
from matplotlib import cm
import matplotlib.patheffects as path_effects
from reportlab.lib.enums import TA_CENTER
import requests



def get_average_color(average):
    if average >= 12:
        return "color: #4CAF50; font-weight: bold;"  # Vert foncé
    elif average >= 10:
        return "color: #8BC34A;"  # Vert clair
    elif average >= 8:
        return "color: #FF9800;"  # Orange
    else:
        return "color: #795548;"  # Marron


def calculate_average(courses):
    averages = {}
    for course, grades in courses.items():
        total_result = sum(result * coefficient for result, coefficient, _ in grades)
        total_coefficient = sum(coefficient for _, coefficient, _ in grades)
        average = total_result / total_coefficient if total_coefficient != 0 else 0
        global_coefficient = grades[0][2]
        averages[course] = {"average": average, "global_coefficient": global_coefficient}
    return averages


def calculate_global_average(averages):
    total_result = sum(avg["average"] * avg["global_coefficient"] for avg in averages.values())
    total_global_coefficient = sum(avg["global_coefficient"] for avg in averages.values())
    global_average = total_result / total_global_coefficient if total_global_coefficient != 0 else 0
    return global_average

# --- COULEURS EDHEC ---
ROUGE_FONCE = "#98002e"
ROUGE_MOYEN = "#c64e62"
ROUGE_CLAIR = "#dfb1b6"

def color_by_value_edhec(val):
    if val >= 12:
        return ROUGE_FONCE
    elif val >= 10:
        return ROUGE_MOYEN
    else:
        return ROUGE_CLAIR

def extract_float(v):
    if isinstance(v, (int, float)):
        return float(v)
    elif isinstance(v, dict):
        for value in v.values():
            val = extract_float(value)
            if val != 0.0:
                return val
    elif isinstance(v, (list, tuple)):
        for item in v:
            val = extract_float(item)
            if val != 0.0:
                return val
    elif isinstance(v, str):
        try:
            return float(v.replace(',', '.'))
        except Exception:
            return 0.0
    return 0.0

# --- FONCTION POUR FAIRE UN BOXEDTITLE DONT LA LARGEUR SUIT LE TEXTE ---
class BoxedTitleAutoWidth(Flowable):
    """
    Une boîte rectangulaire dont la largeur s'adapte au texte + marge, centrée
    On fournit la largeur de la page totale pour pouvoir centrer correctement.
    """
    def __init__(self, text, page_width, margin_char=5, height=32, bg_color=ROUGE_CLAIR, text_color=ROUGE_FONCE, fontSize=15):
        Flowable.__init__(self)
        self.text = text
        self.fontSize = fontSize
        self.height = height
        self.bg_color = bg_color
        self.text_color = text_color
        self.margin_char = margin_char
        self.page_width = page_width

    def draw(self):
        self.canv.saveState()
        fontName = "Helvetica-Bold"
        self.canv.setFont(fontName, self.fontSize)
        # largeur du texte
        text_width = self.canv.stringWidth(self.text, fontName, self.fontSize)
        char_approx = self.canv.stringWidth("a", fontName, self.fontSize)
        margin_width = char_approx * self.margin_char
        box_width = text_width + 2 * margin_width
        # on centre la box
        x0 = (self.page_width - box_width) / 2
        y0 = 0
        self.canv.setFillColor(colors.HexColor(self.bg_color))
        self.canv.roundRect(x0, y0, box_width, self.height, radius=9, fill=1, stroke=0)
        self.canv.setFillColor(colors.HexColor(self.text_color))
        self.canv.drawString(x0 + margin_width, y0 + (self.height-self.fontSize)/2 + 3, self.text)
        self.canv.restoreState()

    def wrap(self, availWidth, availHeight):
        # pour la hauteur, c'est la box. la largeur auto (toute la page, le reste sert pour centrer)
        return self.page_width, self.height

# --- FONCTION REPORTLAB COMPATIBLE POUR LE TITRE PRINCIPAL (boîte grande large) ---
class BoxedTitleFullWidth(Flowable):
    def __init__(self, text, width, height=38, bg_color=ROUGE_CLAIR, text_color=ROUGE_FONCE, fontSize=19):
        Flowable.__init__(self)
        self.text = text
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.text_color = text_color
        self.fontSize = fontSize

    def draw(self):
        self.canv.saveState()
        fontName = "Helvetica-Bold"
        self.canv.setFillColor(colors.HexColor(self.bg_color))
        self.canv.roundRect(0, 0, self.width, self.height, radius=10, fill=1, stroke=0)
        self.canv.setFont(fontName, self.fontSize)
        self.canv.setFillColor(colors.HexColor(self.text_color))
        text_width = self.canv.stringWidth(self.text, fontName, self.fontSize)
        x_text = max(0, (self.width - text_width) / 2)
        y_text = (self.height - self.fontSize) / 2 + 3
        self.canv.drawString(x_text, y_text, self.text)
        self.canv.restoreState()
    def wrap(self, availWidth, availHeight):
        return self.width, self.height
# Fonction pour dessiner le logo sur la première page
def draw_header_with_logo(canvas, doc, logo_url):
    try:
        response = requests.get(logo_url)
        img_data = BytesIO(response.content)
        logo_width, logo_height = 100, 50
        x_position = doc.pagesize[0] - logo_width - 40
        y_position = doc.pagesize[1] - logo_height - 20
        canvas.drawImage(img_data, x_position, y_position, width=logo_width, height=logo_height, mask='auto')
    except Exception as e:
        print("Erreur de chargement du logo :", e)

def generate_pdf(global_average, averages, data, pdf_filename="resume_resultats_edhec.pdf"):
    PAGE_WIDTH, PAGE_HEIGHT = letter
    elements = []

    # Titre principal
    elements.append(Spacer(1, 20))
    elements.append(BoxedTitleFullWidth("Résumé Infographique des Moyennes & Résultats", width=PAGE_WIDTH-80, height=38, fontSize=19))
    elements.append(Spacer(1, 8))
    elements.append(BoxedTitleAutoWidth(f"Moyenne Globale : {float(global_average):.2f}", page_width=PAGE_WIDTH-80, fontSize=15, height=32))
    elements.append(Spacer(1, 16))

    # Logo
    logo_url = "https://raw.githubusercontent.com/Matkermo/Average/main/pngegg.png"
    response = requests.get(logo_url)
    if response.status_code == 200:
        image_data = BytesIO(response.content)
        logo = Image(image_data, width=160, height=90)
    else:
        logo = Paragraph("EDHEC", ParagraphStyle(name='LogoFallback', fontSize=20))

    style_non_off = ParagraphStyle(
        name='NonOff',
        fontSize=14,
        textColor='#911A20',
        alignment=2,
        fontName='Helvetica-Bold'
    )
    non_off_1 = Paragraph('!!! Attention Non officiel EDHEC !!!', style=style_non_off)
    non_off_2 = Paragraph('!!! Résultats informatifs uniquement !!!', style=style_non_off)
    header_table = Table(
        [[logo, [non_off_1, non_off_2]]],
        colWidths=[90, 390],
        hAlign='LEFT',
        style=TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ])
    )

    elements.insert(0, Spacer(1, 5))
    elements.insert(1, header_table)
    elements.insert(2, Spacer(1, 14))

    # ==== Graphique ====
    x_labels = list(averages.keys())
    y_vals = [extract_float(v) for v in averages.values()]
    colors_chart = [color_by_value_edhec(val) for val in y_vals]

    fig, ax = plt.subplots(figsize=(9, 4))
    bars = ax.bar(x_labels, y_vals, color=colors_chart, edgecolor=ROUGE_FONCE, width=0.65)
    ax.axhline(global_average, color=ROUGE_FONCE, linestyle='--', linewidth=1.7, alpha=0.8)
    for bar, val in zip(bars, y_vals):
        val_str = f"{val:.2f}" if round(val, 2) != round(val, 1) else f"{val:.1f}"
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2, val_str, ha='center', va='center', color='white', fontsize=13, fontweight='bold')

    max_idx = len(x_labels) - 1
    max_x = bars[max_idx].get_x() + bars[max_idx].get_width()
    ax.text(len(averages) + 0.2, global_average, f"{global_average:.2f}",
            color=ROUGE_FONCE, va='center', ha='left', fontweight='bold', fontsize=14)

    plt.xticks(rotation=25, ha="right", fontsize=12)
    plt.yticks(fontsize=12)
    ax.margins(y=0.18)
    plt.tight_layout()

    # Graphique temporaire sur disque (obligé avec reportlab)
    tempdir = tempfile.gettempdir()
    chart_filename = os.path.join(tempdir, "chart_edhec.png")
    plt.savefig(chart_filename, bbox_inches='tight', transparent=False)
    plt.close()

    elements.append(BoxedTitleAutoWidth("Moyenne par Matière", page_width=PAGE_WIDTH-80, fontSize=14, height=28))
    elements.append(Spacer(1, 5))
    elements.append(Image(chart_filename, width=420, height=210))
    elements.append(Spacer(1, 16))

     # --- Tableau des moyennes (compact) ---
    elements.append(BoxedTitleAutoWidth("Détail des Moyennes par Matière", page_width=PAGE_WIDTH-80, fontSize=11, height=20))
    elements.append(Spacer(1, 2))
    avg_table_data = [["Matière", "Moyenne"]]
    for mat, val in averages.items():
        v = extract_float(val)
        v_str = f"{v:.2f}" if round(v, 2) != round(v, 1) else f"{v:.1f}"
        avg_table_data.append([mat, v_str])

    avg_table = Table(avg_table_data, colWidths=[120, 60], hAlign='CENTER')
    avg_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(ROUGE_FONCE)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, 0), 2),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(avg_table)
    elements.append(Spacer(1, 8))

    # ----- GESTION SORTIE PDF : disque ou mémoire -----
    if hasattr(pdf_filename, "write"):
        # Mémoire (BytesIO) pour Streamlit
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter, leftMargin=40, rightMargin=40)
        doc.build(elements, onFirstPage=lambda canvas, doc: draw_header_with_logo(canvas, doc, logo_url))
        result = pdf_filename
    else:
        # Disque
        pdf_path = os.path.join(os.getcwd(), pdf_filename)
        doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=40, rightMargin=40)
        doc.build(elements, onFirstPage=lambda canvas, doc: draw_header_with_logo(canvas, doc, logo_url))
        result = pdf_path

    try:
        os.remove(chart_filename)
    except Exception:
        pass

    return result
    
def main():
    # ----- CSS global -----
    st.markdown(
        """
        <style>
        /* Sidebar Styles pour iPad/tablette - Overlay devant le contenu */
        [data-testid="stSidebar"] {
            z-index: 2000 !important;
            position: fixed !important;
            background: #fff !important;
            box-shadow: 0 0 15px rgba(0,0,0,0.08);
        }
        [data-testid="stSidebar"] > div {
            overflow-y: auto;
            height: 100vh;
        }
        @media (max-width: 991px) {
            [data-testid="stSidebar"] {
                width: 200px !important;
                min-width: 150px !important;
            }
        }
        .stSidebar > div:first-child {
            border-radius: 8px;
        }
        .sidebar .sidebar-content {
            border: 1px solid rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 20px;
        }
        [data-baseweb="select"] {
            border: 1px solid rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            padding: 0px;
        }
        section[data-testid="stFileUploaderDropzone"] {
            background-color: #f7f7f7;
            border: 1px solid rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            padding: 10px;
        }
        div[data-baseweb="select"] > div {
            background-color: #f7f7f7;
        }
        [data-testid="stSidebar"] img {
            display: block;
            margin: 0 auto;
            max-width: 100%;
            height: auto;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.sidebar:
        # 1. IMAGE tout en haut
        st.markdown(
            """
            <div style="text-align:center;">
                <img src="https://raw.githubusercontent.com/Matkermo/Average/main/pngegg.png"
                    style="max-width:100%; margin-bottom: 0;">
            </div>
            """,
            unsafe_allow_html=True
        )

        # 2. Sélecteur de langue
        language = st.selectbox("", options=["Français 🇫🇷", "Anglais 🇺🇸"])
        lang_code = "fr" if "Français" in language else "en"

        # 3. Traductions
        titles = {
            "fr": {
                "title": "👩‍🎓 Application de calcul de moyenne 🧑‍🎓",
                "import_data": "📥 Importer des données",
                "global_average": "Moyenne générale",
                "dashboard": "📊 Synthèse globale ",
                "full_synthesis": "📋 Détails par Matière",
                "download": "✏️ Télécharger les résultats",
                "success_message": "✅ Fichier chargé avec succès!",
                "graph_title": "📊 Visualisation des résultats",
                "summary_graph_title": "📊 Synthèse graphique",
                "summary_title": "📝 Synthèse par matière",
                "complete_detail_title": "🧮 Détail complet des notes",
                "example_download": "📤 Télécharger un fichier exemple",
                "title_download_sample": "📤 Exemple de fichier",
                "note": "Note",
                "coefficient": "Coefficient",
                "global_coefficient": "Coef. Global",
                "sidebar_warning": "⚠️Avertissement : non officiel, à titre informatif uniquement ⚠️"
            },
            "en": {
                "title": "👩‍🎓 Average Calculation App 🧑‍🎓 ",
                "import_data": "📥 Import Data",
                "global_average": "General Average",
                "dashboard": "📊 Dashboard",
                "full_synthesis": "📋 Courses Details",
                "download": "✏️ Download results",
                "success_message": "✅ File loaded successfully!",
                "graph_title": "📊 Visualization of Results",
                "summary_graph_title": "📊 Graphical Summary",
                "summary_title": "📝 Subject Summary",
                "complete_detail_title": "🧮 Detailed Scores",
                "title_download_sample": "📤 Sample file",
                "example_download": "📤 Download example file",
                "note": "Grade",
                "coefficient": "Coefficient",
                "global_coefficient": "Global Coefficient",
                "sidebar_warning": "⚠️ Warning: unofficial, for informational purposes only ⚠️"
            }
        }

        # 4. Texte warning
        st.markdown(
            f"""
            <div style='
                    color: #911A20;
                    font-size: 13px;
                    font-family: Helvetica, Arial, sans-serif;
                    font-weight: bold;
                    text-align: center;
                    margin-bottom: 14px;
                    margin-top: 6px;
                    word-break: break-word;
            '>
                {titles[lang_code]["sidebar_warning"]}
            </div>
            """,
            unsafe_allow_html=True
        )

        # 5. Import du fichier
        st.subheader(titles[lang_code]["import_data"])
        uploaded_file = st.file_uploader(
            "Choisissez un fichier Excel",
            type=["xlsx"],
            label_visibility="collapsed"
        )
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                courses = {}
                for _, row in df.iterrows():
                    course = row["Course"]
                    result = float(row["Result"])
                    coefficient = float(row["Coefficient"])
                    global_coefficient = float(row["Global Coefficient"])
                    if course not in courses:
                        courses[course] = []
                    courses[course].append((result, coefficient, global_coefficient))
                st.session_state.courses = courses
                st.success(titles[lang_code]["success_message"])
            except Exception as e:
                st.error(f"❌ Erreur lors de la lecture du fichier : {e}" if lang_code == "fr" else f"❌ Error reading the file: {e}")

        # 6. Exemple de fichier (en bas)
        st.subheader(titles[lang_code]["title_download_sample"])
        exemple_data = {
            "Course": ["Math", "Math", "Math", "Français", "Français", "Anglais"],
            "Result": [12, 15, 10, 14, 12, 16],
            "Coefficient": [2, 3, 1, 2, 3, 1],
            "Global Coefficient": [3, 3, 3, 2, 2, 1]
        }
        exemple_df = pd.DataFrame(exemple_data)
        towrite = BytesIO()
        exemple_df.to_excel(towrite, index=False)
        towrite.seek(0)
        st.download_button(
            label=titles[lang_code]["example_download"],
            data=towrite,
            file_name="exemple_moyennes.xlsx",
            help="Téléchargez un exemple de fichier Excel à remplir" if lang_code == "fr" else "Download a sample Excel file"
        )

    # Création des onglets
    tab1, tab2, tab3 = st.tabs([titles[lang_code]["dashboard"], titles[lang_code]["full_synthesis"], titles[lang_code]["download"]])

    with tab1:
        if 'courses' in st.session_state:
            courses = st.session_state.courses
            averages = calculate_average(courses)
            global_average = calculate_global_average(averages)

            # Détermination de la couleur selon la moyenne
            if global_average < 10:
                color = "red"
            elif global_average < 12:
                color = "orange"
            else:
                color = "green"

            # Affichage stylisé avec saut de ligne et valeur bien visible
            st.markdown(f"""
                <div style="text-align: center; margin: 5px 0 10px; padding: 8px; background-color: #f0f2f6; border-radius: 8px;">
                    <h3 style="margin-bottom: 4px;">🎯 {titles[lang_code]["global_average"]}</h3>
                    <div style="font-size: 1.5em; font-weight: bold; color: {color}; margin-top: 0;">{global_average:.2f}/20</div>
                </div>
            """, unsafe_allow_html=True)

            # Graphique
            st.subheader(titles[lang_code]["graph_title"])
            fig, ax = plt.subplots(figsize=(10, 5))
            bars = ax.bar(averages.keys(), [avg["average"] for avg in averages.values()], color='#6495ED')
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height / 2,
                    f"{height:.2f}",
                    ha='center',
                    va='center',
                    color='white',
                    fontsize=16,
                    fontweight='bold'
                )
            ax.axhline(y=global_average, color='#FF0000', linestyle='-',  
                       label=f"{titles[lang_code]['global_average']} ({global_average:.2f})", linewidth=2)
            ax.set_xlabel("", fontsize=16)
            ax.set_ylabel("", fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            # Ajuster la taille des étiquettes des matières sur l'axe X
            ax.set_xticklabels(averages.keys(), fontsize=18 )  # Taille de police augmentée des matières
            ax.legend(loc='upper right', fontsize=16)
            plt.tight_layout()
            st.pyplot(fig)  # Assurez-vous que `fig` est défini avant cet appel

            # Tableau synthétique
            st.subheader(titles[lang_code]["summary_title"])

            summary_df = pd.DataFrame({
                'Matière': averages.keys(),
                'Moyenne': [avg["average"] for avg in averages.values()],
                'Coefficient global': [avg["global_coefficient"] for avg in averages.values()]
            })

            def colorize(val):
                return get_average_color(val)

            styled_summary = summary_df.style\
                .applymap(colorize, subset=['Moyenne'])\
                .format({
                    "Moyenne": "{:.1f}",
                    "Coefficient global": "{:.1f}"
                })\
                .set_table_styles([
                    {'selector': 'thead th', 'props': [('text-align', 'center')]},
                    {'selector': 'tbody tr:hover', 'props': [('background-color', '#e6f3ff')]}
                ])\
                .set_properties(subset=["Matière"], **{'text-align': 'left'})\
                .set_properties(subset=["Moyenne", "Coefficient global"], **{'text-align': 'center'})

            st.markdown(
                f"""
                <div style="display: flex; justify-content: center;">
                    <div style="width: fit-content;">
                        {styled_summary.to_html(escape=False)}
                """,
                unsafe_allow_html=True
            )


    with tab2:
        #st.header(titles[lang_code]["full_synthesis"])

        if 'courses' in st.session_state:
            courses = st.session_state.courses
            averages = calculate_average(courses)
            global_average = calculate_global_average(averages)

            # Détermination de la couleur selon la moyenne
            if global_average < 10:
                color = "red"
            elif global_average < 12:
                color = "orange"
            else:
                color = "green"

            # Affichage stylisé avec saut de ligne et valeur bien visible
            st.markdown(f"""
                <div style="text-align: center; margin: 5px 0 10px; padding: 8px; background-color: #f0f2f6; border-radius: 8px;">
                    <h3 style="margin-bottom: 4px;">🎯 {titles[lang_code]["global_average"]}</h3>
                    <div style="font-size: 1.5em; font-weight: bold; color: {color}; margin-top: 0;">{global_average:.2f}/20</div>
                </div>
            """, unsafe_allow_html=True)

            # Détail des notes
            # Détail des notes
            st.subheader(titles[lang_code]["complete_detail_title"])

            if 'courses' in locals() and courses:  # Vérifie que courses existe et contient des données
                data = []
                for course, grades in courses.items():
                    for result, coefficient, global_coefficient in grades:
                        data.append({
                            "Matière": course,
                            titles[lang_code]["note"]: result,
                            titles[lang_code]["coefficient"]: coefficient,
                            titles[lang_code]["global_coefficient"]: global_coefficient
                        })

                ordered_columns = [
                    "Matière", 
                    titles[lang_code]["note"], 
                    titles[lang_code]["coefficient"], 
                    titles[lang_code]["global_coefficient"]
                ]

                df_detail = pd.DataFrame(data)[ordered_columns]

                styled_df = df_detail.style\
                    .format({
                        "Matière": "{}", 
                        titles[lang_code]["note"]: "{:.1f}",
                        titles[lang_code]["coefficient"]: "{:.1f}",
                        titles[lang_code]["global_coefficient"]: "{:.1f}"
                    })\
                    .set_table_styles([
                        {'selector': 'thead th', 'props': [('text-align', 'center')]},
                        {'selector': 'tbody tr:hover', 'props': [('background-color', '#e6f3ff')]}
                    ])\
                    .set_properties(subset=["Matière"], **{'text-align': 'left'})\
                    .set_properties(subset=ordered_columns[1:], **{'text-align': 'center'})

                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: center;">
                        <div style="width: fit-content;">
                            {styled_df.to_html(escape=False)}
                    """,
                    unsafe_allow_html=True
                )

            else:
                st.info("ℹ️ Aucune donnée chargée / No Data Loaded ")
    with tab3:

        # Onglet téléchargement des résultats
        st.header(titles[lang_code]["download"])

        if 'courses' in st.session_state:
            courses = st.session_state.courses

            # Calcul et affichage de la moyenne générale
            averages = calculate_average(courses)
            global_average = calculate_global_average(averages)
            color = "red" if global_average < 10 else "orange" if global_average < 12 else "green"

            st.markdown(f"""
                <div style="text-align: center; margin: 5px 0 10px; padding: 8px; background-color: #f0f2f6; border-radius: 8px;">
                    <h3 style="margin-bottom: 4px;">🎯 {titles[lang_code]["global_average"]}</h3>
                    <div style="font-size: 1.5em; font-weight: bold; color: {color}; margin-top: 0;">{global_average:.2f}/20</div>
                </div>
            """, unsafe_allow_html=True)

            # Nouveau tableau synthétique
            st.subheader(titles[lang_code]["summary_title"])

            summary_df = pd.DataFrame({
                'Matière': averages.keys(),
                'Moyenne': [avg["average"] for avg in averages.values()],
                'Coefficient global': [avg["global_coefficient"] for avg in averages.values()]
            })

            def colorize(val):
                return get_average_color(val)

            styled_summary = summary_df.style\
                .applymap(colorize, subset=['Moyenne'])\
                .format({
                    "Moyenne": "{:.1f}",
                    "Coefficient global": "{:.1f}"
                })\
                .set_table_styles([
                    {'selector': 'thead th', 'props': [('text-align', 'center')]},
                    {'selector': 'tbody tr:hover', 'props': [('background-color', '#e6f3ff')]}
                ])\
                .set_properties(subset=["Matière"], **{'text-align': 'left'})\
                .set_properties(subset=["Moyenne", "Coefficient global"], **{'text-align': 'center'})

            st.markdown(
                f"""
                <div style="display: flex; justify-content: center;">
                    <div style="width: fit-content;">
                        {styled_summary.to_html(escape=False)}
                """,
                unsafe_allow_html=True
            )

            # Bouton de téléchargement du PDF
            # Création de deux colonnes pour placer deux boutons côte à côte
            col0, col1, col2 = st.columns([0.70, 1, 1.4])  # [espace, bouton1, bouton2]

            with col1:
                if st.button("📥 Générer un résumé", key="long_button", help="Cliquez ici pour télécharger votre résumé"):
                    if 'courses' in st.session_state:
                        averages = calculate_average(st.session_state.courses)
                        global_average = calculate_global_average(averages)

                        data = []
                        for course, avg in averages.items():
                            data.append({
                                "Matière": course,
                                "Moyenne": round(avg["average"], 1),
                                "Coefficient global": round(avg["global_coefficient"], 1)
                            })

                        pdf_path = generate_pdf(global_average, averages, data)
                        st.session_state['pdf_path'] = pdf_path  # stocke le chemin pour la session
                    else:
                        st.warning("📋 Aucune donnée à inclure dans le PDF. Veuillez importer des cours.")

            with col2:
                if 'pdf_path' in st.session_state and os.path.exists(st.session_state['pdf_path']):
                    with open(st.session_state['pdf_path'], "rb") as f:
                        st.download_button(
                            label="Télécharger le PDF",
                            data=f,
                            file_name="résumé.pdf",
                            mime="application/pdf",
                            help="Téléchargez votre résumé en PDF"
                        )

if __name__ == '__main__':
    main()