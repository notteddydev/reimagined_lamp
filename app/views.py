from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView

class HomeView(LoginRequiredMixin, TemplateView):
    # redirect_field_name = "redirect_to"
    template_name = "home.html"

class SignupView(View):
    def get(self, request):
        form = UserCreationForm()

        return render(request, "registration/signup.html", {"form": form})
    
    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            return redirect("home")
        
        return render(request, "registration/signup.html", {"form": form})