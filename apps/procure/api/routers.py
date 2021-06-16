from django.urls import path, include
from .v1 import routers

urlpatterns = [
    path('procure/v1/', include((routers, 'procure_api'), namespace='procure_api')),
]
