import math
import os
from datetime import datetime
import numpy as np

from fhir.resources.bundle import Bundle, BundleEntry, BundleEntryRequest
from fhir.resources.medicationadministration import MedicationAdministration
from fhir.resources.observation import Observation

from utils import generate_unique_identifier

from utils import replace_commas_with_periods


def generate_glucose_fhir_interpretation(glucose_value, unit):
    interpretation = [
        {
            "coding": [
                {
                    "system": os.getenv("GLUCOSE_INTERPRETATION_SYSTEM", "http://loinc.org"),
                    "code": os.getenv("GLUCOSE_INTERPRETATION_CODE", "LA6576-8"),
                    "display": os.getenv("GLUCOSE_INTERPRETATION_DISPLAY", "Glucose interpretation")
                }
            ]
        }
    ]

    value_map = {
        "mmol": {
            "LU": float(os.getenv("GLUCOSE_INTERPRETATION_LU_MMOL", 3)),
            "L": float(os.getenv("GLUCOSE_INTERPRETATION_L_MMOL", 3.9)),
            "N": float(os.getenv("GLUCOSE_INTERPRETATION_H_MMOL", 10)),
            "H": float(os.getenv("GLUCOSE_INTERPRETATION_HU_MMOL", 13.9)),
            "HU": float(os.getenv("GLUCOSE_INTERPRETATION_HU_MMOL", 13.9))
        },
        "mg": {
            "LU": float(os.getenv("GLUCOSE_INTERPRETATION_LU_MG", 54)),
            "L": float(os.getenv("GLUCOSE_INTERPRETATION_L_MG", 70)),
            "N": float(os.getenv("GLUCOSE_INTERPRETATION_H_MG", 180)),
            "H": float(os.getenv("GLUCOSE_INTERPRETATION_HU_MG", 250)),
            "HU": float(os.getenv("GLUCOSE_INTERPRETATION_HU_MG", 250))
        }
    }

    ranges = value_map[unit]

    for code, threshold in ranges.items():
        if glucose_value <= threshold:
            interpretation[0]['coding'][0]['code'] = os.getenv(f"GLUCOSE_INTERPRETATION_{code}_CODE", code)
            interpretation[0]['coding'][0]['display'] = os.getenv(f"GLUCOSE_INTERPRETATION_{code}_DISPLAY", code)
            break  # Stop checking further thresholds once the condition is met

    return interpretation


# we can create either a CGM OR BG GLUCOSE OBSERVATION
def create_glucose_observation_json(value, scale, timestamp, patient_id, code, scale_display):
    narrative = "<div xmlns=\"http://www.w3.org/1999/xhtml\">Glucose " + scale_display + " in Body Fluid</div>"

    # todo, intepretation depends on the user version, removed in this case
    # "interpretation": interpretation,
    # if scale.lower() == os.getenv("GLUCOSE_SCALE_MMOL", "mmol/l").lower():
    #     interpretation = generate_glucose_fhir_interpretation(value, "mmol")
    # else:
    #     interpretation = generate_glucose_fhir_interpretation(value, "mg")

    unique_id = generate_unique_identifier(["Glucose", patient_id, timestamp, value, code])

    ID_SYSTEM = os.getenv("ID_SYSTEM", "")
    json_obj = {
        "status": "final",
        "identifier": [{
            "system": ID_SYSTEM,  # Replace with your system identifier
            "value": unique_id
        }],
        "subject": {"reference": f"Patient/{patient_id}", "display": "Patient"},
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": code,
                "display": f"Glucose {scale_display} in Body Fluid"
            }]
        },
        "effectiveDateTime": timestamp,
        "valueQuantity": {"value": value, "unit": scale},
        "text": {
            "status": "generated",
            "div": narrative
        }
    }

    return json_obj


def create_glucose_observation(value, scale, timestamp, patient_id, scale_code, scale_display):
    json_obj = create_glucose_observation_json(value, scale, timestamp, patient_id, scale_code, scale_display)
    return Observation.parse_obj(json_obj)


