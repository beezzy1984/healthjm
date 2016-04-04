
from trytond.wizard import StateAction
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.pyson import PYSONEncoder
from trytond.modules.health_encounter.wizard import OneEncounterWizard


class JissFromEncounter(OneEncounterWizard):
    'JISS Registration from Encounter'
    __name__ = 'gnuhealth.jiss.encounter_wizard'

    start_state = 'goto_jiss'
    goto_jiss = StateAction('health_jamaica_jiss.actwin_jiss_formfirst')

    def do_goto_jiss(self, action):

        enctr_id, _ = self._get_active_encounter()

        # Does the jiss entry already exist?
        jiss_entry = Pool().get('gnuhealth.jiss').search([
            ('encounter', '=', enctr_id)])
        if jiss_entry:
            rd = {'active_id': jiss_entry[0].id}
            action['res_id'] = rd['active_id']
        else:
            rd = {}
            action['pyson_domain'] = PYSONEncoder().encode([
                ('encounter', '=', enctr_id)
            ])
            action['pyson_context'] = PYSONEncoder().encode({
                'encounter': enctr_id
            })

        return action, rd
