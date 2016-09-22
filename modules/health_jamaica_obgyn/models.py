
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
    age = fields.Function(fields.Char('Age'), 'get_patient_field')
    puid = fields.Function(fields.Char('UPI'), 'get_patient_field')
    medical_record_num = fields.Function(fields.Char('Medical Record Number'),
                                         'get_patient_field')

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
        cls.prenatal_evaluations.states.update(readonly=True)
        cls.warning.string = "High Risk/Warning"
        cls.warning.help = "Check this box if the pregnancy is not normal\n"+\
                           "or can be considered high risk"

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

    def get_patient_field(self, name):
        return getattr(self.name, name)


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
        cls.name.states.update(readonly=True)
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
        if self.performed_by:
            return self.performed_by.id
        else:
            return None

    def get_report_info(self, name):
        lines = [(u'== Antenatal ==', )]
        ohdp = [(self.overweight, 'Overweight'),
                (self.hypertension, 'Hypertension'),
                (self.diabetes, 'Diabetes'),
                (self.preeclampsia, 'Preeclampsia')]
        lines.append(filter(None, [t if b else False for b, t in ohdp]))
        screen = [(self.screen_hb, 'Hb'),
                  (self.screen_sickle, 'Sickle Cell SC/SS'),
                  (self.screen_syphilis, 'Syphilis'), (self.screen_hiv, 'HIV')]
        stub = []
        for val, title in screen:
            if not (val is None):
                stub.append(('    %s :' % title, val))
        if stub:
            lines.append(('Screening', ))
            lines.extend(stub[:])
            stub = []
        grs = [('Placenta', ['placenta_previa', 'invasive_placentation',
                             'vasa_previa']),
               ('Fetus', ['fundal_height', 'fetus_heart_rate', 'efw',
                'fetal_bpd', 'fetal_hc', 'fetal_ac', 'fetal_fl'])]
        model = Pool().get('gnuhealth.patient.prenatal.evaluation')
        for tt, field_list in grs:
            stub = []
            for fld in field_list:
                val = getattr(self, fld)
                t = model._fields[fld].string
                if val:
                    stub.append(('    %s :' % t, str(val)))
            if stub:
                lines.append((tt,))
                lines.extend(stub[:])
        if self.notes:
            lines.append(('Notes:', ))
            lines.append((self.notes, ))
        return u'\n'.join([u' '.join(x) for x in lines])

    def make_critical_info(self):
        line = []
        hodp = [(self.overweight, 'o'), (self.hypertension, 'h'),
                (self.diabetes, 'd'), (self.preeclampsia, 'p')]
        # OHDP = Overweight, Hypertension, Diabetes, PreEclampsia
        line.append(u''.join([y.upper() if x else y for x, y in hodp]))
        screen = [(self.screen_hb, 'Hb'), (self.screen_sickle, 'SC/SS'),
                  (self.screen_syphilis, 'Syph'), (self.screen_hiv, 'HIV')]
        for fld, title in screen:
            if fld not in ['sample', None]:
                line.append(': '.join([title, fld]))
        if self.tetanus:
            line.append('Immunized: Y')
        if self.fetus_heart_rate:
            line.append('fHeart: %d' % self.fetus_heart_rate)

        return '; '.join(line)

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