def generate_medtronic_glucose_observation(df_original, patient_id):
    # Create a copy of the input DataFrame
    df = df_original.copy()

    observations = []

    scale_cgm, scale_code_cgm, scale_display_cgm = "", "", ""
    scale_bg, scale_code_bg, scale_display_bg = "", "", ""

    # identify based on Medtronic description the variables
    # todo add the ('Sensor Glucose') as a global variable

    cols_with_cgm_glucose = df.columns[df.columns.str.contains('Sensor Glucose')]
    #cols_with_cgm_glucose = [col for col in df.columns if df[col].dtype == 'object' and col.startswith('Sensor Glucose')]

    cols_with_bg_glucose = df.columns[df.columns.str.contains('BG Reading')]
    #cols_with_bg_glucose = [col for col in df.columns if df[col].dtype == 'object' and col.startswith('BG Reading')]

    if len(cols_with_cgm_glucose) != 0:
        for col in cols_with_cgm_glucose:
            # We assume 2 units only
            if "mmol/L" in col:
                scale_cgm = os.getenv("GLUCOSE_SCALE_MMOL", "mmol/L")
                scale_display_cgm = os.getenv("GLUCOSE_SCALE_MMOL_DISPLAY", "[Moles/volume]")
                scale_code_cgm = os.getenv("CGM_GLUCOSE_CODE", "14745-4")
            else:
                scale_cgm = os.getenv("GLUCOSE_SCALE_MG", "mg/dL")
                scale_display_cgm = os.getenv("GLUCOSE_SCALE_MG_DISPLAY", "[Milligrams per deciliter]")
                scale_code_cgm = os.getenv("CGM_GLUCOSE_CODE", "14745-4")

    if len(cols_with_bg_glucose) != 0:
        for col in cols_with_bg_glucose:
            if "mmol/L" in col:
                scale_bg = os.getenv("GLUCOSE_SCALE_MMOL", "mmol/L")
                scale_display_bg = os.getenv("GLUCOSE_SCALE_MMOL_DISPLAY", "[Moles/volume]")
                scale_code_bg = os.getenv("BG_GLUCOSE_CODE", "41653-7")
            else:
                scale_bg = os.getenv("GLUCOSE_SCALE_MG", "mg/dL")
                scale_display_bg = os.getenv("GLUCOSE_SCALE_MG_DISPLAY", "[Milligrams per deciliter]")
                scale_code_bg = os.getenv("BG_GLUCOSE_CODE", "41653-7")

    if len(cols_with_cgm_glucose) == 0 and len(cols_with_bg_glucose) == 0:
        return observations

    # Merge the two index arrays into a single array
    columns_to_check = np.concatenate([cols_with_cgm_glucose, cols_with_bg_glucose])

    # Drop rows where all columns in columns_to_check are NaN
    df.dropna(subset=columns_to_check, how='all', inplace=True)

    # Apply the function only to specific columns in the DataFrame to avoid float issues
    df[columns_to_check] = df[columns_to_check].apply(replace_commas_with_periods)

    # Filter rows based on conditions
    # We can assume that the only relevant value is the BG_READIN_RECEIVED
    df = df[
        ((df['BG Source'] == os.getenv("MEDTRONIC_BG_READIN_RECEIVED", "BG_READIN_RECEIVED")) & (
            df[cols_with_bg_glucose].notna().any(axis=1))) |
        (df[cols_with_cgm_glucose].notna().any(axis=1))
        ]

    # Apply the function only to specific columns in the DataFrame to avoid float issues
    df[cols_with_cgm_glucose] = df[cols_with_cgm_glucose].applymap(replace_commas_with_periods)
    df[cols_with_bg_glucose] = df[cols_with_bg_glucose].applymap(replace_commas_with_periods)

    # df now contains the filtered and modified DataFrame
    for _, row in df.iloc[0:].iterrows():

        if len(cols_with_cgm_glucose) != 0:
            cgm_value = float(row[cols_with_cgm_glucose].iloc[0])
        else:
            cgm_value = math.nan
        if len(cols_with_bg_glucose) != 0:
            bg_value = float(row[cols_with_bg_glucose].iloc[0])
        else:
            bg_value = math.nan

        timestamp = row['Timestamp']

        timestamp = timestamp.strftime(os.getenv("TIMESTAMP_FORMAT", "%Y-%m-%dT%H:%M:%S+00:00"))

        value = cgm_value if math.isnan(bg_value) else bg_value
        scale = scale_cgm if math.isnan(bg_value) else scale_bg
        scale_code = scale_code_cgm if math.isnan(bg_value) else scale_code_bg
        scale_display = scale_display_cgm if math.isnan(bg_value) else scale_display_bg

        observation = create_glucose_observation(value, scale, timestamp, patient_id, scale_code, scale_display)
        observations.append(observation)

    # for debug purposes
    # print(observation.json())
    return observations


