# -*- coding: utf-8 -*-
##############################################################################
#
#    Health-Jamaica: The Jamaica Electronic Patient Administration System
#    Copyright 2015  Ministry of Health (NHIN), Jamaica <admin@mohnhin.info>
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

from trytond.model import ModelView, ModelSQL, fields
from trytond.transaction import Transaction

# JAMAICA_ID=89
# JAMAICA = lambda : (Pool().get('country.country').search([
#                     ('code','=','JM')]))[0]


class PostOffice(ModelSQL, ModelView):
    'Country Post Office'
    __name__ = 'country.post_office'

    code = fields.Char('Code', required=True, size=10)
    name = fields.Char('Post Office', required=True, help="Post Offices")
    subdivision = fields.Many2One('country.subdivision', 'Parish/Province',
                                  help="Enter Parish, State or Province")
    inspectorate = fields.Char('Inspectorate',
                               help="Postal Area that governs this agency")

    @classmethod
    def __setup__(cls):
        super(PostOffice, cls).__setup__()
        cls._sql_constraints = [
            ('code_uniq', 'UNIQUE(code)',
                'The Post Office code be unique.'),
        ]

    @classmethod
    def __register__(cls, module_name):
        '''handles the rewiring of the Jamaica parishes to merge Kingston and
        Saint Andrew (JM-01 and JM-02)'''
        super(PostOffice, cls).__register__(module_name)
        cursor = Transaction().cursor
        # update subdivision table to remove st. andrew and merge with Kgn
        cursor.execute('Select name from country_subdivision where code=%s',
                       ('JM-02',))
        standrew = cursor.fetchone()
        if standrew:
            sql = ['DELETE from country_subdivision where code=%s']
            parms = [('JM-02',)]
            for query, query_param in zip(sql, parms):
                cursor.execute(query, query_param)
            cursor.commit()


class DistrictCommunity(ModelSQL, ModelView):
    'Country District Community'
    __name__ = 'country.district_community'

    code = fields.Char('Code', required=True, size=10)
    name = fields.Char('District Community', required=True,
                       help="District Communities")
    post_office = fields.Many2One('country.post_office', 'Post Office',
                                  required=True)
    parish = fields.Function(fields.Char('Parish'), 'get_parish')

    @classmethod
    def __setup__(cls):
        super(DistrictCommunity, cls).__setup__()
        cls._sql_constraints = [
            ('name_per_po_uniq', 'UNIQUE(name, post_office)',
                'The District Community must be unique for each post office.'),
            ('code_uniq', 'UNIQUE(code)',
                'The Community code be unique.'),
        ]

    def get_parish(self, name):
        try:
            return self.post_office.subdivision
        except AttributeError:
            return None
