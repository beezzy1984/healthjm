from trytond.pool import Pool
from .remote_party import RemoteParty
from .health_professionals import (HealthProfessional,
                                   OpenAppointmentReportStart)

def register():
    Pool.register(
        RemoteParty,
        HealthProfessional,
        OpenAppointmentReportStart,
        module='health_jamaica_sync_satellite', type_='model')
