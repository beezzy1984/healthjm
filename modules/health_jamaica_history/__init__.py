from trytond.pool import Pool
from .history import *

def register():
    Pool.register(
        Party,
        PartyAddress,
        DomiciliaryUnit,
        AlternativePersonID,
        HealthProfessional,
        HealthProfessionalSpecialties, 
        Appointment, 
        PatientData,
        PatientEvaluation, 
        PatientDiseaseInfo, 
        DiagnosticHypothesis,
        PatientVaccination, 
        SecondaryCondition, 
        SignsAndSymptoms,
        Directions,
        module='health_jamaica_history', type_='model')
