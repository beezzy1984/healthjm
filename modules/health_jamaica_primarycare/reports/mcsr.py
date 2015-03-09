
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
        data = {'start_date': self.start.on_or_after,
                'end_date': self.start.on_or_after}

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

        D = {}  # output dictionary

        #--------------------------------------------------------
        # Section A: Curative Visits
        search_criteria = [
            'AND',
            ('institution', '=', data['institution']),
            ('speciality.code', '=', 'CURATIVE'),
            ('state', '=', 'done'),
            ('appointment_date', '>=', start_date),
            ('appointment_date', '<', end_date)
        ]

        appointments = Appointment.search_read(
            search_criteria,
            order=(('speciality', 'ASC'), ('appointment_date', 'ASC')),
            fields_names=['id', 'appointment_date',
                          'patient.name.sex',
                          'speciality.name',
                          'appointment_type'])
        # setup the counts of appointments
        apptcounter = Counter([x['patient.name.sex'] for x in appointments])

        D['A'] = apptcounter.copy()
        D['A'].update(total=sum(apptcounter.values()))

        #--------------------------------------------------------
        # Curative Section
        default_fields_names = ['id', 'patient.name.dob', 'patient.name.sex',
                                'first_visit_this_year',
                                'diagnostic_hypothesis']
        getsex = lambda x: x['patient.name.sex']
        search_criteria = ['AND',
                           ('institution','=',data['institution']),
                           ('state', '=', 'done'),
                           ('evaluation_start', '>=', start_date),
                           ('evaluation_start', '<', end_date)
        ]

        # Newly Diagnosed and First Visits

        age_groups = [
            ('<20', 0, 20), ('20-59', 20, 60), ('60+', 60, None),
            ('Unknown', -1, None)
        ]
        age_grouper = make_age_grouper(age_groups, data['start_date'],
                                       'patient.name.dob')

        disease_groups = [
            ('Diabetes', ['E10 - E14.999z']),
            ('Hypertension', [('I10 - I10.999z',
                               'I15', 'I15.8', 'I15.9')]),
            ('Diabetes and Hypertension', ['E10 - E14.999z',
                                           ('I10 - I10.999z',
                                            'I15', 'I15.8', 'I15.9')])
        ]

        ordering = [('first_visit_this_year', 'ASC')]

        group_counts = []

        for disease_group_name, disease_diagnosis in disease_groups:
            search_clause = search_criteria[:]
            search_clause.extend([
                mk_domain_clause(g,'diagnostic_hypothesis.pathology.code')
                for g in disease_diagnosis
            ])
            all_evals = Evaluation.search_read(
                search_clause, order=ordering,
                fields_names=default_fields_names
            )
            newdiag = {'m': [], 'f': [], 'u': []}
            firstvisit = {'m': [], 'f': [], 'u': []}
            revisit = []

            for e in all_evals:
                newly_diagnosed = False
                diagnostic_search_parm = ['AND',
                        ('id', 'in', e['diagnostic_hypothesis'])
                        ] + [mk_domain_clause(g, 'pathology.code')
                             for g in disease_diagnosis]
                e['diagnostic_hypothesis'] = DiagnosticHypothesis.search_read(
                                                    diagnostic_search_parm,
                                                    fields_names = [
                                                        'pathology.code',
                                                        'first_diagnosis'])
                for dh in e['diagnostic_hypothesis']:
                    if dh['first_diagnosis']:
                        newdiag[e['patient.name.sex']].append(e)
                        newly_diagnosed = True
                        break

                if not newly_diagnosed:
                    if e['first_visit_this_year']:
                        firstvisit[e['patient.name.sex']].append(e)
                    else:
                        revisit.append(e)

            group_counts.append({
                'name': disease_group_name,
                'new': dict([(x, Counter(map(age_grouper, y)))
                            for x, y in newdiag.items()]),
                'first': dict([(x, Counter(map(age_grouper, y)))
                              for x, y in firstvisit.items()]),
                'revisit': Counter(map(getsex, revisit))})

        D['B'] = group_counts[:]

        #--------------------------------------------------------
        # Curative section - regular

        group_counts = []
        age_groups = [('a0_4', 0, 5), ('a5_9', 5, 10), ('a10_14', 10, 15),
                      ('a15_19', 15, 20), ('a20_', 20, None)]

        age_grouper = make_age_grouper(age_groups, data['start_date'],
                                       'patient.name.dob')
        # redefine age_grouper since the age groups have changed

        disease_groups = [
            ('(D) Gastroenteritis', ['A09%']),
            ('(E) Other G.I. Disorders', ['A00 - A08.999z']),
            ('(F) Injuries', 'x'),  # x marks the title
            ('(F)(1) Intentional', ['X60 - X84.999z']),
            ('(F)(2) Unintentional', ['Y60 - Y69.999z']),
            ('(G) Musculoskeletal', ['M00 - M99.999z']),
            ('(H) Leg Ulcers due to :', 'x'),
            ('(H)(1) Diabetes', ['E10 - E14.999z', 'L97']),
            ('(H)(2) Other Conditions', ['L97']),
            ('(I) Genito-Urinary Diseases', 'x'),
            ('(I)(1) STD',[('A56', 'A63.8', 'A56.8', 'A64')]),
            ('(I)(2) PID',['N70 - N74.999z']),
            ('(I)(3) Urinary', ['N30 - N39.999z']),
            # ('(J) Other Gynecological Disorders', ['']),
            ('(K) Psychiatry', ['F00-F99.999z']),
            ('(L) Eye Disorders', ['H00 - H59.999z']),
            ('(M) Diseases of The Respiratory Tract', 'x'),
            ('(M)(1) U.R.T.I.', [('J39%', 'J00 - J06.999z')]),
            ('(M)(2) L.R.T.I.', ['J20 - J22.999z']),
            ('(M)(3) Asthma', ['J45%']),
            ('(N) Skin Disease', [('L00 - L08.999z', 'L10 - L14.999z', 
                                   'L20 - L30.999z', 'L40 - L45.999z',
                                   'L55 - L59.999z', 'L60 - L75.999z',
                                   'L80 - L99.999z')]),
            ('(O) Rheumatic Fever', 'x'),
            ('(O)(1) Number on Register',['I00']),
            ('(O)(2) Number with RHD',['I01']),
            # ('(O)(3) Number given Prophylaxis',),
            ('(P) Other Cardiovascular Disease', [('I52%', 'I51.9')]),
            # ('(Q) Other Diagnoses', [])

        ]  # incomplete list 

        for group_name, group_diagnosis in disease_groups:
            if group_diagnosis == 'x':
                group_counts.append({'title': group_name, 'f': Counter(),
                                     'm': Counter(), 'is_title_row': True})
                continue

            line = {'title': group_name, 'is_title_row': False, 'f': Counter(),
                    'm': Counter()}
            search_clause = search_criteria[:]
            for g in group_diagnosis:
                search_clause.append(
                    mk_domain_clause(g, 'diagnostic_hypothesis.pathology.code')
                )
            all_evals = Evaluation.search_read(
                search_clause,
                fields_names=default_fields_names)
            all_evals.sort(key = getsex)
            for sexkey, sexgroup in groupby(all_evals, getsex):
                line[sexkey] = Counter([age_grouper(x) for x in sexgroup])
                t = sum(line[sexkey].values())
                line[sexkey].update(total=t)

            group_counts.append(line)

        D['C'] = group_counts[:]

        localcontext.update(start_date=start_date,
                            end_date=end_date-timedelta(0, 0.2),
                            D=D,
                            now_date=datetime.now(tz))

        localcontext.update(is_weekly=False, is_monthly=False, subtitle='')
        if (start_date.day == 1 and end_date.day == 1 and
            ((end_date.year == start_date.year and 
             (end_date.month - start_date.month)  == 1) or
            (end_date.year == (1 + start_date.year) and 
             (end_date.month - start_date.month) == -11))):
            localcontext.update(is_monthly=True, mtitle='Monthly',
                                subtitle=start_date.strftime('%B %Y'))
        elif ((end_date - start_date) == timedelta(7)
              and start_date.isoweekday() == 7):
            epiweek = utils.get_epi_week(start_date)  # (sun, sat, yr, week#)
            xsubtitle = ['Week', str(epiweek[3]), 'of', str(epiweek[2]),
                         'ending', epiweek[1].strftime('%F'),
                         '(epidemiological)']
            localcontext.update(subtitle=' '.join(xsubtitle), mtitle='Weekly',
                                is_weekly=True)
        else:
            date_format = '%a %Y-%m-%d'
            xsubtitle = ['Date:', start_date.strftime(date_format)]
            if end_date - start_date > timedelta(1.02):
                # we've got a date range on our hands here
                xsubtitle.extend(['to',
                                  data['end_date'].strftime(date_format)])
                xsubtitle[0] = 'Date range:'
                # use data['end_date'] because end_date is tomorrow
                # alternative would be to subtract a few seconds from end_date
                # But, since end_date calculated from data['end_date'].....
            localcontext.update(subtitle=' '.join(xsubtitle), mtitle='')

        # print('{}\n\n{}\n\n{}'.format('-'*80, repr(localcontext), '-'*80))
        return super(ClinicSummaryReport, cls).parse(
            report, records, data, localcontext
        )
