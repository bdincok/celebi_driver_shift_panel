def role_flags(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {'is_manager': False, 'is_coordinator': False}
    is_manager = user.groups.filter(name='Müdür').exists() or user.username == 'mudur' or user.is_superuser
    is_coordinator = user.groups.filter(name='Koordine').exists() or user.username == 'koordine'
    return {'is_manager': is_manager, 'is_coordinator': is_coordinator}
