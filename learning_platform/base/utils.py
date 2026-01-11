"""
Utilitaires pour la génération de certificats PDF
Avec gestion d'erreurs robuste et logging
"""
import os
import logging
from io import BytesIO
from datetime import date
from django.conf import settings

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Logger pour ce module
logger = logging.getLogger(__name__)


def generate_certificate_pdf(certificate):
    """
    Génère un certificat PDF élégant et moderne avec gestion d'erreurs
    
    Args:
        certificate: Instance du modèle Certificate
        
    Returns:
        BytesIO: Buffer contenant le PDF généré
    """
    try:
        buffer = BytesIO()
        
        # Page en paysage pour un look plus professionnel
        page_width, page_height = landscape(A4)
        c = canvas.Canvas(buffer, pagesize=landscape(A4))
        
        # Couleurs du thème EduSphere
        primary_color = HexColor('#1e40af')  # Bleu foncé
        accent_color = HexColor('#3b82f6')   # Bleu accent
        gold_color = HexColor('#f59e0b')     # Or pour le titre
        dark_bg = HexColor('#0f172a')        # Fond sombre
        light_text = HexColor('#e2e8f0')     # Texte clair
        
        # Fond dégradé (simulé avec rectangles)
        c.setFillColor(dark_bg)
        c.rect(0, 0, page_width, page_height, fill=True, stroke=False)
        
        # Bordure décorative
        c.setStrokeColor(accent_color)
        c.setLineWidth(3)
        c.roundRect(30, 30, page_width - 60, page_height - 60, 20, stroke=True, fill=False)
        
        # Bordure intérieure
        c.setStrokeColor(primary_color)
        c.setLineWidth(1)
        c.roundRect(45, 45, page_width - 90, page_height - 90, 15, stroke=True, fill=False)
        
        # En-tête avec logo textuel
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(page_width / 2, page_height - 80, "EDUSPHERE")
        
        # Titre principal
        c.setFillColor(gold_color)
        c.setFont("Helvetica-Bold", 42)
        c.drawCentredString(page_width / 2, page_height - 140, "CERTIFICAT DE RÉUSSITE")
        
        # Ligne décorative
        c.setStrokeColor(gold_color)
        c.setLineWidth(2)
        c.line(page_width / 2 - 150, page_height - 160, page_width / 2 + 150, page_height - 160)
        
        # Texte de certification
        c.setFillColor(light_text)
        c.setFont("Helvetica", 16)
        c.drawCentredString(page_width / 2, page_height - 200, "Ce certificat atteste que")
        
        # Nom de l'étudiant
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 32)
        student_name = f"{certificate.student.first_name} {certificate.student.last_name}".strip()
        if not student_name:
            student_name = certificate.student.username
        c.drawCentredString(page_width / 2, page_height - 250, student_name)
        
        # Ligne sous le nom
        c.setStrokeColor(accent_color)
        c.setLineWidth(1)
        c.line(page_width / 2 - 200, page_height - 265, page_width / 2 + 200, page_height - 265)
        
        # Texte intermédiaire
        c.setFillColor(light_text)
        c.setFont("Helvetica", 16)
        c.drawCentredString(page_width / 2, page_height - 300, "a complété avec succès le cours")
        
        # Nom du cours
        c.setFillColor(accent_color)
        c.setFont("Helvetica-Bold", 28)
        course_title = certificate.course.title
        # Tronquer si trop long
        if len(course_title) > 50:
            course_title = course_title[:47] + "..."
        c.drawCentredString(page_width / 2, page_height - 345, course_title)
        
        # Informations du cours
        c.setFillColor(light_text)
        c.setFont("Helvetica", 12)
        course_info = f"Niveau: {certificate.course.level} | Durée: {certificate.course.estimated_duration}h"
        c.drawCentredString(page_width / 2, page_height - 375, course_info)
        
        # Date d'émission
        c.setFont("Helvetica", 14)
        date_text = f"Délivré le {certificate.issued_on.strftime('%d %B %Y')}"
        c.drawCentredString(page_width / 2, page_height - 420, date_text)
        
        # Numéro de certificat
        c.setFillColor(HexColor('#64748b'))
        c.setFont("Helvetica", 10)
        c.drawCentredString(page_width / 2, page_height - 445, f"N° {certificate.certificate_number}")
        
        # Instructeur (signature)
        c.setFillColor(light_text)
        c.setFont("Helvetica", 12)
        c.drawCentredString(page_width / 2, 100, "Instructeur")
        
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 16)
        instructor_name = f"{certificate.course.instructor.first_name} {certificate.course.instructor.last_name}".strip()
        if not instructor_name:
            instructor_name = certificate.course.instructor.username
        c.drawCentredString(page_width / 2, 80, instructor_name)
        
        # Ligne de signature
        c.setStrokeColor(light_text)
        c.setLineWidth(1)
        c.line(page_width / 2 - 100, 95, page_width / 2 + 100, 95)
        
        # Éléments décoratifs dans les coins
        c.setFillColor(accent_color)
        c.circle(70, page_height - 70, 8, fill=True, stroke=False)
        c.setFillColor(gold_color)
        c.circle(70, page_height - 70, 4, fill=True, stroke=False)
        
        c.setFillColor(accent_color)
        c.circle(page_width - 70, page_height - 70, 8, fill=True, stroke=False)
        c.setFillColor(gold_color)
        c.circle(page_width - 70, page_height - 70, 4, fill=True, stroke=False)
        
        c.setFillColor(accent_color)
        c.circle(70, 70, 8, fill=True, stroke=False)
        c.setFillColor(gold_color)
        c.circle(70, 70, 4, fill=True, stroke=False)
        
        c.setFillColor(accent_color)
        c.circle(page_width - 70, 70, 8, fill=True, stroke=False)
        c.setFillColor(gold_color)
        c.circle(page_width - 70, 70, 4, fill=True, stroke=False)
        
        # Finaliser le PDF
        c.save()
        buffer.seek(0)
        
        logger.info(f"Certificat généré avec succès: {certificate.certificate_number}")
        return buffer
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du certificat {certificate.id}: {str(e)}", exc_info=True)
        
        # Générer un certificat de secours basique
        return generate_fallback_certificate(certificate)


