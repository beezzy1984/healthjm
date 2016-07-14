

from trytond.model import ModelView, ModelSQL, fields
from trytond.modules.health_jamaica.party import SEX_OPTIONS


class Newborn (ModelSQL, ModelView):
    'Newborn Information'
    __name__ = 'gnuhealth.newborn'

    bba = fields.Boolean('BBA',
                         help='Check this box if born on arrival to facility')

    mother_upi = fields.Function(fields.Char("Mother's UPI"), "get_mother_upi")
    mother_mrn = fields.Function(fields.Char("Medical Record #"),
                                 "get_mother_upi")
    patient_upi = fields.Function(fields.Char("Patients's UPI"), "get_upi")

    def get_upi(self, name):
        '''get baby upi '''
        return self.patient.puid

    def get_mother_upi(self, name):
        '''get mothers upi'''
        if self.mother:
            if name == 'mother_upi':
                return self.mother.puid
            else:
                return self.mother.medical_record_num
        return ''

    @classmethod
    def __setup__(cls):
        super(Newborn, cls).__setup__()

        cls.cephalic_perimeter.string = "Head Circumference"
        cls.length.string = "Crown-Heel Length"

        cls.sex.selection = SEX_OPTIONS
        cls.sex.string = 'Sex at birth'

        cls.newborn_sex = fields.Function(fields.Selection(SEX_OPTIONS, 'Sex'),
                                          'get_newborn_sex')
