

import time
from trytond.cache import LRUDict
from trytond.const import OPERATORS, RECORD_CACHE_SIZE
from trytond.rpc import RPC
from trytond.model import ModelView, ModelStorage, fields
from trytond.wizard import (Wizard, StateView, Button, StateTransition,
                            StateAction)
from trytond.pool import Pool
from trytond.pyson import Eval, Bool, Not

from ..health_jamaica.party import (SEX_OPTIONS, MARITAL_STATUSES)
from tryton_synchronisation import UUID

__all__ = ('RemoteParty', 'RemotePartyImportStart', 'RemotePartyImportDone',
           'RemotePartyImport')
RO = {'readonly':True}
RELATED_LIMIT = 100
# the maximum number of related record types we'll fetch in the foreground

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
    marked_for_import = fields.Boolean('Import party')

    
    @classmethod
    def __setup__(cls, *a, **k):
        super(RemoteParty, cls).__setup__(*a, **k)
        cls.__rpc__['fetch_remote_party'] = RPC(readonly=False)
        if not hasattr(cls, '_xcache'):
            cls._xcache = LRUDict(RECORD_CACHE_SIZE)
        # _zcache stores the records to be import
        if not hasattr(cls, '_zcache'): 
            cls._zcache = LRUDict(RECORD_CACHE_SIZE)
        pool = Pool()
        cls._target_model = pool.get('party.party')
        cls._buttons.update({
            'mark_for_import': {'invisible': Bool(Eval('marked_for_import'))},
            'unmark_import': {'invisible': Not(Bool(Eval('marked_for_import')))}
        })

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
        extra_fields = {
            'code_readonly':True,
            '_timestamp':lambda x:time.mktime(x['create_date'].timetuple()),
            'last_synchronisation':None,
            'marked_for_import':False}
        
        if domain:
            dplus = [('synchronised','=',False)]
            result2 = Party.search_master(dplus + domain, offset, 
                                          100 if limit>100 else limit, order,
                                    fields_names=['name', 'alt_ids', 'upi',
                                                  'is_patient', #'is_healthprof', 'is_institution',
                                                  'sex', 'father_name', 'mother_maiden_name',
                                                  'dob','party_warning_ack', 'maiden_name',
                                                  'marital_status', 'du.uuid',
                                                  'du.full_address','ref',
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
    def get_to_import(cls):
        '''returns the set of records to be imported'''
        #Returns a tuple of (ids, records) where:
        #  ids is a list of ['id'] for the records sorted by name
        #  records is a list dictionary of {id:data}
        records = cls._zcache.items()
        ids = [k[0] for k in records]
        return (ids, dict(records))

    @classmethod
    @ModelView.button
    def mark_for_import(cls, parties):
        read_cache = cls._xcache
        import_cache = cls._zcache
        for party in parties :
            cached_data = read_cache.get(party.id, False)
            if cached_data:
                cached_data['marked_for_import'] = True
                read_cache[party.id] = cached_data
                import_cache[party.id] = cached_data.copy()

    @classmethod
    @ModelView.button
    def unmark_import(cls, parties):
        read_cache = cls._xcache
        import_cache = cls._zcache
        for party in parties:
            cached_data = read_cache.get(party.id)
            if cached_data:
                cached_data['marked_for_import'] = False
                read_cache[party.id] = cached_data
                if import_cache.get(party.id, False):
                    del import_cache[party.id]


class RemotePartyImportStart(ModelView):
    'Party Import Start'
    __name__ = 'party.party.remote_import.start'
    parties = fields.Text('Parties to import', readonly=True)
    num_selected = fields.Integer('There is something to import', readonly=True)


class RemotePartyImportDone(ModelView):
    'Module Install Upgrade Done'
    __name__ = 'party.party.remote_import.done'


class RemotePartyImport(Wizard):
    'Import marked parties'
    __name__ = 'party.party.remote_import.wizard'

    start = StateView(
        'party.party.remote_import.start',
        'health_jamaica_sync_satellite.remote_party_import_start', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Import', 'import_party', 'tryton-ok', default=True,
                   states={'readonly':Not(Bool(Eval('num_selected')))})
        ])
    import_party = StateTransition()
    import_related = StateTransition()
    done = StateView(
        'party.party.remote_import.done',
        'health_jamaica_sync_satellite.remote_party_import_done', [
            Button('Done', 'end', 'tryton-ok', default=True)
            # Button('View imported', 'show_party', tryton-ok)
        ])
    # show_party = StateAction()

    @staticmethod
    def default_start(fields):
        # return a dict with values for each field in the ModelView in start
        ids, datas = RemoteParty.get_to_import()
        num_names,names = len(ids), []
        if num_names:
            names = ['%s (%s)'%(x['name'], x['upi']) for x in datas.values()]
            names.sort()
        else:
            names = ['No patient records have been selected for import']

        return {
            'parties': '\n'.join(names),
            'num_selected': num_names
        }

    def transition_import_party(self):
        ids, datas = RemoteParty.get_to_import()
        pool = Pool()
        party_model = pool.get('party.party')
        du_model = pool.get('gnuhealth.du')
        patient_model = pool.get('gnuhealth.patient')

        party_codes, du_codes, patient_codes = [],[], []
        for c in datas:
            if c.get('code'):
                party_codes.append(c['code'])
            if c.get('ref', False) and c.get('is_patient', False):
                patient_codes.append(c['ref'])
            if c.get('du_code'):
                du_codes.append(c['du_code'])

        if du_codes:
            du_model.pull_master_record(du_codes)
        if party_codes:
            party_model.pull_master_record(party_codes)
        if patient_codes:
            patient_model.pull_master_record(patient_codes)
        self._patient_codes = patient_codes
        self._party_codes = party_codes
        return 'import_related'

    def transition_import_related(self):
        # search for a pull the evaluations and appointments too
        pool = Pool()
        Patient = pool.get('gnuhealth.patient')
        Appointment = pool.get('gnuhealth.appointment')
        Evaluation = pool.get('gnuhealth.patient.evaluation')

        base_domain = [('patient.%s'%Patient.unique_id_column, 'in',
                        self._patient_codes)]
        appointment_domain = [('state', 'in', ['free', 'done'])]
        appointments = Appointment.search_master(base_domain+appointment_domain,
                                                 0, RELATED_LIMIT,
                                                 [('appointment_date', 'DESC')],
                                                 fields_names=['id',
                                                    'appointment_date',
                                                    Appointment.unique_id_column])
        appointment_codes = [x[Appointment.unique_id_column]
                             for x in appointments]
        if appointment_codes:
            Appointment.pull_master_record(appointment_codes)

        evaluation_domain = [('state', 'in', ['done', 'signed'])]
        evaluations = Evaluation.search_master(base_domain+evaluation_domain,
                                               0, RELATED_LIMIT,
                                               [('evaluation_start', 'DESC')],
                                               fields_names=[
                                                    'id', 
                                                    Evaluation.unique_id_column,
                                                    'evaluation_start', 'state'
                                               ])
        evaluation_codes = [x[Evaluation.unique_id_column]
                            for x in evaluations]
        if evaluation_codes:
            Evaluation.pull_master_record(evaluation_codes)

        # and then fetch the One2Many fields on evaluation
        # I.E. secondary_conditions, signs_symptoms, ddx
        evaluation_related_models = []

        return 'done'



