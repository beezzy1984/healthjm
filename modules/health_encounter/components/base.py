from datetime import datetime
from trytond.model import ModelView, ModelSQL, fields, UnionMixin
from trytond.pyson import Eval, Not, Bool
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.wizard import (Wizard, StateView, Button, StateTransition,
                            StateAction)
from trytond.modules.health_jamaica import tryton_utils as utils

SIGNED_STATES = {'readonly': Bool(Eval('signed_by'))}

class BaseComponent(ModelSQL, ModelView):
    encounter = fields.Many2One('gnuhealth.encounter', 'Encounter',
                                readonly=True)
    start_time = fields.DateTime('Start')
    sign_time = fields.DateTime('Finish', readonly=True)
    signed_by = fields.Many2One('gnuhealth.healthprofessional', 'Signed by', 
                                readonly=True)
    performed_by = fields.Many2One('gnuhealth.healthprofessional', 'Clinician')
    warning = fields.Boolean('Warning', help="Check this box to alert the "
        "supervisor about this session. It will be shown in red in the "
        "encounter", states=SIGNED_STATES)
    notes = fields.Text('Notes', states = SIGNED_STATES)
    critical_info = fields.Char('Summary', readonly=True,
                                depends=['notes'])
    report_info = fields.Function(fields.Text('Report'), 'get_report_info')

    @classmethod
    def __setup__(cls):
        super(BaseComponent, cls).__setup__()
        cls._order = [('start_time', 'ASC')]
        cls._order_name = 'start_time'
        cls.critical_info.depends = cls.get_critical_info_fields()

    @staticmethod
    def default_performed_by():
        HealthProfessional = Pool().get('gnuhealth.healthprofessional')
        return HealthProfessional.get_health_professional()

    @classmethod
    def get_critical_info_fields(cls):
        '''
        return the list of field names that are used to calculate
        the critical_info summary field
        '''
        return ['notes']

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
    component_type = fields.Function(fields.Char('Type'),
                                     'get_component_type_name')
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
            'gnuhealth.encounter.ambulatory',
            'gnuhealth.encounter.clinical'
        ]

    def get_start_time_time(self, name):
        # return self.start_time.strftime('%H:%M')
        return utils.localtime(self.start_time).time()

    def get_component_type_name(self, name):
        titles = [
            'Anthro',
            'Vitals',
            'Clinical'
        ]
        recid, title_index = divmod(self.id, len(titles))
        return titles[title_index]

    def get_report_info(self, name):
        real_component = self.union_unshard(self.id)
        return real_component.get_report_info(name)

    @classmethod
    @ModelView.button_action(
        'health_encounter.health_wizard_encounter_edit_component')
    def btn_open(cls, components, *a, **k):
        pass
        # pool = Pool()
        # ModelData = pool.get('ir.model.data')
        # Action = pool.get('ir.action')

        # # we're only gonna act for the first component passed in
        # for comp in components:
        #     fs_id = 'health_wizard_encounter_edit_component'
        #     action_id = Action.get_action_id(
        #         ModelData.get_id('health_encounter', fs_id))
        #     return action_id


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
            ('clinical', 'Clinical')
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
    opener = StateAction('health_encounter.health_actwin_encounter_base')

    # def transition_open_chosen_component(self):
    #     return 'end'
    def transition_selected(self):
        # import pdb; pdb.set_trace()
        ct = self.start.component_type
        self.opener.action_id = 'health_encounter.health_actwin_encounter_'+ct
        return 'opener'

    def __init__(self, sessionid):
        super(ChooseComponentWizard, self).__init__(sessionid)
        t = Transaction()
        SS='*'*80
        print('%s\nChooser_Context = %s\n%s'%(SS, repr(t.context), SS))

    # @staticmethod
    # def do_opener(action):
    #     # check which component is selected in self.start
    #     data = {}
    #     # selected_component = self.start.component_type
    #     selected_component = 'ambulatory'
    #     act = 'health_encounter.health_actwin_encounter'
    #     return_action = '_'.join([act, selected_component])
    #     return action, data

