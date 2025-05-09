import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle  # Added this line
import tempfile
import os
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


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

def generate_pdf(global_average, averages, data):
    # Create a temporary PDF file
    pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    
    # Create the main PDF document
    doc = SimpleDocTemplate(pdf_file.name, pagesize=letter)

    # Création de styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['Normal']
    
    # Créer un style centré
    centered_style = ParagraphStyle('Centered', parent=normal_style, alignment=1)  # 1 pour centré

    # Création de styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['Normal']
    
    # Liste pour contenir le contenu
    elements = []

    # Ajouter le titre
    title = Paragraph("Résumé des Moyennes et Résultats", title_style)
    elements.append(title)

    # Ajouter la moyenne globale
    global_avg_style = styles['Normal'].clone('GlobalAverage')
    global_avg_style.fontSize += 10  # Augmente la taille de police
    global_avg_style.alignment = 1    # Centre le texte

    global_avg_text = f"Moyenne Globale: <b>{global_average:.2f}</b>"
    avg_paragraph = Paragraph(global_avg_text, global_avg_style)
    elements.append(avg_paragraph)

    # Génération du graphique à barres
    fig, ax = plt.subplots(figsize=(10, 6))  # Ajuster la taille du graphique
    courses = list(averages.keys())
    avg_values = [details["average"] for details in averages.values()]

    # Définir des couleurs personnalisées pour les barres
    color = '#1f77b4'  # Couleur bleu standard
    bars = ax.bar(courses, avg_values, color=color)

    # Ajouter les étiquettes de données sur les barres
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, yval + 0.2, round(yval, 2), ha='center', va='bottom')

    # Enlever les titres et axes
    ax.set_title('')  # Supprimer le titre du graphique (ou commenté)
    ax.set_xlabel('')  # Supprimer le label de l'axe des X
    ax.set_ylabel('')  # Supprimer le label de l'axe des Y
    ax.yaxis.grid(True)  # Afficher la grille horizontaleax.set_xlabel('Courses', fontsize=12)
    

    # Ajouter une ligne pour la moyenne globale
    ax.axhline(y=global_average, color='red', linestyle='--', linewidth=2)
    ax.text(len(courses) - 1, global_average + 0.5, f'{global_average:.2f}', color='red')

    plt.tight_layout()
    chart_filename = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    plt.savefig(chart_filename, dpi=300)  # Enregistrer en haute résolution
    plt.close(fig)

    # Ajouter l'image du graphique au PDF
    elements.append(Paragraph("<br/><br/>", normal_style))  # Espacement
    elements.append(Paragraph("Graphique des Moyennes par Cours:", centered_style))  # Style centré
    elements.append(Image(chart_filename, width=400, height=240))  # Ajuster la taille de l'image

    # Ajouter les moyennes par cours
    course_avg_data = [['Course', 'Average']]
    for course, details in averages.items():
        course_avg_data.append([course, f"{details['average']:.2f}"])

    course_table = Table(course_avg_data)
    course_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.dodgerblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(course_table)

    # Ajouter un espace entre les tableaux
    elements.append(Paragraph("<br/><br/>", normal_style))  

    # Ajouter le tableau des données
    data_table_data = [['Matière', 'Note', 'Coefficient', 'Coef. Global']]
    for row in data:
        data_table_data.append([row['Matière'], row['Note'], row['Coefficient'], row['Coef. Global']])

    data_table = Table(data_table_data)
    data_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.dodgerblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(data_table)

    # Construire le PDF
    doc.build(elements)
    
    # Nettoyer le fichier image temporaire
    os.remove(chart_filename)

    return pdf_file.name  # Retourne le chemin du PDF généré

