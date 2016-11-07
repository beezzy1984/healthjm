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



    >>> HealthProfessional = Model.get('gnuhealth.healthprofessional')

    >>> healthprof, = HealthProfessional.find([('id', '=', 1)])





Test Party::



    >>> healthprof == None
    False

    >>> healthprof.main_specialty == None
    False

    >>> COV.stop()

    >>> COV.save()

    >>> report = COV.html_report()

