from functools import wraps
from django.http import Http404

def owned_by_user(model):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if model.objects.filter(pk=kwargs['pk'], user=request.user).exists():
                return view_func(request, *args, **kwargs)
            
            raise Http404(f"No {model._meta.object_name} matches the given query.")
        
        return _wrapped_view
    
    return decorator