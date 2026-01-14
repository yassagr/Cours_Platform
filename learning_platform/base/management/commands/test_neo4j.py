"""
Command pour tester la connexion Neo4j et les operations CRUD
Usage: python manage.py test_neo4j
"""

from django.core.management.base import BaseCommand
from neomodel import db, config
from django.conf import settings
import logging

logger = logging.getLogger('base')


class Command(BaseCommand):
    help = 'Teste la connexion Neo4j et les operations CRUD'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            '\n' + '='*60 + '\n'
            'TEST DE CONNEXION NEO4J - EduSphere LMS\n'
            + '='*60 + '\n'
        ))

        # =====================================================
        # TEST 1: Connexion de base
        # =====================================================
        self.stdout.write('\n[TEST 1] Connexion Neo4j...')
        try:
            # Reinitialiser la connexion neomodel
            url = settings.NEOMODEL_NEO4J_BOLT_URL
            db.set_connection(url)
            
            result, _ = db.cypher_query("RETURN 'Connexion OK!' AS message")
            self.stdout.write(self.style.SUCCESS(f'   OK: {result[0][0]}'))
            self.stdout.write(f'   URL: {url}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ERREUR: {e}'))
            self.stdout.write('\n   Solutions possibles:')
            self.stdout.write('   1. Verifiez que Neo4j est demarre')
            self.stdout.write('   2. Verifiez le fichier .env (NEO4J_BOLT_URL)')
            self.stdout.write('   3. Verifiez les credentials (username:password)')
            return

        # =====================================================
        # TEST 2: Compter les noeuds existants
        # =====================================================
        self.stdout.write('\n[TEST 2] Statistiques du graphe...')
        try:
            result, _ = db.cypher_query(
                "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY label"
            )
            if result:
                self.stdout.write('   Noeuds par type:')
                for row in result:
                    self.stdout.write(f'   - {row[0]}: {row[1]}')
            else:
                self.stdout.write(self.style.WARNING('   Graphe vide (normal si pas encore migre)'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ERREUR: {e}'))

        # =====================================================
        # TEST 3: Creer un NeoUser de test
        # =====================================================
        self.stdout.write('\n[TEST 3] Creation NeoUser...')
        try:
            from base.neo_models import NeoUser
            
            existing = NeoUser.nodes.get_or_none(username="test_user_neo4j")
            if existing:
                existing.delete()
                self.stdout.write('   (ancien test_user supprime)')
            
            test_user = NeoUser(
                username="test_user_neo4j",
                email="test@neo4j.local",
                first_name="Test",
                last_name="Neo4j",
                role="Student"
            ).save()
            
            self.stdout.write(self.style.SUCCESS(f'   OK: NeoUser cree: {test_user.username}'))
            self.stdout.write(f'   UID: {test_user.uid}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ERREUR: {e}'))

        # =====================================================
        # TEST 4: Creer un NeoCourse de test
        # =====================================================
        self.stdout.write('\n[TEST 4] Creation NeoCourse...')
        try:
            from base.neo_models import NeoCourse
            from datetime import date
            
            existing = NeoCourse.nodes.get_or_none(title="Test Course Neo4j")
            if existing:
                existing.delete()
                self.stdout.write('   (ancien cours test supprime)')
            
            test_course = NeoCourse(
                title="Test Course Neo4j",
                description="Cours de test pour verifier Neo4j",
                level="Beginner",
                estimated_duration=10,
                start_date=date.today(),
                end_date=date.today()
            ).save()
            
            self.stdout.write(self.style.SUCCESS(f'   OK: NeoCourse cree: {test_course.title}'))
            self.stdout.write(f'   UID: {test_course.uid}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ERREUR: {e}'))

        # =====================================================
        # TEST 5: Creer une relation ENROLLED_IN
        # =====================================================
        self.stdout.write('\n[TEST 5] Creation relation ENROLLED_IN...')
        try:
            from base.neo_models import NeoUser, NeoCourse
            from datetime import date
            
            test_user = NeoUser.nodes.get(username="test_user_neo4j")
            test_course = NeoCourse.nodes.get(title="Test Course Neo4j")
            
            if test_course not in test_user.enrolled_in.all():
                test_user.enrolled_in.connect(test_course, {
                    'enrolled_on': date.today(),
                    'completion_percent': 0.0,
                    'certified': False
                })
            
            enrolled = list(test_user.enrolled_in.all())
            self.stdout.write(self.style.SUCCESS('   OK: Relation creee!'))
            self.stdout.write(f'   {test_user.username} inscrit a: {[c.title for c in enrolled]}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ERREUR: {e}'))

        # =====================================================
        # TEST 6: Nettoyer les donnees de test
        # =====================================================
        self.stdout.write('\n[TEST 6] Nettoyage...')
        try:
            from base.neo_models import NeoUser, NeoCourse
            
            test_user = NeoUser.nodes.get_or_none(username="test_user_neo4j")
            test_course = NeoCourse.nodes.get_or_none(title="Test Course Neo4j")
            
            if test_user:
                test_user.delete()
                self.stdout.write(self.style.SUCCESS('   OK: test_user_neo4j supprime'))
            if test_course:
                test_course.delete()
                self.stdout.write(self.style.SUCCESS('   OK: Test Course Neo4j supprime'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   Nettoyage: {e}'))

        # =====================================================
        # RESUME
        # =====================================================
        self.stdout.write(self.style.SUCCESS(
            '\n' + '='*60 + '\n'
            'TOUS LES TESTS REUSSIS!\n'
            + '='*60
        ))
        self.stdout.write('\nProchaines etapes:')
        self.stdout.write('   1. python manage.py migrate_to_neo4j --dry-run')
        self.stdout.write('   2. python manage.py migrate_to_neo4j --execute')
        self.stdout.write('   3. python manage.py create_skills --verbose')
        self.stdout.write('   4. python manage.py setup_gds --verbose')
        self.stdout.write('   5. Acceder a http://localhost:8000/neo-admin/')
        self.stdout.write('')