def generate_fallback_certificate(certificate):
    """
    Génère un certificat basique en cas d'erreur avec le certificat principal
    """
    logger.warning(f"Génération du certificat de secours pour {certificate.id}")
    
    buffer = BytesIO()
    page_width, page_height = A4
    c = canvas.Canvas(buffer, pagesize=A4)
    
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(page_width / 2, page_height - 100, "CERTIFICAT DE RÉUSSITE")
    
    c.setFont("Helvetica", 14)
    c.drawCentredString(page_width / 2, page_height - 180, "Ce certificat atteste que")
    
    c.setFont("Helvetica-Bold", 18)
    student_name = f"{certificate.student.first_name} {certificate.student.last_name}".strip()
    if not student_name:
        student_name = certificate.student.username
    c.drawCentredString(page_width / 2, page_height - 220, student_name)
    
    c.setFont("Helvetica", 14)
    c.drawCentredString(page_width / 2, page_height - 280, "a complété avec succès le cours")
    
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(page_width / 2, page_height - 320, certificate.course.title)
    
    c.setFont("Helvetica", 12)
    c.drawCentredString(page_width / 2, page_height - 400, f"Date: {certificate.issued_on}")
    c.drawCentredString(page_width / 2, page_height - 430, f"N° {certificate.certificate_number}")
    
    c.save()
    buffer.seek(0)
    
    return buffer


def save_certificate_to_file(certificate):
    """
    Génère et sauvegarde le certificat dans le système de fichiers
    
    Args:
        certificate: Instance du modèle Certificate
        
    Returns:
        str: Chemin relatif du fichier sauvegardé
    """
    try:
        # Générer le PDF
        pdf_buffer = generate_certificate_pdf(certificate)
        
        # Créer le répertoire si nécessaire
        certificates_dir = os.path.join(settings.MEDIA_ROOT, 'certificates')
        os.makedirs(certificates_dir, exist_ok=True)
        
        # Nom du fichier
        filename = f"certificate_{certificate.certificate_number}.pdf"
        filepath = os.path.join(certificates_dir, filename)
        
        # Sauvegarder le fichier
        with open(filepath, 'wb') as f:
            f.write(pdf_buffer.read())
        
        logger.info(f"Certificat sauvegardé: {filepath}")
        
        # Retourner le chemin relatif pour le champ FileField
        return f"certificates/{filename}"
        
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du certificat: {str(e)}", exc_info=True)
        raise
