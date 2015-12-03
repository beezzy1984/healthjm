# models turned on for sync solely for the purpose of relationships
# the models defined here don't actually send/recieve data for sync
from tryton_synchronisation import SyncMixin, SyncUUIDMixin, SyncMode
from trytond.pool import PoolMeta

__all__ = [
    'Country', 'CountrySubdivision', 'PostOffice', 'DistrictCommunity',
    'OccupationalGroup', 'Ethnicity'
]


class Country(SyncMixin):
    __name__ = 'country.country'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.none


class CountrySubdivision(SyncMixin):
    __name__ = 'country.subdivision'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.none


class PostOffice(SyncMixin):
    __name__ = 'country.post_office'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.none


class DistrictCommunity(SyncMixin):
    __name__ = 'country.district_community'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.none


class OccupationalGroup(SyncMixin):
    '''Occupational Group'''
    __name__ = 'gnuhealth.occupation'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.none


class Ethnicity(SyncMixin):
    __name__ = 'gnuhealth.ethnicity'
    __metaclass__ = PoolMeta
    unique_id_column = 'code'
    sync_mode = SyncMode.none
