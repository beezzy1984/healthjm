
from datetime import datetime, timedelta
import pytz
from trytond.pyson import Eval, PYSONEncoder, Date
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.report import Report
from .tryton_utils import get_timezone, get_start_of_day, get_start_of_next_day

__all__ = ('DailyPatientRegister', )

class BaseReport(Report):
    '''defines basic data elements that are passed to all health_jamaica
    related reports.'''
    __name__ = 'health_jamaica.report_base'

    @classmethod
    def parse(cls, report, records, data, localcontext):
        pool = Pool()
        Institution = pool.get('gnuhealth.institution')
        Company = pool.get('company.company')
        tz = get_timezone()

        localcontext.update(institution=None, sector=None)

        if data.get('institution', False):
            localcontext['institution'] = Institution(data['institution'])
        else:
            institution = Institution.get_institution()
            if institution:
                localcontext['institution'] = institution

        if localcontext.get('institution', False):
            osectors = localcontext['institution'].operational_sectors
            if osectors:
                localcontext['sector'] = osectors[0].operational_sector

        localcontext['now_date']= datetime.now(timezone)

        return super(BaseReport, cls).parse(report, records, data,
                                                      localcontext)


class DailyPatientRegister(BaseReport):
    __name__ = 'health_jamaica.report_patient_register'

    @classmethod
    def parse(cls, report, records, data, localcontext):
        pool = Pool()
        Evaluation = pool.get('gnuhealth.patient.evaluation')
        Specialty = pool.get('gnuhealth.specialty')
        Institution = pool.get('gnuhealth.institution')
        Company = pool.get('company.company')

        localcontext['specialty'] = None
        localcontext['institution'] = None
        localcontext['sector'] = None

        try:
            company = Transaction().context.get('company')
            company = Company(company)
            tzone = company.timezone
        except AttributeError:
            # default timezone
            tzone = 'America/Jamaica' 

        tzone = pytz.timezone(tzone)

        data['start_date'] = datetime(
            *(data['start_date'].timetuple()[:3]+(0,0,0)), tzinfo=tzone)
        data['end_date'] = datetime(
            *(data['end_date'].timetuple()[:3]+(23,59,58)), tzinfo=tzone)

        search_criteria = [
            ('state','=','done'),
            ('evaluation_start','>=',data['start_date']),
            ('evaluation_start', '<=', data['end_date']),
        ]
        
        if data.get('institution', False):
            search_criteria.append(('institution','=',data['institution']))
            localcontext['institution'] = Institution(data['institution'])
            osectors = localcontext['institution'].operational_sectors
            if osectors:
                localcontext['sector'] = osectors[0].operational_sector


        if data.get('specialty', False):
            search_criteria.append(('specialty', '=', data['specialty']))
            localcontext['specialty'] = Specialty(data['specialty'])


        objects = Evaluation.search(search_criteria,
                                    order=(('evaluation_start','ASC'),
                                           ('evaluation_endtime', 'ASC')))
        groups = {}
        myzone = get_timezone()
        for ev in objects:
            group_key = myzone.fromutc(ev.evaluation_start).strftime('%Y-%m-%d')
            groups.setdefault(group_key,[]).append(ev)

        groups = groups.items()
        groups.sort(lambda x,y: cmp(x[0],y[0]))

        localcontext['evaluation_groups'] = groups
        localcontext['eval_date'] = data['start_date'].strftime('%Y-%m-%d')
        localcontext['date_start'] = None
        if timedelta(1) < (data['end_date'] - data['start_date']):
            localcontext['date_start'] = localcontext['eval_date']
            localcontext['date_end'] = data['end_date'].strftime('%Y-%m-%d')

        # print('Now we launch the report with %s'%repr(localcontext))
        # print("*"*80)
        # print('search criteria = %s'%repr(search_criteria))

        return super(DailyPatientRegister, cls).parse(report, records, data,
                                                      localcontext)