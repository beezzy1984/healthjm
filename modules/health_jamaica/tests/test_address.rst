=====================================

Health Encounter Scenario

=====================================


=====================================

General Setup

=====================================


Imports::

    >>> import coverage

    >>> from datetime import datetime, timedelta

    >>> from proteus import config, Model, Wizard

    >>> from random import randrange

    >>> from trytond.modules.health_disease_notification.tests.database_config import set_up_datebase

    >>> from trytond.modules.health_jamaica.tryton_utils import random_id, code_gen



Create database::



    >>> COV = coverage.Coverage()

    >>> COV.start()

    >>> CONFIG = set_up_datebase()

    >>> CONFIG.pool.test = True



Install health_disease_notification, health_disease_notification_history::



    >>> Module = Model.get('ir.module.module')

    >>> modules = Module.find([('name', 'in', 
    ... ['health_encounter', 'health_jamaica']), ])

    >>> Module.install([x.id for x in modules], CONFIG.context)

    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')



Get Patient::



    >>> Patient = Model.get('gnuhealth.patient')

    >>> HealthProfessional = Model.get('gnuhealth.healthprofessional')

    >>> Party = Model.get('party.address')

    >>> PartyAddress = Model.get('party.address')

    >>> Notification = Model.get('gnuhealth.disease_notification')

    >>> Institution = Model.get('gnuhealth.institution')

    >>> institution, = Institution.find([('id', '=', random_id(randrange(25, 89)))])

    >>> patient, = Patient.find([('id', '=', '1')])

    >>> healthprof, = HealthProfessional.find([('id', '=', '1')])



Create Address::



    >>> address = PartyAddress()

    >>> address.streetbis = code_gen()

    >>> address.desc = code_gen()

    >>> address.party = patient.name

    >>> address.save()




Scenario Test::



    >>> address == None
    False

    >>> patient.name.du == address
    True

    >>> COV.stop()

    >>> COV.save()

    >>> report = COV.html_report()

