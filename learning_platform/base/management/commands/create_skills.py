"""
Command pour créer des compétences (NeoSkill) et les lier aux cours
Usage: python manage.py create_skills
"""

from django.core.management.base import BaseCommand
from neomodel import db, config
from django.conf import settings
import logging

logger = logging.getLogger('base')


class Command(BaseCommand):
    help = 'Créer des compétences (NeoSkill) et les lier aux cours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche les détails'
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        # Configurer neomodel
        config.DATABASE_URL = settings.NEOMODEL_NEO4J_BOLT_URL
        
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*60}\n'
            f'CRÉATION DES COMPÉTENCES (NeoSkill)\n'
            f'{"="*60}\n'
        ))

        try:
            from base.neo_models import NeoSkill, NeoCourse
            
            # Compétences par catégorie
            skills_data = {
                'Programming': [
                    'Python', 'JavaScript', 'Java', 'C++', 'PHP', 
                    'Ruby', 'Go', 'TypeScript', 'Kotlin', 'Swift'
                ],
                'Web Development': [
                    'Django', 'React', 'Vue.js', 'Angular', 'Node.js',
                    'HTML/CSS', 'REST API', 'GraphQL', 'Flask', 'FastAPI'
                ],
                'Data Science': [
                    'Machine Learning', 'Data Analysis', 'Pandas', 'NumPy',
                    'Scikit-learn', 'TensorFlow', 'PyTorch', 'Statistics',
                    'Deep Learning', 'NLP'
                ],
                'Databases': [
                    'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Neo4j',
                    'Redis', 'Elasticsearch', 'SQLite', 'GraphQL'
                ],
                'DevOps': [
                    'Docker', 'Kubernetes', 'CI/CD', 'AWS', 'Azure',
                    'Linux', 'Git', 'Jenkins', 'Terraform', 'Ansible'
                ],
                'Design': [
                    'UI/UX', 'Figma', 'Adobe XD', 'Photoshop',
                    'Responsive Design', 'Accessibility', 'CSS Frameworks'
                ],
                'Business': [
                    'Project Management', 'Agile', 'Scrum', 'Leadership',
                    'Communication', 'Excel', 'PowerBI', 'Data Visualization'
                ]
            }
            
            created_count = 0
            self.stdout.write('\n🎯 Création des compétences...\n')
            
            for category, skill_names in skills_data.items():
                if verbose:
                    self.stdout.write(f'\n📁 {category}:')
                    
                for skill_name in skill_names:
                    try:
                        # Vérifier si existe déjà
                        existing = NeoSkill.nodes.get_or_none(name=skill_name)
                        if not existing:
                            skill = NeoSkill(
                                name=skill_name,
                                category=category,
                                description=f"Compétence en {skill_name}"
                            ).save()
                            created_count += 1
                            if verbose:
                                self.stdout.write(f'   ✓ {skill_name}')
                        elif verbose:
                            self.stdout.write(f'   ○ {skill_name} (existe)')
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'   ⚠ {skill_name}: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ {created_count} compétences créées'))
            
            # Lier aux cours existants
            self.link_skills_to_courses(verbose)
            
            self.stdout.write(self.style.SUCCESS(
                f'\n{"="*60}\n'
                f'✅ CRÉATION TERMINÉE\n'
                f'{"="*60}\n'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ ERREUR: {str(e)}'))
            logger.error(f'Create skills error: {str(e)}', exc_info=True)
            raise

    def link_skills_to_courses(self, verbose):
        """Lier automatiquement des skills aux cours selon le titre/description"""
        from base.neo_models import NeoSkill, NeoCourse
        
        self.stdout.write('\n🔗 Liaison des compétences aux cours...\n')
        
        # Mapping keywords -> skills
        keyword_mapping = {
            'python': ['Python', 'Programming'],
            'django': ['Django', 'Python', 'Web Development', 'REST API'],
            'react': ['React', 'JavaScript', 'Web Development', 'HTML/CSS'],
            'javascript': ['JavaScript', 'Web Development', 'HTML/CSS'],
            'machine learning': ['Machine Learning', 'Python', 'Data Science'],
            'data': ['Data Analysis', 'Python', 'Pandas', 'Statistics'],
            'docker': ['Docker', 'DevOps', 'Linux'],
            'kubernetes': ['Kubernetes', 'Docker', 'DevOps'],
            'sql': ['SQL', 'Databases'],
            'database': ['Databases', 'SQL'],
            'neo4j': ['Neo4j', 'Databases', 'GraphQL'],
            'design': ['UI/UX', 'Figma', 'Design'],
            'web': ['Web Development', 'HTML/CSS'],
            'api': ['REST API', 'Web Development'],
            'java': ['Java', 'Programming'],
            'c++': ['C++', 'Programming'],
            'node': ['Node.js', 'JavaScript', 'Web Development'],
            'vue': ['Vue.js', 'JavaScript', 'Web Development'],
            'angular': ['Angular', 'JavaScript', 'Web Development', 'TypeScript'],
            'aws': ['AWS', 'DevOps', 'Cloud'],
            'azure': ['Azure', 'DevOps', 'Cloud'],
            'git': ['Git', 'DevOps'],
            'linux': ['Linux', 'DevOps'],
            'tensorflow': ['TensorFlow', 'Machine Learning', 'Deep Learning', 'Python'],
            'pytorch': ['PyTorch', 'Machine Learning', 'Deep Learning', 'Python'],
            'excel': ['Excel', 'Business', 'Data Analysis'],
            'agile': ['Agile', 'Scrum', 'Project Management'],
        }
        
        try:
            courses = list(NeoCourse.nodes.all())
            linked_count = 0
            
            for course in courses:
                title_lower = course.title.lower() if course.title else ''
                desc_lower = (course.description or '').lower()
                search_text = f"{title_lower} {desc_lower}"
                
                for keyword, skill_names in keyword_mapping.items():
                    if keyword in search_text:
                        for skill_name in skill_names:
                            try:
                                skill = NeoSkill.nodes.get_or_none(name=skill_name)
                                if skill:
                                    # Vérifier si déjà lié
                                    existing_skills = list(course.teaches_skills.all())
                                    if skill not in existing_skills:
                                        course.teaches_skills.connect(skill)
                                        linked_count += 1
                                        if verbose:
                                            self.stdout.write(f'   ✓ {course.title} → {skill_name}')
                            except Exception as e:
                                if verbose:
                                    self.stdout.write(self.style.WARNING(f'   ⚠ Link error: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ {linked_count} liaisons créées'))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'\n⚠ Erreur liaison: {e}'))
