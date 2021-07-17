import uuid

from django.db import models
from simple_history import register
from utils.generals import get_model

Submission = get_model('peerland', 'Submission')
Term = get_model('peerland', 'Term')
State = get_model('peerland', 'State')
Attachment = get_model('peerland', 'Attachment')
Location = get_model('peerland', 'Location')
Payment = get_model('peerland', 'Payment')
Borrower = get_model('peerland', 'Borrower')
Lender = get_model('peerland', 'Lender')


register(Submission, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(Term, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(State, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(Attachment, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(Location, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(Payment, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(Borrower, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))

register(Lender, app=__package__,
         history_id_field=models.UUIDField(default=uuid.uuid4))
