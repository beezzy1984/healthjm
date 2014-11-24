from trytond.pool import Pool
from .celerytools import *
from .health import *
from .remote_party import RemoteParty


def register():
    Pool.register(
        Sync,
        Country,
        CountrySubdivision,
        PostOffice,
        DistrictCommunity,
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
        AlternativePersonID,
        HealthProfessional,
        HealthProfessionalSpecialties, 
        Appointment, 
        HospitalUnit,
        HospitalWard,
        PathologyCategory, 
        PathologyGroup,
        Pathology,
        ProcedureCode,
        PatientData,
        PatientEvaluation, 
        PatientDiseaseInfo, 
        DiagnosticHypothesis,
        #PatientVaccination, 
        SecondaryCondition, 
        SignsAndSymptoms,
        Directions,
        RemoteParty,
        module='health_jamaica_sync', type_='model')
