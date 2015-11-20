import re
from datetime import datetime
from trytond.model import ModelView, ModelSQL, fields
from .tryton_utils import is_not_synchro, get_timezone, get_day_comp


class Appointment(ModelSQL, ModelView):
    'Patient Appointments'
    __name__ = 'gnuhealth.appointment'

    is_today = fields.Function(fields.Boolean('Is Today'), 'get_is_today',
                               searcher='search_is_today')
    tree_color = fields.Function(fields.Char('tree_color'), 'get_tree_color')

    @staticmethod
    def default_state():
        return 'free'

    @classmethod
    def __setup__(cls):
        super(Appointment, cls).__setup__()
        cls.state.selection = [
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
        print('%s\nCalculating is_today with daycomp = %s\n' % ('*'*79, repr(comp)))
        for a in instances:
            print('    testing: %s' % (repr(a.appointment_date), ))
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
        print('doing a seach for is_today with clause= ' + repr(clause))
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
