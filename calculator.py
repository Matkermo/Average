import streamlit as st
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt

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

def main():
    # Configuration de la page avec police plus grande pour les onglets
    st.set_page_config(layout="wide")
    st.markdown("""
        <style>
            button[data-baseweb="tab"] {
                font-size: 18px !important;
                padding: 10px 20px !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("📈 Application de calcul de moyenne")

    # Création des onglets
    tab1, tab2, tab3 = st.tabs(["📊 Tableau de bord", "📋 Synthèse complète", "✏️ Modification"])

    with tab1:
        # Section importation de fichiers
        st.subheader("📤 Importer des données")
        col1, col2 = st.columns([3, 2])
        with col1:
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
                    st.success("✅ Fichier chargé avec succès!")
                except Exception as e:
                    st.error(f"❌ Erreur lors de la lecture du fichier : {e}")

        with col2:
            # Fichier exemple
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
                label="📥 Télécharger un fichier exemple",
                data=towrite,
                file_name="exemple_moyennes.xlsx",
                help="Téléchargez un exemple de fichier Excel à remplir"
            )

        # Affichage de la moyenne générale
        if 'courses' in st.session_state:
            global_average = calculate_global_average(calculate_average(st.session_state.courses))
            color_style = get_average_color(global_average)
            st.markdown(f"""
                <div style="text-align: center; margin: 20px 0; padding: 15px; background-color: #f0f2f6; border-radius: 10px;">
                    <h2 style="margin-bottom: 5px;">🎯 Moyenne Générale</h2>
                    <h1 style="font-size: 3em; margin-top: 0; {color_style}">{global_average:.2f}/20</h1>
                </div>
            """, unsafe_allow_html=True)

            # Graphique
            st.subheader("📊 Visualisation des résultats")
            courses = st.session_state.courses
            averages = calculate_average(courses)
            
            fig, ax = plt.subplots(figsize=(10, 5))
            bars = ax.bar(averages.keys(), [avg["average"] for avg in averages.values()], color='#6495ED')
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height/2, f"{height:.2f}", 
                        ha='center', va='center', color='black', fontsize=10)
            ax.axhline(y=global_average, color='#FFC080', linestyle='-', 
                      label="Moyenne générale", linewidth=2)
            ax.set_xlabel('Matières', fontsize=12)
            ax.set_ylabel('Moyennes', fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            ax.legend(loc='upper right', fontsize=10)
            plt.tight_layout()
            st.pyplot(fig)

    with tab2:
        # Onglet Synthèse complète
        st.header("📋 Synthèse complète des résultats")
        
        if 'courses' in st.session_state:
            courses = st.session_state.courses
            averages = calculate_average(courses)
            global_average = calculate_global_average(averages)
            
            # Affichage de la moyenne générale
            color_style = get_average_color(global_average)
            st.markdown(f"""
                <div style="text-align: center; margin: 10px 0 20px; padding: 15px; background-color: #f0f2f6; border-radius: 10px;">
                    <h2 style="margin-bottom: 5px;">🏆 Moyenne Générale</h2>
                    <h1 style="font-size: 2.5em; margin-top: 0; {color_style}">{global_average:.2f}/20</h1>
                </div>
            """, unsafe_allow_html=True)

            # Graphique dans l'onglet Synthèse
            st.subheader("📊 Synthèse graphique")
            fig, ax = plt.subplots(figsize=(10, 5))
            bars = ax.bar(averages.keys(), [avg["average"] for avg in averages.values()], color='#6495ED')
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height/2, f"{height:.2f}", 
                        ha='center', va='center', color='black', fontsize=10)
            ax.axhline(y=global_average, color='#FFC080', linestyle='-', 
                      label="Moyenne générale", linewidth=2)
            ax.set_xlabel('Matières', fontsize=12)
            ax.set_ylabel('Moyennes', fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            ax.legend(loc='upper right', fontsize=10)
            plt.tight_layout()
            st.pyplot(fig)

            # Tableau synthétique
            st.subheader("📝 Synthèse par matière")
            summary_df = pd.DataFrame({
                'Matière': averages.keys(),
                'Moyenne': [avg["average"] for avg in averages.values()],
                'Coefficient global': [avg["global_coefficient"] for avg in averages.values()]
            })
            
            def colorize(val):
                return get_average_color(val)
            
            st.dataframe(
                summary_df.style
                .applymap(colorize, subset=['Moyenne'])
                .format({"Moyenne": "{:.2f}"})
                .set_properties(**{
                    'text-align': 'center',
                    'min-width': '100px'
                })
                .set_table_styles([{
                    'selector': 'tbody tr:hover',
                    'props': [('background-color', '#e6f3ff')]
                }, {
                    'selector': 'th',
                    'props': [('font-size', '14px'), ('text-align', 'center')]
                }], overwrite=False),
                use_container_width=True,
                hide_index=True
            )
            
            # Détail des notes
            st.subheader("🧮 Détail complet des notes")
            data = []
            for course, grades in courses.items():
                for result, coefficient, global_coefficient in grades:
                    data.append({
                        "Matière": course,
                        "Note": result,
                        "Coefficient": coefficient,
                        "Coef. Global": global_coefficient
                    })
            
            st.dataframe(
                pd.DataFrame(data).style
                .format({"Note": "{:.1f}"})
                .set_properties(**{
                    'text-align': 'center',
                    'min-width': '100px'
                })
                .set_table_styles([{
                    'selector': 'tbody tr:hover',
                    'props': [('background-color', '#e6f3ff')]
                }, {
                    'selector': 'th',
                    'props': [('font-size', '14px'), ('text-align', 'center')]
                }], overwrite=False),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("ℹ️ Aucune donnée chargée. Veuillez importer un fichier dans l'onglet 'Tableau de bord'.")

    with tab3:
        # Onglet Modification
        st.header("✏️ Modification des données")
        
        if 'courses' in st.session_state:
            courses = st.session_state.courses
            
            # Éditeur de données
            st.subheader("🖊️ Éditer les données")
            st.warning("⚠️ Attention : Toute modification sera appliquée après avoir cliqué sur 'Mettre à jour les données'")
            
            # Affichage de la moyenne générale
            global_average = calculate_global_average(calculate_average(courses))
            color_style = get_average_color(global_average)
            st.markdown(f"""
                <div style="text-align: center; margin: 10px 0 20px; padding: 10px; background-color: #f0f2f6; border-radius: 10px;">
                    <h3 style="margin: 5px 0; {color_style}">Moyenne actuelle: {global_average:.2f}/20</h3>
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

            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("🔄 Mettre à jour les données", type="primary", use_container_width=True):
                    new_courses = {}
                    for _, row in edited_df.iterrows():
                        course = row["Matière"]
                        result = row["Note"]
                        coefficient = row["Coefficient"]
                        global_coefficient = row["Coef. Global"]

                        if course not in new_courses:
                            new_courses[course] = []
                        new_courses[course].append((result, coefficient, global_coefficient))
                    st.session_state.courses = new_courses
                    st.success("✔️ Données mises à jour avec succès!")
                    st.rerun()
            
            with col2:
                with st.popover("🗑️ Supprimer une matière", use_container_width=True):
                    if 'courses' in st.session_state:
                        courses = st.session_state.courses
                        course_to_delete = st.selectbox(
                            "Sélectionnez la matière à supprimer",
                            list(courses.keys()),
                            label_visibility="collapsed"
                        )
                        if st.button(f"Confirmer la suppression de {course_to_delete}", type="primary"):
                            del st.session_state.courses[course_to_delete]
                            st.success(f"✔️ Matière {course_to_delete} supprimée!")
                            st.rerrun()
        else:
            st.info("ℹ️ Aucune donnée chargée. Veuillez importer un fichier dans l'onglet 'Tableau de bord'.")

if __name__ == '__main__':
    main()
