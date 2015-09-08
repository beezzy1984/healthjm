
*health_jamaica_sync_satellite* Module
=========================================

:Organization: Ministry of Health - Jamaica
:Authors: Marc Murray <murraym@moh.gov.jm>
:Copyright: 2014-2016 Ministry of Health (Jamaica)

This module adds some menu options and modifies some wizards for users connected
to instances that are not a synchronisation master.

This module should not be installed in a Tryton instance that does not have
a synchronisation section in the configuration file. 

The synchronisation secrion should have at least the following values:

    * id = A numeric value between 2 and 510
    * uri = A url to the Tryton instance that is the sync-master for this one.
      
The uri is written in the format @https://username:password@host:port/dbname@
So, if your synchro username and password are cowpasture and mmmoo

To connect the demo instance as a master you would enter the uri as :

https://cowpasture:mmmoo@nhin.moh.gov.jm:8015/epas12_hospital