def main():
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
    /* Ajuste la largeur sur tablette */
    @media (max-width: 991px) {
        [data-testid="stSidebar"] {
            width: 260px !important;
            min-width: 180px !important;
        }
    }

    .stSidebar > div:first-child {
        border-radius: 8px;
    }
    /* Bordures sur le contenu de la sidebar (si tu veux garder) */
    .sidebar .sidebar-content {
        border: 1px solid rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 20px;
    }

    /* Touche pas aux boutons Upload, etc */
    [data-baseweb="select"] {
        border: 1px solid rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        padding: 0px;
    }
    </style>
    """,
    unsafe_allow_html=True
    )
    # Langue
    language = st.sidebar.selectbox("", options=["Français 🇫🇷", "Anglais 🇺🇸"])
    lang_code = "fr" if "Français" in language else "en"
   
    titles = {
        "fr": {
            "title": "👩‍🎓 Application de calcul de moyenne 🧑‍🎓",
            "import_data": "📤 Importer des données",
            "global_average": "Moyenne générale",
            "dashboard": "📊 synthèse globale ",
            "full_synthesis": "📋 Détails par Matière",
            "download": "✏️ télécharger les résultats",
            "success_message": "✅ Fichier chargé avec succès!",
            "graph_title": "📊 Visualisation des résultats",
            "summary_graph_title": "📊 Synthèse graphique",
            "summary_title": "📝 Synthèse par matière",
            "complete_detail_title": "🧮 Détail complet des notes",
            #"update_button": "🔄 Mettre à jour les données",
            #"alert_message": "⚠️ Attention : Toute modification sera appliquée après avoir cliqué sur 'Mettre à jour les données'", supprimé temporairement
            "example_download": "📥 Télécharger un fichier exemple",
            "title_download_sample": "exemple de fichier",
            "note": "Note",
            "coefficient": "Coefficient",
            "global_coefficient": "Coef. Global"
        },
        "en": {
            "title": "👩‍🎓 Average Calculation App 🧑‍🎓 ",
            "import_data": "📤 Import Data",
            "global_average": "General Average",
            "dashboard": "📊 Dashboard",
            "full_synthesis": "📋 Courses Details",
            "download": "✏️ Download résultats",
            "success_message": "✅ File loaded successfully!",
            "graph_title": "📊 Visualization of Results",
            "summary_graph_title": "📊 Graphical Summary",
            "summary_title": "📝 Subject Summary",
            "complete_detail_title": "🧮 Detailed Scores",
            #"update_button": "🔄 Update Data",
            #"alert_message": "⚠️ Attention: Any changes will be applied after clicking 'Update Data'",
            "title_download_sample": "Download a file",
            "example_download": "📥 Download example file",
            "note": "Note",
            "coefficient": "Coefficient",
            "global_coefficient": "Global Coefficient"
        }
    }
    # Centre le titre
    st.markdown(f"<h1 style='text-align: center;'>{titles[lang_code]['title']}</h1>", unsafe_allow_html=True)

    # Section importation de fichiers dans la sidebar
    with st.sidebar:
        st.subheader(titles[lang_code]["import_data"])
        uploaded_file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx"], label_visibility="collapsed")
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
                st.error(f"❌ Erreur lors de la lecture du fichier : {e}")

        # Fichier exemple
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
            help="Téléchargez un exemple de fichier Excel à remplir"
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
                    fontsize=12,
                    fontweight='bold'
                )
            ax.axhline(y=global_average, color='#FF0000', linestyle='-',  
                       label=f"{titles[lang_code]['global_average']} ({global_average:.2f})", linewidth=2)
            ax.set_xlabel("", fontsize=12)
            ax.set_ylabel("", fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            ax.legend(loc='upper right', fontsize=10)
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

            # Éditeur de données
            #st.warning(titles[lang_code]["alert_message"]) supprimé temporairement

            # Affichage de la moyenne générale
            global_average = calculate_global_average(calculate_average(courses))
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

            data = []
            for course, grades in courses.items():
                for result, coefficient, global_coefficient in grades:
                    data.append({
                        "Matière": course,
                        "Note": result,
                        "Coefficient": coefficient,
                        "Coef. Global": global_coefficient
                    })

            edited_df = st.data_editor(
                pd.DataFrame(data),
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "Matière": st.column_config.TextColumn(width="medium"),
                    "Note": st.column_config.NumberColumn(width="small", format="%.1f"),
                    "Coefficient": st.column_config.NumberColumn(width="small", format="%.1f"),
                    "Coef. Global": st.column_config.NumberColumn(width="small", format="%.1f")
                }
            )

            if st.button("📥 Télécharger le résumé", key="long_button", help="Cliquez ici pour télécharger votre résumé"):
                if 'courses' in st.session_state:
                    averages = calculate_average(st.session_state.courses)
                    global_average = calculate_global_average(averages)

                    data = []
                    for course, grades in st.session_state.courses.items():
                        for result, coefficient, global_coefficient in grades:
                            data.append({
                                "Matière": course,
                                "Note": result,
                                "Coefficient": coefficient,
                                "Coef. Global": global_coefficient
                            })

                    pdf_path = generate_pdf(global_average, averages, data)

                    # Fournir un bouton de téléchargement pour le PDF généré
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="Télécharger le PDF",
                            data=f,
                            file_name="résumé.pdf",
                            mime="application/pdf",
                            help="Téléchargez votre résumé en PDF"
                        )

                    # Nettoyage après le téléchargement
                    os.remove(pdf_path)
                else:
                    st.warning("📋 Aucune donnée à inclure dans le PDF. Veuillez importer des cours.")

            if 'courses' not in st.session_state:
                st.info("ℹ️ Aucune donnée chargée. Veuillez importer un fichier dans l'onglet 'Tableau de bord'.")


if __name__ == '__main__':
    main()
