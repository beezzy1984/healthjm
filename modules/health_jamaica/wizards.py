
from datetime import timedelta

from sql import Literal, Join
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Not, Bool, PYSONEncoder
from trytond.wizard import (Wizard, StateView, StateTransition, Button,
                            StateAction)

from .reports import DailyPatientRegister

__all__ = ['PatientRegisterModel', 'PatientRegisterWizard',
           'AppointmentReport', 'OpenAppointmentReportStart',
           'OpenAppointmentReport']



class StartEndDateModel(ModelView):
    '''Generic ModelView that has start and end date fields. '''
    on_or_after = fields.Date('Start date', required=True)
    on_or_before = fields.Date('End date')
    institution = fields.Many2One('gnuhealth.institution', 'Institution',
                                  required=True)


class PatientRegisterModel(StartEndDateModel):
    '''Patient Evaluation Register'''
    __name__ = 'healthjm.report.patientregister.start'
    specialty = fields.Selection('get_specialty_list', 'Specialty')

    @classmethod
    def __setup__(cls):
        super(PatientRegisterModel, cls).__setup__()
        cls.institution.states.update(readonly=True)
        cls._error_messages.update({
            'required_institution':'''Institution is required.\n
Your user account is not assigned to an institution.
This assignment is needed before you can use this report.
Please contact your system administrator to have this resolved.'''
            })

    @staticmethod
    def default_institution():
        HealthInst = Pool().get('gnuhealth.institution')
        try:
            institution = HealthInst.get_institution()
        except AttributeError:
            self.raise_user_error('required_institution')
        return institution

    @fields.depends('institution')
    def get_specialty_list(self):
        if self.institution:
            return [(x.specialty.id, x.specialty.name)
                    for x in self.institution.specialties]
        else:
            return []


class PatientRegisterWizard(Wizard):
    '''Evaluation Register Wizard'''
    __name__ = 'healthjm.report.patientregister.wizard'
    start = StateView('healthjm.report.patientregister.start',
        'health_jamaica.report_patientregister_start', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Generate Report', 'generate_report', 'tryton-ok',
                    default=True),
        ])
    generate_report = StateAction('health_jamaica.jmreport_patientregister')


    def transition_generate_report(self):
        return 'end'

    def do_generate_report(self, action):
        # specify data that will be passed to .parse on the report object
        data = {'start_date':self.start.on_or_after,
                'end_date':self.start.on_or_after,
                'specialty':None,
                'facility':None}

        if self.start.on_or_before:
            data['end_date'] = self.start.on_or_before

        if self.start.specialty:
            data['specialty'] = self.start.specialty

        if self.start.institution:
            data['institution'] = self.start.institution.id
        else:
            self.start.raise_user_error('required_institution')
            return 'start'

        return action, data


class AppointmentReport(ModelSQL, ModelView):
    'Appointment Report'
    __name__ = 'gnuhealth.appointment.report'
    speciality = fields.Many2One('gnuhealth.specialty', 'Specialty')

    @classmethod
    def table_query(cls):
        pool = Pool()
        xaction = Transaction()
        appointment = pool.get('gnuhealth.appointment').__table__()
        party = pool.get('party.party').__table__()
        patient = pool.get('gnuhealth.patient').__table__()
        join1 = Join(appointment, patient)
        join1.condition = join1.right.id == appointment.patient
        join2 = Join(join1, party)
        join2.condition = join2.right.id == join1.right.name
        where = Literal(True)
        if xaction.context.get('date_start'):
            where &= (appointment.appointment_date >=
                    xaction.context['date_start'])
        if xaction.context.get('date_end'):
            where &= (appointment.appointment_date <
                    xaction.context['date_end'] + timedelta(days=1))
        if xaction.context.get('healthprof'):
            where &= \
                appointment.healthprof == xaction.context['healthprof']

        if xaction.context.get('specialty', False):
            where &= appointment.speciality == xaction.context['specialty']

        return join2.select(
            appointment.id,
            appointment.create_uid,
            appointment.create_date,
            appointment.write_uid,
            appointment.write_date,
            join2.right.ref,
            join1.right.id.as_('patient'),
            join2.right.sex,
            appointment.appointment_date,
            appointment.appointment_date.as_('appointment_date_time'),
            appointment.healthprof,
            appointment.speciality,
            where=where)

class OpenAppointmentReportStart(ModelView):
    'Open Appointment Report'
    __name__ = 'gnuhealth.appointment.report.open.start'
    specialty = fields.Many2One('gnuhealth.specialty', 'Specialty',
                                states={'required':Not(Bool(Eval('healthprof')))})
    healthprof = fields.Many2One('gnuhealth.healthprofessional', 'Health Professional',
        required=False, states={'required':Not(Bool(Eval('specialty')))})


class OpenAppointmentReport(Wizard):
    'Open Appointment Report'
    __name__ = 'gnuhealth.appointment.report.open'

    def do_open_(self, action):
        action_dict = {'date_start': self.start.date_start,
            'date_end': self.start.date_end }
        if self.start.healthprof:
            action_dict['healthprof'] = self.start.healthprof.id
            action['name'] += ' - {}'.format(self.start.healthprof.name.name)
            
        if self.start.specialty:
            action_dict['specialty'] = self.start.specialty.id
            action['name'] += ' - {}'.format(self.start.specialty.name)

        action['pyson_context'] = PYSONEncoder().encode(action_dict)
        return action, {}
