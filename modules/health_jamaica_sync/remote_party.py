

import time
from trytond.cache import LRUDict
from trytond.const import OPERATORS, RECORD_CACHE_SIZE
from trytond.rpc import RPC
from trytond.config import CONFIG
from trytond.model import ModelView, ModelStorage, fields
from trytond.pool import Pool
from trytond.pyson import Eval, Bool

from ..health_jamaica.health_jamaica import (SEX_OPTIONS, MARITAL_STATUSES)
from tryton_synchronisation import UUID

__all__ = ('RemoteParty',)
RO = {'readonly':True}

class RemoteParty(ModelView, ModelStorage):
    'Party'
    __name__ = 'party.party.remote'
    upi = fields.Char('UPI', states=RO)
    name = fields.Char('Name', states=RO)
    alt_ids = fields.Char('Alternate IDs', states=RO)
    father_name = fields.Char('Father\'s Name', states=RO)
    mother_maiden_name = fields.Char('Mother\'s Maiden Name', states=RO)
    marital_status = fields.Selection([(None, '')]+MARITAL_STATUSES,
                                      'Marital status', states=RO)
    alias = fields.Char('Pet Name/Alias', states=RO)
    code = fields.Char('Code', states=RO)
    sex = fields.Selection([(None,'')] + SEX_OPTIONS, 'Sex', states=RO)
    dob = fields.Date('DoB', help='Date of Birth', states=RO)
    maiden_name = fields.Char('Maiden Name', states={'readonly':True,
                                                    'invisible':Bool(Eval('sex') == 'm')})
    du_code = UUID('DU_uuid')
    du_address = fields.Text('Address', states=RO)

    
    @classmethod
    def __setup__(cls, *a, **k):
        super(RemoteParty, cls).__setup__(*a, **k)
        cls.__rpc__['fetch_remote_party'] = RPC(readonly=False)
        if not hasattr(cls, '_xcache'):
            cls._xcache = LRUDict(RECORD_CACHE_SIZE)
        cls._target_model = Pool().get('party.party')
        cls._du_model = Pool().get('gnuhealth.du')

    @classmethod
    def read(cls, ids, fields_names=None):
        ret = []
        for iid in ids:
            data = cls._xcache.get(iid)          
            if data:
                # if fields_names is None:
                ret.append(data)
                # else:
                #     ret.append(dict([(x,data.get(x)) for x in fields_names]))

        return ret

    @classmethod
    def search(cls, domain, offset=0, limit=None, order=None, count=False,
            query=False):
        Party = cls._target_model
        cache = cls._xcache
        keymap={'name':'rec_name', 'du.full_address':'du_address',
                'du.uuid':'du_code'}
        extra_fields = {'code_readonly':True,
        '_timestamp':lambda x:time.mktime(x['create_date'].timetuple()),
        'last_synchronisation':None}
        
        if domain:
            dplus = [('synchronised_instances','bitunset',
                      int(CONFIG['synchronisation_id']))]
            result2 = Party.search_master(dplus + domain, offset, 
                                          100 if limit>100 else limit, order,
                                    fields_names=['name', 'alt_ids', 'upi',
                                                  # 'is_patient', 'is_healthprof', 'is_institution',
                                                  'sex', 'father_name', 'mother_maiden_name',
                                                  'dob','party_warning_ack', 'maiden_name',
                                                  'marital_status', 'du.uuid',
                                                  'du.full_address',
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

                cls._xcache.setdefault(data['id'], {}).update(data)
            return result2_return
        return []

    @classmethod
    def fetch_remote_party(cls, ids):
        party_codes, du_codes = [],[]
        for c in cls.read(ids, ['code', 'du_code']):
            if c.get('code'):
                party_codes.append(c['code'])
            if c.get('du_code'):
                du_codes.append(c['du_code'])

        if du_codes:
            cls._du_model.pull_master_record(du_codes)
        if party_codes:
            cls._target_model.pull_master_record(party_codes)
        
        if du_codes or party_codes:
            from celery_synchronisation import synchronise_new, synchronise_push_all
            synchronise_new.apply_async()
            synchronise_push_all.apply_async()

        return 'switch tree'

