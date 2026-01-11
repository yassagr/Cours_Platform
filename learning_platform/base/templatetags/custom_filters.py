"""
Filtres personnalisés pour les templates Django
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Accéder à un élément de dictionnaire par clé dans un template
    Usage: {{ my_dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def filter_by_student(submissions, student):
    """
    Filtrer les soumissions par étudiant
    Usage: {{ evaluation.submissions.all|filter_by_student:user }}
    """
    return submissions.filter(student=student)


@register.filter
def percentage(value, total):
    """
    Calculer le pourcentage
    Usage: {{ value|percentage:total }}
    """
    try:
        return (float(value) / float(total)) * 100
    except (ValueError, ZeroDivisionError):
        return 0


@register.filter
def subtract(value, arg):
    """
    Soustraire deux valeurs
    Usage: {{ value|subtract:arg }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def multiply(value, arg):
    """
    Multiplier deux valeurs
    Usage: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """
    Diviser deux valeurs
    Usage: {{ value|divide:arg }}
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0


@register.simple_tag
def get_submission_for_student(evaluation, student):
    """
    Récupérer la soumission d'un étudiant pour une évaluation
    Usage: {% get_submission_for_student evaluation user as submission %}
    """
    return evaluation.submissions.filter(student=student).first()
