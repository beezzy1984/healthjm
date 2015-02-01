from trytond.pool import Pool

from .reports import *


def register():
    Pool.register(
        SyndromicSurveillanceWizardModel,
        module='health_jamaica_primarycare', type_='model')

    Pool.register(
        SyndromicSurveillanceWizard,
        module='health_jamaica_primarycare', type_='wizard')


    Pool.register(
        SyndromicSurveillanceReport,
        module='health_jamaica_primarycare', type_='report')

