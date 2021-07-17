from .fellow import *
from .finance import *
from .loan import *

from utils.generals import is_model_registered

__all__ = list()


# 1
if not is_model_registered('peerland', 'Submission'):
    class Submission(AbstractSubmission):
        class Meta(AbstractSubmission.Meta):
            pass

    __all__.append('Submission')


# 2
if not is_model_registered('peerland', 'Term'):
    class Term(AbstractTerm):
        class Meta(AbstractTerm.Meta):
            pass

    __all__.append('Term')


# 3
if not is_model_registered('peerland', 'State'):
    class State(AbstractState):
        class Meta(AbstractState.Meta):
            pass

    __all__.append('State')


# 4
if not is_model_registered('peerland', 'Attachment'):
    class Attachment(AbstractAttachment):
        class Meta(AbstractAttachment.Meta):
            pass

    __all__.append('Attachment')


# 5
if not is_model_registered('peerland', 'Location'):
    class Location(AbstractLocation):
        class Meta(AbstractLocation.Meta):
            pass

    __all__.append('Location')


# 6
if not is_model_registered('peerland', 'Payment'):
    class Payment(AbstractPayment):
        class Meta(AbstractPayment.Meta):
            pass

    __all__.append('Payment')


# 7
if not is_model_registered('peerland', 'Borrower'):
    class Borrower(AbstractBorrower):
        class Meta(AbstractBorrower.Meta):
            pass

    __all__.append('Borrower')


# 8
if not is_model_registered('peerland', 'Lender'):
    class Lender(AbstractLender):
        class Meta(AbstractLender.Meta):
            pass

    __all__.append('Lender')
