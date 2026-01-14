"""
Administration personnalisée pour Neo4j
Remplace django.contrib.admin pour les données stockées dans Neo4j

Ces vues permettent de gérer les nœuds (CRUD) via une interface web.
"""

from django.views import View
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404
from django.conf import settings
from neomodel import db
import logging

logger = logging.getLogger('base')


def ensure_neo4j_connection():
    """S'assurer que la connexion Neo4j est initialisée"""
    try:
        db.set_connection(settings.NEOMODEL_NEO4J_BOLT_URL)
    except Exception as e:
        logger.warning(f"Neo4j connection init failed: {e}")


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin pour restreindre l'accès aux admins"""
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class NeoAdminDashboardView(AdminRequiredMixin, TemplateView):
    """Dashboard principal de l'admin Neo4j"""
    template_name = 'neo_admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Initialiser la connexion Neo4j
        ensure_neo4j_connection()
        
        try:
            # Statistiques des nœuds
            query = """
            MATCH (n)
            RETURN labels(n)[0] AS label, count(n) AS count
            ORDER BY label
            """
            result, _ = db.cypher_query(query)
            context['node_stats'] = [{'label': r[0], 'count': r[1]} for r in result]
            
            # Statistiques des relations
            query = """
            MATCH ()-[r]->()
            RETURN type(r) AS rel_type, count(r) AS count
            ORDER BY rel_type
            """
            result, _ = db.cypher_query(query)
            context['rel_stats'] = [{'type': r[0], 'count': r[1]} for r in result]
            
            # Totaux
            context['total_nodes'] = sum(s['count'] for s in context['node_stats'])
            context['total_relationships'] = sum(s['count'] for s in context['rel_stats'])
            
        except Exception as e:
            context['error'] = f"Erreur de connexion Neo4j: {e}"
            context['node_stats'] = []
            context['rel_stats'] = []
            
        return context


class NeoUserListView(AdminRequiredMixin, TemplateView):
    """Liste des utilisateurs Neo4j"""
    template_name = 'neo_admin/user_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from base.neo_models import NeoUser
            
            # Pagination simple
            page = int(self.request.GET.get('page', 1))
            per_page = 20
            skip = (page - 1) * per_page
            
            # Récupérer les users
            query = """
            MATCH (u:NeoUser)
            RETURN u
            ORDER BY u.username
            SKIP $skip LIMIT $limit
            """
            result, _ = db.cypher_query(query, {'skip': skip, 'limit': per_page})
            
            users = []
            for row in result:
                node = row[0]
                users.append({
                    'uid': node.get('uid'),
                    'username': node.get('username'),
                    'email': node.get('email'),
                    'role': node.get('role'),
                    'is_active': node.get('is_active', True)
                })
            
            context['users'] = users
            context['page'] = page
            
            # Compter le total
            count_result, _ = db.cypher_query("MATCH (u:NeoUser) RETURN count(u)")
            context['total'] = count_result[0][0] if count_result else 0
            context['has_next'] = context['total'] > page * per_page
            context['has_prev'] = page > 1
            
        except Exception as e:
            context['error'] = f"Erreur: {e}"
            context['users'] = []
            
        return context


