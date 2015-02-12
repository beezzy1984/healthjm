

import pytz
from datetime import date, datetime, timedelta
from itertools import groupby
from collections import defaultdict, Counter
from trytond.report import Report
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.pyson import Eval, Not, Bool, PYSONEncoder
from trytond.wizard import (Wizard, StateView, StateTransition, Button,
                            StateAction)
from ..health_jamaica import tryton_utils as utils
from ..health_jamaica.wizards import PatientRegisterModel

__all__ = ['SyndromicSurveillanceWizardModel', 'SyndromicSurveillanceWizard',
           'SyndromicSurveillanceReport',
           'ServiceUtilisationWizardModel', 'ServiceUtilisationWizard',
           'ServiceUtilisationReport']

def make_age_grouper(age_groups, ref_date, dob_field='patient.dob'):
    age_group_dict = {}
    if len(age_groups) == 2 and age_groups[0][2] == age_groups[1][1]:
        age_boundary = utils.get_dob(age_groups[0][2])
        return lambda x: (age_groups[0][0]
                          if x[dob_field] >= age_boundary 
                          else age_groups[1][0])

    # build an age lookup table using the age groups and individual ages 
    age_table = {}
    age_upper_threshold = age_lower_threshold = None
    for title, age_min, age_max in age_groups:
        if age_min is None and age_max is None:
            continue #improperly specified age group
        elif age_min is None and age_max>0:
            age_lower_threshold = age_max-1
            age_table[age_lower_threshold] = title
        elif age_min>0 and age_max is None:
            age_upper_threshold = age_min
            age_table[age_upper_threshold] = title
        elif age_min<0 and age_max is None:
            age_table[None] = title
        elif age_min>=0 and age_max>=0:
            age_table.update([(a, title) for a in range(age_min,age_max)])

    # gfailover handles the connection to the two exception clauses
    # or a default passthru for the regular age.
    # This allows us to pass in the ages higher than age_upper_threshold
    # and that what is returned is the age that represents the treshold.
    # example usage: 
    #   age_upper_threshold = 49; age_lower_threshold=13
    #   gfailover(32) == 32
    #   gfailover(52) == 49
    #   gfailover(60) == 49
    #   gfailover(10) == 13
    def gfailover(age):
        if age_upper_threshold and age >= age_upper_threshold:
            return age_upper_threshold
        elif age_lower_threshold and age <= age_lower_threshold:
            return age_lower_threshold
        return age

    # make the grouper do a simple lookup from the table
    # with a function failover that returns a result from the 3 exct sets
    get_age = utils.get_age_in_years
    def grouper(record):
        # take the age of the each record and lookup the 
        age = get_age(record[dob_field])
        # group from the age_table
        return age_table.get(age,
                             age_table.get(gfailover(age), None))
    return grouper


