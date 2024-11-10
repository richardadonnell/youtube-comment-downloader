import glob
import json
import os


def combine_json_files():
    # Initialize the combined structure
    combined_data = {
        "tutorial_ideas": [],
        "use_cases": [],
        "technical_questions": [],
        "problem_statements": []
    }
    
    # Get all JSON files in the current directory
    json_files = glob.glob("*.json")
    
    # Process each JSON file
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                # Combine each category
                for category in combined_data.keys():
                    if category in data:
                        combined_data[category].extend(data[category])
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    # Sort each category by votes (highest to lowest)
    for category in combined_data.keys():
        combined_data[category] = sorted(
            combined_data[category],
            key=lambda x: (x.get('votes', 0), x.get('hearted', False)),
            reverse=True
        )
    
    # Save the combined data to a new JSON file
    output_file = "combined_comments.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=4, ensure_ascii=False)
    
    print(f"Successfully combined {len(json_files)} files into {output_file}")

if __name__ == "__main__":
    combine_json_files()
