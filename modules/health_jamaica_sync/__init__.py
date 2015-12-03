from trytond.pool import Pool

from .simple import *
from .party import *
from .health import *
from .encounter import *


def register():
    Pool.register(
        # .simple
        Country, CountrySubdivision, PostOffice, DistrictCommunity,
        OccupationalGroup, Ethnicity,

        # .party
        Party, PartyAddress, AlternativePersonID, DomiciliaryUnit,
        PatientData, PatientDiseaseInfo,

        # .health
        OperationalArea, OperationalSector,
        MedicalSpecialty, HealthInstitution, HealthInstitutionSpecialties,
        HealthInstitutionOperationalSector, HealthProfessional, Appointment,
        HealthProfessionalSpecialties, PathologyCategory, PathologyGroup,
        Pathology, DiseaseMembers, ProcedureCode, HospitalUnit, HospitalWard,

        # .encounter
        SecondaryCondition, SignsAndSymptoms, Directions,
        DiagnosticHypothesis, PatientEvaluation, PatientVaccination,
        PatientEncounter, EncounterClinical, EncounterProcedures,
        EncounterAnthro, EncounterAmbulatory, EncounterMentalStatus,

        module='health_jamaica_sync', type_='model')
