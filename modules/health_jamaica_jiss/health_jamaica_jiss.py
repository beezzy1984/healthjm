# -*- coding: utf-8 -*-
##############################################################################
#
#    GNU Health: The Free Health and Hospital Information System
#    Copyright (C) 2008-2014  Luis Falcon <falcon@gnu.org>
#    Copyright (C) 2011-2014  GNU Solidario <health@gnusolidario.org>
#
#    MODULE : JAMAICA INJURY SURVEILLANCE SYSTEM
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
#
# The documentation of the module goes in the "doc" directory.

from trytond.pyson import Eval, Not, Equal
from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
from trytond.pool import Pool
from datetime import datetime
from ..health_jamaica.party import ThisInstitution


__all__ = ['GnuHealthSequences', 'Jiss']


class GnuHealthSequences(ModelSingleton, ModelSQL, ModelView):
    'Standard Sequences for GNU Health'
    __name__ = 'gnuhealth.sequences'

    jiss_sequence = fields.Property(fields.Many2One(
        'ir.sequence', 'JISS Sequence', required=True,
        domain=[('code', '=', 'gnuhealth.jiss')]))


class Jiss (ModelSQL, ModelView):
    'Jamaica Injury Surveillance System Registration'
    __name__ = 'gnuhealth.jiss'

    name = fields.Many2One(
        'gnuhealth.patient.evaluation', 'Evaluation',
        help='Related Patient Evaluation')
    encounter = fields.Many2One(
        'gnuhealth.encounter', 'Encounter',
        help='Related Clinical Encounter', select=True, required=True)

    injury_date = fields.Date('Injury Date',
                              help="Usually same as or before the Encounter")

    registration_date = fields.Date('Registration Date')

    code = fields.Char('Code', help='Injury Code', readonly=True)

    location = fields.Many2One(
        'country.subdivision', 'Location',
        domain=[('country', '=', 'Jamaica')])

    latitude = fields.Numeric('Latitude', digits=(3, 14))
    longitude = fields.Numeric('Longitude', digits=(4, 14))

    urladdr = fields.Char(
        'OSM Map',
        help="Maps the Accident / Injury location on Open Street Map")

    healthcenter = fields.Many2One('gnuhealth.institution', 'Institution')

    patient = fields.Function(
        fields.Char('Patient'),
        'get_patient', searcher='search_patient')

    patient_sex = fields.Function(
        fields.Char('Sex'),
        'get_patient_sex')

    patient_age = fields.Function(
        fields.Char('Age'),
        'get_patient_age')

    complaint = fields.Function(
        fields.Char('Chief Complaint'),
        'get_patient_complaint')

    injury_type = fields.Selection([
        (None, ''),
        ('accidental', 'Accidental / Unintentional'),
        ('violence', 'Violence'),
        ('attempt_suicide', 'Suicide Attempt'),
        ('motor_vehicle', 'Motor Vehicle')],
        'Injury Type', required=True, sort=False)

    mva_mode = fields.Selection([
        (None, ''),
        ('pedestrian', 'Pedestrian'),
        ('bicycle', 'Bicycle'),
        ('motorbike', 'Motorbike'),
        ('car', 'Car'),
        ('van', 'Van / Pickup / Jeep'),
        ('truck', 'Truck / Heavy vehicle'),
        ('bus', 'Bus'),
        ('train', 'Train'),
        ('taxi', 'Taxi'),
        ('boat', 'Boat / Ship'),
        ('aircraft', 'Aircraft'),
        ('other', 'Other'),
        ('unknown', 'Unknown')],
        'Mode', help="Motor Vehicle Accident Mode", sort=False,
        states={'required': Equal(Eval('injury_type'), 'motor_vehicle')})

    mva_position = fields.Selection([
        (None, ''),
        ('driver', 'Driver'),
        ('passenger', 'Passenger'),
        ('outside', 'Outside / on the back'),
        ('bystander', 'Bystander'),
        ('unspecified_vehicle', 'Unspecified vehicle'),
        ('unknown', 'Unknown')],
        'User Position', help="Motor Vehicle Accident user position",
        sort=False, states={
            'required': Equal(Eval('injury_type'), 'motor_vehicle')})

    mva_counterpart = fields.Selection([
        (None, ''),
        ('pedestrian', 'Pedestrian'),
        ('bicycle', 'Bicycle'),
        ('motorbike', 'Motorbike'),
        ('car', 'Car'),
        ('van', 'Van / Pickup / SUV'),
        ('truck', 'Truck / Heavy vehicle'),
        ('bus', 'Bus'),
        ('train', 'Train'),
        ('taxi', 'Taxi'),
        ('boat', 'Boat / Ship'),
        ('aircraft', 'Aircraft'),
        ('other', 'Other'),
        ('unknown', 'Unknown'),
        ], 'Counterpart', help="Motor Vehicle Accident Counterpart",sort=False,
            states={'required': Equal(Eval('injury_type'), 'motor_vehicle')})

    safety_gear = fields.Selection([
        (None, ''),
        ('yes', 'Yes'),
        ('no', 'No'),
        ('unknown', 'Unknown'),
        ], 'Safety Gear', help="Use of Safety Gear - Helmet, safety belt...",sort=False,
           states={'required': Equal(Eval('injury_type'), 'motor_vehicle')})

    alcohol = fields.Selection([
        (None, ''),
        ('yes', 'Yes'),
        ('no', 'No'),
        ('suspected','Suspected'),
        ('unknown', 'Unknown'),
        ], 'Alcohol', required=True,
            help="Is there evidence of alcohol use by the injured person"
                " in the 6 hours before the accident ?",sort=False)

    drugs = fields.Selection([
        (None, ''),
        ('yes', 'Yes'),
        ('no', 'No'),
        ('suspected','Suspected'),
        ('unknown', 'Unknown'),
        ], 'Other Drugs', required=True,
            help="Is there evidence of drug use by the injured person"
                " in the 6 hours before the accident ?",sort=False)

    injury_details = fields.Text('Details')

    # Add victim-perpretator relationship for violence-related injuries
    victim_perpetrator = fields.Selection([
        (None, ''),
        ('parent', 'Parent'),
        ('spouse', 'Wife / Husband'),
        ('girlboyfriend', 'Girl / Boyfriend'),
        ('relative', 'Other relative'),
        ('aquaintance', 'Aquaitance / Friend'),
        ('official', 'Official / Legal'),
        ('stranger', 'Stranger'),
        ('other', 'other'),
        ], 'Relationship', help="Victim - Perpetrator relationship",sort=False,
            states={'required': Equal(Eval('injury_type'), 'violence')})


    violence_circumstances = fields.Selection([
        (None, ''),
        ('fight', 'Fight'),
        ('robbery', 'Robbery'),
        ('drug', 'Drug Related'),
        ('sexual', 'Sexual Assault'),
        ('gang', 'Gang Activity'),
        ('other_crime', 'Committing a crime (other)'),
        ('other', 'Other'),
        ('unknown', 'Unknown'),
        ], 'Context', help="Precipitating Factor",sort=False,
            states={'required': Equal(Eval('injury_type'), 'violence')})

    injury_method = fields.Selection([
        (None, ''),
        ('blunt', 'Blunt object'),
        ('push', 'Push/bodily force'),
        ('sharp', 'Sharp objects'),
        ('gun', 'Gun shot'),
        ('sexual', 'Sexual Assault'),
        ('choking', 'Choking/strangulation'),
        ('other', 'Other'),
        ('unknown', 'Unknown'),
        ], 'Method', help="Method of Injury",sort=False,
            states={'required': Equal(Eval('injury_type'), 'violence')})


    # Place of occurrance . Not used in motor vehicle accidents

    place_occurrance = fields.Selection([
        (None, ''),
        ('home', 'Home'),
        ('street', 'Street'),
        ('institution', 'Institution'),
        ('school', 'School'),
        ('commerce', 'Commercial Area'),
        ('publicbuilding', 'Public Building'),
        ('recreational', 'Recreational Area'),
        ('transportation', 'Public transportation'),
        ('sports', 'Sports event'),
        ('unknown', 'Unknown'),
        ], 'Place', help="Place of occurrance",sort=False,
            states={'required': Not(Equal(Eval('injury_type'), 'motor_vehicle'))})

    disposition = fields.Selection(
        [(None, ''),
         ('treated_sent', 'Treated and Sent Home'),
         ('admitted', 'Admitted to Ward'),
         ('observation', 'Admitted to Observation'),
         ('died', 'Died'),
         ('daa', 'Discharged Against Advice'),
         ('transferred', 'Transferred'),
         ('referred', 'Referred'),
         ('doa', 'Dead on Arrival')],
        'Disposition', help="Place of occurrance", sort=False, required=True)

    def get_patient(self, name):
        return self.encounter.patient.name.name

    def get_patient_sex(self, name):
        return self.encounter.patient.sex_display

    def get_patient_age(self, name):
        return self.encounter.patient.age

    def get_patient_complaint(self, name):
        return self.encounter.primary_complaint

    @classmethod
    def default_patient(cls):
        # print("{}\nContext = {}\n{}".format('%'*80,repr(Transaction().context),
        #                                      '%'*80))
        return '(Save to see patient information)'

    def on_change_name(self):
        k = {
            'patient': self.encounter.patient.name.name,
            'patient_age': self.encounter.patient.age,
            'patient_sex': self.encounter.patient.sex_display}
        # print "{}\non_change_name has been called with \n{}\n{}",format(
        #             '*'*80, repr(k), '*'*80
        #     )
        return k

    @fields.depends('latitude', 'longitude')
    def on_change_with_urladdr(self):
        # Generates the URL to be used in OpenStreetMap
        # The address will be mapped to the URL in the following way
        # If the latitude and longitude of the Accident / Injury
        # are given, then those parameters will be used.

        ret_url = ''
        if (self.latitude and self.longitude):
            ret_url = 'http://openstreetmap.org/?mlat=' + \
                str(self.latitude) + '&mlon=' + str(self.longitude)

        return ret_url

    @classmethod
    def search_patient(cls, name, clause):
        res = []
        value = clause[2]
        res.append(('encounter.patient', clause[1], value))
        return res

    @classmethod
    def generate_injury_code(cls):
        icode = ['ISS']
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('gnuhealth.sequences')
        config = Config(1)
        newcode = Sequence.get_id(config.jiss_sequence.id)
        icode.append(newcode)
        here = ThisInstitution()
        if here:
            here = pool.get('gnuhealth.institution')(here)
            icode.append(here.code)
        return '-'.join(icode)

    @classmethod
    def create(cls, vlist):
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if not 'code' in values:
                values['code'] = cls.generate_injury_code()
        return super(Jiss, cls).create(vlist)

    @classmethod
    def default_healthcenter(cls):
        h = ThisInstitution()
        if h:
            return h
        else:
            return None

    @classmethod
    def default_registration_date(cls):
        return datetime.now().date()
