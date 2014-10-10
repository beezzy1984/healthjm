
from datetime import datetime
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

        localcontext['specialty'] = None
        localcontext['institution'] = None

        data['start_date'] = datetime(*(data['start_date'].timetuple()[:3]+(0,0,0)))
        data['end_date'] = datetime(*(data['end_date'].timetuple()[:3]+(23,59,58)))

        search_criteria = [
            ('evaluation_date.appointment_date','>=',data['start_date']),
            ('evaluation_date.appointment_date', '<=', data['end_date']),
        ]
        
        if data.get('institution', False):
            search_criteria.append(('institution','=',data['institution']))
            localcontext['institution'] = Institution(data['institution'])

        if data.get('specialty', False):
            search_criteria.append(('specialty', '=', data['specialty']))
            localcontext['specialty'] = Specialty(data['specialty'])


        objects = Evaluation.search(search_criteria,
                                    order=(('evaluation_endtime','ASC'),))

        localcontext['patient_evaluations'] = objects
        print('Now we launch the report with %s'%repr(localcontext))
        print('search criteria = %s'%repr(search_criteria))
        
        return super(DailyPatientRegister, cls).parse(report, records, data,
                                                      localcontext)