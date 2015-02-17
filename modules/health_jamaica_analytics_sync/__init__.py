from trytond.pool import Pool
# from .models import ModelName

def register():
    Pool.register(
#        ModelName,
        module='health_jamaica_analytics_sync', type_='model')
