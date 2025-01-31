import requests
import pandas as pd
from genson import SchemaBuilder
from jsonschema import validate, ValidationError
import ace_tools as tools

def fetch_api_data(api_url):
    """Fetch JSON data from an API."""
    response = requests.get(api_url)
    response.raise_for_status()
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

def find_all_lists(schema, path=""):
    """Find all deeply nested and top-level list paths dynamically."""
    lists = []
    if isinstance(schema, dict):
        for key, value in schema.items():
            if isinstance(value, dict) and "type" in value:
                if value["type"] == "array":
                    lists.append(path + key)  # Collect list path
                elif value["type"] == "object":
                    lists.extend(find_all_lists(value.get("properties", {}), path + key + "."))
    return lists

def extract_data_from_json(data, list_paths):
    """Extract both shallow and deeply nested lists while preserving structure."""
    extracted_data = []

    def extract_recursive(data, parent_info={}):
        """Recursively extract lists while keeping parent data."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list) and all(isinstance(i, dict) for i in value):
                    for item in value:
                        merged_item = {**parent_info, **flatten_nested_dict(item)}
                        extracted_data.append(merged_item)
                        extract_recursive(item, merged_item)  # Dive deeper if needed
                else:
                    extract_recursive(value, {**parent_info, key: value})  # Continue processing
        
        elif isinstance(data, list):
            for item in data:
                extract_recursive(item, parent_info)  # Extract list elements

    # Handle simple first-level lists separately
    for path in list_paths:
        keys = path.split(".")
        sub_data = data
        for key in keys:
            sub_data = sub_data.get(key, {}) if isinstance(sub_data, dict) else sub_data
        if isinstance(sub_data, list):
            if all(isinstance(i, dict) for i in sub_data):  # Flat list detected
                extracted_data.extend([flatten_nested_dict(item) for item in sub_data])
            else:
                extract_recursive(sub_data)  # Go deeper if needed

    return extracted_data

def flatten_nested_dict(d, parent_key="", sep="_"):
    """Flatten nested dictionaries into a single level dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_nested_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def convert_to_dataframe(data):
    """Convert extracted list data into a Pandas DataFrame."""
    return pd.DataFrame(data) if data else pd.DataFrame()

def one_click_api_to_dataframe(api_url):
    """Convert API response to DataFrame with improved nested data handling."""
    print(f"Fetching data from {api_url}...\n")

    data = fetch_api_data(api_url)
    schema = generate_schema(data)

    print("\n🔹 Detected Schema:")
    print(schema)

    validate_data(data, schema)

    # Find all lists (shallow + deep)
    list_paths = find_all_lists(schema["properties"])
    print(f"\n📌 Detected List Paths: {list_paths}")

    extracted_data = extract_data_from_json(data, list_paths)
    
    df = convert_to_dataframe(extracted_data)
    
    tools.display_dataframe_to_user("API Data", df)
    return df

# Example APIs (uncomment to test different endpoints)
#api_url = "http://api.jolpi.ca/ergast/f1/circuits.json"
#api_url = "http://api.jolpi.ca/ergast/f1/2024/races.json"
api_url = "http://api.jolpi.ca/ergast/f1/2024/sprint.json"
#api_url = "http://api.jolpi.ca/ergast/f1/2024/qualifying.json"
#api_url = "http://api.jolpi.ca/ergast/f1/2024/1/pitstops.json"
one_click_api_to_dataframe(api_url) 