from django.urls import path, include
from api.views import RootApiView
from apps.person.api import routers as person_routers
from apps.procure.api import routers as procure_routers
from apps.notifier.api import routers as notifier_routers

urlpatterns = [
    path('', RootApiView.as_view(), name='api'),
    path('', include(person_routers)),
    path('', include(procure_routers)),
    path('', include(notifier_routers)),
]
