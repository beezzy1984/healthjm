# -*- coding: utf-8 -*-
##############################################################################
#
#    GNU Health: The Free Health and Hospital Information System
#    Copyright (C) 2008-2014  GNU SOLIDARIO <health@gnusolidario.org>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
#
# Localization module for Jamaica Ministry of Health
#
# The documentation of the module goes in the "doc" directory.

import string
import random
from trytond.pyson import Eval, Not, Bool, PYSONEncoder, Equal
from trytond.model import ModelView, ModelSQL, fields

__all__ = ['PartyUPC','AlternativePersonID','DomiciliaryUnit','Newborn','PartyPatient','Insurance']


class PartyUPC (ModelSQL, ModelView):
    __name__ = 'party.party'

    ref = fields.Char(
        'UPC',
        help='Universal Patient Code',
        states={'invisible': Not(Bool(Eval('is_person')))})

    @staticmethod
    def default_ref():
        # Add a default random string in the ref field.
        # The STRSIZE constant provides the length of the HIN
        # The format of the UPC is XXXNNNXXX
        STRSIZE = 9
        hin = ''
        for x in range(STRSIZE): 
            if ( x < 3 or x > 5 ):
                hin = hin + random.choice(string.ascii_uppercase)
            else:
                hin = hin + random.choice(string.digits)
        return hin



class PartyPatient (ModelSQL, ModelView):
    'Party'
    __name__ = 'party.party'
    
    alias = fields.Char('Pet Name', help="Common name that the Patient is referred to as")
    middlename = fields.Char('Middle Name', help="Middle name of Patient")
    mother_maiden_name = fields.Char('Mother Maiden Name', help="Mother's Maiden Name")
    father_name = fields.Char('Father Name', help="Father's Name")
    
    suffix = fields.Selection([
		(None,''),
		('jr', 'JR. - Junior'),
		('sr', 'SR. - Senior'),
		('II', 'II - The Second'),
		('III', 'III - The Third'),
		], 'Suffix')
		
    marital_status = fields.Selection([
        (None, ''),
        ('s', 'Single'),
        ('m', 'Married'),
        ('c', 'Concubinage'),
        ('w', 'Widowed'),
        ('d', 'Divorced'),
        ('x', 'Separated'),
        ('v', 'Visiting'),
        ], 'Marital Status', sort=False)
        
class AlternativePersonID (ModelSQL, ModelView):
   'Alternative person ID'
   __name__ ='gnuhealth.person_alternative_identification' 
   
   name = fields.Many2One('party.party', 'Party', readonly=True)
   alternative_id_type = fields.Selection(
        [
            ('trn','TRN'),
            ('pathID','PATH ID'),
            ('gojID','GOJ ID'),
            ('medical recordsID','Medical Records ID'),
        ], 'ID type', required=True, sort=False,)
        
   issuedby = fields.Selection(
        [
            ('kph','KPH'),
            ('vjh','VJH'),
            ('crh','CRH'),            
        ], 'Issued By', required=False, sort=True,)

class DomiciliaryUnit(ModelSQL, ModelView):
    'Domiciliary Unit'
    __name__ = 'gnuhealth.du'

    address_subdivision = fields.Many2One(
        'country.subdivision', 'Parish',
        domain=[('country', '=', Eval('address_country'))],
        depends=['address_country'], help="Enter Parish or State or County or Borrow")
       
class Newborn (ModelSQL, ModelView):
    'Newborn Information'
    __name__ = 'gnuhealth.newborn'
    
    bba = fields.Boolean('BBA', help='Check this box if born on arrival to health facility')
    cephalic_perimeter = fields.Integer('Head Circumference',
        help="Perimeter in centimeters (cm)")
    length = fields.Integer('Crown-Heel Length', help="Length in centimeters (cm)")


class Insurance(ModelSQL, ModelView):
    'Insurance'
    __name__ = 'gnuhealth.insurance' #database table, tryton translates this into gnuhealth_insurance
    _rec_name = 'number'

    # Insurance associated to an individual

    name = fields.Many2One('party.party', 'Owner')
    number = fields.Char('Policy#', required=True)

    def get_rec_name(self, name):
        return (self.company.name + ' : ' + self.number)

