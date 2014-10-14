

from trytond.wizard import (Wizard, StateView, StateTransition, Button,
                            StateAction)
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

from .reports import DailyPatientRegister

__all__ = ['PatientRegisterModel', 'PatientRegisterWizard']


class PatientRegisterModel(ModelView):
    '''Patient Evaluation Register'''
    __name__ = 'healthjm.report.patientregister.start'
    on_or_after = fields.Date('Start date', required=True)
    on_or_before = fields.Date('End date')
    institution = fields.Many2One('gnuhealth.institution', 'Institution',
                                  states={'readonly': True}, required=True)
    specialty = fields.Many2One('gnuhealth.specialty', 'Specialty',
                                depends=['institution'])

    @classmethod
    def __setup__(cls):
        super(PatientRegisterModel, cls).__setup__()
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
    def on_change_with_specialty(self):
        # print('we got a inst = '+str(self.institution))
        if self.institution:
            self.specialty.domain = [
                ('id', 'in', tuple([x.specialty.id
                                    for x in self.institution.specialties]))
            ]
        else:
            self.specialty.domain = []
        return {}


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
            data['specialty'] = self.start.specialty.id

        if self.start.institution:
            data['institution'] = self.start.institution.id
        else:
            self.start.raise_user_error('required_institution')
            return 'start'

        return action, data
