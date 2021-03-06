
from datetime import datetime
from trytond.model import ModelSQL, ModelView, fields
from trytond.wizard import Wizard
from trytond.pyson import Eval, Not, In, Equal, Or
from trytond.pool import Pool
from trytond.transaction import Transaction
from ..health_jamaica.tryton_utils import (replace_clause_column, get_timezone)

__all__ = ['HospitalBed', 'InpatientRegistration', 'PatientRounding',
           'HospitalWard', 'CreateBedTransfer']


class HospitalBed(ModelSQL, ModelView):
    'Hospital Bed'
    __name__ = 'gnuhealth.hospital.bed'

    movable = fields.Boolean('movable')

    def get_rec_name(self, name):
        if self.name:
            return self.name.code
        else:
            return "Unlabeled bed %d" % (self.id)

    @classmethod
    def search_rec_name(cls, name, clause):
        return ['OR', replace_clause_column(clause, 'name.name'),
                replace_clause_column(clause, 'name.code')]


class HospitalWard(ModelSQL, ModelView):
    'Hospital Ward'
    __name__ = 'gnuhealth.hospital.ward'

    wardcode = fields.Char('Ward Code')


class InpatientRegistration(ModelSQL, ModelView):
    'Patient admission History'
    __name__ = 'gnuhealth.inpatient.registration'

    expected_discharge = fields.Date('Expected Discharge Date')
    puid = fields.Function(fields.Char('UPI', size=12), 'get_patient_field')
    medical_record_num = fields.Function(fields.Char('Medical Record Number',
                                                     size=10),
                                         'get_patient_field')
    sex_display = fields.Function(fields.Char('Sex', size=12),
                                  'get_patient_field')
    age = fields.Function(fields.Char('Age', size=12), 'get_patient_field')

    speciality = fields.Many2One('gnuhealth.specialty', 'Specialty',
                                 help='Medical Specialty / Sector')

    @classmethod
    def __setup__(cls):
        super(InpatientRegistration, cls).__setup__()
        # Make readonly for bed depends on a person being hospitalised or
        # discharged from the hospital
        cls.bed.states = {'required': True,
                          'readonly': Or(Equal(Eval('state'), 'hospitalized'),
                                         Equal(Eval('state'), 'confirmed'),
                                         Equal(Eval('state'), 'done'))}
        # Changed depends to accommodate state
        cls.bed.depends = ['name', 'state']
        # make discharge_date not required
        cls.discharge_date.required = False
        if not cls.discharge_date.states:
            cls.discharge_date.states = {}
        cls.discharge_date.states['invisible'] = Not(
            In(Eval('state'), ['done', 'hospitalized']))
        # rename the set of states
        cls.state.selection = [
            ('free', 'Pending'),
            ('cancelled', 'Cancelled'),
            ('confirmed', 'Confirmed'),
            ('hospitalized', 'Admitted'),
            ('done', 'Discharged/Done')
        ]
        # discharge_date is the real thing
        cls.discharge_date.string = 'Discharged'

    @classmethod
    def __register__(cls, module_name):
        super(InpatientRegistration, cls).__register__(module_name)
        cursor = Transaction().cursor
        # Make the discharge_date column not required at the DB level
        cursor.execute(
            '''ALTER TABLE gnuhealth_inpatient_registration
               ALTER COLUMN discharge_date DROP NOT NULL;''')

    @classmethod
    @ModelView.button
    def admission(cls, registrations):
        """Hospitalization Date"""
        # redefined to fix a date bug
        registration_id = registrations[0]
        Bed = Pool().get('gnuhealth.hospital.bed')
        tz = get_timezone()
        if (registration_id.hospitalization_date.date() >
                datetime.now(tz).date()):
            cls.raise_user_error("The Admission date must be today or earlier")
        else:
            cls.write(registrations, {'state': 'hospitalized'})
            Bed.write([registration_id.bed], {'state': 'occupied'})

    @classmethod
    @ModelView.button
    def discharge(cls, registrations):
        """Discharge patient and free up beds"""
        signing_hp = Pool().get(
            'gnuhealth.healthprofessional').get_health_professional()
        if not signing_hp:
            cls.raise_user_error(
                "No health professional associated with this user.")
        reg_did = [x for x in registrations if x.discharge_date]
        reg_didnt = [x for x in registrations if not x.discharge_date]
        if reg_didnt:
            cls.write(reg_didnt, {'state': 'done',
                                  'discharge_date': datetime.now(),
                                  'discharged_by': signing_hp})
        if reg_did:
            cls.write(reg_did, {'state': 'done', 'discharged_by': signing_hp})

        bed_model = Pool().get('gnuhealth.hospital.bed')
        bed_model.write([x.bed for x in registrations], {'state': 'free'})

    @classmethod
    @ModelView.button
    def confirmed(cls, registrations):
        """Confirms a patient to be admitted"""
        bed_model = Pool().get('gnuhealth.hospital.bed')
        beds = []
        for reg in registrations:
            if reg.bed.state != 'free':
                cls.raise_user_error('bed_is_not_available')
            if (reg.expected_discharge and
                    reg.expected_discharge <
                    reg.hospitalization_date.date()):
                cls.raise_user_error("The discharge date must later than "
                                     "admission")
            beds.append(reg.bed)
        bed_model.write(beds, {'state': 'reserved'})
        cls.write(registrations, {'state': 'confirmed'})

    def get_rec_name(self, name):
        if self.patient:
            return '%s: %s (%s)' % (self.name, self.patient.name.name,
                                    self.patient.puid)
        else:
            return self.name

    def get_patient_field(self, name):
        """Get patient id"""
        if self.patient:
            return getattr(self.patient, name)
        return ''


