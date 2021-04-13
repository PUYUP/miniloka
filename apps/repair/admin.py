from django.contrib import admin
from django.contrib.auth import get_user_model
from utils.generals import get_model

Improve = get_model('repair', 'Improve')
ImproveTask = get_model('repair', 'ImproveTask')
ImproveLocation = get_model('repair', 'ImproveLocation')


class ImproveTaskInline(admin.StackedInline):
    model = ImproveTask


class ImproveLocationInline(admin.StackedInline):
    model = ImproveLocation


class ImproveExtend(admin.ModelAdmin):
    model = Improve
    inlines = [ImproveTaskInline, ImproveLocationInline,]

    def get_queryset(self, request):
        qs = super().get_queryset(request) \
            .prefetch_related('user', 'location') \
            .select_related('user', 'location')

        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = get_user_model().objects \
                .prefetch_related('profile') \
                .select_related('profile')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Improve, ImproveExtend)
