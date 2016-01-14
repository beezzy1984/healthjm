

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
# from trytond.modules.health_jamaica.reports import BaseReport
from trytond.modules.health_jamaica.wizards import StartEndDateModel

from .common import *


class SyndromicSurveillanceReport(Report):
    '''Syndromic Surveillance Report'''
    __name__ = 'healthjm_primarycare.report.syndromic_surveillance'

    @classmethod
    def get_additional_criteria(cls, for_evaluation = False):
        if for_evaluation:
            return []
        else:
            Speciality = Pool().get('gnuhealth.specialty')
            curative, = Speciality.search([('code', '=', 'CURATIVE')])
            return [('speciality', '=', curative)]

    @classmethod
    def parse(cls, report, records, data, localcontext):
        pool = Pool()
        User = pool.get('res.user')
        Institution = pool.get('gnuhealth.institution')
        Company = pool.get('company.company')
        Encounter = pool.get('gnuhealth.encounter')
        Clinical = pool.get('gnuhealth.encounter.clinical')
        # clinical component
        Appointment = pool.get('gnuhealth.appointment')
        # Patient = pool.get('gnuhealth.patient')

        timezone = utils.get_timezone()
        start_date = utils.get_start_of_day(data['start_date'], timezone)
        end_date = utils.get_start_of_next_day(data['end_date'], timezone)
        search_criteria = ['AND',
            ('signed_by', '!=', None),
            ('encounter.start_time','>=',start_date),
            ('encounter.start_time','<',end_date)
        ] + cls.get_additional_criteria(True)
        appt_search_criteria = ['AND',
            ('state', '=', 'done'),
            ('appointment_date','>=',start_date),
            ('appointment_date','<',end_date)] + cls.get_additional_criteria(False)
        encounter_domain = [('state', '=', 'signed')]
        localcontext['user_name'] = User(Transaction().user).name
        if data.get('institution', False):
            i = data['institution']
            encounter_domain.append(('institution', '=', i))
            appt_search_criteria.append(('institution', '=', i))
            localcontext['institution'] = Institution(i)
            osectors = localcontext['institution'].operational_sectors
            if osectors:
                localcontext['sector'] = osectors[0].operational_sector
            else:
                localcontext['sector'] = ''
            localcontext['parish'] = ''
            for addr in localcontext['institution'].name.addresses:
                if addr.subdivision:
                    localcontext['parish'] = addr.subdivision.name
                    break


        common_age_groups = [('< 5yrs',0,5), ('> 5yrs', 5,None)]
        fevers = ['R50', 'R50.5', 'R50.8', 'R50.9']
        syndromes = [
            ('Fever and Rash', {'signs':['R21', fevers]}),
            ('Fever', {'signs':[fevers], 'age_groups':common_age_groups}),
            ('Gastroenteritis', {'signs':['R19.7'],
                                 'age_groups':common_age_groups}),
            ('Accidents', {'signs':[], 'diagnosis':['V01 - X59'],
                           'age_groups':common_age_groups}),
            ('Violence', {'signs':[], 'diagnosis':['X85 - Y09'],
                          'age_groups':common_age_groups}),
            ('Fever and respiratory symptoms', {
                    'age_groups':[('<5 yrs', 0, 5), ('5-59 yrs', 5, 60),
                                  ('>60 yrs', 60, None)],
                    'signs':['R05 - R07', fevers]
            }),
            ('Fever and Haemorrhagic Symptoms', {'signs':[fevers, ('R58', 'R23.3')]}),
            ('Fever and Jaundice',{'signs':['R17', fevers]}),
            ('Fever and Neurological Symptoms',{
                    'signs':[fevers, ['R40','R56','R26']]}),
            ('Asthma',{'signs':[], 'diagnosis':['J45 - J46']}),
            # ('Severe Acute Respiratory Illness (SARI)', {
            #         'signs':[fevers, 'R06', ['R05', 'R07']],
            #         'diagnosis':[]
            #  }),
            # only for people hospitalised
            # if child is hospitalised with pneumonia then count as SARI as well
            # child is < 5 years old
            ('Upper Respiratory Tract Infections', {
                    'signs':[],
                    'diagnosis': ['J00 - J06.999', 'J30 - J39.999']
             }),
            ('Lower Resiratory Tract Infections', {
                    'signs': [],
                    'diagnosis': ['J09 - J18.999', 'J20 - J22.999']}),
            # ('Upper Repiratory Tract Infections', {})

        ]
        output_lines = []
        total_line = Counter(Sun=0, Mon=0, Tue=0, Wed=0, Thu=0, Fri=0, Sat=0)
        def day_group_counts(evaluation_list, field="start_time"):
            # restricted to using day names as the keys since we're sure
            # this will only be run for a single week
            # dayfunc = lambda x: x['evaluation_start'].timetuple()[:3]
            dayfunc = lambda x: utils.localtime(x[field]).strftime('%a')
            # #assuming evaluations are ordered by evaluation_start
            evgroups = groupby(evaluation_list, dayfunc)
            # return [(d, len(list(i))) for d,i in evgroups]
            counter = Counter(Sun=0, Mon=0, Tue=0, Wed=0, Thu=0, Fri=0, Sat=0,
                             total=0)
            counter.update(Counter(map(dayfunc, evaluation_list)))
            counter.update(total = sum(counter.values()))
            return counter, evgroups

        for heading, params in syndromes:
            search_domain = search_criteria[:]
            if params.get('signs', False):
                for sign in params['signs']:
                    search_domain.append(mk_domain_clause(sign))
            if params.get('diagnosis', False):
                for diag in params['diagnosis']:
                    search_domain.append(['OR',
                        mk_domain_clause(diag, 'diagnosis.code'),
                        mk_domain_clause(diag, 'secondary_conditions.pathology.code')]
                    )
            components = Clinical.search_read(
                search_domain,
                order=(('start_time', 'ASC'), ), fields_names=['encounter'])
            if components:
                encounter_domain_real = encounter_domain[:] + [
                    ('id', 'in', [x['encounter'] for x in components])
                ]
                objects = Encounter.search_read(
                    encounter_domain_real,
                    order=(('start_time', 'ASC'), ('end_time', 'ASC')),
                    fields_names=['start_time', 'patient', 'patient.dob'])
            else:
                objects = []

            line = {'title':heading, 'summary':False}
            counts, eval_groups = day_group_counts(objects)
            line.update(dict(counts))
            # for dayname, evallist in eval_groups:
                # patient_counter = Counter(map((lambda g: g['patient']),
                #                               evallist))

            if params.get('age_groups', False):
                line['title'] = '%s (Total)'%(heading,)
                line['summary'] = True

                output_lines.append(line)  # total Line
                age_groupings = defaultdict(list)
                grouper = make_age_grouper(params['age_groups'], end_date,
                                           'patient.dob')
                for ev in objects:
                    age_groupings[grouper(ev)].append(ev)

                for ag in params['age_groups']:
                    g = age_groupings[ag[0]]
                    line = {'title':'%s: %s'%(heading, ag[0]), 'summary':False}
                    line.update(day_group_counts(g)[0])
                    output_lines.append(line)  # age group line
            else:
                # make a single line for the heading
                output_lines.append(line) # no-age-grouping line

        # Now find the numbers of curative patients that were seen
        appointments = Appointment.search_read(appt_search_criteria,
                                    order=(('appointment_date','ASC'),),
                                    fields_names=['name','appointment_date',
                                                  'patient'])

        tcounts, tgroups = day_group_counts(appointments, 'appointment_date')
        for dayname, evallist in tgroups:
                patients = set(map((lambda g: g['patient']), evallist))
                total_line.update({dayname: len(patients)})
        total_line.update(total=sum(total_line.values()))

        localcontext.update(syndrome_counts=output_lines, totals=total_line,
                            epi_week=data['epi_week'],
                            now_date=datetime.now(timezone),
                            epi_week_year=data['epi_week_year'],
                            end_date=data['end_date'])

        return super(SyndromicSurveillanceReport, cls).parse(report,
                                                             records,
                                                             data,
                                                             localcontext)



class SyndromicSurveillanceWizardModel(StartEndDateModel):
    '''Syndromic Surveillance for'''
    __name__ = 'healthjm_primarycare.report.syndromic_surveillance.start'
    selectdate = fields.Date('Select date', required=True)
    epi_week = fields.Integer('Week Number', states=STATE_INVRO,
                              help="Epidemiological Week")
    epi_week_year = fields.Integer('year', states=STATE_INVRO)
    epi_week_display = fields.Char('Week number', size=12, states=STATE_RO)    

    @classmethod
    def __setup__(cls):
        super(SyndromicSurveillanceWizardModel, cls).__setup__()
        cls.on_or_before.string = 'Week Ending'
        cls.on_or_before.help = 'Saturday'
        cls.on_or_before.states = {'readonly':True}
        cls.on_or_after.states = {'invisible':True}
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
