import os

import hashlib


def convert_datetime_to_iso(date_str, time_str, tz):
    """
    Converts a date and time string to ISO format with timezone.

    Args:
        date_str (str): Date string in YYYY-MM-DD format.
        time_str (str): Time string in HH:MM:SS format.
        tz (str): Timezone string in ±HH:MM format.

    Returns:
        str: Date and time string in ISO 8601 format.
    """
    dt_str = f"{date_str}T{time_str}.000{tz}"
    return dt_str


def replace_commas_with_periods(value):
    """
    Replaces commas with periods in non-float columns of a dataset.

    Args:
        value (str or other): The value to process.

    Returns:
        str or other: Processed value with commas replaced by periods.
    """
    if isinstance(value, str):
        return value.replace(',', '.').replace('"', '')
    return value


def save_bundles_to_files(bundles, resource_name, year, month, week):
    """
    Saves bundles to JSON files.

    Args:
        bundles (list): List of bundles to save.
        resource_name (str): Name of the resource.
        year (int): Year for grouping bundles.
        month (int): Month for grouping bundles.
        week (int): Week for grouping bundles.
    """
    folder_name = os.getenv('FOLDER_BUNDLE_DESTINATION', "Bundles")
    for i, bundle in enumerate(bundles):
        if not isinstance(bundle, int):
            try:
                bundle_json = bundle.json()
                file_path = os.path.join(
                    folder_name, f"{resource_name}_bundle_year_{year}_month_{month}_week_{week}_part_{i+1}.json"
                )
                with open(file_path, "w") as f:
                    f.write(bundle_json)
                    print(f"File '{file_path}' successfully created.")
            except ValueError as e:
                print(f"Error occurred: {e}")


def generate_unique_identifier(data_elements):
    # Concatenate the data elements into a single string
    concatenated_data = '-'.join(map(str, data_elements))

    # Generate a SHA-256 hash of this string
    hash_object = hashlib.sha256(concatenated_data.encode())
    hash_hex = hash_object.hexdigest()

    return hash_hex
