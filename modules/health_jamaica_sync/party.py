
from trytond.pool import PoolMeta
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
    _extra_unsync_domain = ['OR', ('is_healthprof', '=', True),
                            ('is_person', '=', False)]

    def get_wire_value(self):
        values = super(Party, self).get_wire_value()
        if 'internal_user' in values:
            del(values['internal_user'])
        return values

    @classmethod
    def get_to_synchronise(cls, remote_sync_data=None):
        if remote_sync_data:
            return super(Party, cls).get_to_synchronise(remote_sync_data)
        else:
            with Transaction().set_context(active_test=False) as t:
                if cls._extra_unsync_domain:
                    unsync_domain = ['AND', ('synchronised', '=', False),
                                     cls._extra_unsync_domain]
                else:
                    unsync_domain = [('synchronised', '=', False)]
                unsynced = cls.search(unsync_domain)

            return [r.get_wire_value() for r in unsynced]


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
