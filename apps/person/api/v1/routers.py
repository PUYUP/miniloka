from django.urls import path, include

# THIRD PARTY
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

# LOCAL
from .user.views import TokenObtainPairViewExtend, UserApiView
from .verifycode.views import VerifyCodeApiView

# Create a router and register our viewsets with it.
router = DefaultRouter(trailing_slash=True)
router.register('users', UserApiView, basename='user')
router.register('verifycodes', VerifyCodeApiView, basename='verifycode')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairViewExtend.as_view(), name='token_obtain_pair'),
    path('token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
