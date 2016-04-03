# from trytond.model import ModelView, fields
from trytond.wizard import (Wizard, StateAction)
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.pyson import PYSONEncoder


class OneEncounterWizard(Wizard):

    def __init__(self, sessionid):
        super(OneEncounterWizard, self).__init__(sessionid)
        tact = Transaction()
        active_id = tact.context.get('active_id')
        try:
            encounter = Pool().get(
                'gnuhealth.encounter').browse([active_id])[0]
        except:
            self.raise_user_error('no_record_selected')
        self._enctr_data = {'active_id': active_id, 'obj': encounter}

    @classmethod
    def __setup__(cls):
        super(OneEncounterWizard, cls).__setup__()
        cls._error_messages.update({
            'no_record_selected': 'You need to select an Encounter',
        })


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

        print('Launching JISS registration with action, rd = \n%s\n%s\n%s' % (
              repr(action), repr(rd), '*'*77
              ))

        return action, rd
