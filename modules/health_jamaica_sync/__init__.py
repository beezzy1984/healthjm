from trytond.pool import Pool
from .celerytools import *
from .health import *


def register():
    Pool.register(
        Sync,
        Party,
        #PartyAddress,
        Country,
        Subdivision,
        Appointment, 
        DiagnosticHypothesis, 
        DomiciliaryUnit, 
        HealthProfessional, 
        HospitalUnit, 
        HospitalWard, 
        HealthProfessionalSpecialties, 
        OperationalArea, 
        OperationalSector,
        Pathology, 
        PathologyCategory, 
        PathologyGroup, 
        PatientData, 
        PatientDiseaseInfo, 
        PatientEvaluation, 
        PatientVaccination, 
        SecondaryCondition, 
        SignsAndSymptoms,
        module='health_jamaica_sync', type_='model')
