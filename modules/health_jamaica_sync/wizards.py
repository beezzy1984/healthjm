
import time
from trytond.cache import LRUDict
from trytond.const import OPERATORS, RECORD_CACHE_SIZE
from trytond.wizard import (Wizard, StateView, StateTransition, Button,
                            StateAction)
from trytond.model import ModelView, ModelStorage, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Not, Bool, PYSONEncoder
from trytond.transaction import Transaction

from ..health_jamaica.health_jamaica import (SEX_OPTIONS)

__all__ = ('RemoteParty',)


class RemoteParty(ModelView, ModelStorage):
    'Party'
    __name__ = 'party.party.remote'
    upi = fields.Char('UPI')
    name = fields.Char('Name')
    alt_ids = fields.Char('Alternate IDs')
    father_name = fields.Char('Father\'s Name')
    mother_maiden_name = fields.Char('Mother\'s Maiden Name')
    marital_status = fields.Char('Marital status')
    alias = fields.Char('Pet Name/Alias')
    code = fields.Char('Code')
    sex = fields.Selection([(None,'')] + SEX_OPTIONS, 'Sex')
    dob = fields.Date('DoB', help='Date of Birth')
    party_warning_ack = fields.Boolean('Party verified')


    @classmethod
    def read(cls, ids, fields_names=None):
        print(('{}\n    ids={}\n    fields_names={}').format('*'*80,
            repr(ids), repr(fields_names)))
        # transaction = Transaction()
        # cache = transaction.cursor.get_cache(transaction.context)
        # cache_key = cls.__name__
        ret = []
        for iid in ids:
            data = cls.tcache.get(iid)
            print('fetching ID:{} as {}'.format(iid, repr(data)))
            if data:
                ret.append(data)
        print('\n\n return = {}\n{}'.format(repr(ret), '#'*79))
        import pdb; pdb.set_trace()
        return ret
        # return cls.search_master(domain, offset, limit, order) 
                     # fields_names=['name', 'medical_record_num', 'alt_ids', 'upi',
                     # 'is_patient', 'is_healthprof', 'is_institution'])

    @classmethod
    def search(cls, domain, offset=0, limit=None, order=None, count=False,
            query=False):
        Party = Pool().get('party.party')
        if not hasattr(cls, 'tcache'):
            cls.tcache = LRUDict(RECORD_CACHE_SIZE)

        keymap={'name':'rec_name',}
        extra_fields = {'code_readonly':True,
        '_timestamp':lambda x:time.mktime(x['create_date'].timetuple()),
        'last_synchronisation':None}

        import pdb; pdb.set_trace()
        if domain:
            result2 = Party.search_master(domain, offset, limit, order,
                                    fields_names=['name', 'alt_ids', 'upi',
                                                  # 'is_patient', 'is_healthprof', 'is_institution',
                                                  'sex', 'father_name', 'mother_maiden_name',
                                                  'dob','party_warning_ack', 'maiden_name',
                                                  'marital_status',
                                                  'alias','create_date', 'id',
                                                  'activation_date', 'write_date'])
                                    # fields_names=['code', 'create_date', 
                                    # 'citizenship', 'alternative_identification', 
                                    # 'sex', 'insurance_company_type', 
                                    # 'internal_user', 'father_name', 
                                    # 'activation_date', 'vat_number', 
                                    # 'education', 'id', 'occupation', 
                                    # 'create_uid', 'du', 'is_patient', 
                                    # 'is_insurance_company', 'code_length', 
                                    # 'residence', 'mother_maiden_name', 'vat_country', 
                                    # 'firstname', 'maiden_name', 'middlename', 'lastname', 
                                    # 'ethnic_group', 'last_synchronisation', 'active', 
                                    # 'write_uid', 'lang', 'unidentified', 'name', 'dob',
                                    #  'ref', 'marital_status', 'synchronised_instances', 
                                    #  'is_healthprof', 'is_pharmacy', 'alias', 'suffix', 
                                    #  'is_institution', 'write_date', 'is_person', 
                                    #  'party_warning_ack'])
            result2_return = []

            for data in result2:
                result2_return.append(data['id'])
                for k,v in keymap.iteritems():
                    data[v] = data[k]

                for k,v in extra_fields.iteritems():
                    if callable(v):
                        data[k] = v(data)
                    else:
                        data[k] = v
                cls.tcache.setdefault(data['id'], {}).update(data)

            print ('/'*79)
            print ('MASTER = {}\n{}'.format(repr(result2), '\\'*79))
            return result2_return
        return []

# cache[cls.__name__] = LRUDict(RECORD_CACHE_SIZE)

# 'code', 'create_date', 'citizenship', 'alternative_identification', 'sex', 'insurance_company_type', 'internal_user', 'father_name', 'activation_date', 'vat_number', 'education', 'id', 'occupation', 'create_uid', 'du', 'is_patient', 'is_insurance_company', 'code_length', 'residence', 'mother_maiden_name', 'vat_country', 'firstname', 'maiden_name', 'middlename', 'lastname', 'ethnic_group', 'last_synchronisation', 'active', 'write_uid', 'lang', 'unidentified', 'name', 'dob', 'ref', 'marital_status', 'synchronised_instances', 'is_healthprof', 'is_pharmacy', 'alias', 'suffix', 'is_institution', 'write_date', 'is_person', 'party_warning_ack'

    # @classmethod
    # def search_master(cls, domain, offset=0, limit=None, order=None,
    #         fields_names=None)

class PartyMasterSearchModel(ModelView):
    'Party Master Search'
    __name__ = 'party.party.mastersearch.start'
    upi = fields.Char('UPI')
    name = fields.Char('Name')
    alt_ids = fields.Char('Alternate IDs')
    father_name = fields.Char('Father\'s Name')
    mother_maiden_name = fields.Char('Mother\'s Maiden Name')
    marital_status = fields.Char('Marital status')
    alias = fields.Char('Pet Name/Alias')
    code = fields.Char('Code')


class PartyMasterSearchWizard(Wizard):
    'Party Master Search'
    __name__ = 'party.party.mastersearch.wizard'
    start = StateView('party.party.mastersearch.start',
                      'health_jamaica_sync.party_master_search_form', [
                        Button('Cancel', 'end', 'tryton-cancel'),
                        Button('Find', 'performsearch', 'tryton-search',
                            default=True),
                      ])
    search_result = StateView('party.party.remote',
                      'health_jamaica_sync.party_master_search_tree', [
                      Button('New Search', 'start', 'tryton-search', 
                             default=True),
                      Button('Close', 'end', 'tryton-cancel'),
                    ])
    performsearch = StateAction('health_jamaica_sync.remote_party_tree')

    def transition_performsearch(self):
        return 'search_result'

    def do_performsearch(self, action):
        pass
