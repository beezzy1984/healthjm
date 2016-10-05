# Stuff that translates domunits to addresses
from proteus import Model, config as pconfig

TRYTONCONF = {'pwd':'123',
              'conffile':'/home/randy/Projects/MOH/env/epas2/etc/trytond.conf',
              'dbname':'shc_maypen', 'host':'maia.local', 'port':'8000',
              'institution':'Darliston'}

def get_pconfig():
    """Returns a tryton configuration settings"""
    return pconfig.set_trytond(TRYTONCONF['dbname'],
                               user='admin',
                               config_file=TRYTONCONF['conffile'])

CONFIG = get_pconfig()

def get_parties_with_domunits():
    """This function gets all dom units available in the database"""
    party = Model.get('party.party')
    #print dir(domunit)
    party_with_du = party.find([('du', '!=', None)])
    return party_with_du

def getdu(party):
    """Returns party du if party is not None and party has du"""
    if party and hasattr(party, 'du'):
        return party.du

def change_dom_to_party_address():
    """
       Changing dom units to party address on the party the dom unit
       belongs to
    """
    parties_with_du = get_parties_with_domunits()
    if parties_with_du:
        #parties_with_du = sorted(parties_with_du, key=getdu)
        failed = 0
        suceeded = 0
        addr = Model.get('party.address')
        for party in parties_with_du:
            address = addr()
            dom_unit = party.du
            if dom_unit:
                address.party = party
                address.active = True
                address.address_street_num = dom_unit.address_street_num
                if dom_unit.address_district_community:
                    address.district_community = dom_unit.address_district_community
                if dom_unit.desc:
                    address.desc = dom_unit.desc
                if dom_unit.address_country:
                    address.country = dom_unit.address_country
                if dom_unit.address_post_office:
                    address.post_office = dom_unit.address_post_office
                if dom_unit.address_street:
                    address.street = dom_unit.address_street
                if dom_unit.address_street_bis:
                    address.streetbis = dom_unit.address_street_bis
                if dom_unit.address_subdivision:
                    address.subdivision = dom_unit.address_subdivision
                addr_old = addr.find([('party', '=', party.id)])
                if addr_old:
                    old_addr = addr_old[0]
                    old_addr.active = False
                    old_addr.save()
                address.save()
                party.du = None
                party.save()
                suceeded += 1
            else:
                failed += 1

        amount = failed + suceeded
        print "From {}, {} failed and {} suceeded".format(amount, failed, suceeded)

if __name__ == '__main__':
    change_dom_to_party_address()
