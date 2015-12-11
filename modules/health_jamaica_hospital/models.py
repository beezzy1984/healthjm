
from datetime import datetime
from trytond.model import  ModelSQL, ModelView
from trytond.pool import Pool
from ..health_jamaica.tryton_utils import (replace_clause_column, get_timezone)


__all__ = ['HospitalBed', 'InpatientRegistration', 'PatientRounding']


class HospitalBed(ModelSQL, ModelView):
    'Hospital Bed'
    __name__ = 'gnuhealth.hospital.bed'

    def get_rec_name(self, name):
        if self.name:
            return self.name.code
        else:
            return "Unlabeled bed %d" % (self.id)

    @classmethod
    def search_rec_name(cls, name, clause):
        return ['OR', replace_clause_column(clause, 'name.name'),
                replace_clause_column(clause, 'name.code')]


class InpatientRegistration(ModelSQL, ModelView):
    'Patient admission History'
    __name__ = 'gnuhealth.inpatient.registration'

    @classmethod
    @ModelView.button
    def admission(cls, registrations):
        # redefined to fix a date bug
        registration_id = registrations[0]
        Bed = Pool().get('gnuhealth.hospital.bed')
        tz = get_timezone()
        if (registration_id.hospitalization_date.date() >
            datetime.now(tz).date()):
            cls.raise_user_error("The Admission date must be today or earlier")
        else:
            cls.write(registrations, {'state': 'hospitalized'})
            Bed.write([registration_id.bed], {'state': 'occupied'})

    def get_rec_name(self, name):
        if self.patient:
            return '%s: %s (%s)'%(self.name, self.patient.name.name,
                                      self.patient.puid)
        else:
            return self.name


class PatientRounding(ModelSQL, ModelView):
    'Patient Round'
    __name__ = 'gnuhealth.patient.rounding'

    @classmethod
    def __setup__(cls):
        super(PatientRounding, cls).__setup__()
        cls.name.string = "Inpatient"