class NeoCourseListView(AdminRequiredMixin, TemplateView):
    """Liste des cours Neo4j"""
    template_name = 'neo_admin/course_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            query = """
            MATCH (c:NeoCourse)
            OPTIONAL MATCH (i:NeoUser)-[:TEACHES]->(c)
            OPTIONAL MATCH (s:NeoUser)-[:ENROLLED_IN]->(c)
            RETURN c.uid AS uid, 
                   c.title AS title, 
                   c.level AS level,
                   i.username AS instructor,
                   count(DISTINCT s) AS students
            ORDER BY c.title
            """
            result, _ = db.cypher_query(query)
            
            courses = []
            for row in result:
                courses.append({
                    'uid': row[0],
                    'title': row[1],
                    'level': row[2],
                    'instructor': row[3],
                    'students': row[4]
                })
            
            context['courses'] = courses
            
        except Exception as e:
            context['error'] = f"Erreur: {e}"
            context['courses'] = []
            
        return context


class NeoModuleListView(AdminRequiredMixin, TemplateView):
    """Liste des modules Neo4j"""
    template_name = 'neo_admin/module_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Initialiser la connexion Neo4j
            ensure_neo4j_connection()
            
            query = """
            MATCH (m:NeoModule)
            OPTIONAL MATCH (c:NeoCourse)-[:CONTAINS]->(m)
            OPTIONAL MATCH (m)-[:HAS_RESOURCE]->(r:NeoResource)
            OPTIONAL MATCH (m)-[:HAS_EVALUATION]->(e:NeoEvaluation)
            RETURN m.uid AS uid, 
                   m.title AS title, 
                   m.order AS module_order,
                   c.title AS course,
                   count(DISTINCT r) AS resources,
                   count(DISTINCT e) AS evaluations
            ORDER BY course, module_order
            """
            result, _ = db.cypher_query(query)
            
            modules = []
            for row in result:
                modules.append({
                    'uid': row[0],
                    'title': row[1],
                    'course': row[2],
                    'resources': row[3],
                    'evaluations': row[4]
                })
            
            context['modules'] = modules
            
        except Exception as e:
            context['error'] = f"Erreur: {e}"
            context['modules'] = []
            
        return context


class NeoUserDetailView(AdminRequiredMixin, TemplateView):
    """Détail d'un utilisateur Neo4j"""
    template_name = 'neo_admin/user_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        uid = self.kwargs.get('uid')
        
        try:
            from base.neo_models import NeoUser
            
            # Récupérer l'utilisateur
            query = """
            MATCH (u:NeoUser {uid: $uid})
            OPTIONAL MATCH (u)-[:TEACHES]->(tc:NeoCourse)
            OPTIONAL MATCH (u)-[:ENROLLED_IN]->(ec:NeoCourse)
            RETURN u, collect(DISTINCT tc.title) AS teaches, collect(DISTINCT ec.title) AS enrolled
            """
            result, _ = db.cypher_query(query, {'uid': uid})
            
            if not result:
                raise Http404("Utilisateur non trouvé")
            
            node = result[0][0]
            context['user'] = {
                'uid': node.get('uid'),
                'username': node.get('username'),
                'email': node.get('email'),
                'first_name': node.get('first_name'),
                'last_name': node.get('last_name'),
                'role': node.get('role'),
                'is_active': node.get('is_active'),
                'is_staff': node.get('is_staff'),
                'date_joined': node.get('date_joined')
            }
            context['teaches'] = result[0][1]
            context['enrolled'] = result[0][2]
            
        except Http404:
            raise
        except Exception as e:
            context['error'] = f"Erreur: {e}"
            
        return context


class NeoUserDeleteView(AdminRequiredMixin, View):
    """Supprimer un utilisateur Neo4j"""
    
    def post(self, request, uid):
        try:
            from base.neo_models import NeoUser
            
            neo_user = NeoUser.nodes.get(uid=uid)
            username = neo_user.username
            neo_user.delete()
            
            messages.success(request, f"Utilisateur '{username}' supprimé de Neo4j.")
            logger.info(f"NeoUser deleted: {username}")
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression: {e}")
            
        return redirect('neo-admin-users')


class NeoCourseDeleteView(AdminRequiredMixin, View):
    """Supprimer un cours Neo4j"""
    
    def post(self, request, uid):
        try:
            from base.neo_models import NeoCourse
            
            course = NeoCourse.nodes.get(uid=uid)
            title = course.title
            course.delete()
            
            messages.success(request, f"Cours '{title}' supprimé de Neo4j.")
            logger.info(f"NeoCourse deleted: {title}")
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression: {e}")
            
        return redirect('neo-admin-courses')


class NeoSyncView(AdminRequiredMixin, View):
    """Synchroniser manuellement les Users Django vers Neo4j"""
    
    def post(self, request):
        try:
            from django.contrib.auth import get_user_model
            from base.neo_models import NeoUser
            
            User = get_user_model()
            synced = 0
            
            for user in User.objects.all():
                try:
                    NeoUser.get_or_create_from_django_user(user)
                    synced += 1
                except Exception as e:
                    logger.warning(f"Sync failed for {user.username}: {e}")
            
            messages.success(request, f"{synced} utilisateurs synchronisés vers Neo4j.")
            
        except Exception as e:
            messages.error(request, f"Erreur: {e}")
            
        return redirect('neo-admin-dashboard')
