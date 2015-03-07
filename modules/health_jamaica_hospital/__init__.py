from trytond.pool import Pool
from .models import *

def register():
    Pool.register(
        HospitalBed,
        InpatientRegistration,
        PatientRounding,
        module='health_jamaica_hospital', type_='model')
