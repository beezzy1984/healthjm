from trytond.pool import pool
from .models import Newborn


def register():
    Pool.register(
        Newborn,
        module='health_jamaica_pediatrics', type_='model'
    )
