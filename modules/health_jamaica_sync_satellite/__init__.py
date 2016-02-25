from trytond.pool import Pool
from .remote_party import *
from .health_professionals import (HealthProfessional,
                                   OpenAppointmentReportStart)
from .appointment import Appointment


def register():
    Pool.register(
        RemoteParty,
        RemotePartyImportStart,
        RemotePartyImportDone,
        HealthProfessional,
        OpenAppointmentReportStart,
        Appointment,
        module='health_jamaica_sync_satellite', type_='model')

    Pool.register(
        RemotePartyImport,
        module='health_jamaica_sync_satellite', type_='wizard')
