import os
from tryton_synchronisation import SyncMixin, SyncUUIDMixin
from trytond.model import ModelSQL
from trytond.pool import PoolMeta

#__all__ = ['Party', 'Country', 'Subdivision', 'Appointment', 
#    'DiagnosticHypothesis', 'DomiciliaryUnit', 'HealthProfessional', 
#    'HospitalUnit', 'HospitalWard', 'HealthProfessionalSpecialties', 
#    'OperationalArea', 'OperationalSector', 'Pathology', 'PathologyCategory', 
#    'PathologyGroup', 'PatientData', 'PatientDiseaseInfo', 'PatientEvaluation', 
#    'PatientVaccination', 'SecondaryCondition', 'SignsAndSymptoms']
__all__ = ['Party', 'PatientData']


class Party(SyncMixin):
    __name__ = 'party.party'
    __metaclass__ = PoolMeta
    unique_id_column = 'ref'


class PartyAddress(SyncUUIDMixin):
    __name__ = 'party.address'
    __metaclass__ = PoolMeta


class Country(SyncMixin):
    __name__ = 'country.country'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'


class Subdivision(SyncMixin):
    __name__ = 'country.subdivision'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'


class Appointment(SyncUUIDMixin):
    __name__ = 'gnuhealth.appointment'
    __metaclass__ = PoolMeta


class DiagnosticHypothesis(SyncUUIDMixin):
    __name__ = 'gnuhealth.diagnostic_hypothesis'
    __metaclass__ = PoolMeta


class DomiciliaryUnit(SyncUUIDMixin):
    __name__ = 'gnuhealth.du'
    __metaclass__ = PoolMeta


class HealthProfessional(SyncUUIDMixin):
    __name__ = 'gnuhealth.healthprofessional'
    __metaclass__ = PoolMeta


class HospitalUnit(SyncUUIDMixin):
    __name__ = 'gnuhealth.hospital.unit'
    __metaclass__ = PoolMeta


class HospitalWard(SyncUUIDMixin):
    __name__ = 'gnuhealth.hospital.ward'
    __metaclass__ = PoolMeta


class HealthProfessionalSpecialties(SyncUUIDMixin):
    __name__ = 'gnuhealth.hp_specialty'
    __metaclass__ = PoolMeta


class OperationalArea(SyncMixin):
    __name__ = 'gnuhealth.operational_area'
    __metaclass__ = PoolMeta
    unique_id_column = 'name'


class OperationalSector(SyncMixin):
    __name__ = 'gnuhealth.operational_sector'
    __metaclass__ = PoolMeta
    unique_id_column = 'name'


class Pathology(SyncUUIDMixin):
    __name__ = 'gnuhealth.pathology'
    __metaclass__ = PoolMeta


class PathologyCategory(SyncUUIDMixin):
    __name__ = 'gnuhealth.pathology.category'
    __metaclass__ = PoolMeta


class PathologyGroup(SyncMixin):
    __name__ = 'gnuhealth.pathology.group'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'


class PatientData(SyncUUIDMixin):
    __name__ = 'gnuhealth.patient'
    __metaclass__ = PoolMeta


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
