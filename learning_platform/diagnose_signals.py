# Script de diagnostic corrigé
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'learning_platform.settings'
django.setup()

print("="*60)
print("TEST: Création et synchronisation Neo4j")
print("="*60)

# 1. Connexion
from neomodel import db
from django.conf import settings
db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
print("\n✅ Connexion Neo4j OK")

# 2. Test création Question
from base.models import Evaluation, Question

eval = Evaluation.objects.first()
if eval:
    print(f"\n📝 Création d'une question test...")
    q = Question.objects.create(
        evaluation=eval,
        text="TEST SIGNAL - Question diagnostique",
        option1="Option A",
        option2="Option B", 
        option3="Option C",
        option4="Option D",
        correct_option="A",
        points=1
    )
    print(f"   ✅ Question créée dans Django: ID={q.id}")
    
    # Vérifier dans Neo4j
    from base.neo_models import NeoQuestion
    neo_q = NeoQuestion.nodes.filter(text__contains="TEST SIGNAL").first()
    if neo_q:
        print(f"   ✅ Question SYNCHRONISÉE dans Neo4j!")
        print(f"   📍 Neo4j UID: {neo_q.uid}")
    else:
        print(f"   ❌ Question NON trouvée dans Neo4j")
    
    # Nettoyer
    q.delete()
    if neo_q:
        neo_q.delete()
    print("   🧹 Nettoyage OK")
else:
    print("⚠ Pas d'évaluation trouvée")

# 3. Compter les éléments
print("\n📊 Statistiques Neo4j:")
result, _ = db.cypher_query("MATCH (n) RETURN labels(n)[0] as type, count(*) as count ORDER BY count DESC")
for row in result:
    print(f"   {row[0]}: {row[1]}")

print("\n" + "="*60)
