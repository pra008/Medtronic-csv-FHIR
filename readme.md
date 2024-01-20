# MedtronicCSVtoFHIR

MedtronicCSVtoFHIR is a Python SCRIPT that facilitates the conversion of Medtronic CSV data to FHIR (Fast Healthcare Interoperability Resources) bundles for interoperability with healthcare systems.

## Description

This library processes Medtronic CSV data containing patient information and generates FHIR-compliant data bundles. It includes functions for handling glucose observations, carbohydrate observations, and insulin medication administration, allowing seamless integration of data into healthcare systems.

## Features

- Conversion of Medtronic CSV data to FHIR bundles ( in [main.py](main.py)).
- Generation of glucose observations ( in [conversion.py](conversion.py)).
- Generation of carbohydrate observations ( in [conversion.py](conversion.py)).
- Creation of insulin medication administration bundles ( in [conversion.py](conversion.py)).
- Integration with FHIR-compatible systems [VERSION R4] (customizable via environment variables (at [.env](.env}))

## DEMO

We've included anonymized patient data produced between October and November 2023 in a separate folder for testing purposes.

The data is in the [Demo folder](DEMO/data.csv).

Additionally, associated FHIR bundles have been generated based on the provided data using the following format:

- Glucose bundles (e.g., [bundle_year_2023_month_10_week_1_part_1.json](DEMO/Bundles/glucose_bundle_year_2023_month_10_week_1_part_1.json),
)
- Carbohydrate bundles (e.g., [carbs_bundle_year_2023_month_10_week_1_part_1](DEMO/Bundles/carbs_bundle_year_2023_month_10_week_1_part_1.json)
)
- Medication Administration bundles (Insulin) (e.g., [insulin_bundle_year_2023_month_11_week_2_part_2.json](DEMO/Bundles/insulin_bundle_year_2023_month_11_week_2_part_2.json)
)

Note: Some weekly data may be divided into multiple parts, especially larger bundles that could potentially exceed the processing capacity of an FHIR server.

## Setup

1. Clone the repository:

```bash
git clone https://github.com/pra008/Medtronic-csv-FHIR

cd Medtronic-csv-FHIR
```

2. Run the installation script for macOS (and other Unix-like systems like iOS):

```bash
./install.sh
```

2. Run the installation script for Windows:

```bash
install.bat
```

This script will perform the following tasks:

- Checks if Python is installed. If not, it provides instructions to download and install Python.
- Creates a virtual environment named venv in the project directory.
- Activates the virtual environment.
- Installs the required dependencies specified in requirements.txt.
- Once the setup is complete, you can start using the project by following the usage instructions or running your desired commands.

## Running the Application

To run the application, a convenience script is provided which takes care of setting up the necessary environment variables and starting the application.

### On Windows

1. Open the Command Prompt or PowerShell in the directory where your project is located.
2. Execute the provided batch script `run.bat` by typing the following command and pressing Enter:

```bash
run.bat
```

This will load the environment variables from the `.env` file, activate the virtual environment if available, and run the Python script. Ensure that your `.env` file is in the same directory as the script.

3. The script will attempt to execute the Python application and will provide feedback in the command line interface. If there are any errors, the script will display a message with "Failed to run Python script."

Make sure you have Python installed and that the path to your Python executable is correctly set in your system's PATH environment variable before running the script.

### On Unix-based Systems (Linux/macOS)

For Unix-based systems, ensure you have the appropriate permissions to execute the script by running:

```bash
python3 main.py
```

## Installation Step by Step

### Python Installation (if not installed)

If you haven't installed Python, you can download it from the official [a https://www.python.org/downloads/](Python website) and follow the installation instructions based on your operating system.

### Setting up a Virtual Environment (optional but recommended)

While not mandatory, it's recommended to use a virtual environment to isolate project dependencies. To set up a virtual environment:

1. Open a terminal or command prompt.
1. Navigate to the project directory.

```bash
cd /path/to/Medtronic-csv-FHIR
```

3. Run the following command to create a virtual environment (replace venv with your preferred environment name):

```bash
python3 -m venv venv
```