#### Block Insulin:
# An insulin pump is a small device that mimics some of the ways a healthy pancreas works.
# It delivers continuous and customized doses of rapid-acting insulin 24 hours a day to match your body's needs.
# The pump provides insulin to your body in two ways:
# Background (Basal) Insulin: Small amounts of insulin released continuously throughout the day.
# Mealtime (Bolus) Insulin: Additional insulin can be delivered on demand to match food intake or to correct high blood glucose.

# df['Bolus Type']
# The bolus insulin delivery type [Normal, Square, Dual
#     # (normal part), or Dual (square part)].
#
# df['Bolus Volume Selected (U)']
#     # The number of units of insulin selected to be
#     # delivered during the bolus insulin delivery.
#
# df['Bolus Volume Delivered (U)']
#     # The number of insulin units actually delivered during
#     # the bolus insulin delivery.
# # BASAL NOTES
# Basal Rate (U/h) = The active basal insulin delivery rate in units per
# hour.
#
# Temp Basal Amount = If a temp basal was applied on the pump, this value
# is the temp basal amount.
#
# Temp Basal Type = The type of temporary basal adjustment (insulin rate
# or percent of basal).
#
# Temp Basal Duration (m) = The length of time in minutes for the temporary
#
# when the basal rate is 0 it means that there are either rewind or suspend
# df['Rewind']
# This action is necessary when the current insulin supply is exhausted,
# and the user needs to prepare the pump for continued insulin delivery.
# df['Rewind']
# "Suspend" would indicate that the pump has been paused or temporarily halted from delivering insulin.

# Background (Basal) Insulin:
# Small amounts of insulin released continuously throughout the day.
def basal_medication_administration_json(patient_id, insulin_type, dose, timestamp,
                                         temp_basal_amount=None, temp_basal_type=None, temp_basal_duration=None):
    narrative = "<div xmlns=\"http://www.w3.org/1999/xhtml\">Basal Insulin Injection</div>"

    unique_id = generate_unique_identifier(["Insulin", patient_id, timestamp, dose, "BASAL"])
    ID_SYSTEM = os.getenv("ID_SYSTEM", "")

    medication_administration = {
        "resourceType": "MedicationAdministration",
        "status": "completed",
        "identifier": [{
            "system": ID_SYSTEM,  # Replace with your system identifier
            "value": unique_id
        }],
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": os.getenv("MEDICATION_ADMINISTRATION_BASAL_SYSTEM", "http://snomed.info/sct"),
                    "code": os.getenv("MEDICATION_ADMINISTRATION_BASAL_CODE", "25305005"),
                    "display": os.getenv("MEDICATION_ADMINISTRATION_BASAL_DISPLAY", "25305005"),
                }
            ],
            "text": insulin_type,  # Replace with the appropriate display name
        },
        "effectiveDateTime": timestamp,  # Date and time of administration
        # A specific date/time or interval of time during which the administration took place
        "dosage": {
            "rateQuantity": {
                "value": dose,
                "unit": os.getenv("MEDICATION_ADMINISTRATION_BASAL_UNIT_CODE", "U/h"),
                "system": os.getenv("MEDICATION_ADMINISTRATION_BASAL_UNIT_SYSTEM", "http://unitsofmeasure.org")
            }
        },
        "subject": {
            "reference": "Patient/" + patient_id
        },
        "text": {
            "status": "generated",
            "div": narrative
        }
    }

    # Check for and add Temp Basal data if available

    if temp_basal_amount is not None:
        pass  # TODO: FIX for the future
        # medication_administration['extension'].append({
        #     'url': 'http://example.com/temp-basal-amount',
        #     'valueQuantity': {
        #         'value': float(temp_basal_amount),
        #         'unit': 'U',
        #     }
        # })
    if temp_basal_type is not None:
        pass  # TODO: FIX for the future
        # medication_administration['extension'].append({
        #     'url': 'http://example.com/temp-basal-type',
        #     'valueCodeableConcept': {
        #         'coding': [
        #             {
        #                 'system': 'http://snomed.info/sct',
        #                 'code': '789012',  # Replace with the appropriate code for Temp Basal Type
        #                 'display': temp_basal_type,  # Use the provided value
        #             }
        #         ],
        #         'text': temp_basal_type,  # Use the provided value
        #     }
        # })
    if temp_basal_duration is not None:
        pass  # TODO: FIX for the future
        # medication_administration['extension'].append({
        #     'url': 'http://example.com/temp-basal-duration',
        #     'valueDuration': {
        #         'value': float(temp_basal_duration),
        #         'unit': 'minutes',
        #     }
        # })

    return medication_administration


