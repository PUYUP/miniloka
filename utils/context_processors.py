from django.conf import settings


"""Define global attributes for templates"""
def globalvar(request):
    params = {
        'url_name': request.resolver_match.url_name,
        'app_label': settings.APP_NAME,
        'pagination_per_page': settings.PAGINATION_PER_PAGE,
    }

    return params
