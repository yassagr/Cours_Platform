"""
Validators personnalisés pour la validation des fichiers
"""
from django.core.exceptions import ValidationError
import os


def validate_file_size(file, max_size_mb=10):
    """Valide que le fichier ne dépasse pas max_size_mb"""
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"La taille du fichier ne doit pas dépasser {max_size_mb} MB.")


def validate_file_extension(file, allowed_extensions):
    """Valide l'extension du fichier"""
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f"Extension non autorisée. Extensions valides : {', '.join(allowed_extensions)}"
        )


def validate_resource_file(file):
    """Validation spécifique pour les ressources pédagogiques"""
    validate_file_size(file, max_size_mb=50)  # 50 MB pour vidéos
    allowed = ['.pdf', '.mp4', '.mp3', '.pptx', '.ppt', '.docx', '.doc', '.zip', '.jpg', '.jpeg', '.png', '.gif']
    validate_file_extension(file, allowed)


def validate_submission_file(file):
    """Validation pour les soumissions de devoirs"""
    validate_file_size(file, max_size_mb=10)
    allowed = ['.pdf', '.doc', '.docx', '.txt', '.zip', '.rar', '.py', '.java', '.cpp', '.c', '.js', '.html', '.css']
    validate_file_extension(file, allowed)


def validate_course_image(file):
    """Validation pour les images de cours"""
    validate_file_size(file, max_size_mb=5)
    allowed = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    validate_file_extension(file, allowed)
