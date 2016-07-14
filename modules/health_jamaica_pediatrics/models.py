

from trytond.model import ModelView, ModelSQL, fields
from trytond.modules.health_jamaica.party import SEX_OPTIONS


class Newborn (ModelSQL, ModelView):
    'Newborn Information'
    __name__ = 'gnuhealth.newborn'

    bba = fields.Boolean('BBA',
                         help='Check this box if born on arrival to facility')

    mother_upi = fields.Function(fields.Char("Mother's Upi"), getter="get_mother_upi")
    patient_upi = fields.Function(fields.Char("Patients's Upi"), getter="get_upi")

    def get_upi(self, name):
        '''get baby upi '''
        if not self.patient.puid:
            return None

        return self.patient.puid 

    def get_mother_upi(self, name):
        '''get mothers upi'''
        if not self.mother.name.upi:
            return None

        return self.mother.name.upi

    @classmethod
    def __setup__(cls):
        super(Newborn, cls).__setup__()

        cls.cephalic_perimeter.string = "Head Circumference"
        cls.length.string = "Crown-Heel Length"

        cls.sex.selection = SEX_OPTIONS
        cls.sex.string = 'Sex at birth'

        cls.newborn_sex = fields.Function(fields.Selection(SEX_OPTIONS, 'Sex'),
                                          'get_newborn_sex')
      