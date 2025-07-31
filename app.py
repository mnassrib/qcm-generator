import streamlit as st
import json
import random
import zipfile
import io

# --- 🔐 AUTHENTIFICATION SIMPLE ---
USERNAME = "enseignant"
PASSWORD = "ece2025"

def check_password():
    """Affiche un panneau de login simple dans la sidebar"""
    st.sidebar.title("🔐 Authentification")
    username = st.sidebar.text_input("Nom d'utilisateur")
    password = st.sidebar.text_input("Mot de passe", type="password")
    if username == USERNAME and password == PASSWORD:
        return True
    elif username or password:
        st.sidebar.error("❌ Identifiants incorrects")
    return False

# --- 🏗 GÉNÉRATION DU XML ---
def generer_xml(questions, timelimit):
    """
    Génère le contenu XML d'un quiz Moodle avec les paramètres choisis.
    - timelimit : durée du quiz en secondes
    """
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<quiz>\n'
    xml += f'  <timelimit>{timelimit}</timelimit>\n'           # ⏱ Temps total
    xml += '  <attempts>1</attempts>\n'                        # 🔒 Une seule tentative
    xml += '  <navmethod>sequential</navmethod>\n'             # 📄 Mode séquentiel
    xml += '  <shufflequestions>1</shufflequestions>\n'        # 🔀 Mélanger l’ordre des questions

    for q in questions:
        xml += q["xml"] + "\n"  # chaque question est déjà au bon format XML
    xml += '</quiz>'
    return xml

# --- 🎨 INTERFACE ---
st.set_page_config(page_title="QCM Moodle ECE", page_icon="📘")

if check_password():
    st.title("📘 Générateur de QCM Moodle")
    st.write("Générez facilement des QCM différents pour chaque groupe, prêts pour Moodle.")

    # Upload du JSON
    json_file = st.file_uploader("📤 Téléchargez votre fichier JSON de questions", type=["json"])

    # Paramètres
    nb_groupes = st.number_input("Nombre de groupes", min_value=1, max_value=50, value=18)
    nb_questions = st.number_input("Nombre de questions par QCM", min_value=1, max_value=50, value=20)
    duree_quiz = st.number_input("⏱ Durée du quiz (en minutes)", min_value=1, max_value=180, value=30)

    if json_file:
        banque = json.load(json_file)

        if len(banque) < nb_questions:
            st.error(f"La banque ne contient pas assez de questions ({len(banque)} disponibles).")
        else:
            if st.button("📥 Générer les fichiers XML"):
                # Créer un ZIP en mémoire
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zipf:
                    for g in range(1, nb_groupes + 1):
                        # Tirage aléatoire
                        questions = random.sample(banque, nb_questions)
                        # Conversion minutes → secondes
                        timelimit_seconds = duree_quiz * 60
                        # Générer le contenu XML
                        xml_content = generer_xml(questions, timelimit_seconds)
                        # Écrire le fichier dans le ZIP
                        zipf.writestr(f"QCM_Groupe_{g:02}.xml", xml_content)

                zip_buffer.seek(0)
                st.success(f"{nb_groupes} fichiers XML générés ✅")

                # Bouton de téléchargement
                st.download_button(
                    label="📦 Télécharger tous les QCM (ZIP)",
                    data=zip_buffer,
                    file_name="QCM_Groupes.zip",
                    mime="application/zip"
                )
