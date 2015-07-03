from trytond.pool import Pool
from .encounter import PatientEncounter
from .encounter_component_type import EncounterComponentType
from .components import *


def register():
    Pool.register(
        EncounterComponentType,
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
        EditComponentWizard,
        module='health_encounter', type_='wizard')
