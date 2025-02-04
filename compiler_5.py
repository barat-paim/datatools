import requests
import pandas as pd
import hashlib
import json
from collections import defaultdict
from genson import SchemaBuilder
from jsonschema import validate, ValidationError
import ace_tools as tools

class RelationalProcessor:
    def __init__(self):
        self.tables = defaultdict(list)
        self.relationships = []
        self.current_ids = defaultdict(int)
        self.table_configs = []

    def process_api_response(self, api_url):
        """Main processing workflow"""
        raw_data = fetch_api_data(api_url)
        schema = generate_schema(raw_data)
        
        if not validate_data(raw_data, schema):
            return None
        
        self.analyze_schema(schema)
        self.convert_to_relational(raw_data)
        return self.structure_output()

    def analyze_schema(self, schema):
        """Identify potential tables from schema"""
        def find_tables(subschema, path):
            if isinstance(subschema, dict):
                if subschema.get('type') == 'array':
                    clean_path = '.'.join(path).replace('properties.', '')
                    self.table_configs.append({
                        'path': clean_path,
                        'name': clean_path.split('.')[-1],
                        'is_entity': 'items' in subschema and 
                                   'properties' in subschema['items']
                    })
                for k, v in subschema.items():
                    if k == 'properties':
                        find_tables(v, path)
                    else:
                        find_tables(v, path + [k])

        find_tables(schema, [])
        self.table_configs = sorted(self.table_configs, 
                                  key=lambda x: len(x['path'].split('.')))

    def convert_to_relational(self, data):
        """Convert data using schema-guided approach"""
        for config in self.table_configs:
            path = config['path'].split('.')
            current = data
            
            # Safely navigate through the path
            for p in path:
                if isinstance(current, dict):
                    current = current.get(p, {})
                elif isinstance(current, list):
                    # Handle list by processing first element (assuming homogeneous data)
                    if len(current) > 0 and isinstance(current[0], dict):
                        current = current[0].get(p, {})
                    else:
                        current = {}
                        break
                else:
                    current = {}
                    break

            if config['is_entity'] and isinstance(current, list):
                parent_path = '.'.join(path[:-1])
                parent_uid = self.get_parent_uid(parent_path)
                
                for idx, item in enumerate(current):
                    uid = f"{parent_uid}.{idx}" if parent_uid else str(idx)
                    self.store_entity(config['name'], item, uid, parent_uid)

    def store_entity(self, name, data, uid, parent_uid=None):
        """Store normalized entity data"""
        # Base entity fields
        entity_data = {'uid': uid}
        if parent_uid:
            entity_data[f'parent_{name}_uid'] = parent_uid
        
        # Relationships
        if parent_uid:
            parent_entity = parent_uid.split('.')[0]
            self.relationships.append({
                'parent': parent_entity,
                'child': name,
                'foreign_key': f'{parent_entity}_uid'
            })
        
        # Flatten attributes
        for k, v in data.items():
            if not isinstance(v, (dict, list)):
                entity_data[k] = v
            elif isinstance(v, dict):
                # Handle 1:1 relationships
                nested_uid = f"{uid}.{k}"
                entity_data[f'{k}_uid'] = nested_uid
                self.store_entity(k, v, nested_uid, uid)
            elif isinstance(v, list):
                # Handle 1:many relationships
                for i, item in enumerate(v):
                    list_uid = f"{uid}.{k}.{i}"
                    self.store_entity(k, item, list_uid, uid)
        
        self.tables[name].append(entity_data)

    def get_parent_uid(self, path):
        """Generate hierarchical UID based on path"""
        parts = path.split('.')
        uid = []
        for p in parts:
            self.current_ids[p] = self.current_ids.get(p, -1) + 1
            uid.append(str(self.current_ids[p]))
        return '.'.join(uid)

    def structure_output(self):
        """Create final DataFrame structure"""
        structured = {
            'tables': {},
            'relationships': pd.DataFrame(self.relationships).drop_duplicates().to_dict('records')
        }
        
        for name, records in self.tables.items():
            df = pd.DataFrame(records)
            
            # Add auto-increment ID for primary key
            df.insert(0, 'id', range(1, len(df)+1))
            
            # Clean up UID columns
            uid_cols = [c for c in df.columns if 'uid' in c]
            for c in uid_cols:
                if c != 'uid':
                    df = df.drop(c, axis=1)
            
            structured['tables'][name] = df
        
        return structured

def fetch_api_data(api_url):
    """Fetch JSON data from an API endpoint with proper format handling"""
    try:
        # Force JSON response format
        if '?' in api_url:
            api_url += "&format=json"
        else:
            api_url += "?format=json"
        
        response = requests.get(api_url)
        response.raise_for_status()
        
        # Verify content type
        content_type = response.headers.get('Content-Type', '')
        if 'json' not in content_type:
            raise ValueError(f"Unexpected content type: {content_type}")
        
        return response.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"❌ API request failed: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {str(e)}")
        return None

def generate_schema(data):
    """Generate JSON schema from data."""
    builder = SchemaBuilder()
    builder.add_object(data)
    return builder.to_schema()

def validate_data(data, schema):
    """Validate data against schema."""
    try:
        validate(instance=data, schema=schema)
        print("✅ Data validation passed")
        return True
    except ValidationError as e:
        print(f"❌ Validation error: {e.message}")
        return False

def display_results(result):
    """Improved result display"""
    print("\n🏁 Processing Results")
    
    # Show tables
    for name, df in result['tables'].items():
        print(f"\n📦 Table: {name}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Rows: {len(df)}")
        tools.display_dataframe_to_user(name, df.head(3))
    
    # Show relationships
    if result['relationships']:
        print("\n🔗 Relationships:")
        rel_df = pd.DataFrame(result['relationships'])
        # Fallback to simple print if tabulate not available
        try:
            from tabulate import tabulate
            print(tabulate(rel_df[['parent', 'child', 'foreign_key']], 
                         headers='keys', 
                         tablefmt='psql',
                         showindex=False))
        except ImportError:
            print(rel_df[['parent', 'child', 'foreign_key']].to_string(index=False))
    else:
        print("\n⚠️ No relationships found")

# Example test URLs (uncomment to use)
test_urls = [
    "https://data.typeracer.com/games?playerId=tr:barat_paim&universe=play&n=300&beforeId=522.json"
]

# Run test with first URL
if __name__ == "__main__":
    test_url = test_urls[0]  # Change index to test different endpoints
    print(f"\n🚀 Starting test with URL: {test_url}")
    processor = RelationalProcessor()
    result = processor.process_api_response(test_url)
    
    if result:
        display_results(result)
        print("\n✅ Processing completed successfully!")
    else:
        print("\n❌ Processing failed") 