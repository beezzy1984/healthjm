
*health_jamaica_sync_satellite* Module
=========================================

:Organization: Ministry of Health - Jamaica
:Authors: Marc Murray <murraym@moh.gov.jm>
:Copyright: 2014-2016 Ministry of Health (Jamaica)

This module adds some menu options and modifies some wizards for users connected
to instances that are not a synchronisation master.

This module should not be installed in a Tryton instance that does not have
a synchronisation section in the configuration file. 

The synchronisation section should have at least the following values:

    * id = A numeric value between 2 and 510
    * uri = A url to the Tryton instance that is the sync-master for this one.
    * cache_server = host:port to a memcached server. default: 127.0.0.1:11211
      
The uri is written in the format @https://username:password@host:port/dbname@

So, if your synchro username is cow and your and password is  super_mmmooo
To connect to the big_pasture database on bovine.net on port 8000, use the uri:

    https://cow:super_mmmooo@bovine.net:8000/big_pasture


RemoteParty Model
----------------------

This module introduces the RemoteParty model which represents patients
found in the master mentioned above that are marked as not synchronised
with the local database. It may be the case that the record is already
in the local database and the master has not yet been notified. In this
case, any import routines requested will merely update the local record
if needed. 

By default, the remote party screen is blank. This is because the master
quite likely has considerable more records than you are interested in.
To see some records, you must enter a search term - directly into the search
box or using the *Filters* dropdown.
