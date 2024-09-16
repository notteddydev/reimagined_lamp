from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView


class HomeView(LoginRequiredMixin, TemplateView):
    # redirect_field_name = "redirect_to"
    template_name = "home.html"


class SignupView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Display the template and UserCreationForm for SignUp.
        """
        form = UserCreationForm()
        return render(request, "registration/signup.html", {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Use the posted data to create a User - if it's successful, redirect to the home page. If not,
        return the SignUp template again with the form and any errors.
        """
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
        return render(request, "registration/signup.html", {"form": form})
