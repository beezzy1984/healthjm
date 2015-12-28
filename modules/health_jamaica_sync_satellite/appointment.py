
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from ..health_jamaica.party import ThisInstitution


class Appointment(ModelSQL, ModelView):
    'Appointment'
    __name__ = 'gnuhealth.appointment'

    is_local = fields.Function(fields.Boolean('is local'), 'get_is_local',
                               searcher='search_is_local')

    @classmethod
    def get_is_local(cls, instances, name):
        if not (name == 'is_local'):
            return dict([(i.id, None) for i in instances])
        else:
            here = ThisInstitution()
            return dict([(i.id, here == i.institution) for i in instances])

    @classmethod
    def search_is_local(cls, field_name, clause):
        if field_name == 'is_local':
            if clause:
                if clause[-1]:
                    return [('institution', '=', ThisInstitution())]
                else:
                    return ['OR', ('institution', '=', None),
                            ('institution', '!=', ThisInstitution())]
        return []
