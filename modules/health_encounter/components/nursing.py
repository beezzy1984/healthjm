# -*- coding: utf-8 -*-

from trytond.model import ModelView, ModelSQL, fields
from .base import BaseComponent, SIGNED_STATES
from trytond.transaction import Transaction

class EncounterAnthro(BaseComponent):
    'Anthropometry'
    __name__ = 'gnuhealth.encounter.anthropometry'

    weight = fields.Float('Weight', help='Weight in Kilos',
        states = SIGNED_STATES)
    height = fields.Float('Height', help='Height in centimeters, eg 175',
        states = SIGNED_STATES)

    bmi = fields.Float(
        'Body Mass Index',
        readonly=True,
        states = SIGNED_STATES)

    head_circumference = fields.Float(
        'Head Circumference',
        help='Head circumference',
        states = SIGNED_STATES)

    abdominal_circ = fields.Float('Waist',
        states = SIGNED_STATES)
    hip = fields.Float('Hip', help='Hip circumference in centimeters, eg 100',
        states = SIGNED_STATES)

    whr = fields.Float(
        'WHR', help='Waist to hip ratio', readonly=True,
        states = SIGNED_STATES)

    head_circumference = fields.Float(
        'Head Circumference',
        help='Head circumference',
        states = SIGNED_STATES)

    # calculate BMI
    @fields.depends('weight', 'height', 'bmi')
    def on_change_with_bmi(self):
        if self.height and self.weight:
            if (self.height > 0):
                return self.weight / ((self.height / 100) ** 2)
            return 0

    # Calculate WH ratio
    @fields.depends('abdominal_circ', 'hip', 'whr')
    def on_change_with_whr(self):
        waist = self.abdominal_circ
        hip = self.hip
        if (hip > 0):
            whr = waist / hip
        else:
            whr = 0
        return whr

    def __init__(self, id=None, **kwargs):
        print('%s\nAnthro-init with id=%s and \nkwargs = %s\n\n'%('*'*80, str(id), repr(kwargs)))
        print('\ncontext = %s\n%s'%(Transaction().context, '*'*80))
        super(EncounterAnthro, self).__init__(id, **kwargs)



class EncounterAmbulatory(BaseComponent):
    'Ambulatory'
    __name__ = 'gnuhealth.encounter.ambulatory'

    # Vital Signs
    systolic = fields.Integer('Systolic Pressure', states=SIGNED_STATES)
    diastolic = fields.Integer('Diastolic Pressure', states=SIGNED_STATES)
    bpm = fields.Integer('Heart Rate',
        help='Heart rate expressed in beats per minute', states=SIGNED_STATES)
    respiratory_rate = fields.Integer('Respiratory Rate',
        help='Respiratory rate expressed in breaths per minute',
        states=SIGNED_STATES)
    osat = fields.Integer('Oxygen Saturation',
        help='Oxygen Saturation(arterial).', states=SIGNED_STATES)
    temperature = fields.Float('Temperature',
        help='Temperature in degrees celsius', states=SIGNED_STATES)
    glycemia = fields.Float(
        'Glycemia',
        help='Last blood glucose level. Can be an approximate value.',
        states = SIGNED_STATES)

    hba1c = fields.Float(
        'Glycated Hemoglobin',
        help='Last Glycated Hb level. Can be an approximate value.',
        states = SIGNED_STATES)

    cholesterol_total = fields.Integer(
        'Last Cholesterol',
        help='Last cholesterol reading. Can be an approximate value',
        states = SIGNED_STATES)

    hdl = fields.Integer(
        'Last HDL',
        help='Last HDL Cholesterol reading. Can be an approximate value',
        states = SIGNED_STATES)

    ldl = fields.Integer(
        'Last LDL',
        help='Last LDL Cholesterol reading. Can be an approximate value',
        states = SIGNED_STATES)

    tag = fields.Integer(
        'Last TAGs',
        help='Triacylglycerol(triglicerides) level. Can be an approximate.',
        states = SIGNED_STATES)

    malnutrition = fields.Boolean(
        'Malnourished',
        help='Check this box if the patient show signs of malnutrition. If'
        ' associated  to a disease, please encode the correspondent disease'
        ' on the patient disease history. For example, Moderate'
        ' protein-energy malnutrition, E44.0 in ICD-10 coding',
        states = SIGNED_STATES)

    dehydration = fields.Boolean(
        'Dehydration',
        help='Check this box if the patient show signs of dehydration. If'
        ' associated  to a disease, please encode the  correspondent disease'
        ' on the patient disease history. For example, Volume Depletion, E86'
        ' in ICD-10 coding',
        states = SIGNED_STATES)

    # @classmethod
    # def __setup__(cls):
    #     super(EncounterAmbulatory, cls).__setup__()
    #     cls.temperature.string = "Temperature (°C)"