class SyndromicSurveillanceReport(Report):
    '''Syndromic Surveillance Report'''
    __name__ = 'healthjm_primarycare.report.syndromic_surveillance'

    @classmethod
    def parse(cls, report, records, data, localcontext):
        pool = Pool()
        User = pool.get('res.user')
        Institution = pool.get('gnuhealth.institution')
        Company = pool.get('company.company')
        Evaluation = pool.get('gnuhealth.patient.evaluation')
        # Patient = pool.get('gnuhealth.patient')

        timezone = utils.get_timezone()
        start_date = utils.get_start_of_day(data['start_date'], timezone)
        end_date = utils.get_start_of_next_day(data['end_date'], timezone)
        search_criteria = ['AND',
            ('state','=','done'),
            ('evaluation_start','>=',start_date),
            ('evaluation_start','<',end_date)
        ]
        localcontext['user_name'] = User(Transaction().user).name
        if data.get('institution', False):
            search_criteria.append(('institution','=',data['institution']))
            localcontext['institution'] = Institution(data['institution'])
            osectors = localcontext['institution'].operational_sectors
            if osectors:
                localcontext['sector'] = osectors[0].operational_sector
            localcontext['parish'] = ''
            for addr in localcontext['institution'].name.addresses:
                if addr.subdivision:
                    localcontext['parish'] = addr.subdivision.name
                    break


        common_age_groups = [('< 5yrs',0,5), ('> 5yrs', 5,None)]
        syndromes = [
            ('Fever and Rash', {'signs':['R50.1', 'R21']}),
            ('Fever', {'signs':['R50.1'], 'age_groups':common_age_groups}),
            ('Gastrointeritis', {'signs':['R19.7'],
                                 'age_groups':common_age_groups}),
            ('Accidents', {'signs':[], 'diagnosis':['V01 - X59'],
                           'age_groups':common_age_groups}),
            ('Violence', {'signs':[], 'diagnosis':['X85 - Y09'],
                          'age_groups':common_age_groups}),
            ('Fever and respiratory symptoms', {
                    'age_groups':[('<5 yrs', 0, 5), ('5-59 yrs', 5, 60),
                                  ('>60 yrs', 60, None)],
                    'signs':['R50.1', 'R05 - R07']
            }),
            ('Fever and Haemorrhagic Symptoms', {'signs':['R50.1', 'R58']}),
            ('Fever and Jaundice',{'signs':['R50.1', 'R17']}),
            ('Fever and Neurological Symptoms',{
                    'signs':['R50.1', ['R40','R56','R26']]}),
            ('Asthma',{'signs':[], 'diagnosis':['J45 - J46']}),
            ('Severe Acute Respiratory Illness (SARI)', {
                    'signs':['R50.1', 'R06', ['R05', 'R07']],
                    'diagnosis':[]
             }),
            ('Upper Respiratory Tract Infection', {
                    'signs':[],
                    'diagnosis':[('J00 - J06.999',), ('J30 - J39.999')]
             })
            # ('Lower Resiratory Tract Infections', {}),
            # ('Upper Repiratory Tract Infections', {})

        ]
        output_lines = []
        def day_group_counts(evaluation_list, field="evaluation_start"):
            # restricted to using day names as the keys since we're sure
            # this will only be run for a single week
            # dayfunc = lambda x: x['evaluation_start'].timetuple()[:3]
            dayfunc = lambda x: x[field].strftime('%a')
            # #assuming evaluations are ordered by evaluation_start
            evgroups = groupby(evaluation_list, dayfunc)
            # return [(d, len(list(i))) for d,i in evgroups]
            counter = Counter(Sun=0, Mon=0, Tue=0, Wed=0, Thu=0, Fri=0, Sat=0,
                             total=0)
            counter.update(Counter(map(dayfunc, evaluation_list)))
            counter.update(total = len(evaluation_list))
            return counter, evgroups

        def mk_domain_clause(code, column='signs_and_symptoms.clinical.code'):
            if ' - ' in code:
                limits = code.split(' - ')
                return ['AND',
                        (column, '>=', limits[0]),
                        (column, '<=', limits[1])
                ]
            elif isinstance(code, (list, tuple)):
                return ['OR'] + [mk_domain_clause(k, column) for k in code]
            else:
                return (column, '=', code)

        total_line = Counter(Sun=0, Mon=0, Tue=0, Wed=0, Thu=0, Fri=0, Sat=0,
                             total=0)
        for heading, params in syndromes:
            search_domain = search_criteria[:]
            if params.get('signs', False):
                for sign in params['signs']:
                    search_domain.append(mk_domain_clause(sign))
            if params.get('diagnosis', False):
                for diag in params['diagnosis']:
                    search_domain.append(
                        mk_domain_clause(diag,
                                         'diagnostic_hypothesis.pathology.code'
                                        )
                    )
            # print("{}\nsearch_domain = {}\n{}".format('*'*80,
            #                                           repr(search_domain),
            #                                           '*'*80))
            objects = Evaluation.search_read(search_domain,
                                    order=(('evaluation_start','ASC'),
                                           ('evaluation_endtime', 'ASC')),
                                    fields_names=['id','evaluation_start',
                                                  'patient.dob', 'patient.id',
                                                  'signs_and_symptoms',
                                                  'diagnostic_hypothesis'])

            line = {'title':heading, 'summary':False}
            counts, eval_groups = day_group_counts(objects)
            line.update(dict(counts))
            for dayname, evallist in eval_groups:
                patient_counter = Counter(map((lambda g: g['patient.id']),
                                              evallist))
                total_line.update({dayname:len(patient_counter.keys())})

            if params.get('age_groups', False):
                line['title'] = '%s (Total)'%(heading,)
                line['summary'] = True

                output_lines.append(line) # total Line
                age_groupings = defaultdict(list)
                grouper = make_age_grouper(params['age_groups'], end_date)
                for ev in objects:
                    age_groupings[grouper(ev)].append(ev)

                for ag in params['age_groups']:
                    g = age_groupings[ag[0]]
                    line = {'title':'%s: %s'%(heading, ag[0]), 'summary':False}
                    line.update(day_group_counts(g)[0])
                    output_lines.append(line) # age group line
            else:
                # make a single line for the heading
                output_lines.append(line) # no-age-grouping line

        # count Pneumonia Related Deaths


        # count Admissions with LRTI (J09 - J18)

        # print('{}\n OMG, what a function. These are usually quite sexy'.format('*'*80))
        # print('{}\n\n{}'.format(repr(output_lines), '*'*80))
        localcontext.update(syndrome_counts=output_lines, totals=total_line,
                            epi_week=data['epi_week'],
                            now_date=datetime.now(timezone),
                            epi_week_year=data['epi_week_year'],
                            end_date=data['end_date'])

        return super(SyndromicSurveillanceReport, cls).parse(report,
                                                             records,
                                                             data,
                                                             localcontext)

