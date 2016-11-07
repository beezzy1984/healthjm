=====================================

Health Encounter Scenario

=====================================


=====================================

General Setup

=====================================


Imports::

    >>> import coverage

    >>> from random import randrange

    >>> from datetime import datetime, timedelta

    >>> from dateutil.relativedelta import relativedelta

    >>> from decimal import Decimal

    >>> from proteus import config, Model, Wizard

    >>> from trytond.modules.health_disease_notification.tests.database_config import set_up_datebase

    >>> from trytond.modules.health_jamaica.tryton_utils import random_bool, random_id, code_gen

    >>> from trytond.modules.health_encounter.components.mental_status import LOC, MOODS



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

    >>> address.simple_address == None
    False

    >>> COV.stop()

    >>> COV.save()

    >>> report = COV.html_report()

