=====================================

Health Encounter Scenario

=====================================


=====================================

General Setup

=====================================


Imports::

    >>> import coverage

    >>> from datetime import datetime, timedelta

    >>> from proteus import config, Model

    >>> from trytond.modules.health_disease_notification.tests.database_config import set_up_datebase

    >>> from trytond.modules.health_jamaica.tryton_utils import random_id, code_gen



Create database::



    >>> COV = coverage.Coverage()

    >>> COV.start()

    >>> CONFIG = set_up_datebase()

    >>> CONFIG.pool.test = True



Get Alternative Id::



    >>> AltId = Model.get('gnuhealth.person_alternative_identification')

    >>> Institution = Model.get('gnuhealth.institution')

    >>> institution, = Institution.find([('id', '=', random_id(30))])

    >>> # Party = Model.get('party.party')

    >>> # party = Party.find([('id', '=', '1')])

    >>> alt_id = AltId()

    >>> alt_id.issuing_institution = institution

    >>> alt_id.code = code_gen()

    >>> alt_id.issue_date = datetime.now() + timedelta(days=-random_id(20))

    >>> alt_id.expiry_date = alt_id.issue_date + timedelta(weeks=216)

    >>> alt_id.type_display = 'medical_record'

    >>> alt_id.save()



Test Party::



    >>> alt_id == None
    False

    >>> alt_id.type_display == None
    False

    >>> COV.stop()

    >>> COV.save()

    >>> report = COV.html_report()

