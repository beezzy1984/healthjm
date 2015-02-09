#!/usr/bin/env python

# change_global_syncid.py - Marc D. Murray <murraym@moh.gov.jm>, Feb 9, 2015
# Updates the database directly to change the synchronised_instances field for
# all the tables that correspond to models set to synchronise according to 
# the health_jamaica_sync module. 
# This file should be run using the python in the virtualenv that hosts tryton
#-------------------------------------------
# Change these variables before running:
#--------------------------------------
old_sync_id = 35    # this is the syncid we want to change
new_sync_id = 32    # and this is the new syncid

connection_string = " ".join(("dbname=shc_christiana",
                             "user=srha",
                             "password=srhapwd",
                             "port=5432", "host=localhost"))
# db connection string broken down for easier editing

#==============================================================================

import psycopg2
from trytond.modules.health_jamaica_sync import health

def change_syncid(constr, oldid, newid):
    sqltmpl = " ".join(("update {} set synchronised_instances =",
            "set_bit(set_bit(synchronised_instances, %(syncbad)s, 0),"
                      "%(syncrev)s, 1)",
            "where get_bit(synchronised_instances, %(syncrev)s)=0"
            "and get_bit(synchronised_instances, %(syncbad)s)=1;"))

    queries = []
    parms = {'syncbad':511 - oldid, 'syncrev':511 - newid}

    for nom in health.__all__:
        model = getattr(health, nom)
        table = model.__name__.replace('.','_')
        # ToDo: Remove this check when disease_group_members added to sync
        if table == 'gnuhealth_disease_group_members':
            continue
        queries.append((table, sqltmpl.format(table)))


    with psycopg2.connect(constr) as conn:
        with conn.cursor() as cr:
            for tn, qr in queries:
                print("updating {}".format(tn)); cr.execute(qr, parms)



if __name__ == "__main__":
    change_syncid(connection_string, old_sync_id, new_sync_id)



