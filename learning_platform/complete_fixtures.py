# Script temporaire pour compléter les fixtures
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning_platform.settings')
django.setup()

from base.models import *
from datetime import date
import random

print("Création des progressions et certificats...")

progs = 0
certs = 0

# Créer progressions pour 20 inscriptions aléatoires
enrollments = list(Enrollment.objects.all())
random.shuffle(enrollments)

for e in enrollments[:20]:
    modules = list(e.course.modules.all())
    for m in modules:
        Progress.objects.update_or_create(
            enrollment=e, 
            module=m, 
            defaults={'is_completed': True, 'completion_percent': 100}
        )
        progs += 1
    
    # Créer certificat
    if modules:
        cert_num = f"CERT-{e.id:04d}"
        Certificate.objects.get_or_create(
            student=e.student, 
            course=e.course, 
            defaults={
                'certificate_number': cert_num, 
                'issued_on': date.today()
            }
        )
        certs += 1

print(f"Progressions créées: {progs}")
print(f"Certificats créés: {certs}")
print(f"Total certificats: {Certificate.objects.count()}")
