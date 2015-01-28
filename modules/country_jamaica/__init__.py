from trytond.pool import Pool
# from .models import ModelName

def register():
    Pool.register(
#        ModelName,
        module='country_jamaica', type_='model')
