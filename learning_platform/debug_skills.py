# Diagnostic Skills
import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'learning_platform.settings'
django.setup()

from neomodel import db
from django.conf import settings
db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)

print("="*50)
print("DIAGNOSTIC: Relations TEACHES_SKILL")
print("="*50)

# Compter les relations
result, _ = db.cypher_query("MATCH (:NeoCourse)-[r:TEACHES_SKILL]->(:NeoSkill) RETURN count(r)")
print(f"\nRelations TEACHES_SKILL: {result[0][0]}")

# Lister les cours avec skills
result, _ = db.cypher_query("""
    MATCH (c:NeoCourse)-[:TEACHES_SKILL]->(s:NeoSkill)
    RETURN c.title, collect(s.name) as skills
    LIMIT 5
""")
print("\nCours avec Skills:")
for row in result:
    print(f"   {row[0]}: {row[1]}")

if result[0][0] == 0:
    print("\n⚠️ Aucune relation! Il faut recréer les liaisons.")
