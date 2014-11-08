from trytond.pool import Pool
from .celerytools import *
from .health import *


def register():
    Pool.register(
        Sync,
        Party,
        PartyAddress,
        OccupationalGroup,
        OperationalArea,
        OperationalSector,
        DomiciliaryUnit,
        MedicalSpecialty,
        HealthInstitution,
        HealthInstitutionSpecialties,
        HealthInstitutionOperationalSector,
        # AlternativePersonID,
        #Appointment, 
        #DiagnosticHypothesis, 
        #HealthProfessional, 
        #HospitalUnit, 
        #HospitalWard, 
        #HealthProfessionalSpecialties, 
        #PathologyCategory, 
        PatientData, 
        #PatientDiseaseInfo, 
        #PatientEvaluation, 
        #PatientVaccination, 
        #SecondaryCondition, 
        #SignsAndSymptoms,
        module='health_jamaica_sync', type_='model')