4. Activate the virtual environment:

- On Windows:

```bash
venv\Scripts\activate
```

- On macOS and Linux:

```bash
source venv/bin/activate
```

### Installing Dependencies

Once Python is installed and a virtual environment (if desired) is set up, you can install the required packages:

1. Ensure you're in the project directory and the virtual environment is activated.
1. Run the following command to install the required dependencies using pip:

```bash
pip install -r requirements.txt
```

This will install all the necessary dependencies specified in the requirements.txt file for the Medtronic CSV to FHIR conversion library.

## Enviroment Variables and Cusomization

This will install all the necessary dependencies specified in the requirements.txt file for the Medtronic CSV to FHIR conversion library.

## Environment Variables and Customization

Please be aware that some of these constants are defined by Medtronic and they **MAY CHANGE**

Refer to the [Medtronic CSV Documentation](DEMO/Medtronic%20cvs.pdf) for more details.

Please note that the documentation for Medtronic CSV files is incomplete. As a result, some variables were guessed based on the available information.

For example, for glucose data:
- BG_SENT_FOR_CALIB: They use these values and report the manual glucose values

- USER_ACCEPTED_REMOTE_BG: They use these values and report the manual glucose values

### Medtronic specific code in CSV

**Note:** The official documentation lacks explicit details for variables that distinguish between BOLUS, BASAL, and CORRECTION types in Medtronic data. We've defined several constants to fill this gap. These constants are crucial for interpreting the data accurately, particularly in the `auto_bolus` column and similar fields. Here's how we've defined and used these variables:

| Variable Name                                           | Description                                                                                               |
|---------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| `BG_SENT_FOR_CALIB`                                     | Represents manual glucose values, used where `df['BG Source'] == 'BG_SENT_FOR_CALIB'`.                    |
| `USER_ACCEPTED_REMOTE_BG`                               | Indicates remote BG acceptance, used where `df['BG Source'] == 'USER_ACCEPTED_REMOTE_BG'`.                |
| `MEDTRONIC_BG_READIN_RECEIVED`                          | Corresponds to BG readings received, used where `df['BG Source'] == 'BG_READIN_RECEIVED'`.                |
| `MEDTRONIC_CLOSED_LOOP_AUTO_BASAL`                      | Part of `BASAL_CONSTANT`, indicates automated basal insulin delivery.                                     |
| `MEDTRONIC_CLOSED_LOOP_AUTO_INSULIN`                    | Also part of `BASAL_CONSTANT`, signifies automated insulin delivery not specified as basal or bolus.      |
| `MEDTRONIC_CLOSED_LOOP_BG_CORRECTION_AND_FOOD_BOLUS`    | Part of `BOLUS_CONSTANT`, used for food bolus and BG correction combined.                                 |
| `MEDTRONIC_CLOSED_LOOP_AUTO_BOLUS`                      | Part of `CORRECTION_CONSTANT`, used for automated bolus corrections.                                      |
| `MEDTRONIC_CLOSED_LOOP_BG_CORRECTION`                   | Also part of `CORRECTION_CONSTANT`, indicates a BG correction without a food bolus.                        |
| `MEDTRONIC_BOLUS_WIZARD`                                | Represents bolus calculations or suggestions provided by the Bolus Wizard feature.                        |

These variables are set as environment variables in our code, allowing for dynamic adjustment and easier management of the constants used in data processing.

  
### Glucose Scale and Codes for FHIR Resources

