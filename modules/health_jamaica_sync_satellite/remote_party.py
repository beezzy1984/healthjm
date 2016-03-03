

import time
import memcache
from trytond.rpc import RPC
from trytond.model import ModelView, ModelStorage, fields
from trytond.wizard import (Wizard, StateView, Button, StateTransition)
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.pyson import Eval, Bool, Not
from trytond.config import config

from ..health_jamaica.party import (SEX_OPTIONS, MARITAL_STATUSES)
from tryton_synchronisation import UUID

try:
    import cPickle as pickle
except ImportError:
    import pickle

__all__ = ['RemoteParty', 'RemotePartyImportStart',
           'RemotePartyImportDone', 'RemotePartyImport']
RO = {'readonly': True}
RELATED_LIMIT = 100
RECORD_CACHE_SIZE = 500
# the maximum number of related record types we'll fetch in the foreground
CACHE_TIME = 1800


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
    sex = fields.Selection([(None, '')] + SEX_OPTIONS, 'Sex', states=RO)
    dob = fields.Date('DoB', help='Date of Birth', states=RO)
    maiden_name = fields.Char('Maiden Name',
                              states={'readonly': True,
                                      'invisible': Eval('sex', '') == 'm'})
    du_code = UUID('DU_uuid')
    du_address = fields.Text('Address', states=RO)
    marked_for_import = fields.Boolean('To be imported',
                                       states={'readonly': True})

    @classmethod
    def __setup__(cls, *a, **k):
        super(RemoteParty, cls).__setup__(*a, **k)
        cls.__rpc__['fetch_remote_party'] = RPC(readonly=False)
        # if not hasattr(cls, '_xcache'):
        #     cls._xcache = LRUDict(RECORD_CACHE_SIZE)
        # # _zcache stores the records to be import
        # if not hasattr(cls, '_zcache'):
        #     cls._zcache = LRUDict(RECORD_CACHE_SIZE)
        # if not hasattr(cls, '_post_import_cache'):
        #     cls._post_import_cache = LRUDict(RECORD_CACHE_SIZE)
        pool = Pool()
        cls._target_model = pool.get('party.party')
        cache_server = config.get('synchronisation', 'cache_server',
                                  '127.0.0.1:11211')
        cls._cache_client = memcache.Client([cache_server])
        # cls._cache_model = pool.get('party.party.remote_cache')
        cls._cache_field_names = ['searched', 'to_import', 'imported']
        cls._buttons.update({
            'mark_for_import': {'readonly': Eval('marked_for_import', False)},
            'unmark_import': {'readonly': ~Eval('marked_for_import', False)}
        })

    @classmethod
    def _get_cache_key(cls):
        # returns a cache key prefix for this user
        tact = Transaction()
        ckey = 'hjmsync_u%d:' % tact.user
        return ckey

    @classmethod
    def _get_cache(cls):
        '''returns a tuple of readcache, import_cache, imported from
        cls._cache_model'''
        def explode(s):
            return pickle.loads(s) if s else s
        cached = cls._cache_client.get_multi(cls._cache_field_names,
                                             key_prefix=cls._get_cache_key())
        result = tuple([explode(cached.get(k, {}))
                       for k in cls._cache_field_names])
        return result

    @classmethod
    def _set_cache(cls, *arg):  # searched, to_import, imported):
        def implode(val):
            return pickle.dumps(val) if val is not None else val
        key_prefix = cls._get_cache_key()
        values = dict(zip(cls._cache_field_names, [implode(x) for x in arg]))
        not_written = cls._cache_client.set_multi(
            values, time=CACHE_TIME, key_prefix=key_prefix)
        if not_written:  # we'll try one more time
            new_values = dict([(x, values[x]) for x in not_written])
            cls._cache_client.set_multi(new_values, key_prefix=key_prefix)

    @classmethod
    def read(cls, ids, fields_names=None):
        ret = []
        s, i, p = cls._get_cache()
        for iid in ids:
            data = s.get(iid)
            if data:
                ret.append(data)
        return ret

    @classmethod
    def search(cls, domain, offset=0, limit=None, order=None, count=False,
               query=False):
        Party = cls._target_model
        keymap = {'name': 'rec_name', 'du.full_address': 'du_address',
                  'du.uuid': 'du_code'}
        extra_fields = {
            'code_readonly': True,
            '_timestamp': lambda x: time.mktime(x['create_date'].timetuple()),
            'last_synchronisation': None,
            'marked_for_import': False}
        read_cache, i, post_import_cache = cls._get_cache()
        read_cache = {}

        if domain:
            dplus = [('synchronised', '=', False), ('is_person', '=', True)]
            already_imported = post_import_cache.keys()
            if already_imported:
                dplus.append(('id', 'not in', already_imported))
            result2 = Party.search_master(
                dplus + domain, offset, 100 if limit > 100 else limit, order,
                fields_names=['name', 'alt_ids', 'upi', 'is_patient',
                              'sex', 'father_name', 'mother_maiden_name',
                              'dob', 'unidentified', 'maiden_name',
                              'marital_status', 'du.uuid', 'du.full_address',
                              'ref', 'alias', 'create_date', 'id',
                              'activation_date', 'write_date'])
            result2_return = []

            for data in result2:
                for k, v in keymap.iteritems():
                    data[v] = data[k]

                for k, v in extra_fields.iteritems():
                    if callable(v):
                        data[k] = v(data)
                    else:
                        data[k] = v
                result2_return.append(data['id'])

                read_cache.setdefault(data['id'], {}).update(data)
            cls._set_cache(read_cache, i, post_import_cache)
            return result2_return
        return []

    @classmethod
    def get_to_import(cls):
        '''returns the set of records to be imported'''
        # Returns a tuple of (ids, records) where:
        #  ids is a list of ['id'] for the records sorted by name
        #  records is a list dictionary of {id:data}
        s, i, p = cls._get_cache()
        records = i.items()
        ids = [k[0] for k in records]
        return (ids, dict(records))

    @classmethod
    def mark_imported(cls, ids=None):
        '''
        clears the ids passed in from the set of records to be imported
        and puts them in the _post_import_cache for filtering purposes
        '''
        search_cache, import_cache, post_cache = cls._get_cache()
        for z_id in ids:
            if z_id in import_cache:
                post_cache[z_id] = import_cache[z_id]
                del import_cache[z_id]
        cls._set_cache(search_cache, import_cache, post_cache)

    @classmethod
    @ModelView.button
    def mark_for_import(cls, parties):
        read_cache, import_cache, post_cache = cls._get_cache()
        for party in parties:
            cached_data = read_cache.get(party.id, False)
            if cached_data:
                cached_data['marked_for_import'] = True
                read_cache[party.id] = cached_data
                import_cache[party.id] = cached_data.copy()
        cls._set_cache(read_cache, import_cache, post_cache)

    @classmethod
    @ModelView.button
    def unmark_import(cls, parties):
        read_cache, import_cache, post_cache = cls._get_cache()
        for party in parties:
            cached_data = read_cache.get(party.id)
            if cached_data:
                cached_data['marked_for_import'] = False
                read_cache[party.id] = cached_data
                if import_cache.get(party.id, False):
                    del import_cache[party.id]
        cls._set_cache(read_cache, import_cache, post_cache)


