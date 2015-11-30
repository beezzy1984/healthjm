

from trytond.model import ModelView, ModelSQL, fields
from trytond.modules.health_jamaica.party import SEX_OPTIONS


class Newborn (ModelSQL, ModelView):
    'Newborn Information'
    __name__ = 'gnuhealth.newborn'

    bba = fields.Boolean('BBA',
                         help='Check this box if born on arrival to facility')

    @classmethod
    def __setup__(cls):
        super(Newborn, cls).__setup__()

        cls.cephalic_perimeter.string = "Head Circumference"
        cls.length.string = "Crown-Heel Length"

        cls.sex.selection = SEX_OPTIONS
        cls.sex.string = 'Sex at birth'

        cls.newborn_sex = fields.Function(fields.Selection(SEX_OPTIONS, 'Sex'),
                                          'get_newborn_sex')
