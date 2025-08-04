import streamlit as st
import json
import yaml
import random
import zipfile
import io

# --- 🔐 AUTHENTIFICATION SIMPLE ---
USERNAME = st.secrets["USERNAME"]
PASSWORD = st.secrets["PASSWORD"]

def check_password():
    st.sidebar.title("🔐 Authentification")
    username = st.sidebar.text_input("Nom d'utilisateur")
    password = st.sidebar.text_input("Mot de passe", type="password")
    if username == USERNAME and password == PASSWORD:
        return True
    elif username or password:
        st.sidebar.error("❌ Identifiants incorrects")
    return False

# --- 🏗 GÉNÉRATION DU XML ---
def generer_xml(questions):
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    for q in questions:
        xml += q["xml"] + "\n"
    xml += '</quiz>'
    return xml

# --- CONFIG STREAMLIT ---
st.set_page_config(page_title="QCM Moodle ECE", page_icon="📘", layout="wide")

# --- 🌟 CSS GLOBAL ---
st.markdown("""
    <style>
    body { background-color: #f5f6fa; }

    .hero {
        background: rgba(8,111,118,1);
        padding: 25px;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 25px;
    }
    .hero h1 {
        font-size: 38px;
        margin-bottom: 5px;
    }
    .hero p {
        font-size: 18px;
        margin: 0;
        opacity: 0.9;
    }

    .section {
        background-color: #ffffff;
        padding: 20px;
        margin: 15px 0;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    .sidebar-divider {
        border-top: 1px solid rgba(0, 0, 0, 0.1);
        margin: 15px 0;
    }

    .stButton>button {
        width: 100%;
        background-color: rgba(8,111,118,1);
        color: white;
        font-size: 16px;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 15px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #06585C;
    }
    </style>
""", unsafe_allow_html=True)

# --- HERO BANNER ---
st.markdown("""
    <div class='hero'>
        <h1>📘 Générateur de QCM Moodle</h1>
        <p>Créez des QCM uniques grâce au <b>tirage aléatoire</b> des questions – prêts pour Moodle</p>
    </div>
""", unsafe_allow_html=True)

# --- INTERFACE PRINCIPALE ---
if check_password():
    zip_buffer = None
    total_questions = 0
    total_par_diff = {}

    # 📤 UPLOAD
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.header("📤 Upload de la banque de questions")
    uploaded_file = st.file_uploader("Glissez votre fichier JSON ou YAML de questions", type=["json", "yaml", "yml"])
    st.markdown("</div>", unsafe_allow_html=True)

    # ⚙️ PARAMÈTRES
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.header("📦 Nombre de QCM à générer")
    nb_groupes = st.number_input("👥 Nombre de classes", min_value=1, max_value=50, value=1)
    st.markdown("</div>", unsafe_allow_html=True)

    banque = []
    if uploaded_file:
        try:
            if uploaded_file.name.endswith((".yaml", ".yml")):
                banque = yaml.safe_load(uploaded_file)
            elif uploaded_file.name.endswith(".json"):
                banque = json.load(uploaded_file)
            else:
                st.error("⚠️ Format de fichier non supporté.")
        except Exception as e:
            st.error(f"Erreur de chargement du fichier : {e}")

    if banque:
        cours_disponibles = sorted(set(q["cours"] for q in banque))
        difficultes = sorted(set(q["difficulte"] for q in banque))

        # 🎛 QUOTAS
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
                    key=f"{cours}-{diff}"
                )

        total_questions = sum(nb for cours_dict in quotas.values() for nb in cours_dict.values())
        total_par_diff = {diff: sum(q[diff] for q in quotas.values()) for diff in difficultes}

        st.sidebar.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
        st.sidebar.markdown("### 📊 Questions sélectionnées")
        st.sidebar.markdown(f"**Total : {total_questions}**")

        st.sidebar.markdown("**Répartition par difficulté :**")
        for diff, nb in total_par_diff.items():
            emoji = "🟢" if diff.lower() == "facile" else "🟠" if diff.lower() == "moyen" else "🔴"
            st.sidebar.write(f"{emoji} **{diff.capitalize()}** : {nb}")

        st.sidebar.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
        st.sidebar.markdown(f"📦 **QCM à générer : {nb_groupes} fichiers**")
        st.sidebar.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

        if st.sidebar.button("📥 Générer et télécharger les QCM"):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for g in range(1, nb_groupes + 1):
                    questions_selectionnees = []
                    for cours, difficulte_dict in quotas.items():
                        for diff, nb in difficulte_dict.items():
                            if nb > 0:
                                questions_filtrees = [
                                    q for q in banque if q["cours"] == cours and q["difficulte"] == diff
                                ]
                                questions_selectionnees.extend(random.sample(questions_filtrees, nb))
                    xml_content = generer_xml(questions_selectionnees)
                    zipf.writestr(f"QCM_Groupe_{g:02}.xml", xml_content)

            zip_buffer.seek(0)
            st.sidebar.success(f"✅ {nb_groupes} fichiers générés")

        if zip_buffer:
            st.sidebar.download_button(
                label="📦 Télécharger tous les QCM (ZIP)",
                data=zip_buffer,
                file_name="QCM_Groupes.zip",
                mime="application/zip"
            )
