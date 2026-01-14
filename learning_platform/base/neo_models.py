"""
Modèles Neo4j pour EduSphere LMS
Utilise Neomodel pour mapper les nœuds et relations du graphe

Ce fichier remplace l'utilisation de Django ORM pour les données métier.
L'authentification reste dans SQLite (auth_user), synchronisée via signals.
"""

from neomodel import (
    StructuredNode, StructuredRel, StringProperty, IntegerProperty,
    DateTimeProperty, DateProperty, FloatProperty, BooleanProperty,
    RelationshipTo, RelationshipFrom, Relationship,
    UniqueIdProperty, JSONProperty
)
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime
import logging

logger = logging.getLogger('base')


# =====================================================
# RELATIONS (Relationships) - Définies en premier
# =====================================================

class EnrollmentRel(StructuredRel):
    """Relation ENROLLED_IN entre User et Course"""
    enrolled_on = DateProperty(default=lambda: datetime.now().date())
    certified = BooleanProperty(default=False)
    completion_percent = FloatProperty(default=0.0)
    last_accessed = DateTimeProperty(default_now=True)


class SubmissionRel(StructuredRel):
    """Relation SUBMITTED entre User et Evaluation"""
    submitted_on = DateTimeProperty(default_now=True)
    score = FloatProperty()
    max_score = FloatProperty()
    percentage = FloatProperty()
    passed = BooleanProperty(default=False)
    attempt_number = IntegerProperty(default=1)
    status = StringProperty(default='pending')  # pending, graded, late
    instructor_comment = StringProperty()
    file_path = StringProperty()


class ResourceViewRel(StructuredRel):
    """Relation VIEWED entre User et Resource"""
    viewed_on = DateTimeProperty(default_now=True)


class AnswerRel(StructuredRel):
    """Relation ANSWERED entre User et Question"""
    selected_option = StringProperty()
    is_correct = BooleanProperty(default=False)
    points_earned = FloatProperty(default=0.0)
    answered = BooleanProperty(default=False)
    submission_uid = StringProperty()  # Pour lier à une soumission spécifique


class SkillMasteryRel(StructuredRel):
    """Relation MASTERED entre User et Skill"""
    level = IntegerProperty(default=1)
    acquired_on = DateTimeProperty(default_now=True)


class ModuleOrderRel(StructuredRel):
    """Relation CONTAINS entre Course et Module"""
    order = IntegerProperty(default=0)


class ResourceOrderRel(StructuredRel):
    """Relation HAS_RESOURCE entre Module et Resource"""
    order = IntegerProperty(default=0)


class SimilarityRel(StructuredRel):
    """Relation SIMILAR_TO entre Course et Course"""
    similarity_score = FloatProperty()
    calculated_at = DateTimeProperty(default_now=True)


# =====================================================
# NŒUDS (Nodes)
# =====================================================

class NeoUser(StructuredNode):
    """
    Nœud User - Représente un utilisateur dans le graphe
    Synchronisé avec Django auth_user via username
    """
    uid = UniqueIdProperty()
    username = StringProperty(unique_index=True, required=True)
    email = StringProperty(unique_index=True, required=True)
    first_name = StringProperty(default='')
    last_name = StringProperty(default='')
    role = StringProperty(default='Student')  # Student, Instructor, Admin
    
    # Dates
    date_joined = DateTimeProperty(default_now=True)
    last_login = DateTimeProperty()
    
    # Status (synchronisé depuis Django)
    is_active = BooleanProperty(default=True)
    is_staff = BooleanProperty(default=False)
    
    # Relations sortantes
    teaches = RelationshipTo('NeoCourse', 'TEACHES')
    enrolled_in = RelationshipTo('NeoCourse', 'ENROLLED_IN', model=EnrollmentRel)
    submitted = RelationshipTo('NeoEvaluation', 'SUBMITTED', model=SubmissionRel)
    viewed = RelationshipTo('NeoResource', 'VIEWED', model=ResourceViewRel)
    answered = RelationshipTo('NeoQuestion', 'ANSWERED', model=AnswerRel)
    mastered = RelationshipTo('NeoSkill', 'MASTERED', model=SkillMasteryRel)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    @classmethod
    def get_or_create_from_django_user(cls, django_user):
        """Crée ou met à jour un NeoUser depuis un User Django"""
        try:
            neo_user = cls.nodes.get(username=django_user.username)
            # Mise à jour
            neo_user.email = django_user.email
            neo_user.first_name = django_user.first_name
            neo_user.last_name = django_user.last_name
            neo_user.is_active = django_user.is_active
            neo_user.is_staff = django_user.is_staff
            if hasattr(django_user, 'role'):
                neo_user.role = django_user.role
            neo_user.save()
            return neo_user, False
        except cls.DoesNotExist:
            # Création
            neo_user = cls(
                username=django_user.username,
                email=django_user.email,
                first_name=django_user.first_name,
                last_name=django_user.last_name,
                is_active=django_user.is_active,
                is_staff=django_user.is_staff,
                role=getattr(django_user, 'role', 'Student'),
                date_joined=django_user.date_joined
            ).save()
            return neo_user, True


