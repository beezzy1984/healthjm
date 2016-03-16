from trytond.model import ModelSQL
from tryton_synchronisation import SyncUUIDMixin, SyncMixin, SyncMode
from trytond.pool import PoolMeta


class HistoryMixin(SyncUUIDMixin, ModelSQL):
    __metaclass__ = PoolMeta
    _history = True
    sync_mode = SyncMode.full


class DiseaseNotification(SyncMixin, ModelSQL):
    __name__ = 'gnuhealth.disease_notification'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.full
    unique_id_field = 'name'


class RiskFactorCondition(HistoryMixin):
    __name__ = 'gnuhealth.disease_notification.risk_disease'


class NotifiedSpecimen(HistoryMixin):
    __name__ = 'gnuhealth.disease_notification.specimen'


class NotificationSymptom(HistoryMixin):
    __name__ = 'gnuhealth.disease_notification.symptom'


class TravelHistory(HistoryMixin):
    __name__ = 'gnuhealth.disease_notification.travel'


class NotificationStateChange(SyncUUIDMixin):
    __name__ = 'gnuhealth.disease_notification.statechange'
    __metaclass__ = PoolMeta
    sync_mode = SyncMode.push_update
