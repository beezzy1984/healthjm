

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from ..health_jamaica.party import ThisInstitution

class HealthProfessional(ModelSQL, ModelView):
    'Health Professional'
    __name__ = 'gnuhealth.healthprofessional'

    is_local = fields.Function(fields.Boolean('is local'), 'get_is_local',
                               searcher='search_is_local')

    def get_is_local(self, name):
    	if not (name == 'is_local'):
    		return None
    	if self.name.internal_user:
    		return True
    	else:
    		return self.institution == ThisInstitution()

    @classmethod
    def search_is_local(cls, field_name, clause):
        if field_name == 'is_local':
            if clause:
                if clause[-1]:
                    return ['OR',('name.internal_user','!=',None),
                           ('institution','=',ThisInstitution())]
                else:
                    return [['OR',('name.internal_user','=',None),
                           ('institution','!=',ThisInstitution())]]
        return []


# Models associated with HealthProfessional

class OpenAppointmentReportStart(ModelView):
    'Open Appointment Report'
    __name__ = 'gnuhealth.appointment.report.open.start'

    @classmethod
    def __setup__(cls, *args, **kwargs):
        hpdomain = ('is_local','=',True)
        add_domain = True

        if cls.healthprof.domain:
            for clause in cls.healthprof.domain:
                if clause[0] in ['is_local', 'institution']:
                    add_domain = False
                    break
        else:
            cls.healthprof.domain = []

        if add_domain:
            cls.healthprof.domain.append(hpdomain)
