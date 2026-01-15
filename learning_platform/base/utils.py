"""
Utilitaires pour la génération de certificats PDF
Design professionnel style Coursera avec palette EduSphere
Avec gestion d'erreurs robuste et logging détaillé
"""
import os
import logging
from io import BytesIO
from datetime import date

from django.conf import settings

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Logger pour ce module
logger = logging.getLogger(__name__)

# =====================================================
# PALETTE DE COULEURS EDUSPHERE
# =====================================================
PRIMARY_DARK = '#312B1E'      # Titres, texte principal
ACCENT_GREEN = '#A7AA63'      # Accents, bordures principales
BACKGROUND = '#EAE6D2'        # Fond principal
LIGHT_BG = '#F2EFE4'          # Fond secondaire
BORDER_SUBTLE = '#C5B8A8'     # Bordures subtiles
TEXT_SECONDARY = '#505039'    # Texte secondaire
TEXT_MUTED = '#7C6B51'        # Texte discret


def draw_decorative_corners(c, page_width, page_height, color):
    """
    Dessine des motifs géométriques décoratifs dans les coins
    """
    logger.debug("Dessin des coins décoratifs")
    
    corner_offset = 60
    
    # Fonction helper pour un coin
    def draw_corner_pattern(x, y, color):
        c.setStrokeColor(color)
        c.setLineWidth(1)
        # Cercles concentriques
        for radius in [12, 8, 4]:
            c.circle(x, y, radius, stroke=True, fill=False)
    
    # 4 coins
    draw_corner_pattern(corner_offset, page_height - corner_offset, HexColor(ACCENT_GREEN))
    draw_corner_pattern(page_width - corner_offset, page_height - corner_offset, HexColor(ACCENT_GREEN))
    draw_corner_pattern(corner_offset, corner_offset, HexColor(ACCENT_GREEN))
    draw_corner_pattern(page_width - corner_offset, corner_offset, HexColor(ACCENT_GREEN))


def draw_signature_line(c, x, y, width):
    """
    Dessine une ligne de signature élégante style manuscrit
    """
    c.setStrokeColor(HexColor(TEXT_MUTED))
    c.setLineWidth(0.5)
    c.line(x - width/2, y, x + width/2, y)


