from trytond.pool import Pool
from .models import *
from .bed_management import *


def register():
    Pool.register(
        HospitalBed,
        InpatientRegistration,
        PatientRounding,
        BedManagerView,
        BedCreatorView,
        HospitalWard,
        module='health_jamaica_hospital', type_='model')

    Pool.register(
        BedManager,
        BedCreator,
        module='health_jamaica_hospital', type_='wizard')
