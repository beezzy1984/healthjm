from trytond.pool import Pool
from .models import *
from .bed_management import *


def register():
    'Register pool'
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
        CreateBedTransfer,
        module='health_jamaica_hospital', type_='wizard')
