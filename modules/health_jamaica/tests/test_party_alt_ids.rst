=====================================

Health Encounter Scenario

=====================================


=====================================

General Setup

=====================================


Imports::

    >>> import coverage

    >>> from proteus import config, Model

    >>> from trytond.modules.health_disease_notification.tests.database_config import set_up_datebase

    >>> from trytond.modules.health_jamaica.tryton_utils import random_id



Create database::



    >>> COV = coverage.Coverage()

    >>> COV.start()

    >>> CONFIG = set_up_datebase()

    >>> CONFIG.pool.test = True



Get Party::



    >>> Party = Model.get('party.party')

    >>> party, = Party.find([('id', '=', random_id(10))])





Test Party::



    >>> party == None
    False

    >>> party.alt_ids == None
    False

    >>> COV.stop()

    >>> COV.save()

    >>> report = COV.html_report()

