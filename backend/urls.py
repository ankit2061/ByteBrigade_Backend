from django.urls import path
from . import api_views

urlpatterns = [
    # Remove 'api/' from all patterns
    path('login/', api_views.LoginView.as_view(), name='login'),
    path('users/', api_views.UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', api_views.UserDetailView.as_view(), name='user-detail'),
    path('users/<int:user_id>/skills/', api_views.UserUpdateSkillsView.as_view(), name='user-skills'),
    path('search/', api_views.UserSearchView.as_view(), name='user-search'),
    path('skills/', api_views.SkillListCreateView.as_view(), name='skill-list-create'),
    path('skills/<int:pk>/', api_views.SkillDetailView.as_view(), name='skill-detail'),
    path('health/', api_views.HealthCheckView.as_view(), name='health-check'),
    path('debug/skills/', api_views.DebugSkillsView.as_view(), name='debug-skills'),
]
