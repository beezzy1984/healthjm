
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

    # @classmethod
    # def __setup__(cls):
    #     super(JissFromEncounter, cls).__setup__()
    #     cls._error_messages.update({
    #         'appointment_no_institution':
    #         'This appointment does not specify an institution.\n'
    #         'An Encounter cannot be created.',
    #     })

    def do_goto_jiss(self, action):

        pool = Pool()
        enctr_id = Transaction().context.get('active_id')

        try:
            encounter = pool.get(
                'gnuhealth.encounter').browse([enctr_id])[0]
        except:
            self.raise_user_error('no_record_selected')

        # Does the jiss entry already exist?
        jiss_entry = pool.get('gnuhealth.jiss').search([
            ('encounter', '=', encounter.id)])
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
