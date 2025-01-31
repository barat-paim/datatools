import requests
import pandas as pd
from genson import SchemaBuilder
from jsonschema import validate, ValidationError
import ace_tools as tools

def fetch_api_data(api_url):
    """Fetch JSON data from an API."""
    response = requests.get(api_url)
    response.raise_for_status()  # Ensure it's a valid response
    return response.json()

def generate_schema(data):
    """Automatically generate a JSON schema."""
    builder = SchemaBuilder()
    builder.add_object(data)
    return builder.to_schema()

def validate_data(data, schema):
    """Validate data against the detected schema."""
    try:
        validate(instance=data, schema=schema)
        print("✅ Data is valid!")
    except ValidationError as e:
        print(f"❌ Validation failed: {e.message}")

def find_main_data_property(schema):
    """Find the property in the schema that contains the main list of data."""
    def find_list_property(obj, path=""):
        """Recursively search for the deepest array (list) in the schema."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, dict) and "type" in value:
                    if value["type"] == "array":
                        return path + key  # Return the deepest list path
                    elif value["type"] == "object":
                        # Recursively search deeper
                        result = find_list_property(value.get("properties", {}), path + key + ".")
                        if result:
                            return result
        return None

    return find_list_property(schema["properties"])  # Start search from root properties

def extract_data_from_json(data, data_path):
    """Extract the list of objects based on the detected schema path."""
    keys = data_path.split(".")
    for key in keys:
        data = data.get(key, {}) if isinstance(data, dict) else data
    return data if isinstance(data, list) else []

def convert_to_dataframe(data):
    """Convert extracted list data into a Pandas DataFrame."""
    return pd.DataFrame(data) if data else pd.DataFrame()

# 🚀 Fully Automated Flow
def one_click_api_to_dataframe(api_url):
    print(f"Fetching data from {api_url}...\n")
    
    data = fetch_api_data(api_url)
    schema = generate_schema(data)
    
    print("\n🔹 Detected Schema:")
    print(schema)
    
    validate_data(data, schema)
    
    # Automatically detect the main data property
    main_data_path = find_main_data_property(schema)
    print(f"\n📌 Detected Main Data Property: {main_data_path}")
    
    extracted_data = extract_data_from_json(data, main_data_path)
    
    df = convert_to_dataframe(extracted_data)
    
    tools.display_dataframe_to_user("API Data", df)
    return df

# Example API (Replace with any API you want)
#api_url = "http://api.jolpi.ca/ergast/f1/seasons"
#api_url = "http://api.jolpi.ca/ergast/f1/circuits.json"
#api_url = "http://api.jolpi.ca/ergast/f1/2024/races.json"
#api_url = "http://api.jolpi.ca/ergast/f1/2024/constructors.json"
#api_url = "http://api.jolpi.ca/ergast/f1/2024/drivers.json"
api_url = "http://api.jolpi.ca/ergast/f1/2024/sprint.json"
#api_url = "http://api.jolpi.ca/ergast/f1/2024/qualifying.json"
#api_url = "http://api.jolpi.ca/ergast/f1/2024/1/pitstops.json"
#api_url = "http://api.jolpi.ca/ergast/f1/2024/1/laps.json"
#api_url = "http://api.jolpi.ca/ergast/f1/2024/driverstandings.json"
#api_url = "http://api.jolpi.ca/ergast/f1/2024/constructorstandings.json"
#api_url = "http://api.jolpi.ca/ergast/f1/status.json"
one_click_api_to_dataframe(api_url)