| Variable Name                      | Description                                 | Usage                                       |
|------------------------------------|---------------------------------------------|---------------------------------------------|
| `GLUCOSE_SCALE_MMOL`               | Measurement unit: mmol/L                     | Measurement unit for glucose in mmol/L.     |
| `GLUCOSE_SCALE_MMOL_SYSTEM`        | System URL for mmol/L scale                  | URL of the system for mmol/L glucose scale. |
| `GLUCOSE_SCALE_MMOL_CODE`          | Code for mmol/L glucose scale                | Code for mmol/L glucose scale.             |
| `GLUCOSE_SCALE_MMOL_DISPLAY`       | Display name for mmol/L glucose scale        | Display name for mmol/L glucose scale.     |
| `GLUCOSE_SCALE_MG`                 | Measurement unit: mg/dL                      | Measurement unit for glucose in mg/dL.     |
| `GLUCOSE_SCALE_MG_SYSTEM`          | System URL for mg/dL scale                   | URL of the system for mg/dL glucose scale. |
| `GLUCOSE_SCALE_MG_CODE`            | Code for mg/dL glucose scale                 | Code for mg/dL glucose scale.              |
| `GLUCOSE_SCALE_MG_DISPLAY`         | Display name for mg/dL glucose scale         | Display name for mg/dL glucose scale.      |
| `CGM_GLUCOSE_SYSTEM`               | System URL for CGM glucose                   | URL of the system for CGM glucose.         |
| `CGM_GLUCOSE_CODE`                 | Code for CGM glucose measurement             | Code for CGM glucose measurement.         |
| `CGM_GLUCOSE_DISPLAY`              | Display name for CGM glucose measurement     | Display name for CGM glucose measurement. |

### Manual Blood Glucose and Interpretation for FHIR Resources

| Variable Name                              | Description                             | Usage                                            |
|--------------------------------------------|-----------------------------------------|--------------------------------------------------|
| `BG_GLUCOSE_SYSTEM`                         | System URL for manual blood glucose      | URL of the system for manual blood glucose.       |
| `BG_GLUCOSE_CODE`                           | Code for manual blood glucose            | Code for manual blood glucose.                    |
| `BG_GLUCOSE_DISPLAY`                        | Display name for manual blood glucose    | Display name for manual blood glucose.            |
| `GLUCOSE_INTERPRETATION_SYSTEM`             | System URL for glucose interpretation    | URL of the system for glucose interpretation.     |
| `GLUCOSE_INTERPRETATION_CODE`               | Code for glucose interpretation          | Code for glucose interpretation.                  |
| `GLUCOSE_INTERPRETATION_DISPLAY`            | Display name for glucose interpretation  | Display name for glucose interpretation.          |
| `GLUCOSE_INTERPRETATION_LU_CODE`            | Code for significantly low glucose      | Code for significantly low glucose interpretation.|
| `GLUCOSE_INTERPRETATION_LU_DISPLAY`         | Display name for significantly low glucose| Display name for significantly low glucose.      |
| `GLUCOSE_INTERPRETATION_LU_MMOL`           | Significantly low glucose value (mmol/L) | Significantly low glucose value in mmol/L.       |
| `GLUCOSE_INTERPRETATION_LU_MG`             | Significantly low glucose value (mg/dL)  | Significantly low glucose value in mg/dL.        |
| `GLUCOSE_INTERPRETATION_L_CODE`            | Code for low glucose                     | Code for low glucose interpretation.             |
| `GLUCOSE_INTERPRETATION_L_DISPLAY`         | Display name for low glucose             | Display name for low glucose interpretation.     |
| `GLUCOSE_INTERPRETATION_L_MMOL`           | Low glucose value (mmol/L)               | Low glucose value in mmol/L.                     |
| `GLUCOSE_INTERPRETATION_L_MG`             | Low glucose value (mg/dL)                | Low glucose value in mg/dL.                      |
| `GLUCOSE_INTERPRETATION_N_CODE`            | Code for normal glucose                  | Code for normal glucose interpretation.          |
| `GLUCOSE_INTERPRETATION_N_DISPLAY`         | Display name for normal glucose          | Display name for normal glucose interpretation.  |
| `GLUCOSE_INTERPRETATION_H_CODE`            | Code for high glucose                    | Code for high glucose interpretation.            |
| `GLUCOSE_INTERPRETATION_H_DISPLAY`         | Display name for high glucose            | Display name for high glucose interpretation.    |
| `GLUCOSE_INTERPRETATION_H_MMOL`           | High glucose value (mmol/L)              | High glucose value in mmol/L.                    |
| `GLUCOSE_INTERPRETATION_H_MG`             | High glucose value (mg/dL)               | High glucose value in mg/dL.                     |
| `GLUCOSE_INTERPRETATION_HU_CODE`           | Code for significantly high glucose     | Code for significantly high glucose interpretation. |
| `GLUCOSE_INTERPRETATION_HU_DISPLAY`        | Display name for significantly high glucose| Display name for significantly high glucose.     |
| `GLUCOSE_INTERPRETATION_HU_MMOL`          | Significantly high glucose value (mmol/L) | Significantly high glucose value in mmol/L.     |
| `GLUCOSE_INTERPRETATION_HU_MG`            | Significantly high glucose value (mg/dL)  | Significantly high glucose value in mg/dL.      |