class RemotePartyImportStart(ModelView):
    'Party Import Start'
    __name__ = 'party.party.remote_import.start'
    parties = fields.Text('Parties to import', readonly=True)
    num_selected = fields.Integer('Number selected for import', readonly=True)


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
                   states={'readonly': Not(Bool(Eval('num_selected')))})
        ])
    import_party = StateTransition()
    import_related = StateTransition()
    done = StateView(
        'party.party.remote_import.done',
        'health_jamaica_sync_satellite.remote_party_import_done', [
            Button('Done', 'finish', 'tryton-ok', default=True)
            # Button('View imported', 'show_party', tryton-ok)
        ])
    finish = StateTransition()
    # show_party = StateAction()

    @staticmethod
    def default_start(fields):
        # return a dict with values for each field in the ModelView in start
        ids, datas = RemoteParty.get_to_import()
        num_names, names = len(ids), []
        if num_names:
            names = [u'%s (%s)' % (x['name'], x['upi'])
                     for x in datas.values()]
            names.sort()
        else:
            names = ['No patient records have been selected for import']

        return {
            'parties': u'\n'.join(names),
            'num_selected': num_names
        }

    def transition_import_party(self):
        ids, datas = RemoteParty.get_to_import()
        pool = Pool()
        party_model = pool.get('party.party')
        du_model = pool.get('gnuhealth.du')
        patient_model = pool.get('gnuhealth.patient')
        code_map = {}

        party_codes, du_codes, patient_codes = [], [], []
        for d_id, c in datas.items():
            if c.get('code'):
                party_codes.append(c['code'])
                code_map[c['code']] = d_id
            if c.get('ref', False) and c.get('is_patient', False):
                patient_codes.append(c['ref'])
            if c.get('du_code'):
                du_codes.append(c['du_code'])

        if du_codes:
            du_model.pull_master_record(du_codes)
        if party_codes:
            parties_made, n = party_model.pull_master_record(party_codes)
        if patient_codes:
            patient_model.pull_master_record(patient_codes)
        ids_imported = [code_map[p] for p in parties_made]
        if ids_imported:
            RemoteParty.mark_imported(ids_imported)
        self._patient_codes = patient_codes
        self._party_codes = party_codes
        return 'import_related'

    def transition_import_related(self):
        # search for a pull the encounters and appointments too
        pool = Pool()
        Patient = pool.get('gnuhealth.patient')
        Appointment = pool.get('gnuhealth.appointment')
        # Evaluation = pool.get('gnuhealth.patient.evaluation')
        Encounter = pool.get('gnuhealth.encounter')

        base_domain = [('patient.%s' % Patient.unique_id_column, 'in',
                        self._patient_codes)]
        appointment_domain = [('state', 'in', ['confirmed', 'done'])]
        appointments = Appointment.search_master(
            base_domain + appointment_domain, 0, RELATED_LIMIT,
            [('appointment_date', 'DESC')],
            fields_names=['id', 'appointment_date',
                          Appointment.unique_id_column])
        appointment_codes = [x[Appointment.unique_id_column]
                             for x in appointments]
        if appointment_codes:
            Appointment.pull_master_record(appointment_codes)

        encounter_domain = [('state', '=', 'signed')]
        encounters = Encounter.search_master(
            base_domain + encounter_domain, 0, RELATED_LIMIT,
            [('start_time', 'DESC')],
            fields_names=['id', Encounter.unique_id_column,
                          'start_time', 'state'])
        encounter_codes = [x[Encounter.unique_id_column] for x in encounters]
        if encounter_codes:
            Encounter.pull_master_record(encounter_codes)

        # and then fetch the One2Many fields on encounter
        # I.E. secondary_conditions, signs_symptoms, ddx

        # 1. Get the list of enabled encounter components
        # 2. run through the components using the encounter IDs
        encounter_related_models = []

        return 'done'

    def transition_finish(self):
        return 'end'
