from trytond.pool import Pool
from .models import PostOffice, DistrictCommunity

def register():
    Pool.register(
        PostOffice,
        DistrictCommunity,
        module='country_jamaica', type_='model')
