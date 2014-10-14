
from datetime import datetime, timedelta
import pytz
from trytond.pyson import Eval, PYSONEncoder, Date
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.report import Report

__all__ = ('DailyPatientRegister', )

class DailyPatientRegister(Report):
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
                                    order=(('evaluation_endtime','ASC'),))

        localcontext['patient_evaluations'] = objects
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