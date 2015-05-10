from datetime import datetime
from trytond.model import ModelView, ModelSQL, fields, UnionMixin
from trytond.pyson import Eval, Not, Bool
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.wizard import (Wizard, StateView, Button, StateTransition,
                            StateAction)

SIGNED_STATES = {'readonly': Bool(Eval('signed_by'))}

class BaseComponent(ModelSQL, ModelView):
    encounter = fields.Many2One('gnuhealth.encounter', 'Encounter')
    start_time = fields.DateTime('Start')
    sign_time = fields.DateTime('Finish', readonly=True)
    signed_by = fields.Many2One('gnuhealth.healthprofessional', 'Signed by', 
                                readonly=True)
    performed_by = fields.Many2One('gnuhealth.healthprofessional', 'Clinician')
    warning = fields.Boolean('Warning', help="Check this box to alert the "
        "supervisor about this session. It will be shown in red in the "
        "encounter", states=SIGNED_STATES)
    notes = fields.Text('Notes', states = SIGNED_STATES)
    critical_info = fields.Char('Critical Info', readonly=True,
                                depends=['notes'])
    report_info = fields.Function(fields.Text('Report'), 'get_report_info')

    @classmethod
    def __setup__(cls):
        super(BaseComponent, cls).__setup__()
        cls._order = [('start_time', 'ASC')]
        cls._order_name = 'start_time'
        cls.critical_info.depends = cls.get_critical_info_fields()

    def __init__(self, id=None, **kwargs):
        # import pdb; pdb.set_trace()
        # t = Transaction()
        # if id is None:
        #     id = t.context.get('_mm_id', None)
        print('%s\ninit with id=%s and \nkwargs = %s\n%s'%('*'*80, str(id), repr(kwargs), '*'*80))
        super(BaseComponent, self).__init__(id, **kwargs)

    @classmethod
    def get_critical_info_fields(cls):
        '''
        return the list of field names that are used to calculate
        the critical_info summary field
        '''
        return ['notes']

    @staticmethod
    def default_performed_by():
        HealthProfessional = Pool().get('gnuhealth.healthprofessional')
        return HealthProfessional.get_health_professional()

    def make_critical_info(self):
        return ""
        # return a single line, no more than 140 chars to describe the details
        # of what's happening in the measurements in this component

    def get_report_info(self, name):
        return ""
        # return details of the data contained in this component as plain text
        # no length limit

    # @classmethod
    # def write(cls, components, vals, *args):
    #     critical_fields = set(cls.get_critical_info_fields())
    #     for component,val in zip(components, vals):
    #         if set(val.keys())&critical_fields:
    def on_change_with_critical_info(self,*arg, **kwarg):
        return self.make_critical_info()

    @staticmethod
    def default_start_time():
        return datetime.now()

    @classmethod
    @ModelView.button
    def mark_done(cls, components):
        pass
        # save the component and set the state to done


class EncounterComponent(UnionMixin, BaseComponent):
    'Component'
    __name__ = 'gnuhealth.encounter.component'

    start_time_time = fields.Function(fields.Time('Start'),
                                      'get_start_time_time')

    @classmethod
    def __setup__(cls):
        super(EncounterComponent, cls).__setup__()

        if hasattr(cls, '_buttons'):
            pass
        else:
            cls._buttons = {}

        cls._buttons['btn_open'] = {'readonly':Eval(False)}

    @staticmethod
    def union_models():
        return [
            'gnuhealth.encounter.anthropometry',
            'gnuhealth.encounter.ambulatory'
        ]

    def get_start_time_time(self, name):
        # return self.start_time.strftime('%H:%M')
        return self.start_time.time()

    @classmethod
    @ModelView.button
    def btn_open(cls, components, *a, **k):
        model_act_map = {
            'gnuhealth.encounter.ambulatory':'health_actwin_encounter_ambulatory',
            'gnuhealth.encounter.anthropometry':'health_actwin_encounter_anthropometry'
        }
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        Action = pool.get('ir.action')

        # module, fs_id = action.split('.')
        
        # return action_id
        # we're only gonna act for the first component passed in
        print('%s\ncomponents= %ss\nargs = %s\n kwargs = %s\n%s' % ('*'*80, repr(components), 
                                        repr(a), repr(k), '*'*80))
        for comp in components:
            real_comp = cls.union_unshard(comp.id)
            model = real_comp.__name__
            fs_id = model_act_map[model]
            action_id = Action.get_action_id(
                ModelData.get_id('health_encounter', fs_id))
            t = Transaction()
            t.set_context(_mm_id=real_comp.id)
            print('%s\ncontext = %s\n%s'%('*'*80, Transaction().context, '*'*80))
            # import pdb; pdb.set_trace()
            return action_id


class ChooseComponentTypeView(ModelView):
    'Choose Component'
    __name__ = 'gnuhealth.encounter.component_chooser'
    component_type = fields.Selection('component_type_selection', 
                                      'Component Type')

    @classmethod
    def component_type_selection(cls):
        # ToDo: make a better way to turn-on and off component types
        # maybe some kind of registration system
        return [
            ('ambulatory', 'Nursing (Ambulatory)'),
            ('anthropometry', 'Antrhopometry'),
            # ('clinical', 'Clinical')
        ]


class ChooseComponentWizard(Wizard):
    'Choose Component'
    __name__ = 'gnuhealth.encounter.component_chooser.wizard'
    start = StateView(
        'gnuhealth.encounter.component_chooser',
        'health_encounter.health_form_component_chooser', [
         Button('Cancel', 'end', 'tryton-cancel'),
         Button('Next', 'selected', 'tryton-ok', default=True)
                # states={'readonly':Not(Bool(Eval('num_selected')))})
    ])
    selected = StateTransition()
    opener = StateAction(
                            'health_encounter.health_actwin_encounter_base')

    # def transition_open_chosen_component(self):
    #     return 'end'
    def transition_selected(self):
        # import pdb; pdb.set_trace()
        ct = self.start.component_type
        self.opener.action_id = 'health_encounter.health_actwin_encounter_'+ct
        return 'opener'

    @staticmethod
    def do_opener(action):
        # check which component is selected in self.start
        data = {}
        # selected_component = self.start.component_type
        selected_component = 'ambulatory'
        act = 'health_encounter.health_actwin_encounter'
        return_action = '_'.join([act, selected_component])
        print "%s\naction = %s\n%s"%('*'*80, action, '*'*80)
        return action, data
        # return ('health_jamaica_sync_satellite.remote_party_import_wizard',{})


