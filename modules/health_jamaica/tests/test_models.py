"""Automated tests"""
#!/usr/bin/env python

import os
import sys
import doctest
import unittest
import coverage
import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_view, test_depends 
                                       # doctest_setup, doctest_teardown)

DIR = os.path.abspath(os.path.normpath(os.path.join(__file__,
                                                    '..', '..', 
                                                    '..', '..', 
                                                    '..', 'trytond')))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))



class TriageQueueViewTestCase(unittest.TestCase):
    '''
    Test Health_Triage_Queue module.
    '''

    def setUp(self):
        trytond.tests.test_tryton.install_module('health_jamaica')

    def test0001views(self):
        '''
        Test views.
        '''
        test_view('health_jamaica')

    def test0002depends(self):
        '''
        Test depends.
        '''
        test_depends()

def suite():
    """Test suites"""

    cov = coverage.Coverage()
    cov.start()

    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        TriageQueueViewTestCase))
    suite.addTests(doctest.DocFileSuite('test_appointment.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_appointment_is_today.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_appointment_tree_color.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_appointment_upi.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_appointment_medical_record_num.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_appointment_sex_display.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_appointment_can_do_details.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_appointment_state_change.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_appointment_state_change_change_date.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_appointment_state_change_creator.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_address.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_address_simple_address.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_party.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_party_sex_display.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_party_alt_ids.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_party_medical_record_num.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_party_marital_status_display.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_party_birthplace.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_party_current_age.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_patient.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_patient_sex_display.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_patient_firstname.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_patient_middlename.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_patient_mother_maiden_name.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_patient_father_name.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_patient_alt_ids.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_patient_medical_record_num.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_patient_du.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_patient_unidentified.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_patient_full_name.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_patient_summary_info.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_health_professional_main_specialty.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    suite.addTests(doctest.DocFileSuite('test_pathology_track_first.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    # suite.addTests(doctest.DocFileSuite('test_person_alternative_identification.rst',
    #                                     setUp=None, 
    #                                     tearDown=None, 
    #                                     encoding='utf-8', 
    #                                     optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
    #                                     checker=None))
    # suite.addTests(doctest.DocFileSuite('test_du.rst',
    #                                     setUp=None, 
    #                                     tearDown=None, 
    #                                     encoding='utf-8', 
    #                                     optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
    #                                     checker=None))

    cov.stop()
    cov.save()
    cov.html_report()

    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
