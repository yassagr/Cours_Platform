# Script pour lier les cours aux skills
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'learning_platform.settings'
django.setup()

from neomodel import db
from django.conf import settings

db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)

print("="*60)
print("LIAISON COURS → SKILLS")
print("="*60)

# Mapping cours → skills
course_skills = {
    'Python pour Débutants': ['Python'],
    'JavaScript Moderne (ES6+)': ['JavaScript', 'HTML/CSS'],
    'Java pour Applications Enterprise': ['Java'],
    'Introduction au Machine Learning': ['Python', 'Machine Learning', 'Pandas', 'Scikit-learn'],
    'Analyse de Données avec Pandas': ['Python', 'Pandas', 'Data Analysis', 'NumPy'],
    'Développement Web Full-Stack avec Django': ['Django', 'Python', 'REST API', 'HTML/CSS', 'SQL'],
    'React.js - De Zéro à Expert': ['React', 'JavaScript', 'HTML/CSS'],
    'Design UI/UX Fondamentaux': ['UI/UX', 'Figma', 'Responsive Design'],
    'Gestion de Projet Agile (Scrum)': ['Agile', 'Scrum', 'Project Management'],
    'Marketing Digital Stratégique': ['Data Analysis', 'Data Visualization'],
}

links_created = 0

for course_title, skills in course_skills.items():
    # Trouver le cours
    result, _ = db.cypher_query(
        "MATCH (c:NeoCourse {title: $title}) RETURN c",
        {'title': course_title}
    )
    
    if not result:
        print(f"❌ Cours non trouvé: {course_title}")
        continue
    
    print(f"\n📚 {course_title}")
    
    for skill_name in skills:
        # Créer la relation
        query = """
        MATCH (c:NeoCourse {title: $course_title})
        MATCH (s:NeoSkill {name: $skill_name})
        MERGE (c)-[r:TEACHES_SKILL]->(s)
        RETURN count(r)
        """
        result, _ = db.cypher_query(query, {
            'course_title': course_title,
            'skill_name': skill_name
        })
        
        if result and result[0][0] > 0:
            print(f"   ✓ {skill_name}")
            links_created += 1
        else:
            print(f"   ⚠ Skill non trouvé: {skill_name}")

print(f"\n✅ {links_created} liaisons créées!")

# Vérifier
result, _ = db.cypher_query("MATCH (:NeoCourse)-[r:TEACHES_SKILL]->(:NeoSkill) RETURN count(r)")
print(f"📊 Total relations TEACHES_SKILL: {result[0][0]}")