# Mealtime (Bolus) Insulin:
# Additional insulin can be delivered on demand to match food intake or to correct high blood glucose.
def bolus_medication_administration_json(patient_id, insulin_type, bolus_volume_delivered, timestamp,
                                         bolus_type, programmed_duration):
    narrative = "<div xmlns=\"http://www.w3.org/1999/xhtml\">BOLUS Insulin - " + insulin_type + "</div>"

    unique_id = generate_unique_identifier(["Insulin", patient_id, timestamp, bolus_volume_delivered, "BOLUS"])
    ID_SYSTEM = os.getenv("ID_SYSTEM", "")

    medication_administration = {
        "resourceType": "MedicationAdministration",
        "text": {
            "status": "generated",
            "div": narrative
        },
        "identifier": [{
            "system": ID_SYSTEM,  # Replace with your system identifier
            "value": unique_id
        }],
        "status": "completed",
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": os.getenv("MEDICATION_ADMINISTRATION_BOLUS_SYSTEM", "http://snomed.info/sct"),
                    "code": os.getenv("MEDICATION_ADMINISTRATION_BOLUS_CODE", "A10AB"),
                    "display": os.getenv("MEDICATION_ADMINISTRATION_BOLUS_DISPLAY", "Background Insulin"),
                }
            ],
            "text": insulin_type,  # Replace with the appropriate display name
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "effectiveDateTime": timestamp,  # Date and time of administration
        "dosage": {
            "dose": {
                "value": bolus_volume_delivered,  # Use the delivered bolus volume
                "unit": os.getenv("MEDICATION_ADMINISTRATION_BOLUS_UNIT_CODE", "U"),
                "system": os.getenv("MEDICATION_ADMINISTRATION_BOLUS_UNIT_SYSTEM", "http://unitsofmeasure.org"),
            }
        }
    }

    if bolus_type is not None:
        pass  # TODO: FIX for the future
        # medication_administration["extension"].append(
        #     {
        #         "url": "http://example.com/programmedDuration",  # Replace with the appropriate URL
        #         "valueDuration": {
        #             "value": programmed_duration,
        #             "unit": "h",
        #             "system": "http://unitsofmeasure.org",
        #             "code": "h"
        #         }
        #     }
        # )

    if programmed_duration is not None:
        pass  # TODO: FIX for the future
        # medication_administration["extension"].append(
        #     {
        #         "url": "http://example.com/programmedDuration",  # Replace with the appropriate URL
        #         "valueDuration": {
        #             "value": programmed_duration,
        #             "unit": "h",
        #             "system": "http://unitsofmeasure.org",
        #             "code": "h"
        #         }
        #     }
        # )

    return medication_administration


def correction_medication_administration_json(patient_id, insulin_type, dose, timestamp):
    """
    Args:
        patient_id:
        insulin_type:
        dose:
        timestamp:

    Returns:

    """
    narrative = "<div xmlns=\"http://www.w3.org/1999/xhtml\">Correction Insulin Injection</div>"

    unique_id = generate_unique_identifier(["Insulin", patient_id, timestamp, dose, "CORRECTION"])
    ID_SYSTEM = os.getenv("ID_SYSTEM", "")

    medication_administration = {
        "resourceType": "MedicationAdministration",
        "status": "completed",
        "identifier": [{
            "system": ID_SYSTEM,  # Replace with your system identifier
            "value": unique_id
        }],
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": os.getenv("MEDICATION_ADMINISTRATION_CORRECTION_SYSTEM", "http://snomed.info/sct"),
                    "code": os.getenv("MEDICATION_ADMINISTRATION_CORRECTION_CODE", "CORRECTION"),
                    "display": os.getenv("MEDICATION_ADMINISTRATION_CORRECTION_DISPLAY", "Corretion Insulin"),
                }
            ],
            "text": insulin_type,  # Replace with the appropriate display name
        },
        "effectiveDateTime": timestamp,  # Date and time of administration
        # A specific date/time or interval of time during which the administration took place
        "dosage": {
            "dose": {
                "value": dose,
                "unit": os.getenv("MEDICATION_ADMINISTRATION_CORRECTION_UNIT_CODE", "U"),
                "system": os.getenv("MEDICATION_ADMINISTRATION_CORRECTION_UNIT_SYSTEM", "http://unitsofmeasure.org"),
            }
        },
        "subject": {
            "reference": "Patient/" + patient_id
        },
        "text": {
            "status": "generated",
            "div": narrative
        }
    }

    return medication_administration


