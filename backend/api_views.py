

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from .models import User, Skill
from .serializer import UserSerializer, SkillSerializer
import logging

logger = logging.getLogger(__name__)


class LoginView(APIView):
    """
    Simple login endpoint
    """

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({
                'error': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                return Response({
                    'message': 'Login successful',
                    'user_id': user.id,
                    'username': user.username,
                    'name': user.name
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all().prefetch_related("my_skills", "known_skills", "desired_skills")
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Add pagination support
        skip = int(self.request.query_params.get('skip', 0))
        limit = int(self.request.query_params.get('limit', 100))
        return queryset[skip:skip + limit]


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all().prefetch_related("my_skills", "known_skills", "desired_skills")
    serializer_class = UserSerializer


class UserUpdateSkillsView(APIView):
    """
    Update user skills (known_skills, desired_skills)
    """

    def put(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get skill data from request
        known_skills = request.data.get('knownSkills', [])
        desired_skills = request.data.get('desiredSkills', [])

        # Update known_skills
        if known_skills is not None:
            user.known_skills.clear()
            user.my_skills.clear()  # Also clear for backward compatibility
            for skill_name in known_skills:
                if skill_name and skill_name.strip():
                    skill, _ = Skill.objects.get_or_create(
                        name=skill_name.strip().capitalize()
                    )
                    user.known_skills.add(skill)
                    user.my_skills.add(skill)

        # Update desired_skills
        if desired_skills is not None:
            user.desired_skills.clear()
            for skill_name in desired_skills:
                if skill_name and skill_name.strip():
                    skill, _ = Skill.objects.get_or_create(
                        name=skill_name.strip().capitalize()
                    )
                    user.desired_skills.add(skill)

        user.save()

        # Return updated user data
        serializer = UserSerializer(user)
        return Response({
            "message": "Skills updated successfully",
            "user": serializer.data
        }, status=status.HTTP_200_OK)

    def patch(self, request, user_id):
        """
        Partial update of user skills
        """
        return self.put(request, user_id)


class SkillListCreateView(generics.ListCreateAPIView):
    queryset = Skill.objects.all().order_by("name")
    serializer_class = SkillSerializer


class SkillDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer


class UserSearchView(APIView):
    """
    🔧 FIXED: Search users based on skills and filters
    """

    def get(self, request):
        logger.info(f"🔍 Search request received with params: {request.query_params}")

        # Get query parameters
        skills_param = request.query_params.get('skills', '')
        include_beginner = request.query_params.get('include_beginner', 'true').lower() == 'true'
        team_size = request.query_params.get('team_size', '3')

        logger.info(f"📋 Search criteria - Skills: {skills_param}, Include beginners: {include_beginner}")

        # Start with all users
        users = User.objects.all().prefetch_related("known_skills", "desired_skills", "my_skills")
        initial_count = users.count()
        logger.info(f"📊 Initial user count: {initial_count}")

        # 🔧 FIXED: Filter by skills if provided
        if skills_param:
            skill_list = [s.strip() for s in skills_param.split(',') if s.strip()]
            logger.info(f"🎯 Searching for skills: {skill_list}")

            if skill_list:  # Only filter if we have skills
                # Create AND condition for each skill (user must have ALL skills)
                for skill in skill_list:
                    # Use exact match with case-insensitive lookup
                    skill_query = Q(
                        Q(known_skills__name__iexact=skill) |
                        Q(my_skills__name__iexact=skill)
                    )
                    users = users.filter(skill_query).distinct()
                    logger.info(f"🔍 After filtering for '{skill}': {users.count()} users")

        # Filter by beginner preference
        if not include_beginner:
            users = users.filter(is_beginner=False)
            logger.info(f"🎓 After filtering beginners: {users.count()} users")

        final_count = users.count()
        logger.info(f"✅ Final search results: {final_count} users found")

        # Serialize and return
        serializer = UserSerializer(users, many=True)

        # Add debug info to response
        response_data = {
            'results': serializer.data,
            'count': final_count,
            'debug': {
                'initial_count': initial_count,
                'search_skills': skills_param.split(',') if skills_param else [],
                'include_beginner': include_beginner
            }
        }

        return Response(serializer.data, status=status.HTTP_200_OK)


class UserBySkillView(generics.ListAPIView):
    """
    Get users by a specific skill
    """
    serializer_class = UserSerializer

    def get_queryset(self):
        skill_name = self.request.query_params.get("skill", None)
        if skill_name:
            return User.objects.filter(
                Q(my_skills__name__iexact=skill_name.strip()) |
                Q(known_skills__name__iexact=skill_name.strip())
            ).distinct().prefetch_related("my_skills", "known_skills", "desired_skills")
        return User.objects.none()


class HealthCheckView(APIView):
    """
    Health check endpoint
    """

    def get(self, request):
        return Response({"status": "healthy"}, status=status.HTTP_200_OK)


# 🆕 ADDED: Debug endpoint to check skills
class DebugSkillsView(APIView):
    """
    Debug endpoint to see all skills and users
    """

    def get(self, request):
        all_skills = list(Skill.objects.all().values('id', 'name'))
        all_users = list(User.objects.all().values('id', 'name', 'email'))

        # Get users with their skills
        users_with_skills = []
        for user in User.objects.all().prefetch_related('known_skills'):
            user_skills = [skill.name for skill in user.known_skills.all()]
            users_with_skills.append({
                'id': user.id,
                'name': user.name,
                'skills': user_skills
            })

        return Response({
            'total_skills': len(all_skills),
            'total_users': len(all_users),
            'all_skills': all_skills,
            'users_with_skills': users_with_skills
        })
