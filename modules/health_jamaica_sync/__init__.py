from trytond.pool import Pool
from .celerytools import *
from .health import *


def register():
    Pool.register(
        Sync,
        Party,
        PartyAddress,
        Country,
        Subdivision,
        OperationalArea, 
        OperationalSector,
        DomiciliaryUnit,
        HealthInstitution,
        HealthInstitutionSpecialties,
        HealthInstitutionOperationalSector,
        #Appointment, 
        #DiagnosticHypothesis, 
        #HealthProfessional, 
        #HospitalUnit, 
        #HospitalWard, 
        #HealthProfessionalSpecialties, 
        Pathology, 
        #PathologyCategory, 
        PathologyGroup, 
        PatientData, 
        #PatientDiseaseInfo, 
        #PatientEvaluation, 
        #PatientVaccination, 
        #SecondaryCondition, 
        #SignsAndSymptoms,
        module='health_jamaica_sync', type_='model')