def generate_certificate_pdf(certificate):
    """
    Génère un certificat PDF élégant style Coursera avec palette EduSphere
    
    Design:
    - Format A4 paysage
    - Fond dégradé subtil crème
    - Double bordure décorative verte/beige
    - Motifs géométriques dans les coins
    - Typography professionnelle
    
    Args:
        certificate: Instance du modèle Certificate
        
    Returns:
        BytesIO: Buffer contenant le PDF généré
    """
    logger.info(f"Début génération certificat: {certificate.certificate_number}")
    
    try:
        buffer = BytesIO()
        
        # Page en paysage A4
        page_width, page_height = landscape(A4)
        c = canvas.Canvas(buffer, pagesize=landscape(A4))
        
        logger.info("Canvas créé - Format A4 paysage")
        
        # =====================================================
        # FOND - Dégradé subtil de BACKGROUND à LIGHT_BG
        # =====================================================
        logger.debug("Dessin du fond")
        
        # Fond principal crème
        c.setFillColor(HexColor(BACKGROUND))
        c.rect(0, 0, page_width, page_height, fill=True, stroke=False)
        
        # Dégradé simulé avec rectangles (plus clair vers le centre)
        c.setFillColor(HexColor(LIGHT_BG))
        c.roundRect(80, 80, page_width - 160, page_height - 160, 30, fill=True, stroke=False)
        
        # =====================================================
        # WATERMARK - Logo EduSphere en filigrane
        # =====================================================
        logger.debug("Dessin du watermark")
        c.saveState()
        c.setFillColor(HexColor(PRIMARY_DARK))
        c.setFillAlpha(0.03)  # Très transparent
        c.setFont("Helvetica-Bold", 120)
        c.drawCentredString(page_width / 2, page_height / 2 - 30, "EduSphere")
        c.restoreState()
        
        # =====================================================
        # BORDURES DÉCORATIVES
        # =====================================================
        logger.debug("Dessin des bordures")
        
        # Bordure externe - verte (#A7AA63), 3px
        c.setStrokeColor(HexColor(ACCENT_GREEN))
        c.setLineWidth(3)
        c.roundRect(40, 40, page_width - 80, page_height - 80, 20, stroke=True, fill=False)
        
        # Bordure interne - beige (#C5B8A8), 1px, 15px d'espacement
        c.setStrokeColor(HexColor(BORDER_SUBTLE))
        c.setLineWidth(1)
        c.roundRect(55, 55, page_width - 110, page_height - 110, 15, stroke=True, fill=False)
        
        # =====================================================
        # COINS DÉCORATIFS
        # =====================================================
        draw_decorative_corners(c, page_width, page_height, ACCENT_GREEN)
        
        # =====================================================
        # HEADER - Logo EduSphere (Top 15%)
        # =====================================================
        logger.debug("Dessin du header")
        
        c.setFillColor(HexColor(ACCENT_GREEN))
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(page_width / 2, page_height - 75, "EduSphere")
        
        # Icône de graduation (simulée avec texte)
        c.setFont("Helvetica", 14)
        c.drawCentredString(page_width / 2, page_height - 95, "🎓")
        
        # =====================================================
        # TITRE PRINCIPAL - "CERTIFICAT DE RÉUSSITE"
        # =====================================================
        logger.debug("Dessin du titre")
        
        c.setFillColor(HexColor(PRIMARY_DARK))
        c.setFont("Helvetica-Bold", 48)
        c.drawCentredString(page_width / 2, page_height - 150, "CERTIFICAT DE RÉUSSITE")
        
        # Ligne décorative dorée sous le titre
        c.setStrokeColor(HexColor(ACCENT_GREEN))
        c.setLineWidth(2)
        c.line(page_width / 2 - 150, page_height - 170, page_width / 2 + 150, page_height - 170)
        
        # =====================================================
        # CORPS DU CERTIFICAT
        # =====================================================
        logger.debug("Dessin du corps")
        
        # Texte introductif
        c.setFillColor(HexColor(TEXT_SECONDARY))
        c.setFont("Helvetica", 16)
        c.drawCentredString(page_width / 2, page_height - 210, "Certifie que")
        
        # Nom de l'étudiant
        c.setFillColor(HexColor(PRIMARY_DARK))
        c.setFont("Helvetica-Bold", 36)
        
        student_name = ""
        try:
            student_name = f"{certificate.student.first_name} {certificate.student.last_name}".strip()
        except:
            pass
        if not student_name:
            try:
                student_name = certificate.student.username
            except:
                student_name = "Étudiant"
        
        c.drawCentredString(page_width / 2, page_height - 260, student_name)
        
        # Ligne élégante sous le nom (style signature)
        draw_signature_line(c, page_width / 2, page_height - 275, 350)
        
        # Texte intermédiaire
        c.setFillColor(HexColor(TEXT_SECONDARY))
        c.setFont("Helvetica", 16)
        c.drawCentredString(page_width / 2, page_height - 310, "a complété avec succès le cours")
        
        # Titre du cours - en vert accent
        c.setFillColor(HexColor(ACCENT_GREEN))
        c.setFont("Helvetica-Bold", 28)
        
        course_title = ""
        try:
            course_title = certificate.course.title
            if len(course_title) > 50:
                course_title = course_title[:47] + "..."
        except:
            course_title = "Cours"
        
        c.drawCentredString(page_width / 2, page_height - 355, course_title)
        
        # Informations du cours
        c.setFillColor(HexColor(TEXT_MUTED))
        c.setFont("Helvetica", 12)
        
        course_level = "Beginner"
        course_duration = "10"
        try:
            course_level = certificate.course.level or "Beginner"
            course_duration = str(certificate.course.estimated_duration or 10)
        except:
            pass
        
        course_info = f"Niveau: {course_level} | Durée: {course_duration}h"
        c.drawCentredString(page_width / 2, page_height - 380, course_info)
        
        # =====================================================
        # FOOTER - Date, Signature, Numéro
        # =====================================================
        logger.debug("Dessin du footer")
        
        # Date d'émission - formatée en français
        c.setFillColor(HexColor(PRIMARY_DARK))
        c.setFont("Helvetica", 14)
        
        issued_date = date.today()
        try:
            issued_date = certificate.issued_on
        except:
            pass
        
        # Mois en français
        mois_fr = {
            1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril',
            5: 'mai', 6: 'juin', 7: 'juillet', 8: 'août',
            9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
        }
        mois = mois_fr.get(issued_date.month, 'janvier')
        date_text = f"Délivré le {issued_date.day} {mois} {issued_date.year}"
        c.drawCentredString(page_width / 2, page_height - 420, date_text)
        
        # =====================================================
        # SIGNATURE DE L'INSTRUCTEUR (gauche)
        # =====================================================
        signature_x = page_width / 3
        
        c.setFillColor(HexColor(TEXT_SECONDARY))
        c.setFont("Helvetica", 12)
        c.drawCentredString(signature_x, 115, "Instructeur")
        
        # Ligne de signature
        draw_signature_line(c, signature_x, 95, 180)
        
        # Nom de l'instructeur
        c.setFillColor(HexColor(PRIMARY_DARK))
        c.setFont("Helvetica-Bold", 18)
        
        instructor_name = ""
        try:
            instructor_name = f"{certificate.course.instructor.first_name} {certificate.course.instructor.last_name}".strip()
        except:
            pass
        if not instructor_name:
            try:
                instructor_name = certificate.course.instructor.username
            except:
                instructor_name = "Instructeur"
        
        c.drawCentredString(signature_x, 72, instructor_name)
        
        # =====================================================
        # SCEAU / BADGE DE VÉRIFICATION (centre-droit)
        # =====================================================
        badge_x = page_width * 2 / 3
        
        # Cercle de vérification
        c.setFillColor(HexColor(ACCENT_GREEN))
        c.circle(badge_x, 85, 25, fill=True, stroke=False)
        
        c.setFillColor(HexColor(LIGHT_BG))
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(badge_x, 80, "✓")
        
        c.setFillColor(HexColor(TEXT_MUTED))
        c.setFont("Helvetica", 10)
        c.drawCentredString(badge_x, 55, "Vérifié")
        
        # =====================================================
        # NUMÉRO DE CERTIFICAT (bas droite)
        # =====================================================
        c.setFillColor(HexColor(TEXT_MUTED))
        c.setFont("Helvetica", 10)
        
        cert_number = "CERT-0000"
        try:
            cert_number = certificate.certificate_number
        except:
            pass
        
        c.drawRightString(page_width - 70, 55, f"N° {cert_number}")
        
        # =====================================================
        # FINALISATION
        # =====================================================
        c.save()
        buffer.seek(0)
        
        logger.info(f"Certificat généré avec succès: {cert_number}")
        return buffer
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du certificat: {str(e)}", exc_info=True)
        
        # Générer un certificat de secours basique
        return generate_fallback_certificate(certificate)


