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

def get_domunits():
    """This function gets all dom units available in the database"""
    domunit = Model.get('gnuhealth.du')
    #print dir(domunit)
    dom = domunit.find([('active', '=', 'True')])
    return dom

def change_dom_to_party_address():
    """
       Changing dom units to party address on the party the dom unit
       belongs to
    """
    domunits = get_domunits()
    if domunits:
        failed = 0
        suceeded = 0
        party = Model.get('party.party')
        country_model = Model.get('country.country')
        dist = Model.get('country.district_community')
        sub = Model.get('country.subdivision')
        post = Model.get('country.subdivision')
        for domunit in domunits:
            address_model = Model.get('party.address')
            addr = Model.get('party.address')
            address = address_model()
            (party_du, ) = party.find([('du', '=', domunit.id)])
            (country, ) = country_model.find([('id', '=', domunit.address_country.id)])
            (district, ) = dist.find([('id', '=', domunit.address_district_community.id)])
            (subdivision, ) = sub.find([('id', '=', domunit.address_subdivision.id)])
            (post_off, ) = post.find([('id', '=', domunit.address_post_office.id)])
            if party_du:
                address.party = party_du
                address.active = True
                address.address_street_num = domunit.address_street_num
                address.district_community = district
                address.desc = domunit.desc
                address.country = country
                address.post_office = post_off
                address.street = domunit.address_street
                address.streetbis = domunit.address_street_bis
                address.subdivision = subdivision
                domunit.active = False
                addr_old = addr.find([('party', '=', party_du.id)])
                if addr_old:
                    old_addr = addr_old[0]
                    old_addr.active = False
                    old_addr.save()
                address.save()
                domunit.save()
                party_du.du = None
                party_du.save()
                suceeded += 1
            else:
                failed += 1

        amount = failed + suceeded
        print "From {}, {} failed and {} suceeded".format(amount, failed, suceeded)

if __name__ == '__main__':
    change_dom_to_party_address()
