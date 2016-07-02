'''doc'''
from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateView, StateTransition, Button
from trytond.pool import Pool
from trytond.pyson import Eval

__all__ = ['BedManager', 'BedManagerView', 'BedCreator', 'BedCreatorView']


class BedManagerView(ModelView):
    'Manage Hospital Beds'
    __name__ = 'health_jamaica_hospital.manage_beds.start'

    bed = fields.Many2One('gnuhealth.hospital.bed', 'Hospital Bed',
                          required=True)
    source_location = fields.Many2One('gnuhealth.hospital.ward', 'Move From',
                                      required=True)
    target_location = fields.Many2One('gnuhealth.hospital.ward', 'Move To',
                                      required=True)

    @fields.depends('bed')
    def on_change_with_source_location(self):
        """return a new value for source location"""
        if self.bed == None:
            self.raise_user_error("Cannot choose ward \n"
                                  "This is because no bed has been chosen\n")

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

        if 'free' not in self.start.bed.state or not self.start.bed.movable:
            self.raise_user_error("Cannot move this bed\n")

        self.start.bed.ward = self.start.target_location
        self.start.bed.save()

        return 'end'


class BedCreatorView(ModelView):
    'Create Multiple Hospital Beds'
    __name__ = 'health_jamaica_hospital.create_beds.start'

    ward = fields.Many2One('gnuhealth.hospital.ward', 'Ward', required=True)
    number_of_beds = fields.Integer('Amount of beds', required=True)
    bed_transferable = fields.Boolean('Bed is movable')
    bed_type = fields.Selection('get_bed_types', 'Bed Type', required=True)
    telephone = fields.Char('Telephone Number')
    ward_code = fields.Char('Ward Code', states={'invisible':~Eval('ward') or 
                            Eval('ward.wardcode')})
    product_template = fields.Selection('get_template_list', 'Product Template',
                                        required=True)

    @fields.depends('ward')
    def on_change_with_ward_code(self):
        """return a new value for source location"""

        if self.ward == None:
            return " "

        return self.ward.wardcode

    @staticmethod
    def get_bed_types():
        """Returns the list of bed types from the hospital bed model"""
        hospital_bed = Pool().get('gnuhealth.hospital.bed')
        return hospital_bed.bed_type.selection  

    @fields.depends('bed_transferable')
    def on_change_with_source_location(self):
        """return a new value for source location"""
        return int(self.bed.ward)

    @staticmethod
    def get_template_list():
        """return list of product template"""
        prod_template = Pool().get('product.template')
        templates = prod_template.search_read(
            [('type', '=', 'service'), ('name', 'ilike', '%bed%')],
            fields_names=['name', 'id'])

        return [(x['id'], x['name']) for x in templates]
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
        num_bed = start.number_of_beds
        bed_total = self.BedModel.search_count([('ward', '=',
                                                start.ward)]) + num_bed
        self.bed_on_ward = self.BedModel.search_count(
                                            [('ward', '=',self.start.ward.id)])
        if start.ward and bed_total > start.ward.number_of_beds:
            beds_left = self.start.ward.number_of_beds - self.bed_on_ward
            
            self.raise_user_error("This ward's maximum capacity is %d beds\n"
                                  "There are currently %d beds on this ward\n"
                                  "You can only create %d more beds for this ward." % 
                                  (self.start.ward.number_of_beds, self.bed_on_ward,
                                   beds_left))

        def get_prod(bed_number):
            """Creates a bed product from the product template
               returned by get_prod_temp function"""
            #temp_lis = get_prod_temp()
            prod = []
            #assert(len(temp_lis) > 0)

            Product = Pool().get('product.product')
            template_dict = dict(
                template=start.product_template,
                code="%s - %d" %(self.start.ward.wardcode, bed_number),
                is_bed=True,
                active=True
            )

            prod.append(template_dict)
            return Product.create(prod)

        def create_beds(num_bed):
            """Creates beds based on the argument num_bed and on 
               the product returned from get_prod()"""
            beds = []
            self.bed_on_ward = self.bed_on_ward + 1
            for i in range(num_bed):
                prod_lis = get_prod(self.bed_on_ward + i)
                bed_dic = dict(
                    name=prod_lis[0].id,
                    ward=self.start.ward,
                    bed_type=self.start.bed_type,
                    institution=self.start.ward.institution,
                    state='free',
                    telephone_number=self.start.telephone,
                    movable=self.start.bed_transferable
                )
                beds.append(bed_dic)
            self.BedModel.create(beds)
        create_beds(num_bed)

        return 'end'