class PatientRounding(ModelSQL, ModelView):
    'Patient Round'
    __name__ = 'gnuhealth.patient.rounding'

    @classmethod
    def __setup__(cls):
        super(PatientRounding, cls).__setup__()
        cls.name.string = "Inpatient"


class CreateBedTransfer(Wizard):
    """docstring for BedTransfer"ModelSQL
    def __init__(self, arg):
        super(BedTransfer,ModelSQL).__init__()
        self.arg = arg
       """
    __name__ = 'gnuhealth.bed.transfer.create'

    # An edited copy of the function in gnuhealth.patient.rounding
    def transition_create_bed_transfer(self):
        """Making bed tranfer for patients that are not yet admitted
           equal to free"""
        inpatient_registrations = Pool().get(
            'gnuhealth.inpatient.registration')
        bed = Pool().get('gnuhealth.hospital.bed')

        registrations = inpatient_registrations.browse(
            Transaction().context.get('active_ids'))

        # Don't allow mass changes. Work on a single record
        if len(registrations) > 1:
            self.raise_user_error('choose_one')

        registration = registrations[0]
        current_bed = registration.bed
        destination_bed = self.start.newbed
        reason = self.start.reason

        # Check that the new bed is free
        if destination_bed.state == 'free':
            # Free the current bed
            bed.write([current_bed], {'state': 'free'})
            # Set as occupied the new bed

            # Only change the state of the bed to occupied if the patient
            # was hospitalized
            if registration.state == 'hospitalized':
                bed.write([destination_bed], {'state': 'occupied'})
            # Change the state of the bed to reserved if the patient admission
            # has been confirmed but not admitted as yet
            elif registration.state == 'confirmed':
                bed.write([destination_bed], {'state': 'reserved'})
            # Raise error if patient has been discharged, you should not be
            # able to transfer an already discharged patient to a bed
            elif registration.state == 'done':
                self.raise_user_error(
                    'Cannot transfer a discharge patient to a bed')

            # Update the hospitalization record
            hospitalization_info = {}

            hospitalization_info['bed'] = destination_bed

            # Update the hospitalization data
            transfers = []
            transfers.append(('create', [{'transfer_date': datetime.now(),
                                          'bed_from': current_bed,
                                          'bed_to': destination_bed,
                                          'reason': reason}]))
            hospitalization_info['bed_transfers'] = transfers

            inpatient_registrations.write([registration], hospitalization_info)

        else:
            self.raise_user_error('bed_unavailable')

        return 'end'
