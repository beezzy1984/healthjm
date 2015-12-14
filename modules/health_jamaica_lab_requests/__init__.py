
from trytond.pool import Pool
from .health_lab import *


def register():
    Pool.register(
        LabTestRequest,
        LabTestResult,
        module='health_jamaica_lab_requests', type='model')
