import os
from datetime import datetime
import pandas as pd

from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

from conversion import generate_medtronic_glucose_observation, create_bundles, \
    generate_medtronic_carbohydrate_observation, generate_medtronic_insulin_medication_administration, \
    generate_medtronic_carb_ratio

from utils import save_bundles_to_files


def load_data_from_environment():
    """
    Load patient_id and csv_file from environment variables or set default values
    Returns:
        tuple: A tuple containing the file and fhir_id
        """
    # Load patient_id and csv_file from environment variables or set default values
    load_dotenv()
    fhir_id = os.getenv('PATIENT_ID') or "patient_id"
    file = os.getenv('CSV_FILE') or "DEMO/Bundles"
    return file, fhir_id


def process_patient_data(csv_file, patient_id):
    """
    Processes patient data from a CSV file based on date and time.
    Generates FHIR bundles for glucose, carbohydrate, and insulin observations by week.
    """

    # Read the uploaded file using pandas
    df = pd.read_csv(csv_file, skiprows=6, sep=';', index_col=0)

    # Convert 'Date' column to datetime objects with a specific format
    df['Date'] = pd.to_datetime(df['Date'], format='%Y/%m/%d', errors='coerce')

    # Drop rows with NaT (not a time) values in the 'Date' column
    df.dropna(subset=['Date'], inplace=True)
    df['Time'] = pd.to_timedelta(df['Time'])

    # Merge 'Date' and 'Time' columns into a single datetime column 'Timestamp'
    df['Timestamp'] = df['Date'] + df['Time']

    # Find the minimum date in the DataFrame to determine the starting point for iteration
    year = df['Date'].min().year
    end_year = df['Date'].max().year

    # Iterate through months and years starting from the minimum date up to the current year
    while year <= end_year:
        month = df['Date'].min().month
        while month <= 12:  # Loop through all months (1 to 12)

            # Filter the DataFrame for the current year and month
            filtered_df = df[
                (df['Timestamp'].dt.year == year) &
                (df['Timestamp'].dt.month == month)
                ]

            if not filtered_df.empty:
                # Process data for each week in the month
                current_date = datetime(year, month, 1)
                end_date = current_date + relativedelta(day=31)

                week = 1
                while current_date <= end_date:
                    # Calculate the end of the current week
                    end_of_week = current_date + relativedelta(days=7)

                    # get only the week data
                    week_df = filtered_df[
                        (filtered_df['Timestamp'] <= end_of_week) &
                        (filtered_df['Timestamp'] >= current_date)]

                    # Generate and save FHIR bundles for glucose observations
                    glucose_observation = generate_medtronic_glucose_observation(week_df, patient_id)
                    glucose_bundles = create_bundles(glucose_observation, "Observation")
                    save_bundles_to_files(glucose_bundles, 'glucose', year, month, week)

                    # Generate and save FHIR bundles for carbohydrate observations
                    carbohydrate_observation = generate_medtronic_carbohydrate_observation(week_df, patient_id)
                    carbohydrate_bundles = create_bundles(carbohydrate_observation, "Observation")
                    save_bundles_to_files(carbohydrate_bundles, 'carbs', year, month, week)

                    # Generate and save FHIR bundles for insulin medication administrations
                    insulin_medication_administration = generate_medtronic_insulin_medication_administration(week_df,
                                                                                                             patient_id)
                    insulin_bundles = create_bundles(insulin_medication_administration, "MedicationAdministration")
                    save_bundles_to_files(insulin_bundles, 'insulin', year, month, week)

                    # TODO: Uncomment if needed
                    # Generate and save FHIR bundle for Insulin-Carb-Ratio
                    # icr_observation = generate_medtronic_carb_ratio(week_df, patient_id)
                    # icr_bundles = create_bundles(icr_observation, "Observation")
                    # save_bundles_to_files(icr_bundles, 'icr', year, month, week)

                    # Move to the next week
                    current_date += relativedelta(weeks=1)
                    week += 1

            month += 1

        # Reset month to 1 for the next year
        month = 1
        year += 1


if __name__ == "__main__":
    medtronic_file, patient_id_fhir = load_data_from_environment()
    # Presenting the output to the user
    print("Patient ID for FHIR resources:", patient_id_fhir)
    print("CSV File:", medtronic_file)
    process_patient_data(medtronic_file, patient_id_fhir)