def generate_medtronic_insulin_medication_administration(df_original, patient_id):
    # Create a copy of the input DataFrame
    df = df_original.copy()

    medication_administrations = []

    cols_with_bolus = [col for col in df.columns if df[col].dtype == 'object' and 'Bolus' in col]
    cols_with_basal = [col for col in df.columns if df[col].dtype == 'object' and 'Basal' in col]
    columns_to_check = cols_with_bolus + cols_with_basal
    df.dropna(subset=columns_to_check, how='all', inplace=True)

    # Apply the function only to specific columns in the DataFrame to avoid float issues
    df[columns_to_check] = df[columns_to_check].apply(replace_commas_with_periods)

    # Store environment variables in variables
    BOLUS_CONSTANT = os.getenv("MEDTRONIC_CLOSED_LOOP_BG_CORRECTION_AND_FOOD_BOLUS", "CLOSED_LOOP_BG_CORRECTION_AND_FOOD_BOLUS")
    BASAL_CONSTANT = [ os.getenv("MEDTRONIC_CLOSED_LOOP_AUTO_BASAL", "CLOSED_LOOP_AUTO_BASAL"),
                       os.getenv("MEDTRONIC_CLOSED_LOOP_AUTO_INSULIN", "CLOSED_LOOP_AUTO_INSULIN")
    ]
    CORRECTION_CONSTANT = [os.getenv("MEDTRONIC_CLOSED_LOOP_AUTO_BOLUS", "CLOSED_LOOP_AUTO_BOLUS"),
                           os.getenv("MEDTRONIC_CLOSED_LOOP_BG_CORRECTION", "CLOSED_LOOP_BG_CORRECTION")]
    insulin_threshold = float(os.getenv("INSULIN_THRESHOLD", "0"))

    # Iterate over rows and generate MedicationAdministration for each row
    for _, row in df.iloc[1:].iterrows():
        # Extract relevant data from the row
        timestamp = row['Timestamp']

        # If you need to use an environment variable for format, ensure it includes the offset
        timestamp = timestamp.strftime(os.getenv("TIMESTAMP_FORMAT", "%Y-%m-%dT%H:%M:%S+00:00"))

        basal = float(
            replace_commas_with_periods(
                row['Basal Rate (U/h)']
            )
        )
        bolus = float(
            replace_commas_with_periods(
                row['Bolus Volume Delivered (U)']
            )
        )
        auto_bolus = str(row['Bolus Source'])

        json_obj = None

        if not math.isnan(bolus) and bolus >= insulin_threshold:
            insulin_type = auto_bolus + " Insulin"
            if auto_bolus in CORRECTION_CONSTANT:
                json_obj = correction_medication_administration_json(patient_id, insulin_type, bolus, timestamp)
            elif auto_bolus in BOLUS_CONSTANT:
                json_obj = bolus_medication_administration_json(
                    patient_id,
                    insulin_type,
                    bolus,
                    timestamp,
                    row['Bolus Type'],
                    row['Bolus Duration (h:mm:ss)']
                )
            elif auto_bolus in BASAL_CONSTANT:
                insulin_type = "Total Insulin Daily (Basal) Insulin "
                json_obj = basal_medication_administration_json(
                    patient_id,
                    insulin_type,
                    bolus,
                    timestamp,
                    row['Temp Basal Amount'],
                    row['Temp Basal Type'],
                    row['Temp Basal Duration (h:mm:ss)']
                )

        elif not math.isnan(basal) and basal >= insulin_threshold and auto_bolus in BASAL_CONSTANT:
            insulin_type = "Background (Basal) Insulin " + auto_bolus
            json_obj = basal_medication_administration_json(
                patient_id,
                insulin_type,
                basal,
                timestamp,
                row['Temp Basal Amount'],
                row['Temp Basal Type'],
                row['Temp Basal Duration (h:mm:ss)']
            )

        if json_obj is not None:
            medication_administration = MedicationAdministration.parse_obj(json_obj)
            medication_administrations.append(medication_administration)

    return medication_administrations