### Insulin Codes (Bolus and Basal) for FHIR Resources

You can customize these as well.

| Variable Name                                  | Description                           | Usage                                      |
|------------------------------------------------|---------------------------------------|--------------------------------------------|
| `MEDICATION_ADMINISTRATION_SYSTEM`              |                                        |                                            |
| `MEDICATION_ADMINISTRATION_CODE`                |                                        |                                            |
| `MEDICATION_ADMINISTRATION_DISPLAY`             |                                        |                                            |
| `MEDICATION_ADMINISTRATION_BOLUS_SYSTEM`        | URL for bolus insulin system          | System URL for background insulin (bolus). |
| `MEDICATION_ADMINISTRATION_BOLUS_CODE`          | Code for background insulin (bolus)   | Code for background insulin (bolus).       |
| `MEDICATION_ADMINISTRATION_BOLUS_DISPLAY`       | Display name for background insulin   | Display name for background insulin.       |
| `MEDICATION_ADMINISTRATION_BOLUS_UNIT_SYSTEM`   | URL for bolus insulin unit system     | System URL for insulin unit (bolus).       |
| `MEDICATION_ADMINISTRATION_BOLUS_UNIT_CODE`     | Code for insulin unit (bolus)         | Code for insulin unit (bolus).             |
| `MEDICATION_ADMINISTRATION_BOLUS_UNIT_DISPLAY`  | Display name for insulin unit (bolus) | Display name for insulin unit (bolus).     |
| `MEDICATION_ADMINISTRATION_BASAL_SYSTEM`        | URL for basal insulin system          | System URL for bolus insulin.              |
| `MEDICATION_ADMINISTRATION_BASAL_CODE`          | Code for bolus insulin                | Code for bolus insulin.                    |
| `MEDICATION_ADMINISTRATION_BASAL_DISPLAY`       | Display name for bolus insulin        | Display name for bolus insulin.            |
| `MEDICATION_ADMINISTRATION_BASAL_UNIT_SYSTEM`   | URL for basal insulin unit system     | System URL for insulin unit (basal).      |
| `MEDICATION_ADMINISTRATION_BASAL_UNIT_CODE`     | Code for insulin unit (basal)         | Code for insulin unit (basal).            |
| `MEDICATION_ADMINISTRATION_BASAL_UNIT_DISPLAY`  | Display name for insulin unit (basal) | Display name for insulin unit (basal).   |

### Carbohydrates (Estimated)

| Variable Name                            | Description                             | Usage                                          |
|------------------------------------------|-----------------------------------------|------------------------------------------------|
| `CARBOHYDRATES_EST_SYSTEM`               | URL for carbohydrate intake system      | System URL for estimated carbohydrate intake.    |
| `CARBOHYDRATES_EST_CODE`                 | Code for carbohydrate intake            | Code for estimated carbohydrate intake.          |
| `CARBOHYDRATES_EST_DISPLAY`              | Display name for carbohydrate intake    | Display name for estimated carbohydrate intake.  |
| `CARBOHYDRATES_EST_UNIT`                 | Unit of measurement for carbohydrates    | Unit of measurement for estimated carbohydrates. |
| `CARBOHYDRATES_EST_UNIT_SYSTEM`          | URL for carbohydrate unit system        | System URL for carbohydrate unit.                |
| `CARBOHYDRATES_EST_UNIT_CODE`            | Code for carbohydrate unit              | Code for estimated carbohydrate unit.            |
