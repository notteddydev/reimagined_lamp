from django.db.models import QuerySet

class OwnedByUserMixin:
    def get_queryset(self) -> QuerySet:
        user = self.request.user
        queryset = super().get_queryset()
        return queryset.filter(user=user)