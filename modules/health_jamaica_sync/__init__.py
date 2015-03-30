from trytond.pool import Pool
# from .celerytools import *
from .health import *


def register():
    Pool.register(
        # Sync,
        Country,
        CountrySubdivision,
        PostOffice,
        DistrictCommunity,
        Party,
        PartyAddress,
        OperationalArea,
        OperationalSector,
        DomiciliaryUnit,
        MedicalSpecialty,
        HealthInstitution,
        HealthInstitutionSpecialties,
        HealthInstitutionOperationalSector,
        AlternativePersonID,
        HealthProfessional,
        HealthProfessionalSpecialties, 
        Appointment, 
        HospitalUnit,
        HospitalWard,
        PathologyCategory, 
        PathologyGroup,
        Pathology,
        # DiseaseMembers, # removed due to 
            #WARNING:init:unable to add 'UNIQUE(uuid)' constraint on table gnuhealth_disease_group_members !
        ProcedureCode,
        PatientData,
        PatientEvaluation, 
        PatientDiseaseInfo, 
        DiagnosticHypothesis,
        #PatientVaccination, 
        SecondaryCondition, 
        SignsAndSymptoms,
        Directions,
        Ethnicity,
        module='health_jamaica_sync', type_='model')
