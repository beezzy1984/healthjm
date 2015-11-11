# -*- coding: utf-8 -*-
##############################################################################
#
#    Health-Jamaica: The Jamaica Electronic Patient Administration System
#    Copyright 2015  Ministry of Health (NHIN), Jamaica <admin@mohnhin.info>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, And
from trytond.pool import Pool
from trytond.transaction import Transaction
from .tryton_utils import (negate_clause, replace_clause_column, is_not_synchro,
                           get_timezone, make_selection_display, get_day_comp)

__all__ = ['PatientData', 'HealthInstitution', 'Insurance',
           'HealthInstitutionSpecialties', 'HealthProfessional',
           'HealthProfessionalSpecialties', 'Appointment', 'ProcedureCode',
           'PathologyGroup', 'Pathology', 'DiagnosticHypothesis',
           'PatientEvaluation', 'OperationalSector']


class PatientData(ModelSQL, ModelView):
    '''Patient related information'''
    __name__ = 'gnuhealth.patient'

    sex_display = fields.Function(fields.Char('Sex'), 'get_person_field')
    firstname = fields.Function(fields.Char('First name'), 'get_person_field',
                                searcher='search_person_field')
    middlename = fields.Function(fields.Char('Middle name'), 'get_person_field',
                                 searcher='search_person_field')
    mother_maiden_name = fields.Function(
        fields.Char('Mother\'s maiden name'),
        'get_person_field',
        searcher='search_person_field'
    )
    father_name = fields.Function(
        fields.Char('Father\'s name'),
        'get_person_field',
        searcher='search_person_field'
    )
    alt_ids = fields.Function(fields.Char('Alternate IDs'), 'get_person_field',
                              searcher='search_alt_ids')
    medical_record_num = fields.Function(fields.Char('Medical Record Number'),
                                         'get_person_field',
                                         searcher='search_alt_ids')
    du = fields.Function(fields.Char('Address'),
                         'get_person_field', searcher='search_person_field')
    unidentified = fields.Function(
        fields.Boolean('Unidentified'),
        'get_unidentified',
        searcher='search_unidentified'
    )
    full_name = fields.Function(fields.Char('Full name'), 'get_fullname')
    summary_info = fields.Function(fields.Text('Summary Information'),
                                   'get_patient_summary')

    def get_rec_name(self, name):
        return self.name.name

    def get_person_field(self, field_name):
        return getattr(self.name, field_name)

    def get_unidentified(self, field_name):
        return self.name.unidentified

    def get_fullname(self, n):
        return ' '.join(filter(None, [self.name.firstname,
                                      self.name.middlename,
                                      self.name.lastname]))

    @classmethod
    def search_person_field(cls, field_name, clause):
        return [('name.{}'.format(field_name), clause[1], clause[2])]

    @classmethod
    def search_alt_ids(cls, field_name, clause):
        if field_name == 'medical_record_num':
            return ['AND', ('name.alternative_ids.alternative_id_type', '=',
                            'medical_record'),
                    ('name.alternative_ids.code',) + tuple(clause[1:])]
        else:
            return [
                'AND',
                ('name.alternative_ids.alternative_id_type', '!=',
                 'medical_record'),
                ('name.alternative_ids.code', clause[1], clause[2])]

    @classmethod
    def search_unidentified(cls, field_name, clause):
        cond = ['AND', replace_clause_column(clause, 'name.unidentified'),
                negate_clause(replace_clause_column(clause,
                                                    'name.party_warning_ack'))]
        return cond

    def get_patient_puid(self, name):
        return self.name.get_upi_display('upi')

    @classmethod
    def __setup__(cls):
        super(PatientData, cls).__setup__()

        # import pdb; pdb.set_trace()
        cls.dob.getter = 'get_person_field'
        cls.dob.searcher = 'search_person_field'
        cls.dob.string = 'Date of Birth'
        cls.puid.string = 'UPI'

        # if we need to make the Party Editable from Patient :
        # cls.name.states = update_states(cls.name, {'readonly':False})

    # Get the patient age in the following format : 'YEARS MONTHS DAYS'
    # It will calculate the age of the patient while the patient is alive.
    # When the patient dies, it will show the age at time of death.

    def patient_age(self, name):

        def compute_age_from_dates(patient_dob, patient_deceased,
                                   patient_dod, patient_sex):

            now = datetime.now()

            if (patient_dob):
                dob = datetime.strptime(str(patient_dob), '%Y-%m-%d')

                if patient_deceased:
                    dod = datetime.strptime(
                        str(patient_dod), '%Y-%m-%d %H:%M:%S')
                    delta = relativedelta(dod, dob)
                    deceased = '(deceased)'
                else:
                    delta = relativedelta(now, dob)
                    deceased = ''

                # Return the raw age in the integers array [Y,M,D]
                # When name is 'raw_age'
                if name == 'raw_age':
                    return [delta.years, delta.months, delta.days]

                ymd = []
                if delta.years >= 1:
                    ymd.append(str(delta.years) + 'y')
                if (delta.months > 0 or delta.years > 0) and delta.years < 10:
                    ymd.append(str(delta.months) + 'm')
                if delta.years <= 2:
                    ymd.append(str(delta.days) + 'd')
                ymd.append(deceased)

                years_months_days = ' '.join(ymd)
            else:
                years_months_days = '--'

            # Return the age in format y m d when the caller is the field name
            if name == 'age':
                return years_months_days

            # Return if the patient is in the period of childbearing age >10 is
            # the caller is childbearing_potential

            if (name == 'childbearing_age' and patient_dob):
                if (delta.years >= 11
                   and delta.years <= 55 and patient_sex == 'f'):
                    return True
                else:
                    return False

        return compute_age_from_dates(self.dob, self.deceased,
                                      self.dod, self.sex)

    def get_patient_summary(self, name):
        content = [('Date of Birth', self.dob.strftime('%Y-%m-%d')),
                   ('Pet Name/Alias', self.name.alias),
                   # ('Birthplace', self.name.birthplace),
                   ('Marital Status', self.name.marital_status_display),
                   ('Mother\'s Maiden Name', self.name.mother_maiden_name)]
                   # ('Father\'s Name', self.name.father_name)]
        if self.name.du:
            content.append(('Address (DU)', self.name.du.simple_address))
        elif self.name.addresses:
            content.append(('Address', self.name.addresses[0].simple_address))
        else:
            content.append(('Address', '-- no address on record'))
        if self.name.relatives:
            content.append(('Next of Kin', ''))
            for relative in self.name.relatives:
                content.append(('', '    %s (%s)' % (relative.relative.name,
                                                     relative.phone_number)))
        if self.name.occupation:
            content.append(('Occupational Group', self.name.occupation.name))
        return '\n'.join([': '.join(x) for x in content])


