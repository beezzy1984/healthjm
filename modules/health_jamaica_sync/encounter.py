
from tryton_synchronisation import SyncUUIDMixin, SyncMode
from trytond.pool import PoolMeta

__all__ = [
    'SecondaryCondition', 'SignsAndSymptoms', 'Directions',
    'DiagnosticHypothesis', 'PatientEvaluation', 'PatientVaccination',
    'PatientEncounter', 'EncounterClinical', 'EncounterProcedures',
    'EncounterAnthro', 'EncounterAmbulatory', 'EncounterMentalStatus'
]


class SecondaryCondition(SyncUUIDMixin):
    __name__ = 'gnuhealth.secondary_condition'
    __metaclass__ = PoolMeta


class SignsAndSymptoms(SyncUUIDMixin):
    __name__ = 'gnuhealth.signs_and_symptoms'
    __metaclass__ = PoolMeta


class Directions(SyncUUIDMixin):
    __name__ = 'gnuhealth.directions'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.full


class DiagnosticHypothesis(SyncUUIDMixin):
    __name__ = 'gnuhealth.diagnostic_hypothesis'
    __metaclass__ = PoolMeta


class PatientEvaluation(SyncUUIDMixin):
    __name__ = 'gnuhealth.patient.evaluation'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.none


class PatientVaccination(SyncUUIDMixin):
    __name__ = 'gnuhealth.vaccination'
    __metaclass__ = PoolMeta


class PatientEncounter(SyncUUIDMixin):
    __name__ = 'gnuhealth.encounter'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.full

    @classmethod
    def get_unsync_domain(cls):
        return [('state', 'in', ['signed', 'invalid'])]


class EncounterClinical(SyncUUIDMixin):
    __name__ = 'gnuhealth.encounter.clinical'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.full


class EncounterProcedures(SyncUUIDMixin):
    __name__ = 'gnuhealth.encounter.procedures'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.full


class EncounterAnthro(SyncUUIDMixin):
    __name__ = 'gnuhealth.encounter.anthropometry'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.full


class EncounterAmbulatory(SyncUUIDMixin):
    __name__ = 'gnuhealth.encounter.ambulatory'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.full


class EncounterMentalStatus(SyncUUIDMixin):
    __name__ = 'gnuhealth.encounter.mental_status'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.full