def generate_fallback_certificate(certificate):
    """
    Génère un certificat basique en cas d'erreur avec le certificat principal
    Design simplifié mais toujours avec palette EduSphere
    """
    logger.warning(f"Génération du certificat de secours pour certificat ID: {getattr(certificate, 'id', 'unknown')}")
    
    try:
        buffer = BytesIO()
        page_width, page_height = A4
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Fond crème
        c.setFillColor(HexColor(BACKGROUND))
        c.rect(0, 0, page_width, page_height, fill=True, stroke=False)
        
        # Bordure simple
        c.setStrokeColor(HexColor(ACCENT_GREEN))
        c.setLineWidth(2)
        c.rect(30, 30, page_width - 60, page_height - 60, stroke=True, fill=False)
        
        # Titre
        c.setFillColor(HexColor(PRIMARY_DARK))
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(page_width / 2, page_height - 100, "CERTIFICAT DE RÉUSSITE")
        
        c.setFont("Helvetica", 14)
        c.drawCentredString(page_width / 2, page_height - 180, "Ce certificat atteste que")
        
        c.setFont("Helvetica-Bold", 18)
        student_name = ""
        try:
            student_name = f"{certificate.student.first_name} {certificate.student.last_name}".strip()
            if not student_name:
                student_name = certificate.student.username
        except:
            student_name = "Étudiant"
        c.drawCentredString(page_width / 2, page_height - 220, student_name)
        
        c.setFont("Helvetica", 14)
        c.drawCentredString(page_width / 2, page_height - 280, "a complété avec succès le cours")
        
        c.setFillColor(HexColor(ACCENT_GREEN))
        c.setFont("Helvetica-Bold", 16)
        course_title = ""
        try:
            course_title = certificate.course.title
        except:
            course_title = "Cours"
        c.drawCentredString(page_width / 2, page_height - 320, course_title)
        
        c.setFillColor(HexColor(TEXT_MUTED))
        c.setFont("Helvetica", 12)
        issued_on = ""
        cert_num = ""
        try:
            issued_on = str(certificate.issued_on)
            cert_num = certificate.certificate_number
        except:
            issued_on = str(date.today())
            cert_num = "CERT-FALLBACK"
        c.drawCentredString(page_width / 2, page_height - 400, f"Date: {issued_on}")
        c.drawCentredString(page_width / 2, page_height - 430, f"N° {cert_num}")
        
        c.save()
        buffer.seek(0)
        
        logger.info("Certificat de secours généré avec succès")
        return buffer
        
    except Exception as e:
        logger.error(f"Erreur critique dans le certificat de secours: {str(e)}")
        # Dernier recours: PDF vide
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        c.drawString(100, 700, "Erreur de generation du certificat")
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
    logger.info(f"Sauvegarde du certificat: {certificate.certificate_number}")
    
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
