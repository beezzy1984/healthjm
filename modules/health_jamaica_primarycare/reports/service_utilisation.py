
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
from trytond.modules.health_jamaica.wizards import StartEndDateModel
# from trytond.modules.health_jamaica.reports import BaseReport
from .common import *

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
        end_date = utils.get_start_of_day(data['end_date'], timezone)
        end_date_calc = utils.get_start_of_next_day(end_date, timezone)

        search_criteria = ['AND',
            ('state','=','done'),
            ('appointment_date','>=',start_date),
            ('appointment_date','<',end_date_calc)
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
            else:
                localcontext['sector'] = ''
            localcontext['parish'] = ''
            for addr in institution.name.addresses:
                if addr.subdivision:
                    localcontext['parish'] = addr.subdivision.name
                    break
        else:
            default_services = ['Curative', 'Oral Health (Primary Care)',
                                'Family Planning', 'Child Health', 'Antenatal',
                                'Nutrition', 'Postnatal']
            default_services = [{'specialty.name': x, 'is_main_specialty': False}
                                for x  in default_services]

        age_groups = [('0 - 4', 0, 5), ('5 - 9', 5, 10), ('10 - 19', 10, 20),
                      ('20 - 59', 20, 60), ('60+', 60, None),
                      ('Unknown', -1, None)]
                      # negative min_age for dob==null

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
                            end_date=end_date,
                            service_counts=service_counts,
                            total_line=total_line,
                            now_date=datetime.now(timezone),)

        return super(ServiceUtilisationReport, cls).parse(
                        report, records, data, localcontext
                    )

class ServiceUtilisationWizardModel(StartEndDateModel):
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

