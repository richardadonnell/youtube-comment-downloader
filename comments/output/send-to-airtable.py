import json
import os
from datetime import datetime
from typing import Dict, List

import requests

# Constants
AIRTABLE_API_KEY = "pathANodJJYpoWX8J.de32530804bacd1af289d0453ada3d29833daf33d1d6f0e73fefe715cf0ced48"
BASE_ID = "appGGYTvgwHlIlKwT"  
TABLE_ID = "tbl9Kpa81tzFu3DWr"
API_VERSION = "v0"

# Headers with API versioning
headers = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json",
    "User-Agent": "Python/AirtableAPI"
}

def get_base_schema():
    """Get the current base schema including all tables and fields"""
    try:
        schema_url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"
        response = requests.get(schema_url, headers=headers)
        
        print(f"\nAttempting to get schema from: {schema_url}")
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            schema_data = response.json()
            print("\nCurrent base schema:")
            print(json.dumps(schema_data, indent=2))
            return schema_data
        else:
            print(f"Error getting schema: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error getting schema: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None

def get_field_config(field_name: str, field_type: str, options: dict = None) -> dict:
    """Get the appropriate field configuration based on field type"""
    base_config = {
        "name": field_name,
        "type": field_type
    }
    
    # Add type-specific options
    if field_type == "number":
        base_config["options"] = {
            "precision": 0,  # Integer precision
            "format": "integer"  # Format as integer
        }
    elif field_type == "singleSelect" and options and "choices" in options:
        base_config["options"] = options
    elif field_type == "dateTime":
        base_config["options"] = {
            "dateFormat": {"name": "iso", "format": "YYYY-MM-DD"},
            "timeFormat": {"name": "24hour", "format": "HH:mm"},
            "timeZone": "UTC"
        }
    
    return base_config

def create_field(field_name: str, field_type: str, options: dict = None):
    """Create a new field in the table"""
    create_field_url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{TABLE_ID}/fields"
    
    field_config = get_field_config(field_name, field_type, options)
        
    try:
        print(f"\nCreating field: {field_name} ({field_type})")
        print("Field config:")
        print(json.dumps(field_config, indent=2))
        
        response = requests.post(
            create_field_url,
            headers=headers,
            json=field_config
        )
        
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Successfully created field: {field_name}")
            return True
        else:
            print(f"Error creating field: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error creating field: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False

def analyze_schema(schema_data):
    """Analyze the current schema and determine what changes are needed"""
    if not schema_data or 'tables' not in schema_data:
        print("No valid schema data to analyze")
        return
    
    target_table = next((table for table in schema_data['tables'] if table['id'] == TABLE_ID), None)
    
    if not target_table:
        print(f"Table {TABLE_ID} not found in schema")
        return
    
    print("\nCurrent table structure:")
    print(f"Table name: {target_table.get('name', 'Unknown')}")
    print("Fields:")
    for field in target_table.get('fields', []):
        print(f"- {field.get('name', 'Unknown')}: {field.get('type', 'Unknown')}")
    
    required_fields = {
        "Category": ("singleSelect", {
            "choices": [
                {"name": "tutorial_ideas"},
                {"name": "use_cases"},
                {"name": "technical_questions"},
                {"name": "problem_statements"}
            ]
        }),
        "Content": ("multilineText", None),
        "Author": ("singleLineText", None),
        "Votes": ("number", None),
        "Hearted": ("checkbox", None),
        "Has_Replies": ("checkbox", None),
        "Last_Updated": ("dateTime", None)
    }
    
    existing_fields = {field['name']: field['type'] for field in target_table.get('fields', [])}
    missing_fields = {
        name: field_info 
        for name, field_info in required_fields.items() 
        if name not in existing_fields
    }
    
    print("\nMissing fields that need to be added:")
    for name, (field_type, _) in missing_fields.items():
        print(f"- {name} ({field_type})")
    
    return missing_fields

def main():
    print("Getting current base schema...")
    schema_data = get_base_schema()
    
    if schema_data:
        missing_fields = analyze_schema(schema_data)
        
        if missing_fields:
            print("\nWould you like to proceed with creating the missing fields? (y/n): ")
            response = input()
            if response.lower() == 'y':
                success = True
                for field_name, (field_type, options) in missing_fields.items():
                    if not create_field(field_name, field_type, options):
                        success = False
                        print(f"\nFailed to create field: {field_name}")
                        break
                
                if success:
                    print("\nAll fields created successfully!")
                else:
                    print("\nFailed to create all fields.")
        else:
            print("\nTable structure is already correct. Ready to import data.")
    else:
        print("Unable to proceed without schema information")

if __name__ == "__main__":
    main()
