
from datetime import datetime, timedelta
import pytz
from trytond.pyson import Eval, PYSONEncoder, Date
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.report import Report
from .tryton_utils import get_timezone, get_start_of_day, get_start_of_next_day

__all__ = ('DailyPatientRegister', 'PatientRegisterFiltered')


class BaseReport(Report):
    '''defines basic data elements that are passed to all health_jamaica
    related reports.'''
    __name__ = 'health_jamaica.report_base'

    @classmethod
    def parse(cls, report, records, data, localcontext):
        pool = Pool()
        Institution = pool.get('gnuhealth.institution')
        tz = get_timezone()

        localcontext.update(institution=None, sector='', parish='')

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

            for addr in localcontext['institution'].name.addresses:
                if addr.subdivision:
                    localcontext['parish'] = addr.subdivision.name
                    break

        localcontext['now_date'] = datetime.now(tz)

        return super(BaseReport, cls).parse(report, records, data,
                                            localcontext)


class DailyPatientRegister(BaseReport):
    __name__ = 'health_jamaica.report_patient_register'

    @classmethod
    def parse(cls, report, records, data, localcontext):
        pool = Pool()
        Encounter = pool.get('gnuhealth.encounter')
        Specialty = pool.get('gnuhealth.specialty')
        Institution = pool.get('gnuhealth.institution')
        Company = pool.get('company.company')
        Clinical = pool.get('gnuhealth.encounter.clinical')
        Procedures = pool.get('gnuhealth.encounter.procedures')
        Directions = pool.get('gnuhealth.directions')
        Signs = pool.get('gnuhealth.signs_and_symptoms')
        SecondaryCond = pool.get('gnuhealth.secondary_condition')

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

        start_date = get_start_of_day(data['start_date'])
        end_date = get_start_of_next_day(data['end_date'])

        search_criteria = [
            ('state', '=', 'signed'),
            ('start_time', '>=', start_date),
            ('start_time', '<', end_date),
        ]
        encounter_field_names = [
            'patient', 'patient.name.name', 'patient.age', 'patient.puid',
            'patient.medical_record_num', 'fvty', 'start_time',
            'patient.sex_display', 'appointment.speciality.name']

        if data.get('institution', False):
            search_criteria.append(('institution', '=', data['institution']))
            localcontext['institution'] = Institution(data['institution'])
            osectors = localcontext['institution'].operational_sectors
            if osectors:
                localcontext['sector'] = osectors[0].operational_sector

        if data.get('x_extra_criteria', False):
            criteria_remix = [('encounter.%s' % x, y, z)
                              for x, y, z in search_criteria]
            x_clinical = []
            x_procedure = []
            if (data.get('x_dp_perm') in ('d', 'o', 'dp') and
                    data.get('x_search_criteria', {}).get('disease', False)):
                clinical_domain = ['AND', data['x_search_criteria']['disease'],
                                   criteria_remix]
                # print 'clinical domain for filter is %s' % repr(clinical_domain)
                x_clinical = Clinical.search_read(clinical_domain,
                                                  fields_names=['encounter'])
            if (data.get('x_dp_perm') in ('p', 'o', 'dp') and
                    data.get('x_search_criteria', {}).get('procedure', False)):
                proc_domain = ['AND', data['x_search_criteria']['procedure'],
                               criteria_remix]
                x_procedure = Procedures.search_read(proc_domain,
                                                     fields_names=['encounter'])
            idlist = lambda xl: [x['encounter'] for x in xl]
            if data.get('x_dp_perm') == 'd':  # report on diseases only
                search_criteria = [('id', 'in', idlist(x_clinical))]
            elif data.get('x_dp_perm') == 'p':  # report on procedures only
                search_criteria = [('id', 'in', idlist(x_procedure))]
            elif data.get('x_dp_perm') == 'o':  # one or the other
                search_criteria = [['OR', ('id', 'in', idlist(x_clinical)),
                                    ('id', 'in', idlist(x_procedure))]]
            else:  # here we assume dp which means both must match
                x_idlist = list(set(idlist(x_clinical)
                                    ).intersection(idlist(x_procedure)))
                # use set intersection to get the ids of the encounters
                # that happen to match all the disease and procedure
                # conditions
                search_criteria = [('id', 'in', x_idlist)]
            if data.get('x_encounter_fields', False):
                encounter_field_names.extend(data['x_encounter_fields'])

        if data.get('specialty', False):
            search_criteria.append(('appointment.specialty', '=',
                                    data['specialty']))
            localcontext['specialty'] = Specialty(data['specialty'])
        # print 'Encounter search criteria : %s' % repr(search_criteria)
        # print 'Encounter field_names : %s' % repr(encounter_field_names)
        objects = Encounter.search_read(
            search_criteria,
            order=(('start_time', 'ASC'), ('end_time', 'ASC')),
            fields_names=encounter_field_names)

        enc_ids = [x['id'] for x in objects]
        procs = Directions.search_read(
            [('encounter_component.encounter', 'in', enc_ids)],
            order=(('create_date', 'ASC'),),
            fields_names=['encounter_component.encounter',
                          'procedure.name', 'procedure.description'])
        clinicals = Clinical.search_read(
            [('encounter', 'in', enc_ids)],
            order=(('start_time', 'ASC'),),
            fields_names=['encounter', 'start_time', 'diagnosis.code',
                          'diagnosis.name'])
        signs = Signs.search_read(
            [('clinical_component.encounter', 'in', enc_ids)],
            order=(('create_date', 'ASC'),),
            fields_names=['clinical_component.encounter', 'clinical.name',
                          'clinical.code'])
        secondaryconds = SecondaryCond.search_read(
            [('clinical_component.encounter', 'in', enc_ids)],
            order=(('create_date', 'ASC'),),
            fields_names=['clinical_component.encounter', 'pathology.code',
                          'pathology.name'])
        component_dict = {}
        for x in procs:
            xd = component_dict.setdefault(x['encounter_component.encounter'],
                                           {})
            xd.setdefault('procedures', []).append(
                '%(procedure.description)s [%(procedure.name)s]' % x)

        for x in clinicals:
            if x.get('diagnosis.code', False):
                xd = component_dict.setdefault(x['encounter'], {})
                xd.setdefault('diagnosis', []).append(
                    '%(diagnosis.name)s [%(diagnosis.code)s]' % x)

        for x in signs:
            xd = component_dict.setdefault(x['clinical_component.encounter'],
                                           {})
            xd.setdefault('signs', []).append(
                '%(clinical.name)s [%(clinical.code)s]' % x)

        for x in secondaryconds:
            xd = component_dict.setdefault(x['clinical_component.encounter'],
                                           {})
            xd.setdefault('secondary_conditions', []).append(
                '%(pathology.name)s [%(pathology.code)s]' % x)

        num_objects = 0
        groups = {}
        myzone = get_timezone()
        for ev in objects:
            group_key = myzone.fromutc(ev['start_time']).strftime('%Y-%m-%d')
            ev.update(component_dict.get(ev['id'], []))
            groups.setdefault(group_key, []).append(ev)
            num_objects += 1  # low-tech count since len would count them too
            # print '%s\nEV= %s' % ('~'*80, repr(ev))

        groups = sorted(groups.items(), key=lambda x: x[0])

        localcontext['evaluation_count'] = num_objects
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


class PatientRegisterFiltered(DailyPatientRegister):
    __name__ = 'health_jamaica.report_patient_register_filtered'

    @classmethod
    def parse(cls, report, records, data, localcontext):
        localcontext = {} if localcontext is None else localcontext
        localcontext.update(
            selected_diseases='; '.join(data['x_selected']['disease']),
            selected_procedures='; '.join(data['x_selected']['procedure']),
            disease_plural=(data['x_selected_count'].get('disease', 0) != 1),
            procedure_plural=(
                data['x_selected_count'].get('procedures', 0) != 1))

        return super(PatientRegisterFiltered, cls).parse(report, records,
                                                         data, localcontext)
