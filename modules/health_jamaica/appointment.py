import re
from datetime import datetime
from trytond.pool import Pool
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Equal, In, Not, And, Bool
from .tryton_utils import is_not_synchro, get_timezone, get_day_comp

APPOINTMENT_STATES = [
    (None, ''),
    ('free', 'Unassigned'),
    ('confirmed', 'Scheduled'),
    ('arrived', 'Arrived/Waiting'),
    ('processing', 'In-Progress'),
    ('done', 'Done'),
    ('user_cancelled', 'Cancelled by patient'),
    ('center_cancelled', 'Cancelled by facility'),
    ('no_show', 'No show')
]


class Appointment(ModelSQL, ModelView):
    'Patient Appointments'
    __name__ = 'gnuhealth.appointment'

    is_today = fields.Function(fields.Boolean('Is Today'), 'get_is_today',
                               searcher='search_is_today')
    tree_color = fields.Function(fields.Char('tree_color'), 'get_tree_color')
    state_changes = fields.One2Many('gnuhealth.appointment.statechange',
                                    'appointment', 'State Changes',
                                    order=([('create_date', 'DESC')]),
                                    readonly=True)

    @staticmethod
    def default_state():
        return 'free'

    # def get_rec_name(self, name):
    #     return '%s %s' % (self.name, self.appointment_date.strftime('%c'))

    @classmethod
    def __setup__(cls):
        super(Appointment, cls).__setup__()
        cls.state.selection = APPOINTMENT_STATES
        cls._buttons.update({
            'start_encounter': {'readonly': Not(And(Equal(Eval('state'),
                                                'arrived'), Bool(Eval('name')))),
                                'invisible': In(Eval('state'),
                                                ['processing', 'done'])},
            'goto_encounter': {'invisible': Not(In(Eval('state'),
                                               ['processing', 'done']))},
            'client_arrived': {'readonly': Not(And(Equal(Eval('state'),
                                               'confirmed'), Bool(Eval('name'))))}
        })

    @staticmethod
    def default_healthprof():
        return None
        # default to no health_prof.

    # @fields.depends('patient')
    # def on_change_patient(self):
    #     return {}

    @classmethod
    def get_is_today(cls, instances, name):
        comp = get_day_comp()
        out = {}
        for a in instances:
            out[a.id] = comp[0] <= a.appointment_date < comp[1]
        return out

    @classmethod
    def get_tree_color(cls, instances, name):
        out = {}
        for a in instances:
            if a.state in ('done, user_cancelled, center_cancelled, no_show'):
                out[a.id] = 'grey'
            elif a.state in ('arrived', ):
                out[a.id] = 'blue'
            elif a.state in ('processing', ):
                out[a.id] = 'green'
            else:
                out[a.id] = 'black'
        return out

    @classmethod
    def search_is_today(cls, name, clause):
        fld, operator, operand = clause
        comp = get_day_comp()
        domain = []
        if operand and operator in ('=', u'='):
            domain = ['AND', ('appointment_date', '>=', comp[0]),
                      ('appointment_date', '<', comp[1])]
        else:
            domain = ['OR', ('appointment_date', '<', comp[0]),
                      ('appointment_date', '>=', comp[1])]
        return domain

    @classmethod
    def search_rec_name(cls, name, clause):
        "Allow the default search to be by name, upi or appointment ID"
        field, operator, value = clause
        retests = {'patient.name.name': re.compile('^\D+$'),
                   'patient.name.upi': re.compile('^[a-z]{3}\d+?(\w+)?$', re.I)
                  }
        clauses = super(Appointment, cls).search_rec_name(name, clause)
        for newfield, test in retests.items():
            if test.match(value.strip('%')):
                clauses.append((newfield, operator, value))
        if len(clauses) > 1:
            clauses.insert(0, 'OR')
        return clauses

    @classmethod
    def validate(cls, appointments):
        super(Appointment, cls).validate(appointments)
        tz = get_timezone()
        now = datetime.now()
        for appt in appointments:
            if appt.state == 'done' and appt.appointment_date > now:
                cls.raise_user_error(
                    "An appointment in the future cannot be marked done.")

            if appt.patient:
                comp_startdate = datetime(
                    *(appt.appointment_date.timetuple()[:3] + (0, 0, 0)),
                    tzinfo=tz)
                comp_enddate = datetime(
                    *(appt.appointment_date.timetuple()[:3]+(23, 59, 59)),
                    tzinfo=tz)
                search_terms = ['AND',
                                ('patient', '=', appt.patient),
                                ('appointment_date', '>=', comp_startdate),
                                ('appointment_date', '<=', comp_enddate)]
                if appt.id:
                    search_terms.append(('id', '!=', appt.id))
                others = cls.search(search_terms)
            else:
                others = []
            # pop up the warning but not during sync
            if others and is_not_synchro():
                # setup warning params
                other_specialty = others[0].speciality.name
                warning_code = (
                    'healthjm.duplicate_appointment_warning.w_{}_{}'.format(
                        appt.patient.id, appt.appointment_date.strftime('%s')))
                warning_msg = ['Possible Duplicate Appointment\n\n',
                               appt.patient.name.firstname, ' ',
                               appt.patient.name.lastname]
                if other_specialty == appt.speciality.name:
                    warning_msg.append(' already has')
                else:
                    warning_msg.append(' has')

                if re.match('^[aeiou].+', other_specialty, re.I):
                    warning_msg.append(' an ')
                else:
                    warning_msg.append(' a ')
                warning_msg.extend([other_specialty, ' appointment for ',
                                   appt.appointment_date.strftime('%b %d'),
                                   '\nAre you sure you need this ',
                                   appt.speciality.name, ' one?'])

                cls.raise_user_warning(warning_code, u''.join(warning_msg))

    @classmethod
    def write(cls, appointments, values):
        'create an AppointmentStateChange when the state changes'
        newstate = values.get('state', False)
        to_make = []
        if newstate:
            for appt in appointments:
                if appt.state != newstate:
                    to_make.append({'appointment': appt.id,
                                    'orig_state': appt.state,
                                    'target_state': newstate})
        return_val = super(Appointment, cls).write(appointments, values)
        AppointmentStateChange.create(to_make)
        return return_val

    @classmethod
    @ModelView.button_action('health_encounter.act_appointment_encounter_starter')
    def start_encounter(cls, appointments):
        pass

    @classmethod
    @ModelView.button_action('health_encounter.act_appointment_encounter_starter')
    def goto_encounter(cls, appointments):
        pass

    @classmethod
    @ModelView.button
    def client_arrived(cls, appointments):
        cls.write(appointments, {'state': 'arrived'})


class AppointmentStateChange(ModelSQL, ModelView):
    """Appointment State Change"""
    __name__ = 'gnuhealth.appointment.statechange'
    appointment = fields.Many2One('gnuhealth.appointment', 'Appointment')
    orig_state = fields.Selection(APPOINTMENT_STATES, 'Changed From')
    target_state = fields.Selection(APPOINTMENT_STATES, 'Changed to')
    # use the built-in create_date and create_uid to determine who
    # changed the state of the appointment and when it was changed.
    # Records in this model will, be created automatically
    change_date = fields.Function(fields.DateTime('Changed on'),
                                  'get_change_date')
    creator = fields.Function(fields.Char('Changed by'), 'get_creator_name')

    def get_creator_name(self, name):
        pool = Pool()
        Party = pool.get('party.party')
        persons = Party.search([('internal_user', '=', self.create_uid)])
        if persons:
            return persons[0].name
        else:
            return self.create_uid.name

    def get_change_date(self, name):
        # we're sending back the create date since these are readonly
        return self.create_date
