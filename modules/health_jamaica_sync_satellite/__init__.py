from trytond.pool import Pool
from .remote_party import *
from .health_professionals import (HealthProfessional,
                                   OpenAppointmentReportStart)

def register():
    Pool.register(
        RemoteParty,
        RemotePartyImportStart,
        RemotePartyImportDone,
        HealthProfessional,
        OpenAppointmentReportStart,
        module='health_jamaica_sync_satellite', type_='model')

    Pool.register(
        RemotePartyImport,
        module='health_jamaica_sync_satellite', type_='wizard')
