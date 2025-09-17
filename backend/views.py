from django.shortcuts import render
from .models import User,Skill
from django.http import HttpResponse
# filtering users by conditions like skills year
def filter_user_by_skills(request):
    skill_search=request.GET.get('Skills')
    users=[]
    if skill_search:
        users=User.objects.filter(my_skills__name__icontains=skill_search)

    return render(request, "search_results.html", {"users": users, "query": skill_search})