STATE_RO={'readonly':True}
STATE_INVRO={'readonly':True, 'invisible':True}

class SyndromicSurveillanceWizardModel(ModelView):
    '''Syndromic Surveillance for'''
    __name__ = 'healthjm_primarycare.report.syndromic_surveillance.start'
    selectdate = fields.Date('Select date', required=True)
    on_or_before = fields.Date('Week Ending', states=STATE_RO, help="Saturday")
    epi_week = fields.Integer('Week Number', states=STATE_INVRO,
                              help="Epidemiological Week")
    epi_week_year = fields.Integer('year', states=STATE_INVRO)
    epi_week_display = fields.Char('Week number', size=12, states=STATE_RO)
    on_or_after = fields.Date('start date', states=STATE_INVRO)
    institution = fields.Many2One('gnuhealth.institution', 'Institution',
                                  states={'readonly': True}, required=True)

    @classmethod
    def __setup__(cls):
        super(SyndromicSurveillanceWizardModel, cls).__setup__()
        cls._error_messages.update({
            'required_institution':'''Institution is required.\n
Your user account is not assigned to an institution.
This assignment is needed before you can use this report.
Please contact your system administrator to have this resolved.'''
            })

    @staticmethod
    def default_institution():
        HealthInst = Pool().get('gnuhealth.institution')
        try:
            institution = HealthInst.get_institution()
        except AttributeError:
            self.raise_user_error('required_institution')
        return institution

    @fields.depends('selectdate')
    def on_change_selectdate(self):
        if self.selectdate and isinstance(self.selectdate,
                                            (date,datetime)):
            epidata = utils.get_epi_week(self.selectdate)
            d = dict(zip(['on_or_after', 'on_or_before', 'epi_week_year',
                             'epi_week'], epidata))
            d['epi_week_display'] = '%02d of %04d'%(epidata[3], epidata[2])
            return d
        return {}

class SyndromicSurveillanceWizard(Wizard):
    '''Syndromic Surveillance Report Wizard'''
    __name__ = 'healthjm_primarycare.report.syndromic_surveillance.wizard'
    
    start = StateView(
            'healthjm_primarycare.report.syndromic_surveillance.start',
            'health_jamaica_primarycare.report_syndromic_surveillance_start',
            [Button('Cancel', 'end', 'tryton-cancel'),
             Button('Generate report', 'generate_report', 'tryton-ok',
                    default=True)])

    generate_report = StateAction(
                  'health_jamaica_primarycare.jmreport_syndromic_surveillance')

    def transition_generate_report(self):
        return 'end'

    def do_generate_report(self, action):
        # specify data that will be passed to .parse on the report object
        data = {'start_date':self.start.on_or_after,
                'end_date':self.start.on_or_after,
                'facility':None,
                'epi_week': self.start.epi_week,
                'epi_week_year': self.start.epi_week_year}

        if self.start.on_or_before:
            data['end_date'] = self.start.on_or_before

        if self.start.institution:
            data['institution'] = self.start.institution.id
        else:
            self.start.raise_user_error('required_institution')
            return 'start'

        return action, data


# =====================================================================

