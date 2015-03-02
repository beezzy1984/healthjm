
from datetime import datetime, timedelta
from itertools import groupby
from collections import OrderedDict, Counter
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.pyson import Eval, Not, Bool, PYSONEncoder
from trytond.wizard import (Wizard, StateView, StateTransition, Button,
                            StateAction)
from trytond.modules.health_jamaica.wizards import StartEndDateModel
from trytond.modules.health_jamaica.reports import BaseReport
from .common import *

class ClinicSummaryWizardModel(StartEndDateModel):
    '''Select date range for which you want the clinic summary report'''
    __name__ = 'healthjm_primarycare.report.clinic_summary.start'
    # pass


class ClinicSummaryWizard(Wizard):
    '''Service Utilisation Report Wizard'''
    __name__ = 'healthjm_primarycare.report.clinic_summary.wizard'
    start = StateView(
            'healthjm_primarycare.report.clinic_summary.start',
            'health_jamaica_primarycare.report_clinic_summary_start',
            [Button('Cancel', 'end', 'tryton-cancel'),
             Button('Generate report', 'generate_report', 'tryton-ok',
                    default=True)])

    generate_report = StateAction(
                  'health_jamaica_primarycare.jmreport_clinic_summary')

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


class ClinicSummaryReport(BaseReport):
    '''Service Utilisation Report'''
    __name__ = 'healthjm_primarycare.report.clinic_summary'

    @classmethod
    def parse(cls, report, records, data, localcontext):
        pool = Pool()
        User = pool.get('res.user')
        Institution = pool.get('gnuhealth.institution')
        Company = pool.get('company.company')
        Appointment = pool.get('gnuhealth.appointment')
        Evaluation = pool.get('gnuhealth.patient.evaluation')
        DiagnosticHypothesis = pool.get('gnuhealth.diagnostic_hypothesis')
        # Patient = pool.get('gnuhealth.patient')

        tz = utils.get_timezone()
        start_date = utils.get_start_of_day(data['start_date'], tz)
        end_date = utils.get_start_of_next_day(data['end_date'], tz)

        D = {} # output dictionary

        #--------------------------------------------------------
        # Section A: Curative Visits
        search_criteria = ['AND',
            ('institution','=',data['institution']),
            ('speciality.code', '=', 'CURATIVE'),
            ('state','=','done'),
            ('appointment_date','>=',start_date),
            ('appointment_date','<',end_date)
        ]

        appointments = Appointment.search_read(search_criteria,
                                    order=(('speciality','ASC'),
                                           ('appointment_date', 'ASC')),
                                    fields_names=['id','appointment_date',
                                                  'patient.name.sex',
                                                  'speciality.name',
                                                  'appointment_type'])
        # setup the counts of appointments
        apptcounter = Counter(map((lambda x: x['patient.name.sex']), 
                              appointments))

        D['A'] = apptcounter.copy()
        D['A'].update(total = sum(apptcounter.values()))

        #--------------------------------------------------------
        # Newly Diagnosed and First Visits

        age_groups = [
                ('<20', 0, 20), ('20-59', 20, 60), ('60+', 60, None),
                ('Unknown', -1, None)
        ]

        disease_groups = [
                ('Diabetes', {'diagnosis':['E10 - E14.999z'],
                              'age_groups': age_groups, 'signs': []}),
                ('Hypertension', {
                        'diagnosis':[('I10 - I10.999z',
                                     'I15', 'I15.8', 'I15.9')],
                        'age_groups':age_groups, 'signs': []
                 }),
                ('Diabetes and Hypertension', {
                        'diagnosis':['E10 - E14.999z', ('I10 - I10.999z',
                                     'I15', 'I15.8', 'I15.9')],
                        'age_groups': age_groups, 'signs':[]
                 })
        ]

        search_criteria = ['AND',
                ('institution','=',data['institution']),
                ('state', '=', 'done'),
        ]
        ordering = [('first_visit_this_year', 'ASC')]

        group_counts = []

        for disease_group_name, group_mapping in disease_groups:
            search_clause = search_criteria[:]
            search_clause.extend([mk_domain_clause(g,
                                   'diagnostic_hypothesis.pathology.code')
                  for g in group_mapping['diagnosis']])
            all_evals = Evaluation.search_read(search_clause, order=ordering, 
                                               fields_names=['id',
                                                    'patient.name.dob',
                                                    'patient.name.sex',
                                                    'first_visit_this_year',
                                                    'diagnostic_hypothesis'])
            newdiag = {'m':[],'f':[],'u':[]}
            firstvisit = newdiag.copy()
            revisit = []
            age_grouper = make_age_grouper(age_groups, data['start_date'],
                                           'patient.name.dob')
            getsex = lambda x : x['patient.name.sex']

            for e in all_evals:
                e['diagnostic_hypothesis'] = DiagnosticHypothesis.read(
                                                    e['diagnostic_hypothesis'],
                                                    ['pathology.code',
                                                     'first_diagnosis'])
                if e['diagnostic_hypothesis']['first_diagnosis']:
                    newdiag[e['patient.name.sex']].append(e)
                elif e['first_visit_this_year']:
                    firstvisit[e['patient.name.sex']].append(e)
                else:
                    revisit.append(e)

            group_counts.append({
                    'name': disease_group_name,
                    'new':dict([(x, Counter(map(age_grouper, y)))
                            for x,y in newdiag.items()]),
                    'first':dict([(x, Counter(map(age_grouper, y)))
                                  for x,y in firstvisit.items()]),
                    'revisit':Counter(map(getsex, revisit))})

        D['B'] = group_counts[:]

        #--------------------------------------------------------
        # Curative section


        D['C'] = []

        # if ((end_date - start_date) > timedelta(1.05)):
        #     localcontext['report_date_is_range'] = True
        # else : 
        #     localcontext['report_date_is_range'] = False

        # localcontext['user_name'] = User(Transaction().user).name
        # if data.get('institution', False):
            
        #     default_services = InstitutionSpecialties.search_read(
        #                         [('name','=',institution.id)],
        #                         order=(('specialty', 'ASC'),),
        #                         fields_names=['specialty.name',
        #                                       'is_main_specialty'])
        #     osectors = institution.operational_sectors
        #     if osectors:
        #         localcontext['sector'] = osectors[0].operational_sector
        #     else:
        #         localcontext['sector'] = ''
        #     localcontext['parish'] = ''
        #     for addr in institution.name.addresses:
        #         if addr.subdivision:
        #             localcontext['parish'] = addr.subdivision.name
        #             break
        # else:
        #     default_services = ['Curative', 'Oral Health (Primary Care)', 
        #                 'Family Planning', 'Child Health', 'Antenatal',
        #                 'Nutrition', 'Postnatal']
        #     default_services = [{'specialty.name':x, 'is_main_specialty':False}
        #                         for x  in default_services ]

        # age_groups = [('0 - 4',0,5), ('5 - 9', 5,10), ('10 - 19', 10, 20),
        #               ('20 - 59', 20, 60), ('60+', 60, None),
        #               ('Unknown', -1, None)] # negative min_age for dob==null

        # appointments = Appointment.search_read(search_criteria,
        #                             order=(('speciality','ASC'),
        #                                    ('appointment_date', 'ASC')),
        #                             fields_names=['id','appointment_date',
        #                                           'patient.name.dob',
        #                                           'patient.name.sex',
        #                                           'speciality.name','urgency',
        #                                           'appointment_type'])


        # named_age_groups = [('age_group%d'%i, x[1], x[2]) for i,x in
        #                     enumerate(age_groups)]
        # age_grouper = make_age_grouper(named_age_groups, start_date,
        #                     'patient.name.dob')
        # gender_grouper = lambda r: {'m':'male', 'f':'female'}.get(
        #                                             r['patient.name.sex'],
        #                                             'Unknown')
        # make_row = lambda t : Counter(total = t,male=0, female=0,
        #                          **dict([(x[0], 0) for x in named_age_groups]))
        # total_line = make_row(0)
        # service_counts = dict([(x['specialty.name'], make_row(0))
        #                       for x in default_services])
        # for specialty, appts in groupby(appointments,
        #                                 lambda x: x['speciality.name']):
        #     appts = list(appts)
        #     spec_count = make_row(len(appts))
        #     spec_count.update(Counter(map(gender_grouper, appts)) +
        #                                   Counter(map(age_grouper, appts)))

        #     service_counts.setdefault(specialty, Counter()).update(spec_count)
        #     total_line.update(spec_count)
        # service_counts = service_counts.items()
        # service_counts.sort(key=lambda x: x[0])
        localcontext.update(start_date=start_date,
                            end_date=end_date-timedelta(0,0.2),
                            D=D,
                            is_weekly=False, is_monthly=False,
                            now_date=datetime.now(tz),)


        print('{}\n\n{}\n\n{}'.format('-'*80, repr(localcontext), '-'*80))
        return super(ClinicSummaryReport, cls).parse(
                        report, records, data, localcontext
                    )