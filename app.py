import streamlit as st
import json
import random
import zipfile
import io
from collections import defaultdict

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

# --- 🎨 CONFIGURATION INTERFACE ---
st.set_page_config(page_title="QCM Moodle ECE", page_icon="📘", layout="centered")

# --- 🌟 STYLES PERSONNALISÉS ---
st.markdown("""
    <style>
    .main {
        background-color: #f9f9f9;
    }
    .title {
        font-size: 38px;
        color: #2c3e50;
        text-align: center;
        font-weight: bold;
        margin-bottom: -10px;
    }
    .subtitle {
        text-align: center;
        font-size: 18px;
        color: #34495e;
        margin-bottom: 30px;
    }
    .section {
        background-color: #ffffff;
        padding: 20px;
        margin: 15px 0;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- 🏠 INTERFACE ---
if check_password():
    st.markdown("<div class='title'>📘 Générateur de QCM Moodle</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>🎯 Créez des QCM uniques grâce au <b>tirage aléatoire</b> des questions, prêts pour Moodle</div>", unsafe_allow_html=True)

    # 📤 Upload JSON
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.header("📤 Upload de la banque de questions")
    json_file = st.file_uploader("Glissez votre fichier JSON de questions (format Moodle)", type=["json"])
    st.markdown("</div>", unsafe_allow_html=True)

    # 🔧 Paramètres globaux
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.header("⚙️ Paramètres du QCM")
    nb_groupes = st.number_input("👥 Nombre de groupes", min_value=1, max_value=50, value=1)
    duree_quiz = st.number_input("⏱ Durée du quiz (en minutes)", min_value=1, max_value=180, value=10)
    st.markdown("</div>", unsafe_allow_html=True)

    if json_file:
        banque = json.load(json_file)

        # 🔍 Identifier les cours et difficultés
        cours_disponibles = sorted(set(q["cours"] for q in banque))
        difficultes = sorted(set(q["difficulte"] for q in banque))

        # 🎛 Interface pour quotas
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        st.header("🎛 Répartition des questions par cours et difficulté")

        quotas = {}
        for cours in cours_disponibles:
            st.subheader(f"📘 {cours}")
            quotas[cours] = {}
            for diff in difficultes:
                dispo = sum(1 for q in banque if q["cours"] == cours and q["difficulte"] == diff)
                quotas[cours][diff] = st.number_input(
                    f"{diff.capitalize()} (disponibles : {dispo})",
                    min_value=0,
                    max_value=dispo,
                    value=0,
                    key=f"{cours}-{diff}"   # 🔑 Clé unique
                )
        st.markdown("</div>", unsafe_allow_html=True)

        # 📥 Génération des fichiers
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        st.header("📥 Génération des QCM")
        if st.button("🚀 Générer et télécharger les QCM"):
            # Validation
            for cours, difficulte_dict in quotas.items():
                for diff, nb in difficulte_dict.items():
                    dispo = sum(1 for q in banque if q["cours"] == cours and q["difficulte"] == diff)
                    if nb > dispo:
                        st.error(f"⚠️ Pas assez de questions pour {cours} - {diff} (demandé {nb}, dispo {dispo})")
                        st.stop()

            # Création du ZIP
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for g in range(1, nb_groupes + 1):
                    questions_selectionnees = []
                    for cours, difficulte_dict in quotas.items():
                        for diff, nb in difficulte_dict.items():
                            if nb > 0:
                                questions_filtrees = [q for q in banque if q["cours"] == cours and q["difficulte"] == diff]
                                questions_selectionnees.extend(random.sample(questions_filtrees, nb))

                    # Conversion minutes → secondes
                    timelimit_seconds = duree_quiz * 60
                    # Générer XML
                    xml_content = generer_xml(questions_selectionnees, timelimit_seconds)
                    zipf.writestr(f"QCM_Groupe_{g:02}.xml", xml_content)

            zip_buffer.seek(0)
            st.success(f"✅ {nb_groupes} fichiers XML générés avec succès !")

            # 📦 Bouton téléchargement ZIP
            st.download_button(
                label="📦 Télécharger tous les QCM (ZIP)",
                data=zip_buffer,
                file_name="QCM_Groupes.zip",
                mime="application/zip"
            )
        st.markdown("</div>", unsafe_allow_html=True)
