from trytond.model import ModelSQL


class HistoryMixin(ModelSQL):
    _history = True


class DiseaseNotification(HistoryMixin):
    __name__ = 'gnuhealth.disease_notification'


class RiskFactorCondition(HistoryMixin):
    __name__ = 'gnuhealth.disease_notification.risk_disease'


class NotifiedSpecimen(HistoryMixin):
    __name__ = 'gnuhealth.disease_notification.specimen'


class NotificationSymptom(HistoryMixin):
    __name__ = 'gnuhealth.disease_notification.symptom'


class TravelHistory(HistoryMixin):
    __name__ = 'gnuhealth.disease_notification.travel'
