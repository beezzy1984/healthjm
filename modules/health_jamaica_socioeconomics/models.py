

from trytond.model import ModelView, ModelSQL, fields
from trytond.transaction import Transaction

RELIGIONS = [
    ('christianw', 'Christian (Traditional) - Anglican/Baptist/Catholic etc.'),
    ('sda', 'Seventh Day Adventists'),
    ('jehova', 'Jehova\'s Witness'),
    ('christmodern', 'Christian (Modern) - Universal/Mormon etc'),
    ('rasta','Rastafarian'),
    ('jew', 'Jewish (all)'),
    ('muslims', 'Islam (Muslim, all schools)'),
    ('buddhist', 'Buddhist'),
    ('hindu', 'Hindu'),
    ('none', 'None/Atheist/Agnostic'),
    ('unknown', 'Unknown')
]


class PartyPatient(ModelSQL, ModelView):
    'Party'
    __name__ = 'party.party'

    @classmethod
    def __setup__(cls):
        super(PartyPatient, cls).__setup__()
        cls.occupation.string = "Occupational Group"

class PatientData(ModelSQL, ModelView):
    '''Patient Related Information'''
    __name__ = 'gnuhealth.patient'

    religion = fields.Selection([(None, '')] + RELIGIONS,
                                'Religion',
                                help='Religion or religious persuasion',
                                sort=False)

    @classmethod
    def __setup__(cls):
        super(PatientData, cls).__setup__()
        cls.ses.selection = [
            (None, ''),
            ('0', 'Lower'),
            ('1', 'Lower-middle'),
            ('2', 'Middle'),
            ('3', 'Upper-middle'),
            ('4', 'Upper'),
        ]
        cls.ses.string = "Socioeconomic Class"


class OccupationalGroup(ModelSQL, ModelView):
    '''Occupational Group'''
    __name__ = 'gnuhealth.occupation'

    _rec_name = 'name'

    def __unicode__(self):
        return self.name

    def __str__(self):
        return str(self.name)

    @classmethod
    def __register__(cls, module_name):
        super(OccupationalGroup, cls).__register__(module_name)
        # remove the occupations from the table that don't have 4 char codes
        cursor = Transaction().cursor
        cursor.execute('select count(*) from gnuhealth_occupation where char_length(code)=4;')
        possibly_valid, = cursor.fetchone()
        if possibly_valid == 0:
            cursor.execute('delete from gnuhealth_occupation where char_length(code)<4;')
            cursor.execute('alter sequence gnuhealth_occupation_id_seq restart with 1;')
        else:
            print('Mixed occupation list, cannot auto-resolve. Fix by hand')
