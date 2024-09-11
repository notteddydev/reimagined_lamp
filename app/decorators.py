from functools import wraps
from django.db.models import Model
from django.http import Http404, HttpRequest, HttpResponse

from typing import Any, Callable

def owned_by_user(model: Model) -> Callable:
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
            if model.objects.filter(pk=kwargs["pk"], user=request.user).exists():
                return view_func(request, *args, **kwargs)
            
            raise Http404(f"No {model._meta.object_name} matches the given query.")
        
        return _wrapped_view
    
    return decorator