
from trytond.pool import Pool
from .models import (DiseaseNotification, TravelHistory, NotificationSymptom,
                     NotifiedSpecimen, RiskFactorCondition, LabResultType,
                     NotificationStateChange)


def register():
    Pool.register(
        DiseaseNotification,
        NotificationSymptom,
        LabResultType,
        NotifiedSpecimen,
        RiskFactorCondition,
        TravelHistory,
        NotificationStateChange,
        module='health_disease_notification_history', type_='model')
