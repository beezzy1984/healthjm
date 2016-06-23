'''doc'''
from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateView, StateTransition, Button
from trytond.pool import Pool

__all__ = ['BedManager', 'BedManagerView', 'BedCreator', 'BedCreatorView']


class BedManagerView(ModelView):
    'Manage Hospital Beds'
    __name__ = 'health_jamaica_hospital.manage_beds.start'

    bed = fields.Many2One('gnuhealth.hospital.bed', 'Hospital Bed', required=True)
    source_location = fields.Many2One('gnuhealth.hospital.ward', 'Move From', required=True)
    target_location = fields.Many2One('gnuhealth.hospital.ward', 'Move To', required=True)

    @fields.depends('bed')
    def on_change_with_source_location(self):
        """return a new value for source location"""
        return int(self.bed.ward)


class BedManager(Wizard):
    'Manage Hospital Beds'
    __name__ = 'health_jamaica_hospital.manage_beds'

    start = StateView('health_jamaica_hospital.manage_beds.start',
                      'health_jamaica_hospital.bed_management_view', [
                          Button('Cancel', 'end', 'tryton-cancel'), 
                          Button('Ok', 'mover', default=True)])

    mover = StateTransition()

    def transition_mover(self):
        """determines the state to transition to when a selection is made"""

        if 'free' in self.start.bed.state:
            self.start.bed.ward = self.start.target_location
            self.start.bed.save()

            return 'end'


class BedCreatorView(ModelView):
    'Create Multiple Hospital Beds'
    __name__ = 'health_jamaica_hospital.create_beds.start'

    source_location = fields.Many2One('gnuhealth.hospital.ward', 'Ward', required=True)
    number_of_beds = fields.Integer('Amout of beds', required=True)
    bed_transferable = fields.Boolean('Bed is movable')
    bed_type = fields.Selection([('Gatch Bed', 'Gatch Bed'), ('Electric', 'Electric'), 
                                 ('Stretcher', 'Stretcher'), ('Low Bed', 'Low Bed'), 
                                 ('Low Air Loss', 'Low Air Loss'), 
                                 ('Circo Electric', 'Circo Electric'), ('Clinitron', 'Clinitron')], 
                                'Bed Type', required=True)

    telephone = fields.Char('Telephone Number')

class BedCreator(Wizard):

    'Create Multiple Hospital Beds'
    __name__ = 'health_jamaica_hospital.create_beds'

    start = StateView('health_jamaica_hospital.create_beds.start',
                      'health_jamaica_hospital.create_bed_view', [
                          Button('Cancel', 'end', 'tryton-cancel'),
                          Button('Ok', 'mover', default=True)])

    mover = StateTransition()

    def transition_mover(self):
        """determines the state to transition to when a selection is made"""
        start = self.start
        self.BedModel = Pool().get('gnuhealth.hospital.bed')
        num_bed = int(start.number_of_beds)
        bed_total = len(self.BedModel.search([('ward', '=', 
                                               int(self.start.source_location
                                                   ))])) +  num_bed

        if bed_total <= int(start.source_location.number_of_beds):

            self.beds = []
            for i in range(int(start.number_of_beds)):
                bed = {}
                bed['ward'] = int(start.source_location)
                bed['bed_type'] = start.bed_type
                bed['institution'] = int(self.start.source_location.institution)
                bed['state'] = 'Free'
                bed['telephone_number'] = self.start.telephone
                bed['rec_name'] = "%s-unit%s-bed-%s" %(str(start.source_location.name),
                                                   str(start.source_location.unit.name),
                                                   str(i))

                bed['movable'] = bool(start.bed_transferable)
                self.beds.append(bed)

            self.BedModel.create(self.beds)

        return 'end'