class Insurance(ModelSQL, ModelView):
    '''Insurance'''
    __name__ = 'gnuhealth.insurance'

    @classmethod
    def __setup__(cls):
        super(Insurance, cls).__setup__()
        cls.number.string = 'Policy#'


class HealthInstitution(ModelSQL, ModelView):
    'Health Institution'
    __name__ = 'gnuhealth.institution'

    latitude = fields.Numeric('Latitude', digits=(3, 14))
    longitude = fields.Numeric('Longitude', digits=(4, 14))
    altitude = fields.Numeric('Altitude (in meters)', digits=(4, 3))

    @classmethod
    def __setup__(cls):
        cls.main_specialty = fields.Function(
            fields.Many2One(
                'gnuhealth.institution.specialties',
                'Specialty', domain=[('name', '=', Eval('active_id'))],
                depends=['specialties'],
                help="Choose the speciality in the case of Specialized "
                "Hospitals or where this center excels",
                # Allow to select the institution specialty only if the
                # record already exists
                states={
                    'required': And(Eval('institution_type') == 'specialized',
                                    Eval('id', 0) > 0),
                    'readonly': Eval('id', 0) < 0
                }
            ),
            'get_main_specialty',
            'set_main_specialty',
            'search_main_specialty')

    def get_main_specialty(self, name):
        mss = [x for x in self.specialties if x.is_main_specialty]
        if mss:
            return mss[0].id
        return None

    @classmethod
    def search_main_specialty(cls, name, clause):
        return ['AND',
                ('specialties.is_main_specialty', '=', True),
                replace_clause_column(clause, 'specialties.specialty.id')]

    @classmethod
    def set_main_specialty(cls, instances, field_name, value):
        for i in instances:
            turnoff, turnon = [], []
            for spec in i.specialties:
                if spec.id == value:
                    turnon.append(spec)
                elif spec.is_main_specialty:
                    turnoff.append(spec)
        HIS = Pool().get('gnuhealth.institution.specialties')
        if turnoff:
            HIS.write(turnoff, {'is_main_specialty': None})
        if turnon:
            HIS.write(turnon, {'is_main_specialty': True})


