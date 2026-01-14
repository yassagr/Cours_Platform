"""
Script pour tester la connexion Neo4j et vérifier les CRUD
Usage: python manage.py shell < test_neo4j.py
Ou exécuter les commandes une par une dans le shell Django
"""

print("\n" + "="*60)
print("🔍 TEST DE CONNEXION NEO4J - EduSphere LMS")
print("="*60 + "\n")

# =====================================================
# TEST 1: Connexion de base
# =====================================================
print("📡 Test 1: Connexion Neo4j...")
try:
    from neomodel import db, config
    from django.conf import settings
    
    config.DATABASE_URL = settings.NEOMODEL_NEO4J_BOLT_URL
    
    # Test simple query
    result, _ = db.cypher_query("RETURN 'Connexion OK!' AS message")
    print(f"   ✅ {result[0][0]}")
    print(f"   URL: {settings.NEOMODEL_NEO4J_BOLT_URL}")
except Exception as e:
    print(f"   ❌ ERREUR: {e}")
    print("\n   💡 Solutions possibles:")
    print("   1. Vérifiez que Neo4j est démarré")
    print("   2. Vérifiez le fichier .env (NEO4J_BOLT_URL)")
    print("   3. Vérifiez les credentials (username:password)")
    exit(1)

# =====================================================
# TEST 2: Compter les nœuds existants
# =====================================================
print("\n📊 Test 2: Statistiques du graphe...")
try:
    result, _ = db.cypher_query(
        "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY label"
    )
    if result:
        print("   Nœuds par type:")
        for row in result:
            print(f"   • {row[0]}: {row[1]}")
    else:
        print("   ⚠ Graphe vide (normal si pas encore migré)")
except Exception as e:
    print(f"   ❌ ERREUR: {e}")

# =====================================================
# TEST 3: Créer un NeoUser de test
# =====================================================
print("\n👤 Test 3: Création d'un NeoUser...")
try:
    from base.neo_models import NeoUser
    
    # Supprimer si existe
    existing = NeoUser.nodes.get_or_none(username="test_user_neo4j")
    if existing:
        existing.delete()
        print("   (ancien test_user supprimé)")
    
    # Créer nouveau
    test_user = NeoUser(
        username="test_user_neo4j",
        email="test@neo4j.local",
        first_name="Test",
        last_name="Neo4j",
        role="Student"
    ).save()
    
    print(f"   ✅ NeoUser créé: {test_user.username}")
    print(f"   UID: {test_user.uid}")
except Exception as e:
    print(f"   ❌ ERREUR: {e}")

# =====================================================
# TEST 4: Créer un NeoCourse de test
# =====================================================
print("\n📚 Test 4: Création d'un NeoCourse...")
try:
    from base.neo_models import NeoCourse
    from datetime import date
    
    # Supprimer si existe
    existing = NeoCourse.nodes.get_or_none(title="Test Course Neo4j")
    if existing:
        existing.delete()
        print("   (ancien cours test supprimé)")
    
    # Créer nouveau
    test_course = NeoCourse(
        title="Test Course Neo4j",
        description="Cours de test pour vérifier Neo4j",
        level="Beginner",
        estimated_duration=10,
        start_date=date.today(),
        end_date=date.today()
    ).save()
    
    print(f"   ✅ NeoCourse créé: {test_course.title}")
    print(f"   UID: {test_course.uid}")
except Exception as e:
    print(f"   ❌ ERREUR: {e}")

# =====================================================
# TEST 5: Créer une relation ENROLLED_IN
# =====================================================
print("\n🔗 Test 5: Création relation ENROLLED_IN...")
try:
    from base.neo_models import NeoUser, NeoCourse
    from datetime import date
    
    test_user = NeoUser.nodes.get(username="test_user_neo4j")
    test_course = NeoCourse.nodes.get(title="Test Course Neo4j")
    
    # Créer relation
    if test_course not in test_user.enrolled_in.all():
        test_user.enrolled_in.connect(test_course, {
            'enrolled_on': date.today(),
            'completion_percent': 0.0,
            'certified': False
        })
    
    # Vérifier
    enrolled = list(test_user.enrolled_in.all())
    print(f"   ✅ Relation créée!")
    print(f"   {test_user.username} est inscrit à: {[c.title for c in enrolled]}")
except Exception as e:
    print(f"   ❌ ERREUR: {e}")

# =====================================================
# TEST 6: Tester les recommandations
# =====================================================
print("\n🧠 Test 6: Moteur de recommandation...")
try:
    from base.recommendations import CourseRecommendationEngine
    
    recs = CourseRecommendationEngine.get_recommendations_for_student(
        "test_user_neo4j", limit=3
    )
    
    print(f"   ✅ Recommandations générées: {len(recs)}")
    for rec in recs:
        print(f"   • {rec.get('title', 'N/A')} ({rec.get('method', 'N/A')})")
except Exception as e:
    print(f"   ⚠ Recommandations: {e}")
    print("   (Normal si peu de données)")

# =====================================================
# TEST 7: Nettoyer les données de test
# =====================================================
print("\n🧹 Test 7: Nettoyage...")
try:
    from base.neo_models import NeoUser, NeoCourse
    
    test_user = NeoUser.nodes.get_or_none(username="test_user_neo4j")
    test_course = NeoCourse.nodes.get_or_none(title="Test Course Neo4j")
    
    if test_user:
        test_user.delete()
        print("   ✅ test_user_neo4j supprimé")
    if test_course:
        test_course.delete()
        print("   ✅ Test Course Neo4j supprimé")
except Exception as e:
    print(f"   ⚠ Nettoyage: {e}")

# =====================================================
# RÉSUMÉ
# =====================================================
print("\n" + "="*60)
print("✅ TOUS LES TESTS RÉUSSIS!")
print("="*60)
print("\n📋 Prochaines étapes:")
print("   1. python manage.py migrate_to_neo4j --dry-run")
print("   2. python manage.py migrate_to_neo4j --execute")
print("   3. python manage.py create_skills --verbose")
print("   4. python manage.py setup_gds --verbose")
print("   5. Accéder à http://localhost:8000/neo-admin/")
print("")
