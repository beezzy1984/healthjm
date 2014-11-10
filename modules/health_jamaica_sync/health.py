import os
from tryton_synchronisation import SyncMixin, SyncUUIDMixin, SyncMode
from trytond.model import ModelSQL
from trytond.pool import PoolMeta

#__all__ = ['Party', 'Country', 'Subdivision', 'Appointment', 
#    'DiagnosticHypothesis', 'DomiciliaryUnit', 'HealthProfessional', 
#    'HospitalUnit', 'HospitalWard', 'HealthProfessionalSpecialties', 
#    'OperationalArea', 'OperationalSector', 'Pathology', 'PathologyCategory', 
#    'PathologyGroup', 'PatientData', 'PatientDiseaseInfo', 'PatientEvaluation', 
#    'PatientVaccination', 'SecondaryCondition', 'SignsAndSymptoms']

__all__ = ['Party', 'PartyAddress', 'OccupationalGroup', 'OperationalArea',
    'OperationalSector', 'DomiciliaryUnit', 'AlternativePersonID',
    'MedicalSpecialty', 'HealthInstitution', 'HealthInstitutionSpecialties',
    'HealthInstitutionOperationalSector', 'PatientData', 'Country',
    'CountrySubdivision', 'PostOffice', 'DistrictCommunity']


class Party(SyncMixin):
    __name__ = 'party.party'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.push_update

    def get_wire_value(self):
        values = super(Party, self).get_wire_value()
        if 'internal_user' in values:
            del(values['internal_user'])
        return values


class PartyAddress(SyncUUIDMixin):
    __name__ = 'party.address'
    __metaclass__ = PoolMeta


class Country(SyncMixin):
    __name__ = 'country.country'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.none

class CountrySubdivision(SyncMixin):
    __name__ = 'country.subdivision'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.none

class PostOffice(SyncMixin):
    __name__ = 'country.post_office'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.update

class DistrictCommunity(SyncMixin):
    __name__ = 'country.district_community'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.update

class OccupationalGroup(SyncMixin):
    '''Occupational Group'''
    __name__ = 'gnuhealth.occupation'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.none

class OperationalArea(SyncMixin):
    __name__ = 'gnuhealth.operational_area'
    __metaclass__ = PoolMeta
    unique_id_column = 'name'


class OperationalSector(SyncMixin):
    __name__ = 'gnuhealth.operational_sector'
    __metaclass__ = PoolMeta
    unique_id_column = 'name'


class DomiciliaryUnit(SyncUUIDMixin):
    __name__ = 'gnuhealth.du'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.push_update


class AlternativePersonID (SyncUUIDMixin):
    __name__ ='gnuhealth.person_alternative_identification' 
    __metaclass__ = PoolMeta

class MedicalSpecialty(SyncMixin):
    __name__ = 'gnuhealth.specialty'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.none

class HealthInstitution(SyncMixin):
    __name__ = 'gnuhealth.institution'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.update

class HealthInstitutionSpecialties(SyncUUIDMixin):
    __name__ = 'gnuhealth.institution.specialties'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.update

class HealthInstitutionOperationalSector(SyncUUIDMixin):
    __name__ = 'gnuhealth.institution.operationalsector'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.update

class HealthProfessional(SyncMixin):
    __name__ = 'gnuhealth.healthprofessional'
    __metaclass__ = PoolMeta
    unique_id_column = 'puid'


class Appointment(SyncUUIDMixin):
    __name__ = 'gnuhealth.appointment'
    __metaclass__ = PoolMeta


class DiagnosticHypothesis(SyncUUIDMixin):
    __name__ = 'gnuhealth.diagnostic_hypothesis'
    __metaclass__ = PoolMeta


class HospitalUnit(SyncUUIDMixin):
    __name__ = 'gnuhealth.hospital.unit'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.update


class HospitalWard(SyncUUIDMixin):
    __name__ = 'gnuhealth.hospital.ward'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.update


class HealthProfessionalSpecialties(SyncUUIDMixin):
    __name__ = 'gnuhealth.hp_specialty'
    __metaclass__ = PoolMeta


class PatientData(SyncMixin):
    __name__ = 'gnuhealth.patient'
    __metaclass__ = PoolMeta
    unique_id_column = 'puid'


class PatientDiseaseInfo(SyncUUIDMixin):
    __name__ = 'gnuhealth.patient.disease'
    __metaclass__ = PoolMeta


class PatientEvaluation(SyncUUIDMixin):
    __name__ = 'gnuhealth.patient.evaluation'
    __metaclass__ = PoolMeta


class PatientVaccination(SyncUUIDMixin):
    __name__ = 'gnuhealth.vaccination'
    __metaclass__ = PoolMeta


class SecondaryCondition(SyncUUIDMixin):
    __name__ = 'gnuhealth.secondary_condition'
    __metaclass__ = PoolMeta


class SignsAndSymptoms(SyncUUIDMixin):
    __name__ = 'gnuhealth.signs_and_symptoms'
    __metaclass__ = PoolMeta
