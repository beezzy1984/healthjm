from trytond.pool import Pool
from .encounter import *
from .components import *

def register():
    Pool.register(
        PatientEncounter,
        EncounterAnthro,
        EncounterAmbulatory,
        # EncounterClinical,
        EncounterComponent,
        ChooseComponentTypeView,
        module='health_encounter', type_='model')

    Pool.register(
        ChooseComponentWizard,
        module='health_encounter', type_='wizard')