class ServiceUtilisationReport(Report):
    '''Service Utilisation Report'''
    __name__ = 'healthjm_primarycare.report.service_utilisation'

    @classmethod
    def parse(cls, report, records, data, localcontext):
        pool = Pool()
        User = pool.get('res.user')
        Institution = pool.get('gnuhealth.institution')
        Company = pool.get('company.company')
        Appointment = pool.get('gnuhealth.appointment')
        InstitutionSpecialties = pool.get('gnuhealth.institution.specialties')
        # Patient = pool.get('gnuhealth.patient')

        timezone = utils.get_timezone()
        start_date = utils.get_start_of_day(data['start_date'], timezone)
        end_date = utils.get_start_of_next_day(data['end_date'], timezone)

        search_criteria = ['AND',
            # ('state','=','done'),
            ('appointment_date','>=',start_date),
            ('appointment_date','<',end_date)
        ]

        if ((end_date - start_date) > timedelta(1.05)):
            localcontext['report_date_is_range'] = True
        else : 
            localcontext['report_date_is_range'] = False

        localcontext['user_name'] = User(Transaction().user).name
        if data.get('institution', False):
            search_criteria.append(('institution','=',data['institution']))
            institution = Institution(data['institution'])
            localcontext['institution'] = institution
            default_services = InstitutionSpecialties.search_read(
                                [('name','=',institution.id)],
                                order=(('specialty', 'ASC'),),
                                fields_names=['specialty.name',
                                              'is_main_specialty'])
            osectors = institution.operational_sectors
            if osectors:
                localcontext['sector'] = osectors[0].operational_sector
            localcontext['parish'] = ''
            for addr in institution.name.addresses:
                if addr.subdivision:
                    localcontext['parish'] = addr.subdivision.name
                    break
        else:
            default_services = ['Curative', 'Oral Health (Primary Care)', 
                        'Family Planning', 'Child Health', 'Antenatal',
                        'Nutrition', 'Postnatal']
            default_services = [{'specialty.name':x, 'is_main_specialty':False}
                                for x  in default_services ]

        age_groups = [('0 - 4',0,5), ('5 - 9', 5,10), ('10 - 19', 10, 20),
                      ('20 - 59', 20, 60), ('60+', 60, None),
                      ('Unknown', -1, None)] # negative min_age for dob==null

        appointments = Appointment.search_read(search_criteria,
                                    order=(('speciality','ASC'),
                                           ('appointment_date', 'ASC')),
                                    fields_names=['id','appointment_date',
                                                  'patient.name.dob',
                                                  'patient.name.sex',
                                                  'speciality.name','urgency',
                                                  'appointment_type'])


        named_age_groups = [('age_group%d'%i, x[1], x[2]) for i,x in
                            enumerate(age_groups)]
        age_grouper = make_age_grouper(named_age_groups, start_date,
                            'patient.name.dob')
        gender_grouper = lambda r: {'m':'male', 'f':'female'}.get(
                                                    r['patient.name.sex'],
                                                    'Unknown')
        make_row = lambda t : Counter(total = t,male=0, female=0,
                                 **dict([(x[0], 0) for x in named_age_groups]))
        total_line = make_row(0)
        service_counts = dict([(x['specialty.name'], make_row(0))
                              for x in default_services])
        for specialty, appts in groupby(appointments,
                                        lambda x: x['speciality.name']):
            appts = list(appts)
            spec_count = make_row(len(appts))
            spec_count.update(Counter(map(gender_grouper, appts)) +
                                          Counter(map(age_grouper, appts)))

            service_counts.setdefault(specialty, Counter()).update(spec_count)
            total_line.update(spec_count)
        service_counts = service_counts.items()
        service_counts.sort(key=lambda x: x[0])
        localcontext.update(start_date=start_date,
                            end_date=end_date-timedelta(0,2),
                            service_counts=service_counts,
                            total_line=total_line,
                            now_date=datetime.now(timezone),)

        return super(ServiceUtilisationReport, cls).parse(
                        report, records, data, localcontext
                    )

class ServiceUtilisationWizardModel(PatientRegisterModel):
    '''Service Utilisation Report for'''
    __name__ = 'healthjm_primarycare.report.service_utilisation.start'
    pass



class ServiceUtilisationWizard(Wizard):
    '''Service Utilisation Report Wizard'''
    __name__ = 'healthjm_primarycare.report.service_utilisation.wizard'
    start = StateView(
            'healthjm_primarycare.report.service_utilisation.start',
            'health_jamaica_primarycare.report_service_utilisation_start',
            [Button('Cancel', 'end', 'tryton-cancel'),
             Button('Generate report', 'generate_report', 'tryton-ok',
                    default=True)])

    generate_report = StateAction(
                  'health_jamaica_primarycare.jmreport_service_utilisation')

    def transition_generate_report(self):
        return 'end'

    def do_generate_report(self, action):
        data = {'start_date':self.start.on_or_after,
                'end_date':self.start.on_or_after}

        if self.start.on_or_before:
            data['end_date'] = self.start.on_or_before

        if self.start.institution:
            data['institution'] = self.start.institution.id
        else:
            self.start.raise_user_error('required_institution')
            return 'start'

        return action, data                