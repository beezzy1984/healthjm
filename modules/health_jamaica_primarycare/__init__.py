from trytond.pool import Pool

from .reports import *


def register():
    Pool.register(
        ServiceUtilisationWizardModel,
        SyndromicSurveillanceWizardModel,
        module='health_jamaica_primarycare', type_='model')

    Pool.register(
        ServiceUtilisationWizard,
        SyndromicSurveillanceWizard,
        module='health_jamaica_primarycare', type_='wizard')


    Pool.register(
        ServiceUtilisationReport,
        SyndromicSurveillanceReport,
        module='health_jamaica_primarycare', type_='report')

