from trytond.pool import Pool
from .models import PartyPatient, PatientData, OccupationalGroup

def register():
    Pool.register(
        PartyPatient,
        PatientData,
        OccupationalGroup,
        module='healthjm_socioeconomics', type_='model')
