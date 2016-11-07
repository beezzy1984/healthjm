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

    >>> newborn_list = Newborn.find([('id', '!=', None)])

    >>> newborn = Newborn()



Create Newborn::


    >>> patient_list = []
    >>> for baby in newborn_list:
    ...     patient_list.append(baby.patient)

    >>> if patient not in patient_list:
    ...     newborn.patient = patient
    ...     newborn.birth_date = datetime.now()
    ...     newborn.sex = SEX_OPTIONS[random_id(len(SEX_OPTIONS)) - 1][0]
    ...     newborn.save()



Test Party::



    >>> newborn == None
    False

    >>> COV.stop()

    >>> COV.save()

    >>> report = COV.html_report()

