from .improve import *
from utils.generals import is_model_registered

__all__ = list()

# 1
if not is_model_registered('repair', 'Improve'):
    class Improve(AbstractImprove):
        class Meta(AbstractImprove.Meta):
            db_table = 'repair_improve'

    __all__.append('Improve')


# 2
if not is_model_registered('repair', 'ImproveTask'):
    class ImproveTask(AbstractImproveTask):
        class Meta(AbstractImproveTask.Meta):
            db_table = 'repair_improve_task'

    __all__.append('ImproveTask')


# 3
if not is_model_registered('repair', 'ImproveLocation'):
    class ImproveLocation(AbstractImproveLocation):
        class Meta(AbstractImproveLocation.Meta):
            db_table = 'repair_improve_location'

    __all__.append('ImproveLocation')
