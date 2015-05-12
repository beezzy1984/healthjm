
from datetime import datetime
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Not, Bool, PYSONEncoder, Equal, And, Or
from trytond.pool import Pool
from trytond.modules.health import HealthInstitution, HealthProfessional

class PatientEncounter(ModelSQL, ModelView):
    'Patient Encounter'
    __name__ = 'gnuhealth.encounter'

    STATES = {'readonly':Or(Equal(Eval('state'), 'signed'),
                            Equal(Eval('state'), 'done'))}
    SIGNED_STATES = {'readonly': Equal(Eval('state'), 'signed')}

    state = fields.Selection([
        ('in_progress', 'In progress'),
        ('done', 'Done'),
        ('signed', 'Signed'),
        ], 'State', readonly=True, sort=False)
    patient = fields.Many2One('gnuhealth.patient', 'Patient', required=True,
                              states=STATES)
    primary_complaint = fields.Char('Primary complaint', states=STATES)
    start_time = fields.DateTime('Start', required=True, states=STATES)
    end_time = fields.DateTime('End', states=SIGNED_STATES)
    institution = fields.Many2One('gnuhealth.institution', 'Institution',
                                  required=True)
    appointment = fields.Many2One(
        'gnuhealth.appointment', 'Appointment',
        domain=[('patient', '=', Eval('patient'))], depends=['patient'],
        help='Enter or select the appointment related to this encounter',
        states = STATES)
    next_appointment = fields.Many2One(
            'gnuhealth.appointment', 'Next Appointment',
            domain=[('patient', '=', Eval('patient'))],
            depends=['patient'],
            states = SIGNED_STATES)
    signed_by = fields.Many2One(
        'gnuhealth.healthprofessional', 'Signed By', readonly=True,
        states={'invisible': Equal(Eval('state'), 'in_progress')},
        help="Health Professional that finished the patient evaluation")
    sign_time = fields.DateTime('Sign time', readonly=True)
    components = fields.One2Many('gnuhealth.encounter.component', 'encounter',
                                 'Components')
    summary = fields.Function(fields.Text('Summary'), 'get_encounter_summary')
    # Patient identifier fields
    upi = fields.Function(fields.Char('UPI'), getter='get_person_patient_field')
    medical_record_num = fields.Function(fields.Char('Medical Record Number'),
        'get_person_patient_field')
    sex_display = fields.Function(fields.Char('Sex'),
                                  'get_person_patient_field')
    age = fields.Function(fields.Char('Age'), 'get_person_patient_field')

    @classmethod
    @ModelView.button
    def sign_finish(cls, encounters):
        signing_hp = HealthProfessional().get_health_professional()
        # Change the state of the evaluation to "Done"

        #ToDO: set all the not-done components to DONE as well and sign
        # the unsigned ones
        
        cls.write(encounters, {
            'state': 'signed',
            'signed_by': signing_hp,
            'sign_time': datetime.now()
        })

    @classmethod
    @ModelView.button
    def set_done(cls, encounters):
        signing_hp = HealthProfessional().get_health_professional()
        # Change the state of the evaluation to "Done"
        cls.write(encounters, {
            'state': 'done'
            # 'end_time': dateime.now()
        })

    @staticmethod
    def default_start_time():
        return datetime.now()

    @staticmethod
    def default_institution():
        return HealthInstitution().get_institution()

    @staticmethod
    def default_state():
        return 'in_progress'

    @classmethod
    def __setup__(cls):
        super(PatientEncounter, cls).__setup__()
        cls._error_messages.update({
            'health_professional_warning':
                'No health professional associated with this user',
            'end_date_before_start': 'End time "%(end_time)s" BEFORE'
                ' start time "%(start_time)s"'
        })

        cls._buttons.update({
            'set_done': {'invisible': Not(Equal(Eval('state'), 'in_progress'))},
            'sign_finish': {'invisible': Not(Equal(Eval('state'), 'done'))}
            })


    def get_person_patient_field(self, name):
        if name in ['upi', 'sex_display']:
            return getattr(self.patient.name, name)
        if name in ['age']:
            return getattr(self.patient, name)
        return ''

    def get_encounter_summary(self, name):
        summary_texts = []
        for component in self.components:
            real_component = component.union_unshard(component.id)
            summary_texts.append(real_component.report_info)
        return '\n\n'.join(summary_texts)
