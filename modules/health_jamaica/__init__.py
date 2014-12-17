# -*- coding: utf-8 -*-
##############################################################################
#
#    Health-Jamaica: The Jamaica Electronic Patient Administration System
#    Copyright 2014  Ministry of Health (NHIN), Jamaica <admin@mohnhin.info>
#
#    Based on GNU Health
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

from trytond.pool import Pool
from .health_jamaica import *
from .wizards import *
from .reports import *

def register():
    Pool.register(
        OccupationalGroup,
        PartyPatient,
        PatientData,
        AlternativePersonID,
        PostOffice,
        DistrictCommunity,
        PartyAddress,
        DomiciliaryUnit,
        Newborn,
        HealthInstitution,
        Insurance,
        PathologyGroup,
        ProcedureCode,
        HealthProfessional,
        Appointment,
        DiagnosticHypothesis,
        PatientEvaluation,
        SignsAndSymptoms,
        PatientRegisterModel,
        OpenAppointmentReportStart,
        HealthProfessionalSpecialties,
        HealthInstitutionSpecialties,
        AppointmentReport,
        module='health_jamaica', type_='model')

    Pool.register(
        PatientRegisterWizard,
        OpenAppointmentReport,
        module='health_jamaica', type_='wizard'
    )

    Pool.register(
        DailyPatientRegister,
        module='health_jamaica', type_='report'
    )
