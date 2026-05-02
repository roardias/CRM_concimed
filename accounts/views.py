from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from .forms import UserRegistrationForm


def _can_manage_users(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.profile.role in ["ADMIN", "GESTOR"]


@login_required
@user_passes_test(_can_manage_users)
def user_list(request):
    users = User.objects.select_related("profile").all().order_by("first_name", "username")
    return render(request, "accounts/user_list.html", {"users": users})


@login_required
@user_passes_test(_can_manage_users)
def user_create(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            user.profile.role = form.cleaned_data["role"]
            user.profile.save()
            messages.success(request, "Usuario criado com sucesso.")
            return redirect("user-list")
    else:
        form = UserRegistrationForm()

    return render(request, "accounts/user_create.html", {"form": form})
