import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import json
import hashlib
from config import *

def calculate_completion_score(fiche_data):
    """
    Calcule le score de complétude d'une fiche MEDDIC
    
    Args:
        fiche_data (dict): Données de la fiche MEDDIC
        
    Returns:
        float: Score de complétude en pourcentage (0-100)
    """
    completed_fields = 0
    total_fields = len(REQUIRED_MEDDIC_FIELDS)
    
    for field in REQUIRED_MEDDIC_FIELDS:
        if field in fiche_data and fiche_data[field] and str(fiche_data[field]).strip():
            completed_fields += 1
    
    return (completed_fields / total_fields) * 100

def get_status_color(status):
    """
    Retourne la couleur associée à un statut
    
    Args:
        status (str): Statut de la fiche
        
    Returns:
        str: Code couleur hexadécimal
    """
    return STATUS_COLORS.get(status, "#808080")

def format_date(date_str):
    """
    Formate une date pour l'affichage
    
    Args:
        date_str (str): Date au format string
        
    Returns:
        str: Date formatée
    """
    try:
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%d/%m/%Y')
        return date_str
    except:
        return date_str

def get_priority_level(fiche_data):
    """
    Détermine le niveau de priorité d'une fiche basé sur plusieurs critères
    
    Args:
        fiche_data (dict): Données de la fiche
        
    Returns:
        str: Niveau de priorité (Haute, Moyenne, Basse)
    """
    score = 0
    
    # Score basé sur la complétude
    completion = calculate_completion_score(fiche_data)
    if completion >= 80:
        score += 3
    elif completion >= 50:
        score += 2
    else:
        score += 1
    
    # Score basé sur le statut
    if fiche_data.get('status') == 'Qualifié':
        score += 3
    elif fiche_data.get('status') == 'En cours':
        score += 2
    else:
        score += 1
    
    # Score basé sur la date de mise à jour
    if fiche_data.get('updated_at'):
        try:
            last_update = datetime.strptime(fiche_data['updated_at'][:10], '%Y-%m-%d')
            days_since_update = (datetime.now() - last_update).days
            if days_since_update <= 7:
                score += 3
            elif days_since_update <= 30:
                score += 2
            else:
                score += 1
        except:
            score += 1
    
    # Détermination du niveau de priorité
    if score >= 8:
        return "Haute"
    elif score >= 6:
        return "Moyenne"
    else:
        return "Basse"

def get_priority_color(priority):
    """
    Retourne la couleur associée à un niveau de priorité
    
    Args:
        priority (str): Niveau de priorité
        
    Returns:
        str: Code couleur hexadécimal
    """
    colors = {
        "Haute": "#FF4B4B",
        "Moyenne": "#FFA500", 
        "Basse": "#00D4AA"
    }
    return colors.get(priority, "#808080")

def generate_fiche_summary(fiche_data):
    """
    Génère un résumé textuel d'une fiche MEDDIC
    
    Args:
        fiche_data (dict): Données de la fiche
        
    Returns:
        str: Résumé formaté de la fiche
    """
    summary = f"## Résumé MEDDIC - {fiche_data.get('company', 'N/A')}\n\n"
    summary += f"**Client:** {fiche_data.get('client_name', 'N/A')}\n"
    summary += f"**Commercial:** {fiche_data.get('commercial', 'N/A')}\n"
    summary += f"**Date RDV:** {format_date(fiche_data.get('meeting_date', ''))}\n"
    summary += f"**Statut:** {fiche_data.get('status', 'N/A')}\n\n"
    
    completion = calculate_completion_score(fiche_data)
    summary += f"**Score de complétude:** {completion:.0f}%\n\n"
    
    # Sections MEDDIC
    meddic_sections = [
        ("📊 METRICS", fiche_data.get('metrics', '')),
        ("💰 ECONOMIC BUYER", fiche_data.get('economic_buyer', '')),
        ("📋 DECISION CRITERIA", fiche_data.get('decision_criteria', '')),
        ("⚙️ DECISION PROCESS", fiche_data.get('decision_process', '')),
        ("🎯 IDENTIFY PAIN", fiche_data.get('identify_pain', '')),
        ("🤝 CHAMPION", fiche_data.get('champion', ''))
    ]
    
    for title, content in meddic_sections:
        summary += f"### {title}\n"
        if content and content.strip():
            summary += f"{content}\n\n"
        else:
            summary += "*Non renseigné*\n\n"
    
    if fiche_data.get('notes'):
        summary += f"### 📝 NOTES\n{fiche_data['notes']}\n\n"
    
    return summary

def validate_fiche_data(fiche_data):
    """
    Valide les données d'une fiche MEDDIC
    
    Args:
        fiche_data (dict): Données à valider
        
    Returns:
        tuple: (is_valid, errors_list)
    """
    errors = []
    
    # Champs obligatoires
    required_basic_fields = ['client_name', 'company']
    for field in required_basic_fields:
        if not fiche_data.get(field) or not str(fiche_data[field]).strip():
            errors.append(f"Le champ '{field}' est obligatoire")
    
    # Validation de la date
    if fiche_data.get('meeting_date'):
        try:
            if isinstance(fiche_data['meeting_date'], str):
                datetime.strptime(fiche_data['meeting_date'], '%Y-%m-%d')
        except ValueError:
            errors.append("Format de date invalide pour 'meeting_date'")
    
    # Validation du statut
    if fiche_data.get('status') and fiche_data['status'] not in MEDDIC_STATUS:
        errors.append(f"Statut invalide: {fiche_data['status']}")
    
    return len(errors) == 0, errors

