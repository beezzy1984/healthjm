=====================================

General Setup

=====================================


Imports::

    >>> import coverage

    >>> from datetime import datetime

    >>> from proteus import config, Model

    >>> from trytond.modules.health_disease_notification.tests.database_config import set_up_datebase

    >>> from trytond.modules.health_jamaica.tryton_utils import random_id

    >>> from trytond.modules.health_jamaica.party import SEX_OPTIONS



Create database::



    >>> COV = coverage.Coverage()

    >>> COV.start()

    >>> CONFIG = set_up_datebase()

    >>> CONFIG.pool.test = True



Get Patient::



    >>> Patient = Model.get('gnuhealth.patient')

    >>> patient, = Patient.find([('id', '=', 1)])

    >>> Newborn = Model.get('gnuhealth.newborn')

    >>> newborn, = Newborn.find([('id', '=', '1')])


Test Party::



    >>> newborn == None
    False

    >>> newborn.mother_upi == None
    False

    >>> COV.stop()

    >>> COV.save()

    >>> report = COV.html_report()

