
from trytond.pool import Pool
from .models import (DiseaseNotification, TravelHistory, NotificationSymptom,
                     NotifiedSpecimen, RiskFactorCondition)

def register():
    Pool.register(
        DiseaseNotification,
        NotificationSymptom,
        NotifiedSpecimen,
        RiskFactorCondition,
        TravelHistory,
        module='health_disease_notification_history', type_='model')
