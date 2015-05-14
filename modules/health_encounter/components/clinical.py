from trytond.model import ModelSQL, ModelView, fields
from .base import BaseComponent, SIGNED_STATES as STATES

class EncounterClinical(BaseComponent):
    'Clinical'
    __name__ = 'gnuhealth.encounter.clinical'

    diagnosis = fields.Many2One(
        'gnuhealth.pathology', 'Presumptive Diagnosis',
        help='Presumptive Diagnosis. If no diagnosis can be made'
        ', encode the main sign or symptom.',
        states = STATES)

    secondary_conditions = fields.One2Many(
        'gnuhealth.secondary_condition',
        'clinical_component', 'Secondary Conditions',
        help='Other, Secondary conditions found on the patient',
        states = STATES)

    diagnostic_hypothesis = fields.One2Many(
        'gnuhealth.diagnostic_hypothesis',
        'clinical_component', 'Hypotheses / DDx',
        help='Other Diagnostic Hypotheses / Differential Diagnosis (DDx)',
        states = STATES)

    signs_symptoms = fields.One2Many(
        'gnuhealth.signs_and_symptoms',
        'clinical_component', 'Signs and Symptoms',
        help='Enter the Signs and Symptoms for the patient in this evaluation.',
        states = STATES)
    procedures = fields.One2Many(
        'gnuhealth.directions', 'clinical_component', 'Procedures',
        help='Procedures / Actions to take',
        states = STATES)

# Modification to GNU Health Default classes to point them here instead 
class RewireEvaluationPointer(ModelSQL):
    clinical_component = fields.Many2One('gnuhealth.encounter.clinical',
                                         'Clinic', readonly=True)

    # @classmethod
    # def __setup__(cls):
    #     super(RewireEvaluationPointer, cls).__setup__()
    #     evaluation_field = getattr(cls, cls._evalutaion_field_name)
    #     evaluation_field.model_name = 'gnuhealth.encounter.clinical'

# PATIENT EVALUATION DIRECTIONS
class Directions(RewireEvaluationPointer, ModelView):
    'Patient Directions'
    __name__ = 'gnuhealth.directions'
    _evalutaion_field_name = 'name'


# SECONDARY CONDITIONS ASSOCIATED TO THE PATIENT IN THE EVALUATION
class SecondaryCondition(RewireEvaluationPointer, ModelView):
    'Secondary Conditions'
    __name__ = 'gnuhealth.secondary_condition'


# PATIENT EVALUATION OTHER DIAGNOSTIC HYPOTHESES
class DiagnosticHypothesis(RewireEvaluationPointer, ModelView):
    'Other Diagnostic Hypothesis'
    __name__ = 'gnuhealth.diagnostic_hypothesis'


# PATIENT EVALUATION CLINICAL FINDINGS (SIGNS AND SYMPTOMS)
class SignsAndSymptoms(RewireEvaluationPointer, ModelView):
    'Evaluation Signs and Symptoms'
    __name__ = 'gnuhealth.signs_and_symptoms'
