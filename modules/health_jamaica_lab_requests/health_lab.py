
from trytond.model import ModelView, ModelSQL, fields, ModelSingleton
from trytond.pool import Pool
from trytond.transaction import Transaction


class LabTestRequest(ModelSQL, ModelView):
    'Patient Lab Test'
    __name__ = 'gnuhealth.patient.lab.test'
    pass


class LabTestResult(ModelSQL, ModelView):
    'Lab Test Result'
    __name__ = 'gnuhealth.lab'

    @classmethod
    def __setup__(cls):
        super(LabTestResult, cls).__setup__()
        cls.critearea.string = 'Lab Test Criteria'
        cls.date_analysis.states = {'required': True}


class LabTestCriteria(ModelSQL, ModelView):
    'Lab Test Criteria'
    __name__ = 'gnuhealth.lab.test.critearea'

    @classmethod
    def __setup__(cls):
        super(LabTestCriteria, cls).__setup__()
