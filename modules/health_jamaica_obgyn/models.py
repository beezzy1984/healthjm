
from trytond.model import ModelSQL, ModelView, fields
from trytond.pyson import Eval, Not, Bool
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.modules.health_encounter.components import BaseComponent
from datetime import date


HB_OPTIONS = [
    (None, ''),
    ('11+', 'Normal (Hb 11+ g/dl)'),
    ('8+', 'Mild (Hb 8-10 g/dl)'),
    ('<8', 'Severe (Hb less than 8 g/dl)'),
    ('sample', 'Sample taken today')]

POSNEG_OPTIONS = [
    (None, ''),
    ('neg', '-Negative'),
    ('pos', '+Positive'),
    ('sample', 'Sample taken today')]


class PatientPregnancy(ModelSQL, ModelView):
    'Patient Pregnancy'
    __name__ = 'gnuhealth.patient.pregnancy'
    gestation_weeks = fields.Function(fields.Integer('Gestational weeks'),
                                      'get_gestation_age')
    gestation_days = fields.Function(fields.Integer('Gestational days'),
                                     'get_gestation_age')

    def get_gestation_age(self, name):
        gestational_age = date.today() - self.lmp
        if name == 'gestation_weeks':
            return (gestational_age.days) / 7
        if name == 'gestation_days':
            return gestational_age.days

    @classmethod
    def __setup__(cls):
        super(PatientPregnancy, cls).__setup__()
        cls._error_messages.update(
            no_pregnancy='Current pregnancy does not exist.\n'
                         'Create a new entry under the patient\'s\n'
                         'obstetric history.')

    def get_rec_name(self, name):
        tmpl = "Pregnancy #%(gravida)d. LMP %(lmp)s (%(gesw)d weeks) for " +\
               "%(upimrn)s. %(high_risk)s"
        p = self
        val = {'gravida': p.gravida,
               'lmp': p.lmp.strftime('%b %e'),
               'gesw': p.gestation_weeks,
               'upimrn': p.name.puid,
               'high_risk': ''}
        if p.warning:
            val['high_risk'] = 'High risk'

        return tmpl % val

    @classmethod
    def get_for_encounter(cls, encounter_id):
        '''Returns the current pregnancy based on the encounter'''
        pool = Pool()
        encounter_model = pool.get('gnuhealth.encounter')
        encounter, = encounter_model.browse([encounter_id])
        patient = encounter.patient
        pregnancies = cls.search([('name', '=', patient.id),
                                  ('current_pregnancy', '=', True),
                                  ('pregnancy_end_result', '=', None)],
                                 order=[('lmp', 'DESC')])
        print "pregnancies = %s" % repr(pregnancies)
        if pregnancies:
            return pregnancies[0]
        else:
            # what if the current pregnancy doesn't exist?
            cls.raise_user_error('no_pregnancy')
        # Can we not return an unsaved object?


class PrenatalComponent(BaseComponent):
    'Prenatal Component'
    __name__ = 'gnuhealth.patient.prenatal.evaluation'

    screen_hb = fields.Selection(HB_OPTIONS, 'Anemia')
    screen_sickle = fields.Selection(POSNEG_OPTIONS, 'Sickle Cell (SC/SS)')
    screen_syphilis = fields.Selection(POSNEG_OPTIONS, 'Syphilis')
    screen_hiv = fields.Selection(POSNEG_OPTIONS, 'HIV')
    tetanus = fields.Boolean('Tetanus/Fully Immunized')

    @classmethod
    def __setup__(cls):
        super(PrenatalComponent, cls).__setup__()
        # in original prenatal_evaluation table
        # cls.start_time.name = 'evaluation_date'
        # cls.performed_by.name = 'healthprof'
        # cls.evaluation_date = fields.Function(
        #     fields.DateTime('Evaluation Date'), 'get_legacy_field')
        # cls.healthprof = fields.Function(
        #     fields.Many2One('gnuhealth.health_professional', 'HealthProf'),
        #                     'get_legacy_field')

        # cls.start_time = fields.Function(
        #     fields.DateTime('Evaluation Date'), 'get_new_field')
        # cls.performed_by = fields.Function(
        #     fields.Many2One('gnuhealth.health_professional', 'HealthProf'),
        #                     'get_new_field')

    # setup component base fields to put value in counterpart column
    @fields.depends('start_time')
    def on_change_with_evaluation_date(self):
        return self.start_time

    @fields.depends('performed_by')
    def on_change_with_healthprof(self):
        return self.performed_by.id

    def get_report_info(self, name):
        lines = [(u'== Antenatal ==', )]

        return u'\n'.join([u' '.join(x) for x in lines])

    def make_critical_info(self):
        return 'antenatel info dot dot dot'

    @staticmethod
    def default_name():
        pregnancy = Pool().get('gnuhealth.patient.pregnancy')
        tact = Transaction()
        active_model = tact.context.get('active_model')
        active_id = tact.context.get('active_id')
        if active_model == 'gnuhealth.encounter':
            return int(pregnancy.get_for_encounter(active_id))
        else:
            return None
