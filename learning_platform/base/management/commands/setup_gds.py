"""
Command pour configurer Neo4j Graph Data Science (GDS)
Usage: python manage.py setup_gds

Ce script crée les indexes et prépare le graphe pour les algorithmes de recommandation.
"""

from django.core.management.base import BaseCommand
from neomodel import db, config
from django.conf import settings
import logging

logger = logging.getLogger('base')


class Command(BaseCommand):
    help = 'Configure Neo4j indexes et graph projections pour les recommandations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche les détails'
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*60}\n'
            f'CONFIGURATION NEO4J GDS\n'
            f'{"="*60}\n'
        ))

        # Configurer neomodel
        config.DATABASE_URL = settings.NEOMODEL_NEO4J_BOLT_URL

        try:
            # Étape 1: Créer les indexes
            self.create_indexes(verbose)

            # Étape 2: Compter les entités
            self.count_entities()

            # Étape 3: Créer les constraints
            self.create_constraints(verbose)

            # Étape 4: Créer la projection GDS
            self.create_gds_projection(verbose)

            self.stdout.write(self.style.SUCCESS(
                f'\n{"="*60}\n'
                f'✅ CONFIGURATION TERMINÉE\n'
                f'{"="*60}\n'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ ERREUR: {str(e)}'))
            logger.error(f'GDS setup error: {str(e)}', exc_info=True)
            raise

    def create_indexes(self, verbose):
        """Créer les indexes pour optimiser les requêtes"""
        self.stdout.write('\n🔍 Création des indexes...')
        
        indexes = [
            # Users
            ("NeoUser", "username"),
            ("NeoUser", "email"),
            ("NeoUser", "role"),
            # Courses
            ("NeoCourse", "title"),
            ("NeoCourse", "level"),
            # Modules
            ("NeoModule", "title"),
            # Evaluations
            ("NeoEvaluation", "title"),
            # Skills
            ("NeoSkill", "name"),
        ]
        
        created = 0
        for label, prop in indexes:
            try:
                query = f"CREATE INDEX {label.lower()}_{prop}_idx IF NOT EXISTS FOR (n:{label}) ON (n.{prop})"
                db.cypher_query(query)
                created += 1
                if verbose:
                    self.stdout.write(f'   ✓ Index {label}.{prop}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ Index {label}.{prop}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'✅ {created} indexes créés'))

    def create_constraints(self, verbose):
        """Créer les contraintes d'unicité"""
        self.stdout.write('\n🔒 Création des contraintes...')
        
        constraints = [
            ("NeoUser", "uid"),
            ("NeoUser", "username"),
            ("NeoCourse", "uid"),
            ("NeoModule", "uid"),
            ("NeoResource", "uid"),
            ("NeoEvaluation", "uid"),
            ("NeoQuestion", "uid"),
            ("NeoSkill", "uid"),
        ]
        
        created = 0
        for label, prop in constraints:
            try:
                query = f"CREATE CONSTRAINT {label.lower()}_{prop}_unique IF NOT EXISTS FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
                db.cypher_query(query)
                created += 1
                if verbose:
                    self.stdout.write(f'   ✓ Unique {label}.{prop}')
            except Exception as e:
                # Les contraintes peuvent déjà exister
                if verbose:
                    self.stdout.write(self.style.WARNING(f'   ⚠ Constraint {label}.{prop}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'✅ {created} contraintes créées'))

    def count_entities(self):
        """Afficher un résumé des entités"""
        self.stdout.write('\n📊 État actuel du graphe:')
        
        try:
            # Compter les nœuds
            result, _ = db.cypher_query(
                "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY label"
            )
            
            if result:
                for row in result:
                    self.stdout.write(f'   • {row[0]}: {row[1]}')
            else:
                self.stdout.write('   Aucun nœud (graphe vide)')
                
            # Compter les relations
            result, _ = db.cypher_query(
                "MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count ORDER BY type"
            )
            
            if result:
                self.stdout.write('\n   Relations:')
                for row in result:
                    self.stdout.write(f'   • {row[0]}: {row[1]}')
                    
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   Impossible de compter: {e}'))

    def create_gds_projection(self, verbose):
        """Créer la projection graphe pour GDS (si GDS est installé)"""
        self.stdout.write('\n📊 Configuration de la projection GDS...')
        
        try:
            # Vérifier si GDS est disponible
            try:
                result, _ = db.cypher_query("RETURN gds.version() AS version")
                gds_version = result[0][0] if result else 'unknown'
                self.stdout.write(f'   GDS version: {gds_version}')
            except Exception:
                self.stdout.write(self.style.WARNING(
                    '   ⚠ GDS non détecté - projection ignorée\n'
                    '   Les recommandations utiliseront les requêtes Cypher natives'
                ))
                return
            
            # Supprimer projection existante
            try:
                db.cypher_query("CALL gds.graph.drop('courseGraph', false)")
                if verbose:
                    self.stdout.write('   ✓ Ancienne projection supprimée')
            except Exception:
                pass
            
            # Créer nouvelle projection
            projection_query = """
            CALL gds.graph.project(
                'courseGraph',
                ['NeoUser', 'NeoCourse', 'NeoSkill'],
                {
                    ENROLLED_IN: {
                        type: 'ENROLLED_IN',
                        orientation: 'UNDIRECTED'
                    },
                    TEACHES: {
                        type: 'TEACHES',
                        orientation: 'UNDIRECTED'
                    },
                    SIMILAR_TO: {
                        type: 'SIMILAR_TO',
                        orientation: 'UNDIRECTED'
                    }
                }
            )
            YIELD graphName, nodeCount, relationshipCount
            RETURN graphName, nodeCount, relationshipCount
            """
            
            result, _ = db.cypher_query(projection_query)
            
            if result:
                self.stdout.write(self.style.SUCCESS(
                    f'   ✅ Projection créée: {result[0][0]}'
                ))
                self.stdout.write(f'   • Nœuds: {result[0][1]}')
                self.stdout.write(f'   • Relations: {result[0][2]}')
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f'   ⚠ Projection GDS non créée: {e}\n'
                '   Les recommandations utiliseront les requêtes Cypher natives'
            ))