class NeoCourse(StructuredNode):
    """Nœud Course - Représente un cours"""
    uid = UniqueIdProperty()
    title = StringProperty(required=True)
    description = StringProperty()
    level = StringProperty(default='Beginner')  # Beginner, Intermediate, Advanced
    estimated_duration = IntegerProperty(default=1)
    start_date = DateProperty()
    end_date = DateProperty()
    image_path = StringProperty()  # Chemin vers l'image
    
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)
    
    # Relations
    instructor = RelationshipFrom('NeoUser', 'TEACHES')
    students = RelationshipFrom('NeoUser', 'ENROLLED_IN', model=EnrollmentRel)
    modules = RelationshipTo('NeoModule', 'CONTAINS', model=ModuleOrderRel)
    teaches_skills = RelationshipTo('NeoSkill', 'TEACHES')
    similar_to = RelationshipTo('NeoCourse', 'SIMILAR_TO', model=SimilarityRel)
    
    def get_instructor(self):
        """Retourne l'instructeur du cours"""
        instructors = self.instructor.all()
        return instructors[0] if instructors else None
    
    def get_modules_ordered(self):
        """Retourne les modules triés par ordre"""
        modules_with_order = []
        for module in self.modules.all():
            rel = self.modules.relationship(module)
            modules_with_order.append((rel.order if rel else 0, module))
        modules_with_order.sort(key=lambda x: x[0])
        return [m for _, m in modules_with_order]
    
    def __str__(self):
        return self.title


class NeoModule(StructuredNode):
    """Nœud Module - Représente un module de cours"""
    uid = UniqueIdProperty()
    title = StringProperty(required=True)
    description = StringProperty()
    order = IntegerProperty(default=0)
    
    created_at = DateTimeProperty(default_now=True)
    
    # Relations
    course = RelationshipFrom('NeoCourse', 'CONTAINS')
    resources = RelationshipTo('NeoResource', 'HAS_RESOURCE', model=ResourceOrderRel)
    evaluations = RelationshipTo('NeoEvaluation', 'HAS_EVALUATION')
    
    def get_course(self):
        """Retourne le cours parent"""
        courses = self.course.all()
        return courses[0] if courses else None
    
    def get_resources_ordered(self):
        """Retourne les ressources triées"""
        resources_with_order = []
        for resource in self.resources.all():
            rel = self.resources.relationship(resource)
            resources_with_order.append((rel.order if rel else 0, resource))
        resources_with_order.sort(key=lambda x: x[0])
        return [r for _, r in resources_with_order]
    
    def __str__(self):
        return self.title


class NeoResource(StructuredNode):
    """Nœud Resource - Représente une ressource pédagogique"""
    uid = UniqueIdProperty()
    title = StringProperty(required=True)
    resource_type = StringProperty(default='fichier')  # video, pdf, image, fichier
    url = StringProperty()  # URL externe
    file_path = StringProperty()  # Chemin fichier local
    
    created_at = DateTimeProperty(default_now=True)
    
    # Relations
    module = RelationshipFrom('NeoModule', 'HAS_RESOURCE')
    viewed_by = RelationshipFrom('NeoUser', 'VIEWED', model=ResourceViewRel)
    
    def get_module(self):
        """Retourne le module parent"""
        modules = self.module.all()
        return modules[0] if modules else None
    
    def __str__(self):
        return self.title


