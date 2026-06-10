from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def is_manager(user):
    return user.is_authenticated and (user.is_superuser or user.username == 'mudur' or user.groups.filter(name='Müdür').exists())


def is_coordinator(user):
    return user.is_authenticated and (user.username == 'koordine' or user.groups.filter(name='Koordine').exists())


def allowed_for_coordinator_or_manager(user):
    return is_manager(user) or is_coordinator(user)


def manager_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not is_manager(request.user):
            messages.error(request, 'Bu sayfaya sadece müdür girişi erişebilir.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def coordinator_or_manager_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not allowed_for_coordinator_or_manager(request.user):
            messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