# Function to generate a FHIR Observation resource for carbohydrates as JSON
def generate_carbohydrate_fhir_observation(patient_id, bwz_carb_input, timestamp):
    # Create a narrative for the observation
    narrative = "<div xmlns=\"http://www.w3.org/1999/xhtml\">Carbohydrate intake estimated</div>"

    unique_id = generate_unique_identifier(["Obervation", patient_id, timestamp, bwz_carb_input, "CARB"])
    ID_SYSTEM = os.getenv("ID_SYSTEM", "")

    observation = {
        "resourceType": "Observation",
        "status": "final",
        "identifier": [{
            "system": ID_SYSTEM,  # Replace with your system identifier
            "value": unique_id
        }],
        "code": {
            "coding": [
                {
                    "system": os.getenv("CARBOHYDRATES_EST_SYSTEM", "http://loinc.org"),
                    "code": os.getenv("CARBOHYDRATES_EST_CODE", "9059-7"),
                    "display": os.getenv("CARBOHYDRATES_EST_DISPLAY", "Carbohydrate intake estimated"),
                }
            ],
            "text": "Carbohydrates"
        },
        "subject": {
            "reference": "Patient/" + patient_id
        },
        "effectiveDateTime": timestamp,
        "valueQuantity": {
            "value": float(bwz_carb_input),
            "unit": os.getenv("CARBOHYDRATES_EST_UNIT", "g"),
            "system": os.getenv("CARBOHYDRATES_EST_UNIT_SYSTEM", "http://unitsofmeasure.org"),
            "code": os.getenv("CARBOHYDRATES_EST_UNIT_CODE", "g"),
        },
        "text": {
            "status": "generated",
            "div": narrative
        }
    }

    return observation


####  Grams information
# BWZ Carb Ratio
# The setting for insulin-to-carbohydrate ratio. If grams
# are used as the units, the ratio is the number of
# grams covered by one unit of insulin. If exchanges
# are used for units, the ratio is the number of insulin
# units used to cover one exchange.

# BWZ Carb Input Amount of carbohydrates entered into the Bolus
# Wizard and used to estimate a bolus.

# BWZ Food Estimate (U)
# The estimated units of bolus insulin to give to cover
# the expected amount of carbohydrate consumption,
# as calculated through the Bolus Wizard feature.

def generate_medtronic_carbohydrate_observation(df_original, patient_id):
    # Create a copy of the input DataFrame
    df = df_original.copy()

    observations = []
    cols_with_grams = [col for col in df.columns if df[col].dtype == 'object' and 'Carb' in col]
    cols_with_grams.append("BWZ Food Estimate (U)")
    df.dropna(subset=cols_with_grams, how='all', inplace=True)

    # Apply the function only to specific columns in the DataFrame to avoid float issues
    df[cols_with_grams] = df[cols_with_grams].applymap(replace_commas_with_periods)

    # Iterate over rows and generate MedicationAdministration for each row
    for _, row in df.iloc[1:].iterrows():
        # Extract relevant data from the row
        json_obj = ''

        timestamp = row['Timestamp']

        # If you need to use an environment variable for format, ensure it includes the offset
        timestamp = timestamp.strftime(os.getenv("TIMESTAMP_FORMAT", "%Y-%m-%dT%H:%M:%S+00:00"))

        bwz_carb_input = row['BWZ Carb Input (grams)']

        # TODO decide what we can use for it
        bwz_carb_ratio = row['BWZ Carb Ratio (g/U)']
        bwz_food_estimate = row['BWZ Food Estimate (U)']

        json_obj = generate_carbohydrate_fhir_observation(patient_id, bwz_carb_input, timestamp)

        if json_obj != '':
            observation = Observation.parse_obj(json_obj)
            observations.append(observation)
            # for debug purposes
            # print(observation.json())

    return observations


def create_insulin_carb_ratio_json(value, unit, timestamp, patient_id, system, code, display):

    narrative = "Insulin Carb Ratio set by the pump"

    unique_id = generate_unique_identifier(["InsulinCarbRatio", patient_id, timestamp, value, "ICR"])
    ID_SYSTEM = os.getenv("ID_SYSTEM", "")


    json_obj = {
        "resourceType": "Observation",
        "status": "final",
        "identifier": [{
            "system": ID_SYSTEM,  # Replace with your system identifier
            "value": unique_id
        }],
        "code": {
            "coding": [{
                "system": system,
                "code": code,
                "display": display
            }]
        },
        "subject": {
            "reference": f"Patient/{patient_id}",
            "display": "Patient"
        },
        "effectiveDateTime": timestamp,
        "valueQuantity": {
            "value": value,
            "unit": unit
        },
        "text": {
            "status": "generated",
            "div": narrative
        }
    }

    return json_obj


