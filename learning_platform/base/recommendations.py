"""
Moteur de recommandation intelligent basé sur Neo4j
Utilise les algorithmes de graphe pour suggérer des cours pertinents aux étudiants.
"""

from neomodel import db
import logging

logger = logging.getLogger('base')


class CourseRecommendationEngine:
    """
    Moteur de recommandation pour suggérer des cours pertinents.
    
    Algorithmes utilisés:
    1. Filtrage Collaboratif: "Les étudiants qui ont suivi X ont aussi suivi Y"
    2. Filtrage par Contenu: Cours similaires basés sur les compétences
    3. Cours Populaires: Cours avec le plus d'inscriptions
    """
    
    @staticmethod
    def get_recommendations_for_student(username, limit=5):
        """
        Obtenir des recommandations de cours pour un étudiant.
        
        Args:
            username: Le nom d'utilisateur de l'étudiant
            limit: Nombre de recommandations à retourner
            
        Returns:
            Liste de dictionnaires avec les cours recommandés
        """
        try:
            all_recs = []
            
            # Algorithme 1: Filtrage Collaboratif
            collab_recs = CourseRecommendationEngine._collaborative_filtering(
                username, limit
            )
            all_recs.extend(collab_recs)
            
            # Algorithme 2: Cours Populaires (fallback si peu de données)
            if len(all_recs) < limit:
                popular_recs = CourseRecommendationEngine._popular_courses(
                    username, limit
                )
                all_recs.extend(popular_recs)
            
            # Dédupliquer par titre
            seen = set()
            unique_recs = []
            
            for rec in all_recs:
                if rec['title'] not in seen:
                    seen.add(rec['title'])
                    unique_recs.append(rec)
                    if len(unique_recs) >= limit:
                        break
            
            return unique_recs[:limit]
            
        except Exception as e:
            logger.error(f'Recommendation error for {username}: {str(e)}')
            return []
    
    @staticmethod
    def _collaborative_filtering(username, limit):
        """
        Filtrage collaboratif: trouver des cours suivis par des étudiants 
        ayant des intérêts similaires (cours en commun).
        
        Logique:
        1. Trouver les cours que l'étudiant suit
        2. Trouver d'autres étudiants qui suivent ces cours
        3. Recommander les cours que ces étudiants suivent mais pas l'étudiant cible
        """
        query = """
        // Trouver l'étudiant
        MATCH (me:NeoUser {username: $username})-[:ENROLLED_IN]->(my_course:NeoCourse)
        
        // Trouver des étudiants similaires (qui suivent les mêmes cours)
        MATCH (other:NeoUser)-[:ENROLLED_IN]->(my_course)
        WHERE other.username <> $username
        
        // Trouver les cours que ces étudiants suivent mais pas moi
        MATCH (other)-[:ENROLLED_IN]->(rec:NeoCourse)
        WHERE NOT (me)-[:ENROLLED_IN]->(rec)
        
        // Compter combien d'étudiants similaires ont suivi chaque cours
        WITH rec, count(DISTINCT other) AS popularity
        
        // Récupérer l'instructeur
        OPTIONAL MATCH (instructor:NeoUser)-[:TEACHES]->(rec)
        
        RETURN rec.uid AS course_uid,
               rec.title AS title,
               rec.level AS level,
               rec.description AS description,
               rec.image_path AS image_path,
               popularity AS score,
               instructor.username AS instructor,
               'collaborative' AS method
        ORDER BY popularity DESC
        LIMIT $limit
        """
        
        try:
            result, _ = db.cypher_query(query, {
                'username': username,
                'limit': limit
            })
            
            return [
                {
                    'course_uid': row[0],
                    'title': row[1],
                    'level': row[2],
                    'description': row[3][:100] + '...' if row[3] and len(row[3]) > 100 else row[3],
                    'image_path': row[4],
                    'score': row[5],
                    'instructor': row[6],
                    'method': row[7]
                }
                for row in result
            ]
        except Exception as e:
            logger.warning(f'Collaborative filtering failed: {e}')
            return []
    
    @staticmethod
    def _popular_courses(username, limit):
        """
        Cours populaires: cours avec le plus d'inscriptions,
        excluant ceux déjà suivis par l'étudiant.
        """
        query = """
        // Trouver les cours que l'étudiant ne suit pas encore
        MATCH (c:NeoCourse)
        WHERE NOT EXISTS {
            MATCH (me:NeoUser {username: $username})-[:ENROLLED_IN]->(c)
        }
        
        // Compter les inscriptions
        OPTIONAL MATCH (student:NeoUser)-[:ENROLLED_IN]->(c)
        WITH c, count(student) AS enrollments
        
        // Récupérer l'instructeur
        OPTIONAL MATCH (instructor:NeoUser)-[:TEACHES]->(c)
        
        RETURN c.uid AS course_uid,
               c.title AS title,
               c.level AS level,
               c.description AS description,
               c.image_path AS image_path,
               enrollments AS score,
               instructor.username AS instructor,
               'popular' AS method
        ORDER BY enrollments DESC
        LIMIT $limit
        """
        
        try:
            result, _ = db.cypher_query(query, {
                'username': username,
                'limit': limit
            })
            
            return [
                {
                    'course_uid': row[0],
                    'title': row[1],
                    'level': row[2],
                    'description': row[3][:100] + '...' if row[3] and len(row[3]) > 100 else row[3],
                    'image_path': row[4],
                    'score': row[5],
                    'instructor': row[6],
                    'method': row[7]
                }
                for row in result
            ]
        except Exception as e:
            logger.warning(f'Popular courses query failed: {e}')
            return []
    
    @staticmethod
    def get_similar_courses(course_title, limit=3):
        """
        Trouver des cours similaires à un cours donné.
        Basé sur les étudiants communs et les skills enseignés.
        """
        query = """
        MATCH (c:NeoCourse {title: $title})
        
        // Trouver des cours suivis par les mêmes étudiants
        MATCH (c)<-[:ENROLLED_IN]-(student:NeoUser)-[:ENROLLED_IN]->(similar:NeoCourse)
        WHERE similar <> c
        
        WITH similar, count(DISTINCT student) AS common_students
        
        OPTIONAL MATCH (instructor:NeoUser)-[:TEACHES]->(similar)
        
        RETURN similar.uid AS course_uid,
               similar.title AS title,
               similar.level AS level,
               common_students AS similarity_score,
               instructor.username AS instructor
        ORDER BY common_students DESC
        LIMIT $limit
        """
        
        try:
            result, _ = db.cypher_query(query, {
                'title': course_title,
                'limit': limit
            })
            
            return [
                {
                    'course_uid': row[0],
                    'title': row[1],
                    'level': row[2],
                    'similarity_score': row[3],
                    'instructor': row[4]
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f'Similar courses query failed: {e}')
            return []
    
    @staticmethod
    def get_student_stats(username):
        """
        Obtenir les statistiques d'apprentissage d'un étudiant.
        Retourne le nombre de cours, les compétences, la progression, etc.
        """
        query = """
        MATCH (u:NeoUser {username: $username})
        
        // Cours suivis
        OPTIONAL MATCH (u)-[e:ENROLLED_IN]->(c:NeoCourse)
        WITH u, count(c) AS courses_enrolled, 
             avg(e.completion_percent) AS avg_completion
        
        // Évaluations passées
        OPTIONAL MATCH (u)-[s:SUBMITTED]->(eval:NeoEvaluation)
        WHERE s.passed = true
        WITH u, courses_enrolled, avg_completion, count(eval) AS evals_passed
        
        // Ressources vues
        OPTIONAL MATCH (u)-[:VIEWED]->(r:NeoResource)
        
        RETURN courses_enrolled,
               coalesce(avg_completion, 0) AS avg_completion,
               evals_passed,
               count(r) AS resources_viewed
        """
        
        try:
            result, _ = db.cypher_query(query, {'username': username})
            if result:
                row = result[0]
                return {
                    'courses_enrolled': row[0] or 0,
                    'avg_completion': round(row[1] or 0, 1),
                    'evaluations_passed': row[2] or 0,
                    'resources_viewed': row[3] or 0
                }
            return {}
        except Exception as e:
            logger.error(f'Student stats query failed: {e}')
            return {}
    
    @staticmethod
    def get_instructor_stats(username):
        """
        Obtenir les statistiques d'un instructeur.
        """
        query = """
        MATCH (u:NeoUser {username: $username})-[:TEACHES]->(c:NeoCourse)
        
        // Total étudiants inscrits
        OPTIONAL MATCH (student:NeoUser)-[:ENROLLED_IN]->(c)
        WITH u, count(DISTINCT c) AS courses_created, 
             count(DISTINCT student) AS total_students
        
        RETURN courses_created, total_students
        """
        
        try:
            result, _ = db.cypher_query(query, {'username': username})
            if result:
                row = result[0]
                return {
                    'courses_created': row[0] or 0,
                    'total_students': row[1] or 0
                }
            return {}
        except Exception as e:
            logger.error(f'Instructor stats query failed: {e}')
            return {}
