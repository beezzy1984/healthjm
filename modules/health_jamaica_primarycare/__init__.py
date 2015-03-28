from trytond.pool import Pool
from .health import Appointment, SignsAndSymptoms
from .reports import *


def register():
    Pool.register(
        Appointment,
        SignsAndSymptoms,
        ClinicSummaryWizardModel,
        ServiceUtilisationWizardModel,
        SyndromicSurveillanceWizardModel,
        module='health_jamaica_primarycare', type_='model')

    Pool.register(
        ClinicSummaryWizard,
        ServiceUtilisationWizard,
        SyndromicSurveillanceWizard,
        module='health_jamaica_primarycare', type_='wizard')


    Pool.register(
        ClinicSummaryReport,
        ServiceUtilisationReport,
        SyndromicSurveillanceReport,
        module='health_jamaica_primarycare', type_='report')