def generate_medtronic_carb_ratio(df_original, patient_id):
    # Assuming df is your DataFrame

    # Create a copy of the input DataFrame
    df = df_original.copy()

    filtered_df = df[df[df.columns[df.columns.str.startswith('BWZ Carb Ratio')]].notna().all(axis=1)]

    system = (os.getenv("ICR_SYSTEM", "http://loinc.org"))
    code = (os.getenv("ICR_CODE", "Insulin-carb-ratio"))
    display = (os.getenv("ICR_DISPLAY", "Insulin-Carb Ratio"))
    unit = (os.getenv("ICR_UNIT", "units/g"))
    # unit_system = (os.getenv("ICR_UNIT_SYSTEM", "http://unitsofmeasure.org"))

    col_with_icr = [col for col in df.columns if df[col].dtype == 'object' and 'BWZ Carb Ratio' in col]

    observations = []

    for _, row in filtered_df.iloc[1:].iterrows():
        # Extract relevant data from the row
        json_obj = ''

        timestamp = row['Timestamp']
        timestamp = timestamp.strftime(os.getenv("TIMESTAMP_FORMAT", "%Y-%m-%dT%H:%M:%S+00:00"))

        # TODO make it more secure
        value = float(replace_commas_with_periods(row[col_with_icr].iloc[0]))

        json_obj = create_insulin_carb_ratio_json(value, unit, timestamp, patient_id, system, code, display)

        if json_obj != '':
            observation = Observation.parse_obj(json_obj)
            observations.append(observation)

    return observations


def create_bundles(resource_list, resource_type):
    """
        This function takes two parameters and performs a specific task.

        Parameters:
        param1 (int): Description of parameter 1.
        param2 (str): Description of parameter 2.

        Returns:
        bool: Returns True if the task was successful, False otherwise.
    """
    bundles = []
    observation_size = len(resource_list)

    if observation_size == 0:
        return bundles  # If observation_list is empty, return an empty list of bundles

    # to avoid that the bundle is too big
    max_bundle_size = int(os.getenv("MAX_BUNDLE_SIZE", 500))
    if observation_size > max_bundle_size:
        num_bundles = (observation_size + max_bundle_size - 1) // max_bundle_size

        for i in range(num_bundles):
            start_index = i * max_bundle_size
            end_index = min((i + 1) * max_bundle_size, observation_size)
            partial_resource = resource_list[start_index:end_index]
            bundle = create_fhir_bundle(partial_resource, resource_type)
            bundles.append(bundle)
    else:
        bundles.append(create_fhir_bundle(resource_list, resource_type))

    return bundles


def create_fhir_bundle(entries, resource_type, method="POST"):
    # Step 1: Create the FHIR bundle resource
    bundle = Bundle(type='transaction')

    # Step 2: Create BundleEntry instances for each entry
    bundle_entries = []
    for entry in entries:
        # Check for identifier and its fields
        if entry.identifier and len(entry.identifier) > 0:
            identifier = entry.identifier[0]

            system = identifier.system.strip() if identifier.system else None
            value = identifier.value.strip() if identifier.value else None

            # Ensure that system and value are not empty or whitespace
            if system and value:
                # Create the BundleEntry instance
                bundle_entry = BundleEntry(resource=entry)

                # Set the request field for the entry
                bundle_entry.request = BundleEntryRequest(
                    method=method,  # Set the HTTP method (e.g., "POST" or "PUT")
                    url=resource_type,  # Set the resource type as the URL
                    ifNoneExist=f"identifier={system}|{value}"
                )

                bundle_entries.append(bundle_entry)
            else:
                # TODO: # Handle the case where identifier is not valid
                pass

    # Set the BundleEntry instances as the entry in the bundle
    bundle.entry = bundle_entries

    bundle.id = "0"  # It's not important

    # Get the current date and time
    current_datetime = datetime.now()
    bundle.timestamp = current_datetime.strftime(os.getenv("TIMESTAMP_FORMAT", "%Y-%m-%dT%H:%M:%S+00:00"))

    return bundle