class NeoEvaluation(StructuredNode):
    """Nœud Evaluation - Quiz ou Assignment"""
    uid = UniqueIdProperty()
    title = StringProperty(required=True)
    description = StringProperty()
    evaluation_type = StringProperty(default='Quiz')  # Quiz, Assignment
    deadline = DateProperty()
    
    # Configuration
    max_score = IntegerProperty(default=100)
    passing_score = IntegerProperty(default=60)
    allow_retake = BooleanProperty(default=False)
    max_attempts = IntegerProperty(default=1)
    show_correct_answers = BooleanProperty(default=True)
    time_limit_minutes = IntegerProperty()
    
    created_at = DateTimeProperty(default_now=True)
    
    # Relations
    module = RelationshipFrom('NeoModule', 'HAS_EVALUATION')
    questions = RelationshipTo('NeoQuestion', 'HAS_QUESTION')
    submissions = RelationshipFrom('NeoUser', 'SUBMITTED', model=SubmissionRel)
    
    def get_module(self):
        """Retourne le module parent"""
        modules = self.module.all()
        return modules[0] if modules else None
    
    def get_questions_ordered(self):
        """Retourne les questions triées par ordre"""
        questions = list(self.questions.all())
        questions.sort(key=lambda q: q.order)
        return questions
    
    def __str__(self):
        return self.title


class NeoQuestion(StructuredNode):
    """Nœud Question - Question de quiz"""
    uid = UniqueIdProperty()
    text = StringProperty(required=True)
    option1 = StringProperty(required=True)
    option2 = StringProperty(required=True)
    option3 = StringProperty(required=True)
    option4 = StringProperty(required=True)
    correct_option = StringProperty(required=True)  # A, B, C, D
    points = FloatProperty(default=1.0)
    order = IntegerProperty(default=0)
    
    # Relations
    evaluation = RelationshipFrom('NeoEvaluation', 'HAS_QUESTION')
    answered_by = RelationshipFrom('NeoUser', 'ANSWERED', model=AnswerRel)
    
    def get_evaluation(self):
        """Retourne l'évaluation parente"""
        evaluations = self.evaluation.all()
        return evaluations[0] if evaluations else None
    
    def __str__(self):
        return self.text[:50]


class NeoSkill(StructuredNode):
    """Nœud Skill - Compétence (pour recommandations)"""
    uid = UniqueIdProperty()
    name = StringProperty(unique_index=True, required=True)
    category = StringProperty()
    description = StringProperty()
    
    # Relations
    taught_by = RelationshipFrom('NeoCourse', 'TEACHES')
    mastered_by = RelationshipFrom('NeoUser', 'MASTERED', model=SkillMasteryRel)
    
    def __str__(self):
        return self.name


class NeoNotification(StructuredNode):
    """Nœud Notification - Notifications utilisateur"""
    uid = UniqueIdProperty()
    message = StringProperty(required=True)
    notification_type = StringProperty(default='info')  # info, success, warning, error
    is_read = BooleanProperty(default=False)
    created_at = DateTimeProperty(default_now=True)
    link = StringProperty()
    
    # Relations
    recipient = RelationshipFrom('NeoUser', 'HAS_NOTIFICATION')
    
    def __str__(self):
        return self.message[:50]


class NeoCertificate(StructuredNode):
    """Nœud Certificate - Certificat de complétion"""
    uid = UniqueIdProperty()
    issued_on = DateTimeProperty(default_now=True)
    certificate_id = StringProperty(unique_index=True)
    
    # Relations
    student = RelationshipFrom('NeoUser', 'EARNED')
    course = RelationshipFrom('NeoCourse', 'GRANTS')
    
    def __str__(self):
        return f"Certificate {self.certificate_id}"


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def get_neo_user(request):
    """
    Helper pour récupérer le NeoUser correspondant au user Django authentifié.
    À utiliser dans les views.
    
    Usage:
        neo_user = get_neo_user(request)
        if neo_user:
            enrolled_courses = neo_user.enrolled_in.all()
    """
    if request.user.is_authenticated:
        try:
            return NeoUser.nodes.get(username=request.user.username)
        except NeoUser.DoesNotExist:
            # Créer le NeoUser s'il n'existe pas (cas rare après migration)
            neo_user, created = NeoUser.get_or_create_from_django_user(request.user)
            if created:
                logger.info(f"NeoUser créé automatiquement pour {request.user.username}")
            return neo_user
    return None


def sync_django_user_to_neo4j(django_user):
    """
    Synchronise un User Django vers Neo4j.
    Appelé par les signals.
    """
    try:
        neo_user, created = NeoUser.get_or_create_from_django_user(django_user)
        action = "créé" if created else "mis à jour"
        logger.info(f"NeoUser {action}: {django_user.username}")
        return neo_user
    except Exception as e:
        logger.error(f"Erreur sync NeoUser {django_user.username}: {e}")
        return None
