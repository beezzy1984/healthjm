

from trytond.pool import Pool
from .models import PatientPregnancy, PrenatalComponent


def register():
    Pool.register(
        PatientPregnancy,
        PrenatalComponent,
        module='health_jamaica_obgyn', type_='model')
