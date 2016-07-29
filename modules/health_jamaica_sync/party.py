
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from tryton_synchronisation import SyncMixin, SyncUUIDMixin, SyncMode

__all__ = ['Party', 'PartyAddress', 'AlternativePersonID', 'DomiciliaryUnit',
           'PatientData', 'PatientDiseaseInfo', 'PartyRelative',
           'ContactMechanism']


class Party(SyncMixin):
    __name__ = 'party.party'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.full

    def get_wire_value(self):
        values = super(Party, self).get_wire_value()
        if 'internal_user' in values:
            del(values['internal_user'])
        return values

    @classmethod
    def get_unsync_domain(cls):
        context = Transaction().context
        extra_domain = ['OR', ('is_healthprof', '=', True),
                        ('is_person', '=', False)]
        if 'extra_unsync_model' in context and 'extra_unsync_field' in context:
            eu_model = context['extra_unsync_model']
            eu_field = context['extra_unsync_field']
            eu_domain = context.get('extra_unsync_domain',
                                    [['synchronised', '=', False]])
            extra_model = Pool().get(eu_model)
            extra = extra_model.search_read(eu_domain, fields_names=[eu_field])
            if extra:
                extra_domain.append(('id', 'in', [x[eu_field] for x in extra]))
        return extra_domain


class PartyAddress(SyncUUIDMixin):
    __name__ = 'party.address'
    __metaclass__ = PoolMeta


class AlternativePersonID (SyncUUIDMixin):
    __name__ = 'gnuhealth.person_alternative_identification'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.full


class DomiciliaryUnit(SyncUUIDMixin):
    __name__ = 'gnuhealth.du'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.push_update


class PatientData(SyncMixin):
    __name__ = 'gnuhealth.patient'
    __metaclass__ = PoolMeta
    unique_id_column = 'puid'


class PatientDiseaseInfo(SyncUUIDMixin):
    __name__ = 'gnuhealth.patient.disease'
    __metaclass__ = PoolMeta


class PartyRelative(SyncUUIDMixin):
    __name__ = 'party.relative'
    __metaclass__ = PoolMeta


class ContactMechanism(SyncUUIDMixin):
    __name__ = 'party.contact_mechanism'
    __metaclass__ = PoolMeta
