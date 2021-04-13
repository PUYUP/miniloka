from django.conf import settings


class Pagination:
    def __init__(self, request, queryset, queryset_paginate, page_num, paginator):
        self.request = request  
        self.can_show_all = True
        self.full_result_count = queryset.count()
        self.list_max_show_all = 200
        self.list_per_page = settings.PAGINATION_PER_PAGE
        self.multi_page = True
        self.page_num = page_num
        self.paginator = paginator
        self.queryset = queryset
        self.result_count = queryset_paginate.paginator.count
        self.result_list = queryset_paginate
        self.root_queryset = queryset
        self.show_all = False
        self.show_full_result_count = True


def build_result_pagination(self, _PAGINATOR, serializer):
    result = {
        'offset': _PAGINATOR.offset,
        'limit': _PAGINATOR.limit,
        'total': _PAGINATOR.count,
        'previous': _PAGINATOR.get_previous_link(),
        'next': _PAGINATOR.get_next_link(),
        'results': serializer.data,
    }
    
    return result
