import os
from tryton_synchronisation import SyncMixin, SyncUUIDMixin, SyncMode
from trytond.model import ModelSQL
from trytond.pool import PoolMeta
from trytond.transaction import Transaction
__all__ = ['Party', 'PartyAddress', 'OperationalArea',
    'OperationalSector', 'DomiciliaryUnit', 'AlternativePersonID',
    'MedicalSpecialty', 'HealthInstitution', 'HealthInstitutionSpecialties',
    'HospitalUnit', 'HospitalWard', 'HealthProfessional',
    'HealthProfessionalSpecialties',  'PathologyCategory', 'PathologyGroup',
    'Pathology', 'DiseaseMembers', 'HealthInstitutionOperationalSector',
    'PatientData', 'Country', 'CountrySubdivision', 'PostOffice',
    'DistrictCommunity', 'ProcedureCode', 'Appointment', 'PatientDiseaseInfo',
    'Directions', 'PatientEvaluation', 'SecondaryCondition',
    'SignsAndSymptoms', 'DiagnosticHypothesis', 'Ethnicity']


class Party(SyncMixin):
    __name__ = 'party.party'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.full

    def get_wire_value(self):
        values = super(Party, self).get_wire_value()
        if 'internal_user' in values:
            del(values['internal_user'])
        return values

    @classmethod
    def get_to_synchronise(cls, remote_sync_data=None):
        if remote_sync_data:
            return super(Party, cls).get_to_synchronise(remote_sync_data)
        else:
            with Transaction().set_context(active_test=False) as t:
                unsync_domain = ['AND',('synchronised', '=', False),
                                ['OR', ('is_healthprof','=',True),
                                ('is_institution','=',True)]]
                unsynced = cls.search(unsync_domain)

            return [r.get_wire_value() for r in unsynced]


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
    sync_mode = SyncMode.none

class DistrictCommunity(SyncMixin):
    __name__ = 'country.district_community'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.none

class OperationalArea(SyncMixin):
    __name__ = 'gnuhealth.operational_area'
    __metaclass__ = PoolMeta
    unique_id_column = 'name'
    sync_mode = SyncMode.none


class OperationalSector(SyncMixin):
    __name__ = 'gnuhealth.operational_sector'
    __metaclass__ = PoolMeta
    unique_id_column = 'name'
    sync_mode = SyncMode.none


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

    def get_wire_value(self):
        values = super(HealthInstitution, self).get_wire_value()
        if 'main_specialty' in values:
            del(values['main_specialty'])
        return values


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
    sync_mode = SyncMode.full

    def get_wire_value(self):
        values = super(HealthProfessional, self).get_wire_value()
        if 'main_specialty' in values:
            del(values['main_specialty'])
        return values


class HealthProfessionalSpecialties(SyncUUIDMixin):
    __name__ = 'gnuhealth.hp_specialty'
    __metaclass__ = PoolMeta


class Appointment(SyncUUIDMixin):
    __name__ = 'gnuhealth.appointment'
    __metaclass__ = PoolMeta

class PathologyCategory(SyncMixin):
    __name__ = 'gnuhealth.pathology.category'
    __metaclass__ = PoolMeta
    unique_id_column = 'name'
    sync_mode = SyncMode.update

class PathologyGroup(SyncMixin):
    __name__ = 'gnuhealth.pathology.group'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.update

class Pathology(SyncMixin):
    __name__ = 'gnuhealth.pathology'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.none


class DiseaseMembers(SyncUUIDMixin):
    __name__ = 'gnuhealth.disease_group.members'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.update


class ProcedureCode(SyncMixin):
    __name__ = 'gnuhealth.procedure'
    __metaclass__ = PoolMeta
    unique_id_column = 'name'
    sync_mode = SyncMode.none


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


class PatientData(SyncMixin):
    __name__ = 'gnuhealth.patient'
    __metaclass__ = PoolMeta
    unique_id_column = 'puid'


class PatientDiseaseInfo(SyncUUIDMixin):
    __name__ = 'gnuhealth.patient.disease'
    __metaclass__ = PoolMeta


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


class PatientEvaluation(SyncUUIDMixin):
    __name__ = 'gnuhealth.patient.evaluation'
    __metaclass__ = PoolMeta


class PatientVaccination(SyncUUIDMixin):
    __name__ = 'gnuhealth.vaccination'
    __metaclass__ = PoolMeta


class Ethnicity(SyncMixin):
    __name__ = 'gnuhealth.ethnicity'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
