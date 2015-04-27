#!/usr/bin/env python

# reset_sync.py - Marc D. Murray <murraym@moh.gov.jm>, Feb 9, 2015
# Updates the database directly to change the synchronised_instances field for
# all the tables that correspond to models set to synchronise according to 
# the health_jamaica_sync module. 
# This file should be run using the python in the virtualenv that hosts tryton
#-------------------------------------------
# Change these variables before running:
#--------------------------------------

new_sync_id = 311    # and this is the new syncid

connection_string = " ".join(("dbname=nho_stannsbay",
                             "user=nerha_sab",
                             "password=nerhasabpwd",
                             "port=5432", "host=localhost"))
# db connection string broken down for easier editing

#==============================================================================

import psycopg2
from trytond.modules.health_jamaica_sync import health

def change_syncid(constr, newid):
    sqltmpl = " ".join(("update {} set synchronised_instances =",
            "set_bit(B'0'::bit(512), %(syncrev)s, 1),",
            "last_synchronisation = null"))

    queries = []
    parms = {'syncrev':511 - newid}

    for nom in health.__all__:
        model = getattr(health, nom)
        table = model.__name__.replace('.','_')
        # ToDo: Remove this check when disease_group_members added to sync
        if table == 'gnuhealth_disease_group_members':
            continue
        queries.append((table, sqltmpl.format(table)))


    with psycopg2.connect(constr) as conn:
        with conn.cursor() as cursor:
            for table_nom, query in queries:
                print("updating {}".format(table_nom))
                cursor.execute(query, parms)



if __name__ == "__main__":
    change_syncid(connection_string, new_sync_id)



