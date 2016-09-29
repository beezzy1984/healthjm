
from datetime import datetime
from trytond.pool import Pool
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
        cls.mother.domain = [('name.sex', '!=', 'm')]
        super(Newborn, cls).__setup__()

        cls.cephalic_perimeter.string = "Head Circumference"
        cls.length.string = "Crown-Heel Length"

        cls.sex.selection = SEX_OPTIONS
        cls.sex.string = 'Sex at birth'

        cls.newborn_sex = fields.Function(fields.Selection(SEX_OPTIONS, 'Sex'),
                                          'get_newborn_sex')

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        newvlist = []
        patient_model = pool.get('gnuhealth.patient')
        party_model = pool.get('party.party')
        all_patients = patient_model.search([('id', 'in',
                                              [x['patient'] for x in vlist])])
        party_dict = dict([(p.id, p.name) for p in all_patients])
        party_to_write = []
        for values in vlist:
            patient_id = values['patient']
            dob = datetime.date(values['birth_date'])
            party_obj = party_dict[patient_id]
            values['name'] = party_obj.ref
            newvlist.append(values)
            party_to_write.extend([[party_obj], {'dob': dob}])
        # print('%s\nCreating newborn as %s\n%s\n%s' % ('*'*65, repr(newvlist), repr(vlist), '~'*65))
        return_val = super(Newborn, cls).create(newvlist)
        party_model.write(*party_to_write)
        return return_val
