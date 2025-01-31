import requests
import pandas as pd
from genson import SchemaBuilder
from jsonschema import validate, ValidationError
import ace_tools as tools
import json

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
    """Hybrid approach combining path detection and recursive extraction"""
    extracted_data = []
    
    def extract_recursive(data, parent_context=None):
        """Improved recursive extraction with context preservation"""
        parent_context = parent_context or {}
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    merged = {**parent_context, **flatten_nested_dict(item)}
                    extracted_data.append(merged)
                    # Preserve context for nested lists
                    new_context = {**parent_context, **flatten_nested_dict(item)}
                    for value in item.values():
                        extract_recursive(value, new_context)
        
        elif isinstance(data, dict):
            for value in data.values():
                extract_recursive(value, parent_context)

    # Process detected list paths first
    for path in list_paths:
        keys = path.split('.')
        current_data = data
        for key in keys:
            current_data = current_data.get(key, {}) if isinstance(current_data, dict) else current_data
        
        if isinstance(current_data, list):
            parent_context = get_parent_context(data, path)
            extract_recursive(current_data, parent_context)

    # Fallback to full recursive extraction if no paths found
    if not list_paths:
        extract_recursive(data)

    return extracted_data

def get_parent_context(data, path):
    """Get context from parent nodes of a list path"""
    context = {}
    keys = path.split('.')
    current = data
    
    for key in keys[:-1]:  # Stop before the list itself
        current = current.get(key, {})
        if isinstance(current, dict):
            context.update(flatten_nested_dict(current))
    
    return context

def flatten_nested_dict(d, parent_key="", sep="_"):
    """Improved flattening that handles nested lists and dicts."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_nested_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Handle lists by converting to JSON strings
            items.append((new_key, json.dumps(v) if v else None))
        else:
            items.append((new_key, v))
    return dict(items)

def convert_to_dataframe(data):
    """Convert structured data to DataFrame with column hierarchy."""
    if not data:
        print("⚠️ No extractable list data found in API response")
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Clean column names and sort by hierarchy
    df.columns = [col.split(".")[-1] for col in df.columns]
    
    if not df.empty:
        hierarchy_levels = sorted(set(
            ".".join(col.split(".")[:-1]) for col in data[0].keys()
        ), key=lambda x: x.count("."))
        
        # Organize columns by hierarchy depth
        column_order = []
        for level in hierarchy_levels:
            column_order.extend([
                col for col in df.columns
                if col.startswith(level.split(".")[-1] + ".")
            ])
        
        return df[column_order] if column_order else df
    
    return df

def one_click_api_to_dataframe(api_url):
    """Convert API response to DataFrame with improved nested data handling."""
    print(f"Fetching data from {api_url}...\n")

    data = fetch_api_data(api_url)
    schema = generate_schema(data)

    print("\n🔹 Detected Schema:")
    print(schema)

    validate_data(data, schema)

    # Extract data using recursive extraction
    list_paths = find_all_lists(schema)
    extracted_data = extract_data_from_json(data, list_paths)
    
    if not extracted_data:
        print("❌ No structured data could be extracted from the API response")
        return pd.DataFrame()
    
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