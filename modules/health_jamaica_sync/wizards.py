
from trytond.wizard import (Wizard, StateView, StateTransition, Button,
                            StateAction)
from trytond.model import ModelView, ModelStorage, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Not, Bool, PYSONEncoder
from trytond.transaction import Transaction

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
