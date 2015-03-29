from trytond.pool import Pool
from .models import Newborn


def register():
    Pool.register(
        Newborn,
        module='health_jamaica_pediatrics', type_='model'
    )