class HealthInstitutionSpecialties(ModelSQL, ModelView):
    'Health Institution Specialties'
    __name__ = 'gnuhealth.institution.specialties'

    is_main_specialty = fields.Boolean(
        'Main Specialty',
        help="Check if this is the main specialty"
        " e.g. in the case of specialized hospital"
        " or an area in which this institution excels.")

    @staticmethod
    def default_is_main_specialty():
        return False


class HealthProfessional(ModelSQL, ModelView):
    'Health Professional'
    __name__ = 'gnuhealth.healthprofessional'

    @classmethod
    def __setup__(cls):
        super(HealthProfessional, cls).__setup__()
        cls.main_specialty = fields.Function(
            fields.Many2One(
                'gnuhealth.hp_specialty',
                'Main Specialty',
                domain=[('name', '=', Eval('active_id'))]
            ),
            'get_main_specialty',
            'set_main_specialty',
            'search_main_specialty'
        )

    def get_rec_name(self, name):
        return self.name.name

    def get_main_specialty(self, name):
        mss = [x for x in self.specialties if x.is_main_specialty]
        if mss:
            return mss[0].id
        return None

    @classmethod
    def search_main_specialty(cls, name, clause):
        return ['AND',
                ('specialties.is_main_specialty', '=', True),
                replace_clause_column(clause, 'specialties.specialty.id')]

    @classmethod
    def set_main_specialty(cls, instances, field_name, value):
        for i in instances:
            turnoff, turnon = [], []
            for spec in i.specialties:
                if spec.id == value:
                    turnon.append(spec)
                elif spec.is_main_specialty:
                    turnoff.append(spec)
        HPS = Pool().get('gnuhealth.hp_specialty')
        if turnoff:
            HPS.write(turnoff, {'is_main_specialty': None})
        if turnon:
            HPS.write(turnon, {'is_main_specialty': True})


class HealthProfessionalSpecialties(ModelSQL, ModelView):
    'Health Professional Specialties'
    __name__ = 'gnuhealth.hp_specialty'
    is_main_specialty = fields.Boolean(
        'Main Specialty',
        help="Check if this is the main specialty i.e. in the case of "
        "specialty doctor or an area in which this professional excels."
    )

    @staticmethod
    def default_is_main_specialty():
        return False

    @classmethod
    def __setup__(cls):
        super(HealthProfessionalSpecialties, cls).__setup__()
        cls.specialty.ondelete = 'CASCADE'
        cls.specialty.required = True
        cls._sql_constraints.append(('name_specialty_uniq',
                                     'UNIQUE(name, specialty)',
                                     'Duplicate specialty assignment'))


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
        if operand and operator == '=':
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


class ProcedureCode(ModelSQL, ModelView):
    'Medcal Procedures'
    __name__ = 'gnuhealth.procedure'

    @classmethod
    def __setup__(cls):
        super(ProcedureCode, cls).__setup__()
        if not isinstance(cls._sql_constraints, (list,)):
            cls._sql_constraints = []
        cls._sql_constraints.append(('name_uniq', 'UNIQUE(name)',
                                     'Medical procedure code must be unique'))


class PathologyGroup(ModelSQL, ModelView):
    'Pathology Groups'
    __name__ = 'gnuhealth.pathology.group'
    track_first = fields.Boolean('Track first diagnosis',
            help='Ask for status of first-diagnosis of diseases in this category upon creation of a diagnisis or diagnostic hypothesis',
                                )

    @staticmethod
    def default_track_first():
        return False


class Pathology(ModelSQL, ModelView):
    'Diseases'
    __name__ = 'gnuhealth.pathology'

    track_first = fields.Function(fields.Boolean('Track first diagnosis'),
                                  'get_track_first')

    def get_track_first(self, name):
        for g in self.groups:
            if g.disease_group.track_first:
                return True

        return False


class DiagnosticHypothesis(ModelSQL, ModelView):
    'Diagnostic Hypotheses'
    __name__ = 'gnuhealth.diagnostic_hypothesis'

    first_diagnosis = fields.Boolean(
        'First diagnosis',
        help='First time being diagnosed with this ailment')

    @staticmethod
    def default_first_diagnosis():
        return False


