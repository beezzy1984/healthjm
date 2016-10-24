"""Driver for testing modules"""
import logging
import argparse
import os
import time
import unittest
import sys

from trytond.config import config

MAIN_CONFIG_FILE = os.path.abspath(os.path.normpath(os.path.join(__file__, 
                                                                 '..', 
                                                                 'test_trytond.conf')))

TEST_MODULES = ['country', 'currency', 'product', 'party', 'company', 
                'account', 'stock', 'account_product', 'account_invoice', 
                'stock_lot', 'calendar', 'health', 'health_archives', 
                'health_calendar', 'health_crypto', 'health_genetics', 
                'health_gyneco', 'health_socioeconomics', 'health_surgery', 
                'health_lifestyle', 'health_history', 'health_icd10', 
                'health_icd10pcs', 'health_icpm', 'health_inpatient', 
                'health_nursing', 'health_icu', 'health_imaging', 
                'health_inpatient_calendar', 'health_iss', 'health_lab', 
                'health_mdg6', 'health_ntd', 'health_ntd_chagas', 
                'health_ntd_dengue', 'health_pediatrics', 
                'health_pediatrics_growth_charts', 'health_pediatrics_growth_charts_who', 
                'health_profile', 'health_qrcodes', 'health_reporting', 
                'health_services', 'health_stock', 'health_who_essential_medicines', 
                'health_encounter', 'country_jamaica', 'health_jamaica', 
                'health_triage_queue', 'health_jamaica_analytics', 
                'health_jamaica_analytics_sync', 'health_jamaica_history', 
                'health_jamaica_primarycare', 'health_jamaica_hospital', 
                'health_jamaica_jiss', 'health_jamaica_obgyn', 
                'health_jamaica_pediatrics', 'health_jamaica_socioeconomics', 
                'health_jamaica_sync', 'health_jamaica_icd_icpm', 
                'health_disease_notification', 'health_disease_notification_history', 
                'health_jamaica_sync_satellite', 'jmmoh_base', 'jmmoh_health_centre_profile', 
                'jmmoh_institutions', 'jmmoh_hospital_profile', 'test_synchronisation']

if __name__ != '__main__':
    raise ImportError('%s can not be imported' % __name__)

def tester():
    """Tester function for modules"""
    logging.basicConfig(level=logging.ERROR)
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", dest="config",
                        help="specify config file")
    parser.add_argument("-m", "--modules", action="store_true", dest="modules",
                        default=False, help="Run also modules tests")
    parser.add_argument("-v", action="count", default=0, dest="verbosity",
                        help="Increase verbosity")
    parser.add_argument('tests', metavar='test', nargs='*')
    opt = parser.parse_args()

    config.set('database', 'db_type', 'sqlite')

    if not opt.config:
        config.update_etc(MAIN_CONFIG_FILE)
    else:
        config.update_etc(opt.config)

    if not config.get('session', 'super_pwd'):
        config.set('session', 'super_pwd', '123')

    database_name = 'shc_maypen'

    os.environ['DB_NAME'] = database_name

    from trytond.tests.test_tryton import all_suite, modules_suite

    from trytond.tests.test_tryton import drop_create

    # drop_create()

    if not opt.modules:
        suite = modules_suite(TEST_MODULES)
    else:
        suite = modules_suite(opt.tests)

    result = unittest.TextTestRunner(verbosity=opt.verbosity).run(suite)
    sys.exit(not result.wasSuccessful)

if __name__ == '__main__':

    tester()
