from django.urls import path, include
from api.views import RootApiView
from apps.person.api.v1 import routers as person_routers
from apps.core.api.v1 import routers as core_routers

urlpatterns = [
    path('', RootApiView.as_view(), name='api'),
    path('person/v1/', include((person_routers, 'person_api'), namespace='person_v1')),
    path('core/v1/', include((core_routers, 'core_api'), namespace='core_v1')),
]
