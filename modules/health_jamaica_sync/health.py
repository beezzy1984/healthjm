import os
from tryton_synchronisation import SyncMixin, SyncUUIDMixin, SyncMode
from trytond.model import ModelSQL
from trytond.pool import PoolMeta
__all__ = [
    'OperationalArea', 'OperationalSector',
    'MedicalSpecialty', 'HealthInstitution', 'HealthInstitutionSpecialties',
    'HealthInstitutionOperationalSector', 'HealthProfessional', 'Appointment',
    'HealthProfessionalSpecialties', 'PathologyCategory', 'PathologyGroup',
    'Pathology', 'DiseaseMembers', 'ProcedureCode', 'HospitalUnit',
    'HospitalWard'
]


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


class MedicalSpecialty(SyncMixin):
    __name__ = 'gnuhealth.specialty'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.none


class HealthInstitution(SyncMixin):
    __name__ = 'gnuhealth.institution'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.none

    def get_wire_value(self):
        values = super(HealthInstitution, self).get_wire_value()
        if 'main_specialty' in values:
            del(values['main_specialty'])
        return values


class HealthInstitutionSpecialties(SyncUUIDMixin):
    __name__ = 'gnuhealth.institution.specialties'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.update


class HealthInstitutionOperationalSector(SyncMixin):
    __name__ = 'gnuhealth.institution.operationalsector'
    __metaclass__ = PoolMeta
    unique_id_column = 'sync_code'
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


class HospitalUnit(SyncUUIDMixin):
    __name__ = 'gnuhealth.hospital.unit'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.update


class HospitalWard(SyncUUIDMixin):
    __name__ = 'gnuhealth.hospital.ward'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.update
