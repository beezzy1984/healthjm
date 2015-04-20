from datetime import datetime
from trytond.model import ModelView, ModelSQL, fields, UnionMixin
from trytond.pyson import Eval, Not, Bool

SIGNED_STATES = {'readonly': Bool(Eval('signed_by'))}

class BaseComponent(ModelSQL, ModelView):
    encounter = fields.Many2One('gnuhealth.encounter', 'Encounter')
    start_time = fields.DateTime('Start')
    sign_time = fields.DateTime('Finish', readonly=True)
    signed_by = fields.Many2One('gnuhealth.healthprofessional', 'Signed by', 
                                readonly=True)
    warning = fields.Boolean('Warning', help="Check this box to alert the "
        "supervisor about this session. It will be shown in red in the "
        "encounter", states=SIGNED_STATES)
    notes = fields.Text('Notes', states = SIGNED_STATES)
    critical_info = fields.Char('Critical Info', readonly=True)
    report_info = fields.Function(fields.Text('Report'), 'get_report_info')

    @classmethod
    def __setup__(cls):
        super(BaseComponent, cls).__setup__()
        cls._order = [('start_time', 'ASC')]
        cls._order_name = 'start_time'

    def make_critical_info(self):
        return ""
        # return a single line, no more than 140 chars to describe the details
        # of what's happening in the measurements in this component

    def get_report_info(self, name):
        return ""
        # return details of the data contained in this component as plain text
        # no length limit

    @staticmethod
    def default_start_time():
        return datetime.now()


class EncounterComponent(BaseComponent, UnionMixin):
    'Component'
    __name__ = 'gnuhealth.encounter.component'

    start_time_time = fields.Function(fields.Time('Start'),
                                      'get_start_time_time')

    @staticmethod
    def union_models():
        return [
            'gnuhealth.encounter.antrhopometry',
            'gnuhealth.encounter.ambulatory'
        ]

    def get_start_time_time(self, name):
        return self.start_time.strftime('%H:%M')
