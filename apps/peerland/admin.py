from django.contrib import admin
from utils.generals import get_model

Submission = get_model('peerland', 'Submission')
Term = get_model('peerland', 'Term')
State = get_model('peerland', 'State')
Location = get_model('peerland', 'Location')
Attachment = get_model('peerland', 'Attachment')
Payment = get_model('peerland', 'Payment')
Borrower = get_model('peerland', 'Borrower')
Lender = get_model('peerland', 'Lender')


class TermInline(admin.StackedInline):
    model = Term


class StateInline(admin.StackedInline):
    model = State


class LocationInline(admin.StackedInline):
    model = Location


class BorrowerInline(admin.StackedInline):
    model = Borrower


class LenderInline(admin.StackedInline):
    model = Lender


class SubmissionExtend(admin.ModelAdmin):
    model = Submission
    inlines = (TermInline, StateInline, LocationInline,
               BorrowerInline, LenderInline,)


admin.site.register(Submission, SubmissionExtend)
admin.site.register(Attachment)
admin.site.register(Payment)
