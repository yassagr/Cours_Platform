# Test distribution recommandations
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'learning_platform.settings'
django.setup()

from base.recommendations import CourseRecommendationEngine
from base.models import User

print("="*60)
print("TEST: Distribution des Recommandations")
print("Attendu: 3 Collaborative, 2 Skill, 1 Popular")
print("="*60)

student = User.objects.filter(role='Student').first()
print(f"\n👤 Étudiant: {student.username}")

# Test direct des algorithmes
print("\n📊 Résultats par algorithme:")

collab = CourseRecommendationEngine._collaborative_filtering(student.username, 10)
print(f"   Collaborative: {len(collab)} résultats")

skill = CourseRecommendationEngine._skill_based_filtering(student.username, 10)
print(f"   Skill: {len(skill)} résultats")

popular = CourseRecommendationEngine._popular_courses(student.username, 10)
print(f"   Popular: {len(popular)} résultats")

# Recommandations finales
recs = CourseRecommendationEngine.get_recommendations_for_student(student.username, limit=6)

print(f"\n🎯 Distribution finale ({len(recs)} recs):")
counts = {}
for r in recs:
    method = r.get('method', 'unknown')
    counts[method] = counts.get(method, 0) + 1
    print(f"   [{method.upper():12}] {r['title'][:40]}")

print(f"\n📈 Comptage:")
print(f"   Collaborative: {counts.get('collaborative', 0)}/3")
print(f"   Skill:         {counts.get('skill', 0)}/2")
print(f"   Popular:       {counts.get('popular', 0)}/1")
