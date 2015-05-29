

from trytond.wizard import (Wizard, StateView, Button, StateTransition)
from trytond.pool import Pool
from trytond.model import ModelView, fields
from trytond.transaction import Transaction
from .base import EncounterComponentType, EncounterComponent


def model2dict(record, fields=None, with_one2many=True):
    '''rudimentary utility that copies fields from a record into a dict'''
    out = {}
    if fields is None:
        pass  # ToDo: Process record._fields to get a sensible list
    field_names = fields[:]
    if 'id' not in field_names:
        field_names.insert(0, 'id')
    for field_name in field_names:
        field = record._fields[field_name]
        value = getattr(record, field_name, None)
        if field._type in ('many2one', 'reference'):
            if value:
                out[field_name] = value.id
            else:
                out[field_name] = value
        elif field._type in ('one2many'):
            if with_one2many and value:
                out[field_name] = [x.id for x in value]
            elif with_one2many:
                out[field_name] = []
        else:
            out[field_name] = value
    return out


class ChooseComponentTypeView(ModelView):
    'Choose Component'
    __name__ = 'gnuhealth.encounter.component_chooser'
    component_type = fields.Selection('component_type_selection',
                                      'Component Type')

    @classmethod
    def component_type_selection(cls):
        triple = EncounterComponentType.get_selection_list()
        return [x[:2] for x in triple]


class ComponentStateView(StateView):
    '''use this StateView to get the boilerplate that sets up the
    appropriate instance of the component for creation or editing.'''
    def __init__(self, model_name, view_id):
        buttons = [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Save', 'save_x', 'tryton-save'),
            Button('Sign', 'sign_x', 'health-certify')
        ]
        super(ComponentStateView, self).__init__(model_name, view_id, buttons)

    def get_defaults(self, wiz, state_name, fields):
        _real_comp = wiz._component_data['obj']
        return model2dict(_real_comp, fields)


class CStateView(ComponentStateView):  # initialise a StateView from DB
    def __init__(self, component_type_id):
        mvd = EncounterComponentType.read([int(component_type_id)],
                                          fields_names=['model', 'view_name'])
        super(CStateView, self).__init__(mvd['model'], view['view_name'])


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
        ]
    )
    selected = StateTransition()
    # ambulatory = CStateView('ambulatory')
    # anthropometry = CStateView('anthropometry')
    # clinical = CStateView('clinical')
    save_x = StateTransition()
    sign_x = StateTransition()

    def __init__(self, sessionid):
        super(EditComponentWizard, self).__init__(sessionid)
        tact = Transaction()
        active_model = tact.context.get('active_model')
        active_id = tact.context.get('active_id')
        self._component_data = {'model': active_model, 'active_id': active_id}

    def _make_component_state_view(self, component_type_id, model_name=None):
        component_view = None
        if component_type_id:
            component_view = CStateView(component_type_id)
        elif model_name:
            cvm = EncounterComponentType.search([('model', '=', model_name)])
            if cvm:
                component_view = CStateView(cvm[0])
        if component_view:
            self.states['component'] = component_view
        return component_view

    def transition_start(self):
        model = self._component_data['model']
        if model == 'gnuhealth.encounter':
            # going to the selector
            return 'selector'
        else:
            compid = self._component_data['active_id']
            real_component = EncounterComponent.union_unshard(compid)
            self._make_component_state_view(0, real_component.__name__)
            # typename = real_component.__name__.split('.')[-1]
            self._component_data.update(obj=real_component,
                                        id=real_component.id)
            return 'component'

    def transition_selected(self):
        # import pdb; pdb.set_trace()
        state = self._make_component_state_view(self.selector.component_type)
        ComponentModel = Pool().get(state.model_name)
        encounter_id = self._component_data['active_id']
        component_data = {'encounter': encounter_id}
        view = state.get_view()
        field_names = view['fields'].keys()
        if 'id' in field_names:
            del field_names[field_names.index['id']]
        component_data.update(ComponentModel.default_get(field_names))

        real_component = ComponentModel(**component_data)
        self._component_data.update(obj=real_component)
        return 'component'

    def transition_sign_x(self):
        return 'end'

    def transition_save_x(self):
        model = self._component_data['model']
        component = None
        # state_name = 'component'
        if model != 'gnuhealth.encounter':
            compid = self._component_data['active_id']
            component = EncounterComponent.union_unshard(compid)
        state_model = self.component
        state_model.critical_info = state_model.make_critical_info()
        # next_state = state_name #set to return there on error
        if component:
            state = self.states['component']
            view = state.get_view()
            field_names = view['fields'].keys()
            if 'critical_info' not in field_names:
                field_names.append('critical_info')
            data = model2dict(state_model, field_names, False)
            model = Pool().get(component.__name__)
            model.write([component], data)
        else:
            state_model.save()
        next_state = 'end'
        return next_state
