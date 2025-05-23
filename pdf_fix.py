import streamlit as st
from fpdf import FPDF

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
            pdf.set_font('Arial', '', 10)
            
            # Gestion du texte long
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
        
        # Retourner les données PDF sans encoder (fpdf2 retourne déjà un bytearray)
        return pdf.output(dest='S')

# Test de la fonction
if __name__ == "__main__":
    test_data = {
        "company": "Entreprise Test",
        "client_name": "Client Test",
        "commercial": "Commercial Test",
        "meeting_date": "2023-05-01",
        "metrics": "Test metrics\nMultiline",
        "economic_buyer": "Test buyer",
        "decision_criteria": "Test criteria",
        "decision_process": "Test process",
        "identify_pain": "Test pain",
        "champion": "Test champion"
    }
    
    generator = MEDDICPDFGenerator()
    pdf_data = generator.generate_fiche_pdf(test_data)
    print(f"Type de données PDF: {type(pdf_data)}")
    print(f"Taille des données: {len(pdf_data)} octets")