def model2dict(record, fields=None):
    '''rudimentary utility that copies fields from a record into a dict'''
    out = {}
    if fields is None:
        pass # ToDo: Process record._fields to get a sensible list
    field_names = fields[:]
    if 'id' not in field_names:
        field_names.insert(0, 'id')
    for field_name in field_names:
        field = record._fields[field_name]
        value = getattr(record, field_name, None)
        if field._type in ('many2one', 'reference'):
            if value:
                out[field_name] = value.id 
            else :
                out[field_name] = value
        elif field._type in ('one2many'):
            out[field_name] = [x.id for x in value]
        else:
            out[field_name] = value
    return out


class CStateView(StateView):
    def __init__(self, component_type_name):
        model = 'gnuhealth.encounter.%s'%component_type_name
        view = 'health_encounter.health_view_form_encounter_%s'%component_type_name
        buttons = [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Save', 'save_x', 'tryton-save'),
            Button('Sign', 'sign_x', 'health-certify')
        ]
        super(CStateView, self).__init__(model, view, buttons)

    def get_defaults(self, wiz, state_name, fields):
        _real_comp = wiz._component_data['obj']
        return model2dict(_real_comp, fields)


class EditComponentWizard(Wizard):
    'Edit Component'
    __name__ = 'gnuhealth.encounter.component_editor.wizard'
    start = StateTransition()
    selector = StateView(
        'gnuhealth.encounter.component_chooser',
        'health_encounter.health_form_component_chooser', [
         Button('Cancel', 'end', 'tryton-cancel'),
         Button('Next', 'selected', 'tryton-ok', default=True)
                # states={'readonly':Not(Bool(Eval('num_selected')))})
    ])
    selected = StateTransition()
    ambulatory = CStateView('ambulatory')
    anthropometry = CStateView('anthropometry')
    clinical = CStateView('clinical')
    save_x = StateTransition()
    sign_x = StateTransition()

    def __init__(self, sessionid):
        super(EditComponentWizard, self).__init__(sessionid)
        tact = Transaction()
        active_model = tact.context.get('active_model')
        active_id = tact.context.get('active_id')
        self._component_data = {'model':active_model, 'active_id': active_id}

    def transition_start(self):
        model = self._component_data['model']
        if model == 'gnuhealth.encounter':
            # going to the selector
            return 'selector'
        else:
            compid = self._component_data['active_id']
            real_component = EncounterComponent.union_unshard(compid)
            typename = real_component.__name__.split('.')[-1]
            self._component_data.update(obj=real_component,
                                        id=real_component.id)
            return typename

    def transition_selected(self):
        # import pdb; pdb.set_trace()
        comp_type = self.selector.component_type
        ComponentModel = Pool().get('gnuhealth.encounter.%s'%comp_type)
        encounter_id = self._component_data['active_id']
        component_data = {'encounter':encounter_id}
        view = self.states[comp_type].get_view()
        field_names = view['fields'].keys()
        if 'id' in field_names:
            del field_names[field_names.index['id']]
        component_data.update(ComponentModel.default_get(field_names))

        real_component = ComponentModel(**component_data)
        self._component_data.update(obj=real_component)
        return comp_type

    def transition_sign_x(self):
        return 'end'

    def transition_save_x(self):
        import pdb; pdb.set_trace()
        component = self._component_data['obj']
        state_name = component.__name__.split('.')[-1]
        state_model = getattr(self, state_name)
        state = self.states[state_name]
        view = state.get_view()
        fields = view['fields'].keys()
        if 'critical_info' not in fields:
            fields.append('critical_info')
        state_model.critical_info = state_model.make_critical_info()
        data = model2dict(state_model, fields)
        model = Pool().get(component.__name__)
        next_state = state_name
        # try:
        if component.id > 0:
            model.write([component], data)
        else:
            # model.create([data])
            state_model.save()
        next_state = 'end'
        # except:
        #     raise
        
        return next_state
