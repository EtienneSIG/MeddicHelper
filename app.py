import streamlit as st
import sqlite3
import pandas as pd
import json
import time
from datetime import datetime, date
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import io

# Import des modules locaux
from config import *
from utils import *

# Configuration de la page
st.set_page_config(
    page_title="MEDDIC HELPER",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
<style>
.meddic-card {
    border-left: 4px solid #1f77b4;
    padding: 10px;
    margin: 10px 0;
    background-color: #f8f9fa;
    border-radius: 5px;
}

.priority-high {
    border-left-color: #FF4B4B !important;
}

.priority-medium {
    border-left-color: #FFA500 !important;
}

.priority-low {
    border-left-color: #00D4AA !important;
}

.completion-score {
    font-size: 1.2em;
    font-weight: bold;
}

.status-badge {
    padding: 4px 8px;
    border-radius: 12px;
    color: white;
    font-size: 0.8em;
    font-weight: bold;
}

.metric-container {
    background-color: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

class MEDDICDatabase:
    def __init__(self, db_path=DATABASE_CONFIG["db_name"]):
        """Initialise la base de données SQLite pour MEDDIC"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Crée les tables si elles n'existent pas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table principale des fiches MEDDIC
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meddic_fiches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                company TEXT NOT NULL,
                meeting_date DATE,
                commercial TEXT,
                metrics TEXT,
                economic_buyer TEXT,
                decision_criteria TEXT,
                decision_process TEXT,
                identify_pain TEXT,
                champion TEXT,
                status TEXT DEFAULT 'En cours',
                notes TEXT,
                priority TEXT DEFAULT 'Moyenne',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table d'audit trail
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fiche_id INTEGER,
                action TEXT,
                field_changed TEXT,
                old_value TEXT,
                new_value TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fiche_id) REFERENCES meddic_fiches(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_fiche(self, fiche_data):
        """Sauvegarde une fiche MEDDIC avec audit trail"""
        # Validation des données
        is_valid, errors = validate_fiche_data(fiche_data)
        if not is_valid:
            raise ValueError(f"Données invalides: {', '.join(errors)}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calcul de la priorité
        priority = get_priority_level(fiche_data)
        fiche_data['priority'] = priority
        
        if fiche_data.get('id'):
            # Récupération des anciennes valeurs pour l'audit
            cursor.execute("SELECT * FROM meddic_fiches WHERE id=?", (fiche_data['id'],))
            old_data = cursor.fetchone()
            
            # Mise à jour
            cursor.execute("""
                UPDATE meddic_fiches 
                SET client_name=?, company=?, meeting_date=?, commercial=?, 
                    metrics=?, economic_buyer=?, decision_criteria=?, 
                    decision_process=?, identify_pain=?, champion=?, 
                    status=?, notes=?, priority=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (
                fiche_data['client_name'], fiche_data['company'], 
                fiche_data['meeting_date'], fiche_data['commercial'],
                fiche_data['metrics'], fiche_data['economic_buyer'],
                fiche_data['decision_criteria'], fiche_data['decision_process'],
                fiche_data['identify_pain'], fiche_data['champion'],
                fiche_data['status'], fiche_data['notes'], priority, fiche_data['id']
            ))
            
            # Audit trail pour mise à jour
            if SECURITY_CONFIG["audit_trail_enabled"]:
                cursor.execute("""
                    INSERT INTO audit_log (fiche_id, action, timestamp)
                    VALUES (?, 'UPDATE', CURRENT_TIMESTAMP)
                """, (fiche_data['id'],))
        else:
            # Création
            cursor.execute("""
                INSERT INTO meddic_fiches 
                (client_name, company, meeting_date, commercial, metrics, 
                 economic_buyer, decision_criteria, decision_process, 
                 identify_pain, champion, status, notes, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fiche_data['client_name'], fiche_data['company'], 
                fiche_data['meeting_date'], fiche_data['commercial'],
                fiche_data['metrics'], fiche_data['economic_buyer'],
                fiche_data['decision_criteria'], fiche_data['decision_process'],
                fiche_data['identify_pain'], fiche_data['champion'],
                fiche_data['status'], fiche_data['notes'], priority
            ))
            
            # Audit trail pour création
            if SECURITY_CONFIG["audit_trail_enabled"]:
                fiche_id = cursor.lastrowid
                cursor.execute("""
                    INSERT INTO audit_log (fiche_id, action, timestamp)
                    VALUES (?, 'CREATE', CURRENT_TIMESTAMP)
                """, (fiche_id,))
        
        conn.commit()
        conn.close()
    
    def get_all_fiches(self, include_stats=False):
        """Récupère toutes les fiches MEDDIC avec statistiques optionnelles"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM meddic_fiches ORDER BY updated_at DESC", conn)
        conn.close()
        
        if include_stats and not df.empty:
            # Ajout des statistiques calculées
            df['completion_score'] = df.apply(lambda row: calculate_completion_score(row), axis=1)
            df['formatted_date'] = df['meeting_date'].apply(format_date)
        
        return df
    
    def get_fiche_by_id(self, fiche_id):
        """Récupère une fiche par son ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meddic_fiches WHERE id=?", (fiche_id,))
        result = cursor.fetchone()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            fiche_dict = dict(zip(columns, result))
            conn.close()
            return fiche_dict
        
        conn.close()
        return None
    
    def delete_fiche(self, fiche_id):
        """Supprime une fiche avec audit trail"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Audit trail pour suppression
        if SECURITY_CONFIG["audit_trail_enabled"]:
            cursor.execute("""
                INSERT INTO audit_log (fiche_id, action, timestamp)
                VALUES (?, 'DELETE', CURRENT_TIMESTAMP)
            """, (fiche_id,))
        
        cursor.execute("DELETE FROM meddic_fiches WHERE id=?", (fiche_id,))
        conn.commit()
        conn.close()
    
    def get_statistics(self):
        """Récupère les statistiques globales"""
        fiches_df = self.get_all_fiches(include_stats=True)
        return get_statistics(fiches_df)
    
    def search_fiches(self, search_term):
        """Recherche dans les fiches"""
        fiches_df = self.get_all_fiches()
        return search_fiches(fiches_df, search_term)

class MEDDICPDFGenerator:
    def __init__(self):
        """Générateur de PDF pour les fiches MEDDIC"""
        pass
    def generate_fiche_pdf(self, fiche_data):
        """Génère un PDF pour une fiche MEDDIC"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        
        # Titre
        pdf.cell(0, 10, f'Fiche MEDDIC - {fiche_data["company"]}', 0, 1, 'C')
        pdf.ln(10)
        
        # Informations générales
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Informations Générales', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f'Client: {fiche_data["client_name"]}', 0, 1)
        pdf.cell(0, 6, f'Entreprise: {fiche_data["company"]}', 0, 1)
        pdf.cell(0, 6, f'Commercial: {fiche_data["commercial"]}', 0, 1)
        pdf.cell(0, 6, f'Date RDV: {fiche_data["meeting_date"]}', 0, 1)
        pdf.ln(5)
        
        # MEDDIC
        sections = [
            ('Metrics', fiche_data.get('metrics', '')),
            ('Economic Buyer', fiche_data.get('economic_buyer', '')),
            ('Decision Criteria', fiche_data.get('decision_criteria', '')),
            ('Decision Process', fiche_data.get('decision_process', '')),
            ('Identify Pain', fiche_data.get('identify_pain', '')),
            ('Champion', fiche_data.get('champion', ''))
        ]
        
        for title, content in sections:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, title, 0, 1)
            pdf.set_font('Arial', '', 10)            # Gestion du texte long
            if content:
                lines = content.split('\n')
                for line in lines:
                    if len(line) > 80:
                        words = line.split(' ')
                        current_line = ''
                        for word in words:
                            if len(current_line + word) < 80:
                                current_line += word + ' '
                            else:
                                pdf.cell(0, 5, current_line.strip(), 0, 1)
                                current_line = word + ' '
                        if current_line:
                            pdf.cell(0, 5, current_line.strip(), 0, 1)
                    else:
                        pdf.cell(0, 5, line, 0, 1)
            else:
                pdf.cell(0, 5, '(Non renseigné)', 0, 1)
            pdf.ln(3)
        
        # Convertir le bytearray en bytes pour Streamlit
        pdf_bytes = pdf.output(dest='S')
        if isinstance(pdf_bytes, bytearray):
            pdf_bytes = bytes(pdf_bytes)
        return pdf_bytes

# Initialisation de la base de données
@st.cache_resource
def init_database():
    return MEDDICDatabase()

# Interface principale
def main():
    db = init_database()
    
    # Sidebar pour la navigation
    st.sidebar.title("🎯 MEDDIC CRM")
    
    # Affichage des statistiques rapides dans la sidebar
    try:
        stats = db.get_statistics()
        if stats:
            st.sidebar.markdown("### 📈 Aperçu Rapide")
            st.sidebar.metric("Total Fiches", stats.get('total_fiches', 0))
            st.sidebar.metric("Taux Qualification", f"{stats.get('qualified_rate', 0):.1f}%")
            st.sidebar.metric("Complétude Moy.", f"{stats.get('avg_completion', 0):.0f}%")
    except:
        pass
      # Initialisation de la page par défaut dans session_state
    if 'page' not in st.session_state:
        st.session_state.page = "📊 Dashboard"
    
    page = st.sidebar.selectbox(
        "Navigation",
        ["📊 Dashboard", "✏️ Nouvelle Fiche", "📋 Toutes les Fiches", "📈 Analytiques", "🎯 Recommandations"],
        index=["📊 Dashboard", "✏️ Nouvelle Fiche", "📋 Toutes les Fiches", "📈 Analytiques", "🎯 Recommandations"].index(st.session_state.page) if st.session_state.page in ["📊 Dashboard", "✏️ Nouvelle Fiche", "📋 Toutes les Fiches", "📈 Analytiques", "🎯 Recommandations"] else 0
    )
    
    # Synchroniser la sélection avec session_state
    if page != st.session_state.page:
        st.session_state.page = page
        st.rerun()
    
    # Options avancées
    with st.sidebar.expander("⚙️ Options Avancées"):
        if st.button("💾 Sauvegarder BDD"):
            try:
                backup_path = backup_database(db.db_path)
                st.success(f"Sauvegarde créée: {backup_path}")
            except Exception as e:
                st.error(f"Erreur sauvegarde: {str(e)}")
        
        # Export global
        if st.button("📤 Export CSV Global"):
            fiches_df = db.get_all_fiches(include_stats=True)
            if not fiches_df.empty:
                csv_data = export_to_csv(fiches_df)
                st.download_button(
                    label="Télécharger CSV",
                    data=csv_data,
                    file_name=f"meddic_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"                )
    
    # Navigation vers les pages
    if st.session_state.page == "📊 Dashboard":
        show_dashboard(db)
    elif st.session_state.page == "✏️ Nouvelle Fiche":
        show_fiche_form(db)
    elif st.session_state.page == "📋 Toutes les Fiches":
        show_all_fiches(db)
    elif st.session_state.page == "📈 Analytiques":
        show_analytics(db)
    elif st.session_state.page == "🎯 Recommandations":
        show_recommendations_page(db)

def show_dashboard(db):
    """Affiche le dashboard principal amélioré"""
    st.title("📊 Dashboard MEDDIC")
    
    # Récupération des données avec statistiques
    fiches_df = db.get_all_fiches(include_stats=True)
    
    if fiches_df.empty:
        st.info("🚀 Bienvenue dans MEDDIC CRM ! Commencez par créer votre première fiche.")
        
        # Bouton d'action rapide
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("✏️ Créer ma première fiche MEDDIC", type="primary"):
                st.session_state.page = "✏️ Nouvelle Fiche"
                st.rerun()
        return
    
    # Métriques principales avec design amélioré
    st.markdown("### 📈 Métriques Clés")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_fiches = len(fiches_df)
        st.markdown("""
        <div class="metric-container">
            <h3 style="margin:0; color:#1f77b4;">Total Fiches</h3>
            <h1 style="margin:0;">{}</h1>
        </div>
        """.format(total_fiches), unsafe_allow_html=True)
    
    with col2:
        qualified = len(fiches_df[fiches_df['status'] == 'Qualifié'])
        qualified_rate = (qualified / total_fiches * 100) if total_fiches > 0 else 0
        color = "#32CD32" if qualified_rate > 50 else "#FFA500" if qualified_rate > 25 else "#FF6347"
        st.markdown(f"""
        <div class="metric-container">
            <h3 style="margin:0; color:{color};">Qualifiées</h3>
            <h1 style="margin:0;">{qualified}</h1>
            <p style="margin:0; color:gray;">{qualified_rate:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        in_progress = len(fiches_df[fiches_df['status'] == 'En cours'])
        st.markdown(f"""
        <div class="metric-container">
            <h3 style="margin:0; color:#FFA500;">En Cours</h3>
            <h1 style="margin:0;">{in_progress}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        avg_completion = fiches_df['completion_score'].mean() if 'completion_score' in fiches_df.columns else 0
        color = "#32CD32" if avg_completion > 75 else "#FFA500" if avg_completion > 50 else "#FF6347"
        st.markdown(f"""
        <div class="metric-container">
            <h3 style="margin:0; color:{color};">Complétude</h3>
            <h1 style="margin:0;">{avg_completion:.0f}%</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        complete_fiches = len(fiches_df[fiches_df['completion_score'] == 100]) if 'completion_score' in fiches_df.columns else 0
        st.markdown(f"""
        <div class="metric-container">
            <h3 style="margin:0; color:#1f77b4;">Complètes</h3>
            <h1 style="margin:0;">{complete_fiches}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Section graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Répartition par Statut")
        status_counts = fiches_df['status'].value_counts()
        colors = [get_status_color(status) for status in status_counts.index]
        
        fig_pie = px.pie(
            values=status_counts.values, 
            names=status_counts.index,
            color_discrete_sequence=colors,
            title="Distribution des statuts"
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Score de Complétude")
        if 'completion_score' in fiches_df.columns:
            fig_hist = px.histogram(
                fiches_df, 
                x='completion_score', 
                nbins=10,
                title="Distribution des scores MEDDIC",
                color_discrete_sequence=['#1f77b4']
            )
            fig_hist.update_layout(
                xaxis_title="Score de Complétude (%)",
                yaxis_title="Nombre de Fiches"
            )
            st.plotly_chart(fig_hist, use_container_width=True)
    
    # Fiches prioritaires
    st.subheader("🚨 Fiches Prioritaires")
    priority_fiches = fiches_df[fiches_df.get('priority', 'Moyenne') == 'Haute'].head(5)
    
    if not priority_fiches.empty:
        for _, fiche in priority_fiches.iterrows():
            priority_color = get_priority_color(fiche.get('priority', 'Moyenne'))
            status_color = get_status_color(fiche['status'])
            completion = fiche.get('completion_score', 0)
            
            st.markdown(f"""
            <div class="meddic-card priority-high">
                <h4 style="margin-top:0;">🏢 {fiche['company']} - {fiche['client_name']}</h4>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span class="status-badge" style="background-color: {status_color};">{fiche['status']}</span>
                        <span style="margin-left: 10px;"><b>Commercial:</b> {fiche.get('commercial', 'N/A')}</span>
                    </div>
                    <div class="completion-score" style="color: {get_priority_color('Haute' if completion > 75 else 'Moyenne' if completion > 50 else 'Basse')};">
                        {completion:.0f}% complète
                    </div>
                </div>
                <p style="margin-bottom:0;"><b>Date RDV:</b> {format_date(fiche.get('meeting_date', ''))}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Aucune fiche prioritaire détectée.")
    
    # Barre de recherche améliorée
    st.subheader("🔍 Recherche Rapide")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("Rechercher par entreprise, client, ou contenu...", placeholder="Ex: Microsoft, Jean Dupont, CRM...")
    
    with col2:
        search_button = st.button("🔍 Rechercher", type="primary")
    
    if search_term or search_button:
        if search_term:
            filtered_df = search_fiches(fiches_df, search_term)
            
            if not filtered_df.empty:
                st.success(f"✅ {len(filtered_df)} résultat(s) trouvé(s)")
                
                for _, fiche in filtered_df.head(5).iterrows():  # Limiter à 5 résultats
                    completion_score = fiche.get('completion_score', 0)
                    status_color = get_status_color(fiche['status'])
                    priority = fiche.get('priority', 'Moyenne')
                    priority_color = get_priority_color(priority)
                    
                    # Recommandations rapides
                    recommendations = generate_recommendations(fiche)
                    
                    st.markdown(f"""
                    <div class="meddic-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h4 style="margin:0;">{fiche['company']} - {fiche['client_name']}</h4>
                            <div>
                                <span class="status-badge" style="background-color: {status_color};">{fiche['status']}</span>
                                <span class="status-badge" style="background-color: {priority_color}; margin-left: 5px;">P: {priority}</span>
                            </div>
                        </div>
                        <p><b>Commercial:</b> {fiche.get('commercial', 'N/A')} | <b>Date RDV:</b> {format_date(fiche.get('meeting_date', ''))}</p>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span><b>Complétude:</b> <span style="color: {get_priority_color('Haute' if completion_score > 75 else 'Moyenne' if completion_score > 50 else 'Basse')};">{completion_score:.0f}%</span></span>
                            <span><b>Prochaine action:</b> {recommendations[0] if recommendations else 'Aucune recommandation'}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("❌ Aucun résultat trouvé pour cette recherche.")
    
    # Actions rapides
    st.markdown("---")
    st.subheader("⚡ Actions Rapides")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✏️ Nouvelle Fiche"):
            st.session_state.page = "✏️ Nouvelle Fiche"
            st.rerun()
    
    with col2:
        if st.button("📋 Voir Toutes"):
            st.session_state.page = "📋 Toutes les Fiches"
            st.rerun()
    
    with col3:
        if st.button("📈 Analytiques"):
            st.session_state.page = "📈 Analytiques"
            st.rerun()
    
    with col4:
        if st.button("🎯 Recommandations"):
            st.session_state.page = "🎯 Recommandations"
            st.rerun()

def show_fiche_form(db, fiche_id=None):
    """Affiche le formulaire de création/édition de fiche MEDDIC amélioré"""
    if fiche_id:
        st.title("✏️ Édition Fiche MEDDIC")
    else:
        st.title("✏️ Nouvelle Fiche MEDDIC")
    
    # Récupération des données existantes si édition
    existing_fiche = None
    if fiche_id:
        existing_fiche = db.get_fiche_by_id(fiche_id)
        if existing_fiche:
            st.success(f"📝 Édition de la fiche: {existing_fiche['company']} - {existing_fiche['client_name']}")
            
            # Affichage du score actuel
            current_score = calculate_completion_score(existing_fiche)
            st.info(f"Score de complétude actuel: {current_score:.0f}%")
    
    with st.form("meddic_form", clear_on_submit=False):
        # Section informations générales
        st.markdown("### 👤 Informations Générales")
        
        col1, col2 = st.columns(2)
        with col1:
            client_name = st.text_input(
                "Nom du client *", 
                value=existing_fiche['client_name'] if existing_fiche else "",
                help="Nom et prénom du contact principal"
            )
            company = st.text_input(
                "Entreprise *", 
                value=existing_fiche['company'] if existing_fiche else "",
                help="Nom de l'entreprise cliente"
            )
        
        with col2:
            meeting_date = st.date_input(
                "Date du rendez-vous", 
                value=datetime.strptime(existing_fiche['meeting_date'], '%Y-%m-%d').date() 
                if existing_fiche and existing_fiche['meeting_date'] else date.today(),
                help="Date du rendez-vous ou de la prochaine interaction"
            )
            commercial = st.text_input(
                "Commercial", 
                value=existing_fiche['commercial'] if existing_fiche else "",
                help="Nom du commercial en charge"
            )
        
        status = st.selectbox(
            "Statut de l'opportunité", 
            MEDDIC_STATUS,
            index=MEDDIC_STATUS.index(existing_fiche['status']) if existing_fiche and existing_fiche['status'] in MEDDIC_STATUS else 0,
            help="Statut actuel de l'opportunité commerciale"
        )
        
        st.markdown("---")
        
        # Section MEDDIC avec design amélioré
        st.markdown("### 🎯 Analyse MEDDIC")
        st.markdown("*Complétez chaque section pour maximiser vos chances de succès*")
        
        # Metrics
        st.markdown("#### 📊 M - Metrics")
        st.markdown("*Quels sont les KPIs quantitatifs que le client souhaite améliorer ?*")
        metrics = st.text_area(
            "Metrics",
            value=existing_fiche['metrics'] if existing_fiche else "",
            placeholder=MEDDIC_TEMPLATES['metrics']['placeholder'],
            help=MEDDIC_TEMPLATES['metrics']['help'],
            label_visibility="collapsed",
            height=100
        )
        
        # Economic Buyer
        st.markdown("#### 💰 E - Economic Buyer")
        st.markdown("*Qui a le pouvoir de décision budgétaire ?*")
        economic_buyer = st.text_area(
            "Economic Buyer",
            value=existing_fiche['economic_buyer'] if existing_fiche else "",
            placeholder=MEDDIC_TEMPLATES['economic_buyer']['placeholder'],
            help=MEDDIC_TEMPLATES['economic_buyer']['help'],
            label_visibility="collapsed",
            height=100
        )
        
        # Decision Criteria
        st.markdown("#### 📋 D - Decision Criteria")
        st.markdown("*Quels sont les critères de décision principaux ?*")
        decision_criteria = st.text_area(
            "Decision Criteria",
            value=existing_fiche['decision_criteria'] if existing_fiche else "",
            placeholder=MEDDIC_TEMPLATES['decision_criteria']['placeholder'],
            help=MEDDIC_TEMPLATES['decision_criteria']['help'],
            label_visibility="collapsed",
            height=100
        )
        
        # Decision Process
        st.markdown("#### ⚙️ D - Decision Process")
        st.markdown("*Quel est le processus de décision ? Qui est impliqué ?*")
        decision_process = st.text_area(
            "Decision Process",
            value=existing_fiche['decision_process'] if existing_fiche else "",
            placeholder=MEDDIC_TEMPLATES['decision_process']['placeholder'],
            help=MEDDIC_TEMPLATES['decision_process']['help'],
            label_visibility="collapsed",
            height=100
        )
        
        # Identify Pain
        st.markdown("#### 🎯 I - Identify Pain")
        st.markdown("*Quelles sont les douleurs/problèmes identifiés ?*")
        identify_pain = st.text_area(
            "Identify Pain",
            value=existing_fiche['identify_pain'] if existing_fiche else "",
            placeholder=MEDDIC_TEMPLATES['identify_pain']['placeholder'],
            help=MEDDIC_TEMPLATES['identify_pain']['help'],
            label_visibility="collapsed",
            height=100
        )
        
        # Champion
        st.markdown("#### 🤝 C - Champion")
        st.markdown("*Qui est votre champion interne ? Pourquoi vous soutient-il ?*")
        champion = st.text_area(
            "Champion",
            value=existing_fiche['champion'] if existing_fiche else "",
            placeholder=MEDDIC_TEMPLATES['champion']['placeholder'],
            help=MEDDIC_TEMPLATES['champion']['help'],
            label_visibility="collapsed",
            height=100
        )
        
        # Notes additionnelles
        st.markdown("---")
        st.markdown("#### 📝 Notes Additionnelles")
        notes = st.text_area(
            "Notes libres",
            value=existing_fiche['notes'] if existing_fiche else "",
            placeholder="Observations, prochaines étapes, remarques, concurrents, objections...",
            help="Toute information complémentaire utile pour le suivi",
            height=120
        )
        
        # Calcul du score en temps réel (simulation)
        temp_fiche = {
            'metrics': metrics,
            'economic_buyer': economic_buyer,
            'decision_criteria': decision_criteria,
            'decision_process': decision_process,
            'identify_pain': identify_pain,
            'champion': champion
        }
        current_completion = calculate_completion_score(temp_fiche)
        
        # Affichage du score
        score_color = "#32CD32" if current_completion > 75 else "#FFA500" if current_completion > 50 else "#FF6347"
        st.markdown(f"""
        <div style="background-color: {score_color}20; border: 2px solid {score_color}; border-radius: 10px; padding: 15px; margin: 20px 0;">
            <h3 style="margin: 0; color: {score_color};">Score de Complétude: {current_completion:.0f}%</h3>
            <p style="margin: 5px 0 0 0; color: #666;">
                {6 - int(current_completion / 100 * 6)} champ(s) MEDDIC restant(s) à compléter
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Boutons de soumission
        st.markdown("---")
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
        
        with col2:
            submitted = st.form_submit_button("💾 Sauvegarder", type="primary", use_container_width=True)
        
        with col3:
            if existing_fiche:
                delete_clicked = st.form_submit_button("🗑️ Supprimer", type="secondary", use_container_width=True)
                
                if delete_clicked:
                    # Confirmation de suppression
                    if st.session_state.get('confirm_delete') != existing_fiche['id']:
                        st.session_state.confirm_delete = existing_fiche['id']
                        st.warning("⚠️ Cliquez à nouveau pour confirmer la suppression")
                    else:
                        db.delete_fiche(existing_fiche['id'])
                        st.success("✅ Fiche supprimée avec succès !")
                        del st.session_state.confirm_delete
                        st.session_state.page = "📋 Toutes les Fiches"
                        st.rerun()
        
        # Traitement de la soumission
        if submitted:
            # Validation des champs obligatoires
            if not client_name or not company:
                st.error("❌ Les champs 'Nom du client' et 'Entreprise' sont obligatoires.")
            else:
                # Préparation des données
                fiche_data = {
                    'client_name': client_name.strip(),
                    'company': company.strip(),
                    'meeting_date': meeting_date.strftime('%Y-%m-%d'),
                    'commercial': commercial.strip(),
                    'metrics': metrics.strip(),
                    'economic_buyer': economic_buyer.strip(),
                    'decision_criteria': decision_criteria.strip(),
                    'decision_process': decision_process.strip(),
                    'identify_pain': identify_pain.strip(),
                    'champion': champion.strip(),
                    'status': status,
                    'notes': notes.strip()
                }
                
                if existing_fiche:
                    fiche_data['id'] = existing_fiche['id']
                
                try:
                    # Sauvegarde
                    db.save_fiche(fiche_data)
                    
                    # Messages de succès avec analyse
                    st.success("✅ Fiche sauvegardée avec succès !")
                    
                    final_score = calculate_completion_score(fiche_data)
                    
                    if final_score == 100:
                        st.balloons()
                        st.success("🎉 Excellente qualification MEDDIC complète ! Votre opportunité est prête pour la suite du processus.")
                    elif final_score >= 75:
                        st.info("👍 Bonne qualification ! Quelques détails supplémentaires permettraient d'optimiser votre approche.")
                    elif final_score >= 50:
                        st.warning("⚠️ Qualification partielle. Complétez les champs manquants pour améliorer vos chances de succès.")
                    else:
                        st.error("🔴 Qualification insuffisante. Il est recommandé de compléter davantage d'informations MEDDIC.")
                    
                    # Génération de recommandations
                    recommendations = generate_recommendations(fiche_data)
                    if recommendations:
                        st.markdown("### 🎯 Recommandations")
                        for i, rec in enumerate(recommendations[:3], 1):
                            st.markdown(f"{i}. {rec}")
                    
                    # Auto-redirection après 3 secondes (simulation)
                    time.sleep(1)
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de la sauvegarde: {str(e)}")
        
        # Aide contextuelle
        with st.expander("💡 Aide pour remplir MEDDIC"):
            st.markdown("""
            ### Guide de Qualification MEDDIC
            
            **📊 Metrics:** Soyez spécifique avec des chiffres
            - ❌ "Améliorer l'efficacité"
            - ✅ "Réduire le temps de traitement de 30%, économiser 50k€/an"
            
            **💰 Economic Buyer:** Identifiez le vrai décideur
            - ❌ "Le responsable IT"
            - ✅ "Jean Dupont, CFO, décision finale sur budgets >100k€"
            
            **📋 Decision Criteria:** Listez TOUS les critères
            - Prix, fonctionnalités, support, références, délais...
            
            **⚙️ Decision Process:** Cartographiez le processus
            - Qui, quand, comment, étapes, comités, validations...
            
            **🎯 Identify Pain:** Quantifiez l'impact
            - Coût du problème, urgence, conséquences de l'inaction...
            
            **🤝 Champion:** Trouvez votre allié
            - Qui vous soutient activement et pourquoi ?
            """)
    
    # Liens rapides
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Retour Dashboard"):
            st.session_state.page = "📊 Dashboard"
            st.rerun()
    
    with col2:
        if st.button("📋 Toutes les Fiches"):
            st.session_state.page = "📋 Toutes les Fiches"
            st.rerun()
    
    with col3:
        if existing_fiche:
            pdf_generator = MEDDICPDFGenerator()
            try:
                pdf_data = pdf_generator.generate_fiche_pdf(existing_fiche)
                st.download_button(
                    label="📄 Exporter PDF",
                    data=pdf_data,
                    file_name=f"MEDDIC_{existing_fiche['company']}_{existing_fiche['id']}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Erreur génération PDF: {str(e)}")

def show_all_fiches(db):
    """Affiche toutes les fiches avec options de filtrage"""
    st.title("📋 Toutes les Fiches MEDDIC")
    
    fiches_df = db.get_all_fiches()
    
    if fiches_df.empty:
        st.info("Aucune fiche créée.")
        return
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("Filtrer par statut", 
                                   ["Tous"] + list(fiches_df['status'].unique()))
    
    with col2:
        company_filter = st.selectbox("Filtrer par entreprise", 
                                    ["Toutes"] + list(fiches_df['company'].unique()))
    
    with col3:
        commercial_filter = st.selectbox("Filtrer par commercial", 
                                       ["Tous"] + list(fiches_df['commercial'].unique()))
    
    # Application des filtres
    filtered_df = fiches_df.copy()
    if status_filter != "Tous":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    if company_filter != "Toutes":
        filtered_df = filtered_df[filtered_df['company'] == company_filter]
    if commercial_filter != "Tous":
        filtered_df = filtered_df[filtered_df['commercial'] == commercial_filter]
    
    st.write(f"**{len(filtered_df)}** fiche(s) trouvée(s)")
    
    # Affichage des fiches
    for _, fiche in filtered_df.iterrows():
        completion_score = calculate_completion_score(fiche)
        status_color = get_status_color(fiche['status'])
        
        with st.expander(f"🏢 {fiche['company']} - {fiche['client_name']} ({completion_score:.0f}% complète)"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Commercial:** {fiche['commercial']}")
                st.write(f"**Date RDV:** {fiche['meeting_date']}")
                st.write(f"**Statut:** {fiche['status']}")
                
                if fiche['metrics']:
                    st.markdown("**📊 Metrics:**")
                    st.write(fiche['metrics'][:200] + "..." if len(fiche['metrics']) > 200 else fiche['metrics'])
                
                if fiche['identify_pain']:
                    st.markdown("**🎯 Pain Points:**")
                    st.write(fiche['identify_pain'][:200] + "..." if len(fiche['identify_pain']) > 200 else fiche['identify_pain'])
            
            with col2:
                if st.button(f"✏️ Éditer", key=f"edit_{fiche['id']}"):
                    st.session_state.edit_fiche_id = fiche['id']
                    st.rerun()                # Génération PDF
                pdf_generator = MEDDICPDFGenerator()
                try:
                    # Récupérer les données PDF (maintenant sous forme de bytes)
                    pdf_data = pdf_generator.generate_fiche_pdf(fiche)
                    # Vérifier que le format est correct pour Streamlit
                    if not isinstance(pdf_data, bytes):
                        pdf_data = bytes(pdf_data)
                    st.download_button(
                        label="📄 PDF",
                        data=pdf_data,
                        file_name=f"MEDDIC_{fiche['company']}_{fiche['id']}.pdf",
                        mime="application/pdf",
                        key=f"pdf_{fiche['id']}"
                    )
                except Exception as e:
                    st.error(f"Erreur génération PDF: {str(e)}")
    
    # Redirection vers l'édition
    if 'edit_fiche_id' in st.session_state:
        show_fiche_form(db, st.session_state.edit_fiche_id)
        del st.session_state.edit_fiche_id

def show_analytics(db):
    """Affiche les analytiques et statistiques"""
    st.title("📈 Analytiques MEDDIC")
    
    fiches_df = db.get_all_fiches()
    
    if fiches_df.empty:
        st.info("Aucune donnée disponible pour les analytiques.")
        return
    
    # Calcul des scores de complétude
    fiches_df['completion_score'] = fiches_df.apply(lambda row: calculate_completion_score(row), axis=1)
    
    # Métriques globales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_completion = fiches_df['completion_score'].mean()
        st.metric("Complétude Moyenne", f"{avg_completion:.1f}%")
    
    with col2:
        qualified_rate = (len(fiches_df[fiches_df['status'] == 'Qualifié']) / len(fiches_df)) * 100
        st.metric("Taux de Qualification", f"{qualified_rate:.1f}%")
    
    with col3:
        complete_fiches = len(fiches_df[fiches_df['completion_score'] == 100])
        st.metric("Fiches Complètes", complete_fiches)
    
    with col4:
        unique_companies = fiches_df['company'].nunique()
        st.metric("Entreprises Uniques", unique_companies)
      # Graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribution des Scores de Complétude")
        fig_hist = px.histogram(fiches_df, x='completion_score', nbins=10,
                               title="Répartition des scores de complétude MEDDIC")
        fig_hist.update_layout(
            xaxis_title="Score de Complétude (%)",
            yaxis_title="Nombre de Fiches"
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        st.subheader("Performance par Commercial")
        if 'commercial' in fiches_df.columns and fiches_df['commercial'].notna().any():
            commercial_stats = fiches_df.groupby('commercial').agg({
                'completion_score': 'mean',
                'id': 'count'
            }).round(1)
            commercial_stats.columns = ['Score Moyen', 'Nb Fiches']
            st.dataframe(commercial_stats)
    
    # Évolution temporelle
    st.subheader("Évolution dans le Temps")
    if 'created_at' in fiches_df.columns:
        fiches_df['created_date'] = pd.to_datetime(fiches_df['created_at']).dt.date
        daily_counts = fiches_df.groupby('created_date').size().reset_index(name='count')
        
        fig_line = px.line(daily_counts, x='created_date', y='count',
                          title="Nombre de fiches créées par jour")
        st.plotly_chart(fig_line, use_container_width=True)
    
    # Top des entreprises
    st.subheader("Top Entreprises")
    top_companies = fiches_df['company'].value_counts().head(10)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        fig_bar = px.bar(x=top_companies.index, y=top_companies.values,
                        title="Nombre de fiches par entreprise")
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        st.dataframe(top_companies.reset_index())

def show_recommendations_page(db):
    """Affiche la page des recommandations intelligentes"""
    st.title("🎯 Recommandations MEDDIC")
    
    fiches_df = db.get_all_fiches(include_stats=True)
    
    if fiches_df.empty:
        st.info("Aucune fiche disponible pour générer des recommandations.")
        if st.button("✏️ Créer ma première fiche"):
            st.session_state.page = "✏️ Nouvelle Fiche"
            st.rerun()
        return
    
    # Calcul des scores pour chaque fiche
    fiches_df['completion_score'] = fiches_df.apply(lambda row: calculate_completion_score(row), axis=1)
    fiches_df['priority'] = fiches_df.apply(lambda row: get_priority_level(row), axis=1)
    
    # Métriques globales des recommandations
    st.markdown("### 📊 Vue d'Ensemble des Recommandations")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Fiches à Compléter", len(fiches_df[fiches_df['completion_score'] < 100]), 
                 delta=f"-{100-fiches_df['completion_score'].mean():.0f}% à combler")
    
    with col2:
        st.metric("Priorité Haute", len(fiches_df[fiches_df['priority'] == 'Haute']),
                 delta="Attention requise" if len(fiches_df[fiches_df['priority'] == 'Haute']) > 0 else "Aucune urgence")
    
    with col3:
        st.metric("Fiches Stagnantes", len(fiches_df[fiches_df['status'] == 'En attente']),
                 delta="À relancer" if len(fiches_df[fiches_df['status'] == 'En attente']) > 0 else "Toutes actives")
    
    with col4:
        st.metric("Prêtes à Qualifier", len(fiches_df[(fiches_df['completion_score'] >= 80) & (fiches_df['status'] == 'En cours')]),
                 delta="Proposer démo" if len(fiches_df[(fiches_df['completion_score'] >= 80) & (fiches_df['status'] == 'En cours')]) > 0 else "Continuer qualification")
    
    st.markdown("---")
    
    # Recommandations par catégorie
    tab1, tab2, tab3, tab4 = st.tabs(["🔴 Actions Urgentes", "📈 Optimisations", "💡 Conseils", "📊 Analyses"])
    
    with tab1:
        st.markdown("### 🔴 Actions Urgentes à Réaliser")
        
        urgent_actions = []
        
        # Fiches incomplètes avec haute priorité
        urgent_incomplete = fiches_df[
            (fiches_df['completion_score'] < 50) & 
            (fiches_df['priority'] == 'Haute')
        ]
        
        for _, fiche in urgent_incomplete.iterrows():
            recommendations = generate_recommendations(fiche)
            urgent_actions.extend([{
                'fiche': fiche,
                'type': 'Qualification Urgente',
                'action': rec,
                'priority': 'Critique'
            } for rec in recommendations[:2]])
        
        # Fiches stagnantes
        stagnant = fiches_df[fiches_df['status'] == 'En attente']
        for _, fiche in stagnant.iterrows():
            urgent_actions.append({
                'fiche': fiche,
                'type': 'Relance Client',
                'action': f"⏰ Relancer {fiche['company']} - {fiche['client_name']} (en attente depuis le {format_date(fiche.get('updated_at', ''))})",
                'priority': 'Haute'
            })
        
        # Fiches prêtes à qualifier
        ready_to_qualify = fiches_df[
            (fiches_df['completion_score'] >= 80) & 
            (fiches_df['status'] == 'En cours')
        ]
        
        for _, fiche in ready_to_qualify.iterrows():
            urgent_actions.append({
                'fiche': fiche,
                'type': 'Progression',
                'action': f"✅ Proposer une démonstration à {fiche['company']} (qualification à {fiche['completion_score']:.0f}%)",
                'priority': 'Moyenne'
            })
        
        if urgent_actions:
            for i, action in enumerate(urgent_actions[:10], 1):  # Limiter à 10 actions urgentes
                priority_color = "#FF4B4B" if action['priority'] == 'Critique' else "#FFA500"
                
                st.markdown(f"""
                <div class="meddic-card" style="border-left-color: {priority_color};">
                    <h4 style="margin-top: 0; color: {priority_color};">{i}. {action['type']} - {action['fiche']['company']}</h4>
                    <p style="margin-bottom: 5px;">{action['action']}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span><strong>Commercial:</strong> {action['fiche'].get('commercial', 'N/A')}</span>
                        <span class="status-badge" style="background-color: {priority_color};">{action['priority']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Bouton d'action rapide
                if st.button(f"✏️ Modifier cette fiche", key=f"urgent_{action['fiche']['id']}"):
                    st.session_state.edit_fiche_id = action['fiche']['id']
                    st.rerun()
        else:
            st.success("🎉 Aucune action urgente ! Votre pipeline MEDDIC est bien géré.")
    
    with tab2:
        st.markdown("### 📈 Optimisations Recommandées")
        
        # Analyse des champs MEDDIC les moins remplis
        meddic_fields = ['metrics', 'economic_buyer', 'decision_criteria', 'decision_process', 'identify_pain', 'champion']
        field_completion = {}
        
        for field in meddic_fields:
            filled_count = len(fiches_df[fiches_df[field].notna() & (fiches_df[field].str.strip() != '')])
            field_completion[field] = (filled_count / len(fiches_df)) * 100
        
        st.markdown("#### 📊 Complétude par Champ MEDDIC")
        
        # Graphique des champs les moins remplis
        field_df = pd.DataFrame([
            {'Champ': k.replace('_', ' ').title(), 'Complétude (%)': v}
            for k, v in field_completion.items()
        ])
        
        fig_fields = px.bar(field_df, x='Champ', y='Complétude (%)',
                           title="Complétude par critère MEDDIC",
                           color='Complétude (%)',
                           color_continuous_scale=['red', 'orange', 'green'])
        fig_fields.update_layout(showlegend=False)
        st.plotly_chart(fig_fields, use_container_width=True)
        
        # Recommandations d'amélioration
        worst_fields = sorted(field_completion.items(), key=lambda x: x[1])[:3]
        
        st.markdown("#### 💡 Points d'Amélioration Prioritaires")
        for field, completion in worst_fields:
            field_name = field.replace('_', ' ').title()
            st.markdown(f"""
            **{field_name}** - {completion:.0f}% de complétude
            - Focus formation équipe commerciale sur ce critère
            - Intégrer des questions spécifiques dans les call scripts
            - Prévoir des templates et exemples
            """)
        
        # Analyse par commercial
        if 'commercial' in fiches_df.columns and fiches_df['commercial'].notna().any():
            st.markdown("#### 👥 Performance par Commercial")
            
            commercial_performance = fiches_df.groupby('commercial').agg({
                'completion_score': ['mean', 'count'],
                'status': lambda x: (x == 'Qualifié').sum()
            }).round(1)
            
            commercial_performance.columns = ['Score Moyen', 'Nb Fiches', 'Nb Qualifiées']
            commercial_performance['Taux Qualification'] = (
                commercial_performance['Nb Qualifiées'] / commercial_performance['Nb Fiches'] * 100
            ).round(1)
            
            st.dataframe(commercial_performance)
            
            # Recommandations par commercial
            low_performers = commercial_performance[commercial_performance['Score Moyen'] < 60]
            if not low_performers.empty:
                st.warning("⚠️ Commerciaux nécessitant un accompagnement MEDDIC:")
                for commercial in low_performers.index:
                    score = low_performers.loc[commercial, 'Score Moyen']
                    st.markdown(f"- **{commercial}**: Score moyen {score}% - Formation recommandée")
    
    with tab3:
        st.markdown("### 💡 Conseils et Bonnes Pratiques")
        
        # Conseils basés sur les données
        total_fiches = len(fiches_df)
        avg_completion = fiches_df['completion_score'].mean()
        qualified_rate = (len(fiches_df[fiches_df['status'] == 'Qualifié']) / total_fiches) * 100
        
        st.markdown("#### 🎯 Conseils Personnalisés")
        
        if avg_completion < 60:
            st.markdown("""
            **🔴 Amélioration Urgente de la Qualification**
            - Votre score de complétude moyen est faible ({:.0f}%)
            - Organisez une formation MEDDIC pour l'équipe
            - Utilisez des check-lists pour chaque rendez-vous
            - Planifiez des suivis systématiques post-RDV
            """.format(avg_completion))
        
        elif avg_completion < 80:
            st.markdown("""
            **🟡 Bonne Base, Optimisation Possible**
            - Score correct ({:.0f}%) mais perfectible
            - Focalisez sur les champs les moins remplis
            - Développez des templates de questions
            - Partagez les bonnes pratiques entre commerciaux
            """.format(avg_completion))
        
        else:
            st.markdown("""
            **🟢 Excellente Qualification MEDDIC**
            - Score excellent ({:.0f}%) - Continuez ainsi !
            - Partagez vos méthodes avec d'autres équipes
            - Focus sur l'accélération du cycle de vente
            - Développez des cas d'usage avancés
            """.format(avg_completion))
        
        # Conseils génériques
        st.markdown("#### 📚 Bonnes Pratiques MEDDIC")
        
        tips = [
            "🎯 **Metrics**: Toujours quantifier l'impact business (€, %, temps)",
            "💰 **Economic Buyer**: Valider le budget ET le pouvoir de décision",
            "📋 **Decision Criteria**: Lister TOUS les critères, même les non-dits",
            "⚙️ **Decision Process**: Cartographier qui fait quoi, quand",
            "🔍 **Identify Pain**: Quantifier le coût de l'inaction",
            "🤝 **Champion**: Développer plusieurs champions pour réduire les risques"
        ]
        
        for tip in tips:
            st.markdown(tip)
        
        # Ressources utiles
        with st.expander("📖 Ressources et Templates"):
            st.markdown("""
            #### Questions Types par Critère MEDDIC
            
            **Metrics:**
            - Quels sont vos objectifs chiffrés pour cette année ?
            - Comment mesurez-vous le succès de ce projet ?
            - Quel ROI attendez-vous ?
            
            **Economic Buyer:**
            - Qui valide les investissements de cette ampleur ?
            - Quel est le processus de validation budgétaire ?
            - Qui signe le bon de commande final ?
            
            **Decision Criteria:**
            - Quels sont vos critères de choix prioritaires ?
            - Qu'est-ce qui vous ferait dire NON à une solution ?
            - Y a-t-il des critères non-négociables ?
            
            **Decision Process:**
            - Qui d'autre est impliqué dans cette décision ?
            - Quelles sont les étapes de votre processus ?
            - Quel est votre timeline de décision ?
            
            **Identify Pain:**
            - Quel est l'impact de ce problème sur votre business ?
            - Que se passe-t-il si vous ne faites rien ?
            - Combien cela vous coûte actuellement ?
            
            **Champion:**
            - Qui bénéficierait le plus de cette solution ?
            - Qui pourrait nous soutenir en interne ?
            - Qui d'autre partage cette vision ?
            """)
    
    with tab4:
        st.markdown("### 📊 Analyses Détaillées")
        
        # Analyse de corrélation
        st.markdown("#### 🔗 Analyse de Corrélation")
          # Matrice de corrélation entre complétude et succès
        success_analysis = []
        
        for _, fiche in fiches_df.iterrows():
            success_analysis.append({
                'completion_score': fiche['completion_score'],
                'is_qualified': 1 if fiche['status'] == 'Qualifié' else 0,
                'is_won': 1 if fiche['status'] == 'Fermé - Gagné' else 0,
                'priority_score': 3 if fiche.get('priority') == 'Haute' else 2 if fiche.get('priority') == 'Moyenne' else 1
            })
        
        analysis_df = pd.DataFrame(success_analysis)
        
        if len(analysis_df) > 5:  # Suffisamment de données
            correlation = analysis_df['completion_score'].corr(analysis_df['is_qualified'])
            
            st.metric("Corrélation Complétude ↔ Qualification", f"{correlation:.2f}",
                     help="Plus proche de 1 = forte corrélation positive")
            
            if correlation > 0.6:
                st.success("🎉 Forte corrélation : Une meilleure qualification MEDDIC améliore vos résultats !")
            elif correlation > 0.3:
                st.info("👍 Corrélation modérée : MEDDIC a un impact positif sur vos qualifications.")
            else:
                st.warning("⚠️ Corrélation faible : Analysez d'autres facteurs de succès.")

if __name__ == "__main__":
    main()
