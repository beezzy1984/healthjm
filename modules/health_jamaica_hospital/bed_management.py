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
    ward_code = fields.Char('Ward Code', required=True)

    @staticmethod
    def get_bed_types():
        """Returns the list of bed types from the hospital bed model"""
        hospital_bed = Pool().get('gnuhealth.hospital.bed')
        return hospital_bed.bed_type.selection  

    @fields.depends('bed_transferable')
    def on_change_with_source_location(self):
        """return a new value for source location"""
        return int(self.bed.ward)


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
        bed_on_ward = self.BedModel.search_count(
                                            [('ward', '=',self.start.ward.id)])
        if start.ward and bed_total > start.ward.number_of_beds:
            beds_left = self.start.ward.number_of_beds - bed_on_ward
            
            self.raise_user_error("This ward's maximum capacity is %d beds\n"
                                  "There are currently %d beds on this ward\n"
                                  "You can only create %d more beds for this ward." % 
                                  (self.start.ward.number_of_beds, bed_on_ward,
                                   beds_left))

        def get_prod_temp():
            """Returns an available bed template. If none is available
               it creates one"""
            template = Pool().get('product.template')

            if template.search(['name', '=', 'Bed']):
                return template.search(['name', '=', 'Bed'])

            def get_uom():
                """Checks for unit of measurement dollar, if it is not found 
                then the object is created and returned to the calling 
                function in a list"""
                uom = Pool().get('product.uom')

                if uom.search(['name', '=', 'Dollar']):
                    return uom.search(['name', '=', 'Dollar'])

                uom_category = Pool().get('product.uom.category')
                cat_list = [{'name':'Money'}]
                cat_list = uom_category.create(cat_list)
                assert(len(cat_list) > 0)

                uom_lis = []
                uom_dict = dict(
                    name="Jamaican Dollars",
                    symbol='JMD',
                    category=cat_list[0].id,
                    rate=1.00,
                    factor=1.00,
                    rounding=0.01,
                    digits=2,
                    active=True
                )

                uom_lis.append(uom_dict)
                return uom.create(uom_lis)

            temp_lis = []
            uom_lis = []
            uom_lis = get_uom()
            template_dict = dict(
                name="Bed",
                type="assets",
                consumable=False,
                list_price=0.00,
                cost_price=0.00,
                cost_price_method='fixed',
                active=True,
                default_uom=uom_lis[0].id
            )

            temp_lis.append(template_dict)
            return template.create(temp_lis)

        def get_prod(bed_number):
            """Creates a bed product from the product template
               returned by get_prod_temp function"""
            temp_lis = get_prod_temp()
            prod = []
            assert(len(temp_lis) > 0)

            Product = Pool().get('product.product')
            template_dict = dict(
                template=temp_lis[0].id,
                code="%s - %d" %(self.start.ward_code, bed_number),
                is_bed=True,
                active=True
            )

            prod.append(template_dict)
            return Product.create(prod)

        def create_beds(num_bed):
            """Creates beds based on the argument num_bed and on 
               the product returned from get_prod()"""
            beds = []
            for i in range(num_bed):
                prod_lis = get_prod(i)
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