class PatientEvaluation(ModelSQL, ModelView):
    'Patient Evaluation'
    __name__ = 'gnuhealth.patient.evaluation'

    first_visit_this_year = fields.Boolean('First visit this year',
                                           help='First visit this year')

    visit_type_display = fields.Function(fields.Char('Visit Type'),
                                         'get_selection_display')
    upi = fields.Function(fields.Char('UPI'), getter='get_person_patient_field')
    sex_display = fields.Function(fields.Char('Sex'),
                                  'get_person_patient_field')
    age = fields.Function(fields.Char('Age'), 'get_person_patient_field')

    def get_selection_display(self, fn):
        return make_selection_display()(self, 'visit_type')

    def get_person_patient_field(self, name):
        if name in ['upi', 'sex_display']:
            return getattr(self.patient.name, name)
        if name in ['age']:
            return getattr(self.patient, name)
        return ''

    def get_patient_age(self, name):
        if self.patient:
            return self.patient.patient_age(name)

    @classmethod
    def __setup__(cls):
        super(PatientEvaluation, cls).__setup__()
        cls._error_messages.update({
            'no_enddate_error': 'End time is required for finishing evaluation'
        })
        cls.evaluation_endtime.required = False

    @classmethod
    def __register__(cls, module_name):
        super(PatientEvaluation, cls).__register__(module_name)
        cursor = Transaction().cursor
        # Make the endtime column not required at the DB level
        cursor.execute(
            '''ALTER TABLE gnuhealth_patient_evaluation
               ALTER COLUMN evaluation_endtime DROP NOT NULL;''')

    @fields.depends('patient', 'evaluation_start', 'institution')
    def on_change_with_first_visit_this_year(self, *arg, **kwarg):
        if self.institution and self.patient:
            M = Pool().get('gnuhealth.patient.evaluation')
            search_parms = ['AND',
                            ('evaluation_start', '<', self.evaluation_start),
                            ('evaluation_start', '>=',
                             datetime(self.evaluation_start.year,1,1,0,0,0)),
                            ('patient', '=', self.patient.id),
                            ('institution', '=', self.institution.id)]

            others = M.search(search_parms)
            if others:
                return False

        return True

    @fields.depends('patient')
    def on_change_patient(self, *arg, **kwarg):
        return {'upi':self.patient.puid,
                'sex_display':self.patient.name.sex_display,
                'age':self.patient.age}

    @classmethod
    def write(cls, evaluations, vals):
        # Don't allow to write the record if the evaluation has been done
        if is_not_synchro():
            for ev in evaluations:
                if ev.state == 'done':
                    cls.raise_user_error(
                        "This evaluation is in a Done state.\n"
                        "You can no longer modify it.")
        return super(PatientEvaluation, cls).write(evaluations, vals)

    @classmethod
    @ModelView.button
    def discharge(cls, evaluations):
        for evaluation in evaluations:
            if not evaluation.evaluation_endtime:
                cls.raise_user_error('no_enddate_error')
        super(PatientEvaluation, cls).discharge(evaluations)


class OperationalSector(ModelSQL, ModelView):
    'Operational Sector'
    __name__ = 'gnuhealth.operational_sector'

    subdivision = fields.Many2One('country.subdivision', 'Parish/Province',
                                  required=True)

    def get_rec_name(self, name):
        return ' - '.join([self.subdivision.name, self.name])


class PatientEncounter(ModelSQL, ModelView):
    'gnuhealth.encounter'
    fvty = fields.Boolean('First visit this year',
                          help='Check if this is known to be the first time '
                          'this patient is visiting this institution '
                          'for this year')

    @fields.depends('patient', 'start_time', 'institution')
    def on_change_with_fvty(self, *arg, **kwarg):
        if self.institution and self.patient and self.start_time:
            M = Pool().get('gnuhealth.encounter')
            search_parms = ['AND',
                            ('start_time', '<', self.start_time),
                            ('evaluation_start', '>=',
                             datetime(self.start_time.year,1,1,0,0,0)),
                            ('patient', '=', self.patient.id),
                            ('institution', '=', self.institution.id)]

            others = M.search(search_parms)
            if others:
                return False
        return True
