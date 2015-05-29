from datetime import datetime
from trytond.model import ModelView, ModelSQL, fields, UnionMixin
from trytond.pyson import Eval, Bool
from trytond.pool import Pool

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
    warning = fields.Boolean(
        'Warning',
        help="Check this box to alert the supervisor about this session."
        " It will be shown in red in the encounter",
        states=SIGNED_STATES)
    notes = fields.Text('Notes', states=SIGNED_STATES)
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
        # return a single line, no more than 140 chars to describe the details
        # of what's happening in the measurements in this component
        return ""

    def get_report_info(self, name):
        # return details of the data contained in this component as plain text
        # no length limit
        return ""

    def on_change_with_critical_info(self, *arg, **kwarg):
        return self.make_critical_info()

    @staticmethod
    def default_start_time():
        return datetime.now()

    @classmethod
    @ModelView.button
    def mark_done(cls, components):
        pass
        # save the component and set the state to done


class EncounterComponentType(ModelSQL, ModelView):
    'Encounter Component'
    __name__ = 'gnuhealth.encounter.component_model'
    name = fields.Char('Type Name')
    code = fields.Char('Code', size=15,
                       help="Short name Displayed in the first column of the"
                       "encounter. Maximum 15 characters")
    model = fields.Char('Model name', help='e.g. gnuhealth.encounter.clinical',
                        required=True)
    view_form = fields.Char('View name', required=True,
                            help='full xml id of view, e.g. module.xml_id')
    ordering = fields.Integer('Display order')
    active = fields.Boolean('Active')

    @classmethod
    def __setup__(cls):
        super(EncounterComponentType, cls).__setup__()
        cls._order = [('ordering', 'ASC'), ('name', 'ASC')]

    @classmethod
    def register_type(cls, model_class, view):
        # first check if it was previously registered and deactivated
        registration = cls.search([('model', '=', model_class.__name__),
                                   ('view_form', '=', view)])
        if registration:
            registration = cls.browse(registration)
            if not registration.active:
                cls.write(registration, {'active': True})
        else:
            cdata = {'model': model_class.__name__, 'view_form': view}
            cdata['name'] = ''.join(filter(None,
                                           model_class.__doc__.split('\n'))[:1])
            cdata['code'] = cdata['name'][:15]

            # we need to create the registration
            cls.create([cdata])
        return True

    @classmethod
    def get_selection_list(cls):
        '''returns a list of active Encounter component types in a tuple
        of (id, Name, Code)'''
        etypes = cls.search_read([('active', '=', True)],
                                 fields_names=['id', 'name', 'code'])
        return [(x['id'], x['name'], x['code']) for x in etypes]

    @classmethod
    def get_view_name(cls, ids):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        # ids = map(int, ids)
        forms = cls.read(ids, fields_names=['view_form'])
        if forms:
            return forms[0]['view_form']
        return None


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

        cls._buttons['btn_open'] = {'readonly': Eval(False)}

    @staticmethod
    def union_models():
        models = EncounterComponentType.search_read([('active', '=', True)],
                                                    fields_names=('model'),
                                                    order=[('id', 'ASC')])
        return [x['model'] for x in models]

    def get_start_time_time(self, name):
        # return self.start_time.strftime('%H:%M')
        return utils.localtime(self.start_time).time()

    def get_component_type_name(self, name):
        id_names = EncounterComponentType.get_selection_list()
        id_names.sort(key=lambda x: x[0])
        titles = [x[2] for x in id_names]
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
