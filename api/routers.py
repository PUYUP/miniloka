from django.urls import path, include
from api.views import RootApiView, ping
from apps.person.api import routers as person_routers
from apps.servo.api import routers as servo_routers

urlpatterns = [
    path('', RootApiView.as_view(), name='api'),
    path('ping/', ping, name='ping'),
    path('', include(person_routers)),
    path('', include(servo_routers)),
]
