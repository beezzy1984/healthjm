from trytond.pool import Pool
from .remote_party import RemoteParty


def register():
    Pool.register(
        RemoteParty,
        module='health_jamaica_sync_satellite', type_='model')
