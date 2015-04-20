from trytond.model import fields
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
        'evaluation', 'Secondary Conditions', help='Other, Secondary'
        ' conditions found on the patient',
        states = STATES)

    diagnostic_hypothesis = fields.One2Many(
        'gnuhealth.diagnostic_hypothesis',
        'evaluation', 'Hypotheses / DDx', help='Other Diagnostic Hypotheses /'
        ' Differential Diagnosis (DDx)',
        states = STATES)

    signs_symptoms = fields.One2Many(
        'gnuhealth.signs_and_symptoms',
        'evaluation', 'Signs and Symptoms', help='Enter the Signs and Symptoms'
        ' for the patient in this evaluation.',
        states = STATES)
    procedures = fields.One2Many(
        'gnuhealth.directions', 'name', 'Procedures',
        help='Procedures / Actions to take',
        states = STATES)
