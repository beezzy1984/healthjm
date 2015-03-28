

from trytond.model import ModelView, ModelSQL, fields
from ..health_jamaica.tryton_utils import update_states

class Appointment(ModelSQL, ModelView):
    'Patient Appointment'
    __name__ = 'gnuhealth.appointment'
    @classmethod
    def __setup__(cls):
        super(Appointment, cls).__setup__()
        cls.speciality.states = update_states(cls.speciality,
                                              {'required':True})


class SignsAndSymptoms(ModelSQL, ModelView):
    'Evaluation Signs and Symptoms'
    __name__ = 'gnuhealth.signs_and_symptoms'

    @classmethod
    def __setup__(cls):
        super(SignsAndSymptoms, cls).__setup__()
        cls.sign_or_symptom.states = update_states(cls.sign_or_symptom,
                                                   {'invisible':True})

    @staticmethod
    def default_sign_or_symptom():
        return 'symptom'

