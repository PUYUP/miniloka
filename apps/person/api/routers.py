from django.urls import path, include
from apps.person.api.v1 import routers

urlpatterns = [
    path('person/v1/', include((routers, 'person_api'), namespace='person_api')),
]
