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



Create database::



    >>> COV = coverage.Coverage()

    >>> COV.start()

    >>> CONFIG = set_up_datebase()

    >>> CONFIG.pool.test = True



Get Party::



    >>> Party = Model.get('party.party')

    >>> party, = Party.find([('id', '=', '1')])





Test Party::



    >>> party == None
    False

    >>> party.current_age == None
    False

    >>> COV.stop()

    >>> COV.save()

    >>> report = COV.html_report()

