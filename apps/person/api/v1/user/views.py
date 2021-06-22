from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.core.exceptions import (
    ObjectDoesNotExist,
    MultipleObjectsReturned,
    ValidationError as DjangoValidationError
)
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.core.validators import validate_email

# THIRD PARTY
from rest_framework import serializers, status as response_status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, NotAcceptable, ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import JSONParser, MultiPartParser

# JWT
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView

# SERIALIZERS
from .serializers import (
    BaseUserSerializer,
    CreateUserSerializer,
    UpdateUserSerializer,
    RetrieveUserSerializer,
    UserMetaSerializer
)
from ..profile.serializers import ProfileSerializer

# GET MODELS FROM GLOBAL UTILS
from utils.generals import get_model
from utils.pagination import build_result_pagination
from utils.validators import csrf_protect_drf

from apps.person.utils.permissions import IsCurrentUserOrReject
from apps.person.utils.auth import validate_username
from apps.person.utils.password import ChangePassword, PasswordRecovery

UserModel = get_user_model()
Profile = get_model('person', 'Profile')
SecureCode = get_model('person', 'SecureCode')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class UserApiView(viewsets.ViewSet):
    """
    POST
    ------------
        If :email provided :msisdn not required
        If :email NOT provide :msisdn required

        If :group not define will used Customer as default group

        {
            "password": "string with special character",
            "username": "string",
            "email": "string email",
            "msisdn": "string number",
            "group": "string",                             [optional]
            "verification": {
                "passcode": "123456",
                "challenge": "email_validation",
                "token": "akfagakjg",
            }
        }
    """

    def __init__(self, **kwargs):
        self._uuid = None
        self._instance = None
        self._instances = UserModel.objects.none()
        self._context = {}
        super().__init__(**kwargs)

    # this part of DRF
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)
    permission_action = {
        'list': [IsAuthenticated],
        'retrieve': [IsAuthenticated],
        'partial_update': [IsAuthenticated, IsCurrentUserOrReject],
    }

    def get_permissions(self):
        """
        Instantiates and returns
        the list of permissions that this view requires.
        """
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]

    def dispatch(self, request, *args, **kwargs):
        # Must call first because will used everywhere
        self._uuid = kwargs.get('uuid')
        self._instances = self._get_instances()
        self._context = {'request': request}
        return super().dispatch(request, *args, **kwargs)

    def _get_instances(self):
        """General query affected for entire object"""
        return UserModel.objects.prefetch_related('profile') \
            .select_related('profile')

    def _get_instance(self):
        """Return single object"""
        try:
            return self._instances.get(uuid=self._uuid)
        except ObjectDoesNotExist:
            raise NotFound()

    def _get_instance_for_update(self):
        """Return single object for update purpose"""
        try:
            instance = self._instances.select_for_update() \
                .get(uuid=self._uuid)
        except ObjectDoesNotExist:
            raise NotFound()
        return instance

    # All Users
    def list(self, request, format=None):
        keyword = request.query_params.get('keyword')
        instances = self._instances
        if keyword:
            instances = instances.filter(Q(username__icontains=keyword)
                                         | Q(first_name__icontains=keyword))

        paginator = _PAGINATOR.paginate_queryset(instances, request)
        serializer = BaseUserSerializer(paginator, many=True, context=self._context,
                                        fields=('uuid', 'username', 'url', 'profile',))
        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)

    # Single User
    def retrieve(self, request, uuid=None, format=None):
        instance = self._get_instance()

        # limit fields when other user see the user
        fields = ('__all__')
        if str(request.user.uuid) != uuid:
            fields = ('uuid', 'username', 'url', 'profile', 'first_name',)

        serializer = RetrieveUserSerializer(instance, many=False, context=self._context,
                                            fields=fields)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    # Register User
    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        # Only guest can register
        user = request.user
        if user and user.is_authenticated:
            raise NotAcceptable(
                detail=_("You has loggedin as {}".format(user.username)))

        serializer = CreateUserSerializer(data=request.data,
                                          context=self._context)
        if serializer.is_valid(raise_exception=True):
            error_status = response_status.HTTP_406_NOT_ACCEPTABLE
            error_code = None
            error_content = None

            try:
                serializer.save()
            except ValidationError as e:
                error_content = e
                error_code = getattr(e, 'code', None)
                if error_code == 'verification_failure':
                    error_status = response_status.HTTP_401_UNAUTHORIZED
            except ValueError as e:
                error_content = str(e)

            if error_content:
                return Response({'detail': error_content}, status=error_status)

            _serializer = RetrieveUserSerializer(serializer.instance,
                                                 context=self._context)
            return Response(_serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # Update basic user data
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        instance = self._get_instance_for_update()
        serializer = UpdateUserSerializer(instance, data=request.data,
                                          partial=True, context=self._context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # Sub-action return single user
    @transaction.atomic
    @action(methods=['get'], detail=False, permission_classes=[IsAuthenticated],
            url_path='me', url_name='me')
    def me(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=response_status.HTTP_401_UNAUTHORIZED)

        self._uuid = user.uuid
        instance = self._get_instance()
        serializer = BaseUserSerializer(instance, many=False,
                                        context=self._context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    # Sub-action logout!
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False, permission_classes=[IsAuthenticated],
            url_path='logout', url_name='logout')
    def logout(self, request, uuid=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=response_status.HTTP_401_UNAUTHORIZED)

        logout(request)
        return Response({'detail': _("Logout!")}, status=response_status.HTTP_200_OK)

    # Sub-action check email available
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False, permission_classes=[AllowAny],
            url_path='check-email', url_name='check-email')
    def check_email(self, request):
        """
        POST
        ------------------

        Param:

            {
                "email": "my@email.com"
            }
        """
        data = request.data
        email = data.get('email', None)
        if not email:
            raise NotFound(_("Email not provided"))

        # check format email valid or not
        try:
            validate_email(email)
        except ValidationError as e:
            raise NotAcceptable(detail=_(" ".join(e.messages)))

        try:
            UserModel.objects.get(email=email, is_email_verified=True)
            raise NotAcceptable(_("Email `{email}` sudah terdaftar."
                                  " Jika ini milik Anda hubungi kami.".format(email=email)))
        except MultipleObjectsReturned:
            raise NotAcceptable(_("Email `{email}` terdaftar lebih dari satu akun. Jika merasa belum pernah mendaftar"
                                  " dengan email tersebut silahkan hubungi kami.".format(email=email)))
        except ObjectDoesNotExist:
            # Check the email has been used in SecureCode
            check = SecureCode.objects.filter(
                email=email, is_used=False, is_expired=False)
            return Response(
                {
                    'detail': _("Email tersedia!"),
                    'is_used_before': check.exists(),  # if True indicate email has used before
                    'email': email
                },
                status=response_status.HTTP_200_OK
            )

    # Sub-action check msisdn available
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False, permission_classes=[AllowAny],
            url_path='check-msisdn', url_name='check-msisdn')
    def check_msisdn(self, request):
        """
        POST
        ------------------

        Param:

            {
                "msisdn": "1234567890"
            }
        """
        data = request.data
        msisdn = data.get('msisdn', None)
        if not msisdn:
            raise NotFound(_("Masukkan MSISDN"))

        try:
            UserModel.objects.get(msisdn=msisdn, is_msisdn_verified=True)
            raise NotAcceptable(_("MSISDN `{msisdn}` sudah digunakan."
                                  " Jika ini milik Anda hubungi kami.".format(msisdn=msisdn)))
        except MultipleObjectsReturned:
            raise NotAcceptable(_("MSISDN `{msisdn}` terdaftar lebih dari satu akun. Jika merasa belum pernah mendaftar"
                                  " dengan msisdn tersebut silahkan hubungi kami.".format(msisdn=msisdn)))
        except ObjectDoesNotExist:
            # Check whether the msisdn has been used
            check = SecureCode.objects.filter(
                msisdn=msisdn, is_used=False, is_expired=False)
            return Response(
                {
                    'detail': _("MSISDN tersedia!"),
                    'is_used_before': check.exists(),
                    'msisdn': msisdn
                },
                status=response_status.HTTP_200_OK
            )

    # Sub-action check user available
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False, permission_classes=[AllowAny],
            url_path='check-user', url_name='check-user')
    def check_user(self, request):
        """
        POST
        ------------------

        Param:

            {
                "credential": "my@email.com / username / msisdn"
            }
        """
        data = request.data
        credential = data.get('credential', None)

        if not credential:
            raise NotFound(_("Masukkan email, nama pengguna atau MSISDN"))

        try:
            user = UserModel.objects.get(Q(username=credential)
                                         | Q(email=credential) & Q(is_email_verified=True)
                                         | Q(msisdn=credential) & Q(is_msisdn_verified=True))

            return Response(
                {
                    'detail': _("Akun ditemukan"),
                    'email': user.email if user.email == credential else None,
                    'msisdn': user.msisdn if user.msisdn == credential else None
                },
                status=response_status.HTTP_200_OK
            )

        except MultipleObjectsReturned:
            raise NotAcceptable(
                {'detail': _("Akun `{credential}` sudah digunakan".format(
                    credential=credential))}
            )

        except ObjectDoesNotExist:
            raise NotFound(
                {'detail': _("Akun `{credential}` tidak ditemukan".format(
                    credential=credential))}
            )

    # Sub-action check email available
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False, permission_classes=[AllowAny],
            url_path='check-username', url_name='check-username')
    def check_username(self, request):
        """
        POST
        ------------------

        Param:

            {
                "username": "string"
            }
        """
        data = request.data
        username = data.get('username', None)
        if not username:
            raise NotFound(_("Masukkan nama pengguna"))

        # check a username is valid string
        try:
            validate_username(username)
        except ValidationError as e:
            raise NotAcceptable(detail=_(" ".join(e.messages)))

        if UserModel.objects.filter(username=username).exists():
            raise NotAcceptable(detail=_("Nama pengguna `{username}` "
                                         "sudah digunakan.".format(username=username)))
        return Response({'detail': _("Nama pengguna tersedia!")},
                        status=response_status.HTTP_200_OK)

    # Sub-action update Profile
    # Parses classes must provided because we used this to save JSON and Multipart (upload file)
    @method_decorator(never_cache)
    @transaction.atomic
    @action(detail=True, methods=['get', 'patch'],
            permission_classes=[IsAuthenticated, IsCurrentUserOrReject],
            parser_classes=[JSONParser, MultiPartParser],
            url_path='profile', url_name='profile')
    def profile(self, request, uuid=None):
        try:
            queryset = Profile.objects.get(user__uuid=uuid)
        except ObjectDoesNotExist:
            raise NotFound()

        if request.method == 'PATCH':
            serializer = ProfileSerializer(queryset, data=request.data,
                                           partial=True, context=self._context)

            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=response_status.HTTP_200_OK)

        if request.method == 'GET':
            serializer = ProfileSerializer(
                queryset, many=False, context=self._context)
            return Response(serializer.data, status=response_status.HTTP_200_OK)

    # Password recovery as guest
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False, permission_classes=[AllowAny],
            url_path='password-recovery', url_name='password-recovery')
    def password_recovery(self, request):
        """
        POST
        ------------------

        Param:

            {
                "securecode_email": "string",
                "securecode_msisdn": "string",
                "securecode_passcode": "string",
                "securecode_token": "string",
                "new_password": "string",
                "retype_password": "string",
                "password_token": "string",
                "password_uidb64": "string"
            }

        :token captured from securecode validation
        """

        SECURECODE_EMAIL = 'email'
        SECURECODE_EMAIL_PARAM = 'securecode_{}'.format(SECURECODE_EMAIL)
        SECURECODE_MSISDN = 'msisdn'
        SECURECODE_MSISDN_PARAM = 'securecode_{}'.format(SECURECODE_MSISDN)

        if SECURECODE_EMAIL_PARAM in request.data and SECURECODE_MSISDN_PARAM in request.data:
            raise ValidationError(
                detail=_("Can't use both email and msisdn"))

        securecode_value = request.data.get(
            SECURECODE_EMAIL_PARAM) or request.data.get(SECURECODE_MSISDN_PARAM)
        securecode_field = next((key for key, value in request.data.items()
                                 if value == securecode_value), None)

        if securecode_field is None:
            raise ValidationError(
                detail=_("securecode_msisdn or securecode_email required"))

        new_password = request.data.get('new_password')
        retype_password = request.data.get('retype_password')
        password_uidb64 = request.data.get('password_uidb64')
        password_token = request.data.get('password_token')
        securecode_passcode = request.data.get('securecode_passcode')
        securecode_token = request.data.get('securecode_token')

        # Init recovery function
        # If all passed will return None
        recover = PasswordRecovery(new_password, retype_password,
                                   password_token, password_uidb64)

        # Check and validate securecode
        recover.get_securecode(securecode_token, securecode_field.replace('securecode_', ''),
                               securecode_value, securecode_passcode)

        # Finally, set the password
        try:
            recover.save_password()
        except DjangoValidationError as e:
            raise ValidationError(detail=' '.join(e))

        return Response({'detail': _("Password berhasil diperbarui. "
                                     "Silahkan masuk dengan password baru")},
                        status=response_status.HTTP_200_OK)

    # Change password
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['patch'], detail=True, permission_classes=[IsAuthenticated],
            url_path='change-password', url_name='change-password')
    def change_password(self, request, uuid=None):
        """
        PATCH
        ------------------

        Param:

            {
                "old_password": "string",
                "new_password": "string",
                "retype_password": "string"
            }
        """
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        retype_password = request.data.get('retype_password')

        changer = ChangePassword(user, old_password, new_password,
                                 retype_password)

        # Finally, set the password
        try:
            changer.save_password()
        except DjangoValidationError as e:
            raise ValidationError(detail=' '.join(e))

        return Response({'detail': _("Password berhasil diperbarui. "
                                     "Silahkan masuk dengan password baru")},
                        status=response_status.HTTP_200_OK)

    # Meta
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=True, permission_classes=[IsAuthenticated],
            url_path='metas', url_name='meta')
    def meta(self, request, uuid=None):
        """
        POST
        ------------------

        Param:

            {
                "meta_key": "string",
                "meta_value": "string"
            }
        """
        serializer = UserMetaSerializer(data=request.data, many=False,
                                        context=self._context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except DjangoValidationError as e:
                raise ValidationError({'detail': str(e)})
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)


class TokenObtainPairSerializerExtend(TokenObtainPairSerializer):
    def validate(self, attrs):
        context = {}
        data = super().validate(attrs)
        serializer = RetrieveUserSerializer(self.user, many=False,
                                            context=self.context)

        context.update({
            'token': data,
            'user': serializer.data
        })
        return context


class TokenObtainPairViewExtend(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializerExtend

    @method_decorator(never_cache)
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        except ValueError as e:
            raise ValidationError({'detail': str(e)})

        # Make user logged-in
        if (
            'rest_framework.authentication.SessionAuthentication'
            in settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']
        ):
            username = request.data.get('username')
            password = request.data.get('password')

            user = authenticate(request=request, username=username,
                                password=password)
            if user:
                login(request, user)
        return Response(serializer.validated_data, status=response_status.HTTP_200_OK)
