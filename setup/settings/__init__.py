from setup.settings.base import *
from setup.settings.project import *

# check setting load from live server
# this time all live server mark as production grade
if os.environ.get('PRODUCTION', False):
    from .development import *
else:
    from .development import *
