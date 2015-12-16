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
        PatientEncounter,
        EncounterClinical,
        EncounterProcedures,
        EncounterAnthro,
        EncounterAmbulatory,
        EncounterMentalStatus,
        module='health_jamaica_history', type_='model')
