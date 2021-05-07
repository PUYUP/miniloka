from django.urls import path, include
from .v1 import routers

urlpatterns = [
    path('servo/v1/', include((routers, 'servo_api'), namespace='servo_api')),
]
