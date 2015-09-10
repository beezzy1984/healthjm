import os
from trytond.model import ModelSQL
from trytond.pool import PoolMeta
from trytond.transaction import Transaction
__all__ = ['Party', 'PartyAddress', 'DomiciliaryUnit', 'AlternativePersonID',
    'HealthProfessional', 'PatientVaccination', 
    'HealthProfessionalSpecialties', 'PatientData', 'Appointment',
    'PatientDiseaseInfo', 'Directions', 'PatientEvaluation',
    'SecondaryCondition', 'SignsAndSymptoms', 'DiagnosticHypothesis']

class HistoryMixin(ModelSQL):
    _history = True


class Party(HistoryMixin):
    __name__ = 'party.party'

class PartyAddress(HistoryMixin):
    __name__ = 'party.address'


class DomiciliaryUnit(HistoryMixin):
    __name__ = 'gnuhealth.du'


class AlternativePersonID (HistoryMixin):
    __name__ = 'gnuhealth.person_alternative_identification' 


class PatientData(HistoryMixin):
    __name__ = 'gnuhealth.patient'


class PatientDiseaseInfo(HistoryMixin):
    __name__ = 'gnuhealth.patient.disease'


class Appointment(HistoryMixin):
    __name__ = 'gnuhealth.appointment'

class HealthInstitutionSpecialties(HistoryMixin):
    __name__ = 'gnuhealth.institution.specialties'

class HealthProfessional(HistoryMixin):
    __name__ = 'gnuhealth.healthprofessional'

class HealthProfessionalSpecialties(HistoryMixin):
    __name__ = 'gnuhealth.hp_specialty'


class DiagnosticHypothesis(HistoryMixin):
    __name__ = 'gnuhealth.diagnostic_hypothesis'


class SecondaryCondition(HistoryMixin):
    __name__ = 'gnuhealth.secondary_condition'


class SignsAndSymptoms(HistoryMixin):
    __name__ = 'gnuhealth.signs_and_symptoms'


class Directions(HistoryMixin):
    __name__ = 'gnuhealth.directions'


class PatientEvaluation(HistoryMixin):
    __name__ = 'gnuhealth.patient.evaluation'


class PatientVaccination(HistoryMixin):
    __name__ = 'gnuhealth.vaccination'
