from django.urls import path, include
from .customer import routers as customer_routers
from .owner import routers as owner_routers

urlpatterns = [
    path('customer/', include((customer_routers, 'customer'))),
    path('owner/', include((owner_routers, 'owner'))),
]
