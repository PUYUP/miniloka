from django.urls import path, include
from .v1 import routers

urlpatterns = [
    path('notifier/v1/', include((routers, 'notifier_api'), namespace='notifier_api')),
]