def export_to_csv(fiches_df, filename=None):
    """
    Exporte les fiches au format CSV
    
    Args:
        fiches_df (DataFrame): Données à exporter
        filename (str): Nom du fichier (optionnel)
        
    Returns:
        str: Données CSV au format string
    """
    if filename is None:
        filename = f"meddic_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return fiches_df.to_csv(index=False)

def backup_database(db_path, backup_dir="backups"):
    """
    Crée une sauvegarde de la base de données
    
    Args:
        db_path (str): Chemin vers la base de données
        backup_dir (str): Répertoire de sauvegarde
        
    Returns:
        str: Chemin vers le fichier de sauvegarde
    """
    import shutil
    import os
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"meddic_backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    shutil.copy2(db_path, backup_path)
    return backup_path

def search_fiches(fiches_df, search_term):
    """
    Recherche dans les fiches MEDDIC
    
    Args:
        fiches_df (DataFrame): DataFrame des fiches
        search_term (str): Terme de recherche
        
    Returns:
        DataFrame: Fiches correspondant à la recherche
    """
    if not search_term:
        return fiches_df
    
    search_term = search_term.lower()
    
    # Colonnes dans lesquelles chercher
    search_columns = ['company', 'client_name', 'commercial', 'metrics', 
                     'economic_buyer', 'decision_criteria', 'decision_process',
                     'identify_pain', 'champion', 'notes']
    
    mask = pd.Series([False] * len(fiches_df))
    
    for col in search_columns:
        if col in fiches_df.columns:
            mask |= fiches_df[col].astype(str).str.lower().str.contains(search_term, na=False)
    
    return fiches_df[mask]

def get_statistics(fiches_df):
    """
    Calcule des statistiques sur les fiches MEDDIC
    
    Args:
        fiches_df (DataFrame): DataFrame des fiches
        
    Returns:
        dict: Dictionnaire des statistiques
    """
    if fiches_df.empty:
        return {}
    
    # Calcul des scores de complétude
    completion_scores = fiches_df.apply(lambda row: calculate_completion_score(row), axis=1)
    
    stats = {
        'total_fiches': len(fiches_df),
        'avg_completion': completion_scores.mean(),
        'complete_fiches': len(completion_scores[completion_scores == 100]),
        'status_distribution': fiches_df['status'].value_counts().to_dict(),
        'companies_count': fiches_df['company'].nunique(),
        'commercials_count': fiches_df['commercial'].nunique() if 'commercial' in fiches_df.columns else 0,
        'qualified_rate': (len(fiches_df[fiches_df['status'] == 'Qualifié']) / len(fiches_df)) * 100,
        'avg_completion_by_status': fiches_df.groupby('status').apply(
            lambda x: x.apply(lambda row: calculate_completion_score(row), axis=1).mean()
        ).to_dict()
    }
    
    return stats

def generate_recommendations(fiche_data):
    """
    Génère des recommandations basées sur l'analyse de la fiche MEDDIC
    
    Args:
        fiche_data (dict): Données de la fiche
        
    Returns:
        list: Liste des recommandations
    """
    recommendations = []
    completion_score = calculate_completion_score(fiche_data)
    
    # Recommandations basées sur la complétude
    if completion_score < 50:
        recommendations.append("🔴 Priorité haute: Compléter les informations MEDDIC manquantes")
    elif completion_score < 80:
        recommendations.append("🟡 Finaliser la qualification MEDDIC")
    
    # Recommandations spécifiques par champ
    if not fiche_data.get('metrics') or not fiche_data['metrics'].strip():
        recommendations.append("📊 Définir des métriques quantifiables avec le client")
    
    if not fiche_data.get('economic_buyer') or not fiche_data['economic_buyer'].strip():
        recommendations.append("💰 Identifier et qualifier l'Economic Buyer")
    
    if not fiche_data.get('champion') or not fiche_data['champion'].strip():
        recommendations.append("🤝 Développer un Champion interne")
    
    if not fiche_data.get('decision_process') or not fiche_data['decision_process'].strip():
        recommendations.append("⚙️ Cartographier le processus de décision")
    
    # Recommandations basées sur le statut
    if fiche_data.get('status') == 'En cours' and completion_score >= 80:
        recommendations.append("✅ Opportunité bien qualifiée - Proposer une démonstration")
    
    if fiche_data.get('status') == 'En attente':
        recommendations.append("⏰ Relancer le contact et identifier les blocages")
    
    return recommendations

class MEDDICReportGenerator:
    """Générateur de rapports MEDDIC avancés"""
    
    @staticmethod
    def generate_executive_summary(fiches_df):
        """Génère un résumé exécutif des activités MEDDIC"""
        stats = get_statistics(fiches_df)
        
        summary = "# Résumé Exécutif MEDDIC\n\n"
        summary += f"## Vue d'ensemble\n"
        summary += f"- **Total des opportunités:** {stats.get('total_fiches', 0)}\n"
        summary += f"- **Taux de qualification:** {stats.get('qualified_rate', 0):.1f}%\n"
        summary += f"- **Score de complétude moyen:** {stats.get('avg_completion', 0):.1f}%\n"
        summary += f"- **Entreprises uniques:** {stats.get('companies_count', 0)}\n\n"
        
        summary += f"## Répartition par statut\n"
        for status, count in stats.get('status_distribution', {}).items():
            percentage = (count / stats.get('total_fiches', 1)) * 100
            summary += f"- **{status}:** {count} ({percentage:.1f}%)\n"
        
        return summary
