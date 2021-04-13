from django.utils.translation import ugettext_lazy as _

(JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC) = range(1, 13)
MONTH_CHOICES = (
    (JAN, _("January")),
    (FEB, _("February")),
    (MAR, _("March")),
    (APR, _("April")),
    (MAY, _("May")),
    (JUN, _("June")),
    (JUL, _("July")),
    (AUG, _("August")),
    (SEP, _("September")),
    (OCT, _("October")),
    (NOV, _("November")),
    (DEC, _("December")),
)
