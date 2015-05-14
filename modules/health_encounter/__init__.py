from trytond.pool import Pool
from .encounter import *
from .components import *

def register():
    Pool.register(
        PatientEncounter,
        EncounterAnthro,
        EncounterAmbulatory,
        EncounterClinical,
        Directions,
        SecondaryCondition,
        DiagnosticHypothesis,
        SignsAndSymptoms,
        EncounterComponent,
        ChooseComponentTypeView,
        module='health_encounter', type_='model')

    Pool.register(
        ChooseComponentWizard,
        EditComponentWizard,
        module='health_encounter', type_='wizard')
