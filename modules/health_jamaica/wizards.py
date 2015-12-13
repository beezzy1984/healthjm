
from datetime import timedelta

from sql import Literal, Join
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Not, Bool, PYSONEncoder, Equal
from trytond.wizard import (Wizard, StateView, StateTransition, Button,
                            StateAction)

from .reports import DailyPatientRegister

__all__ = ['PatientRegisterModel', 'PatientRegisterWizard',
           'PatientRegisterFilterView', 'PatientRegisterFilteredWizard',
           'AppointmentReport', 'OpenAppointmentReportStart',
           'OpenAppointmentReport', 'StartEndDateModel', 'PRFDisease',
           'PRFProcedure']



class StartEndDateModel(ModelView):
    '''Generic ModelView that has start and end date fields. '''
    __name__ = 'healthjm.report.startenddate_generic'

    on_or_after = fields.Date('Start date', required=True)
    on_or_before = fields.Date('End date')
    institution = fields.Many2One('gnuhealth.institution', 'Institution',
                                  required=True, states={'readonly':True})

    @classmethod
    def __setup__(cls):
        super(StartEndDateModel, cls).__setup__()
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


class PatientRegisterModel(StartEndDateModel):
    '''Patient Evaluation Register'''
    __name__ = 'healthjm.report.patientregister.start'
    specialty = fields.Selection('get_specialty_list', 'Specialty')

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
        'health_jamaica.healthjm_form_patientregister_report_start', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Generate Report', 'generate_report', 'tryton-ok',
                    default=True),
        ])
    generate_report = StateAction(
                            'health_jamaica.healthjm_report_patientregister')


    def transition_generate_report(self):
        return 'end'

    def do_generate_report(self, action):
        # specify data that will be passed to .parse on the report object
        data = {'start_date':self.start.on_or_after,
                'end_date':self.start.on_or_after,
                'specialty':None,
                'facility':None,
                'x_extra_criteria': False}

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


def permute_opts(name='diseases'):
    return [
        ('OR', 'Include ANY of the selected %s (OR)' % name),
        ('AND', 'Include ALL of the selected %s (AND)' % name)]
        # ('nor', 'Include None of the selected %s (NOR)' % name)]


class PatientRegisterFilterView(PatientRegisterModel):
    'Patient Evaluation Register (by Disease)'
    __name__ = 'healthjm.report.patientregister_filtered.start'
    dp_perm = fields.Selection(
        [('dp', 'Both Diseases and Procedures'), ('d', 'Diseases Only'),
         ('p', 'Procedures Only'), ('o', 'Either Diseases or Procedures')],
        'Filter by', sort=False)
    diseases = fields.One2Many(
        'healthjm.report.patientregister_filtered.disease_o2m', 'prf',
        'Selected Diseases', states={'readonly': Equal(Eval('dp_perm'), 'p')})
    procedures = fields.One2Many(
        'healthjm.report.patientregister_filtered.procedure_o2m', 'prf',
        'Selected Procedures', states={'readonly': Equal(Eval('dp_perm'), 'd')})

    disease_perm = fields.Selection(permute_opts(), 'Disease option', sort=False)
    procedure_perm = fields.Selection(permute_opts('procedures'),
                                      'Procedure option', sort=False)

    @staticmethod
    def default_disease_perm():
        return 'AND'

    @staticmethod
    def default_procedure_perm():
        return 'AND'

    @staticmethod
    def default_dp_perm():
        return 'o'


class PRFDisease(ModelView):
    'Patient Evaluation Register - Diseases'
    __name__ = 'healthjm.report.patientregister_filtered.disease_o2m'
    prf = fields.Many2One('healthjm.report.patientregister_filtered.start',
                          'PRF', readonly=True)
    pathology = fields.Many2One('gnuhealth.pathology', 'Disease',
                                required=True)
    invert = fields.Boolean('Invert',
                            help='exclude rather than include this one')


class PRFProcedure(ModelView):
    'Patient Evaluation Register - Procedures'
    __name__ = 'healthjm.report.patientregister_filtered.procedure_o2m'
    prf = fields.Many2One('healthjm.report.patientregister_filtered.start',
                          'PRF', readonly=True)
    procedure = fields.Many2One('gnuhealth.procedure', 'Procedure',
                                required=True)
    invert = fields.Boolean('Invert',
                            help='exclude rather than include this one')


class PatientRegisterFilteredWizard(PatientRegisterWizard):
    '''Evaluation Register Wizard'''
    __name__ = 'healthjm.report.patientregister_filtered.wizard'

    start = StateView(
        'healthjm.report.patientregister_filtered.start',
        'health_jamaica.healthjm_form_patientregisterflt_report_start', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Generate Report', 'generate_report', 'tryton-ok',
                   default=True),
        ])
    generate_report = StateAction(
        'health_jamaica.healthjm_report_patientregister_filtered')

    def transition_generate_report(self):
        return 'end'

    def do_generate_report(self, action):
        def make_disease_domain(disease):
            if disease.invert:
                return (['AND', ('diagnosis', '!=', disease.pathology.id),
                        ('secondary_conditions.pathology', '!=',
                         disease.pathology.id)],
                        u'Not(%s [%s])' % (disease.pathology.name,
                                           disease.pathology.code))
            else:
                return (['OR', ('diagnosis', '=', disease.pathology.id),
                        ('secondary_conditions.pathology', '=',
                         disease.pathology.id)],
                        u'%s [%s]' % (disease.pathology.name,
                                      disease.pathology.code))

        def make_procedure_domain(procedure):
            if procedure.invert:
                return (('procedures.procedure', '=', procedure.procedure.id),
                        u'Not(%s [%s])' % (procedure.description,
                                           procedure.name))
            else:
                return (('procedures.procedure', '=', procedure.procedure.id),
                        u'%s [%s]' % (procedure.procedure.description,
                                      procedure.procedure.name))

        bad_action, data = super(
            PatientRegisterFilteredWizard, self).do_generate_report(action)

        search_criteria = {'disease': [], 'procedure': []}
        search_criteria_names = {'disease': [], 'procedure': []}

        if self.start.dp_perm in ('dp', 'd', 'o') and self.start.diseases:
            for disease in self.start.diseases:
                criteria, name = make_disease_domain(disease)
                search_criteria['disease'].append(criteria)
                search_criteria_names['disease'].append(name)
            if len(search_criteria_names['disease']) == 1:
                search_criteria['disease'] = search_criteria['disease'][0]
            else:
                search_criteria['disease'].insert(0, self.start.disease_perm)

        if self.start.dp_perm in ('dp', 'p', 'o') and self.start.procedures:
            for proc in self.start.procedures:
                criteria, name = make_procedure_domain(proc)
                search_criteria['procedure'].append(criteria)
                search_criteria_names['procedure'].append(name)
            if len(search_criteria_names['procedure']) == 1:
                search_criteria['procedure'] = search_criteria['procedure'][0]
            else:
                search_criteria['procedure'].insert(0,
                                                    self.start.procedure_perm)

        data.update(x_extra_criteria=True, x_search_criteria=search_criteria,
                    x_selected=search_criteria_names,
                    x_dp_perm=self.start.dp_perm,
                    x_encounter_fields=['patient.name.du.simple_address',
                    'patient.name.du.address_subdivision.name'],
                    x_selected_count=dict(
                        [(a, len(b))
                         for a, b in search_criteria_names.items()]))

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
