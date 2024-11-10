import json
import os
import time
from pathlib import Path
from html import unescape

from openai import OpenAI

# WSL paths for JSON input files and output directory
json_directory = r'\\wsl.localhost\Ubuntu\home\richa\youtube-comment-downloader\youtube-comment-downloader\comments'
output_directory = r'\\wsl.localhost\Ubuntu\home\richa\youtube-comment-downloader\youtube-comment-downloader\comments\output'

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

def validate_json_structure(json_obj):
    """Enhanced validation of JSON structure and content"""
    expected_keys = ["tutorial_ideas", "use_cases", "technical_questions", "problem_statements"]
    
    # Basic structure validation
    if not all(key in json_obj for key in expected_keys):
        return False
    
    # Validate each array
    for key in expected_keys:
        # Check if it's an array
        if not isinstance(json_obj[key], list):
            return False
        
        # Check each item in the array
        for item in json_obj[key]:
            # Must be a dictionary with all required fields
            if not isinstance(item, dict):
                return False
            if not all(k in item for k in ["content", "author", "votes", "hearted", "has_replies"]):
                return False
            # Type validation for each field
            if not isinstance(item["content"], str):
                return False
            if not isinstance(item["author"], str):
                return False
            if not isinstance(item["votes"], (int, float)):
                return False
            if not isinstance(item["hearted"], bool):
                return False
            if not isinstance(item["has_replies"], bool):
                return False
            # Content must not be empty
            if not item["content"].strip():
                return False
            # Must be a reasonable length
            if len(item["content"]) < 10 or len(item["content"]) > 500:
                return False
            # Must not contain placeholder-like text
            placeholder_indicators = ['example', 'placeholder', 'idea1', 'use case1', 'question1']
            if any(indicator in item["content"].lower() for indicator in placeholder_indicators):
                return False
    
    return True

def clean_model_output(output):
    """Clean the model output by removing markdown formatting and extracting JSON"""
    output = output.strip()
    
    # Remove markdown code block formatting if present
    if output.startswith('```'):
        # Find the first { and last }
        start_idx = output.find('{')
        end_idx = output.rfind('}')
        if start_idx != -1 and end_idx != -1:
            output = output[start_idx:end_idx + 1]
    
    return output.strip()

def is_valid_json_response(output):
    """Check if the output can be parsed as valid JSON with the expected structure"""
    output = clean_model_output(output)
    if not (output.startswith('{') and output.endswith('}')):
        return False
    try:
        json_obj = json.loads(output)
        return validate_json_structure(json_obj)
    except json.JSONDecodeError:
        return False

def load_config():
    """Load configuration from config.json file"""
    config_path = Path(__file__).parent / 'config.json'
    if not config_path.exists():
        # Create default config file if it doesn't exist
        default_config = {
            "openai_api_key": "your-api-key-here"
        }
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
        print(f"Please edit {config_path} and add your OpenAI API key")
        exit(1)
    
    with open(config_path) as f:
        config = json.load(f)
    return config

def clean_text(text):
    """Clean and normalize text content"""
    if not isinstance(text, str):
        return ""
    
    # Unescape HTML entities
    text = unescape(text)
    
    # Replace common Unicode quotes with standard quotes
    text = text.replace('\u2018', "'")  # Left single quote
    text = text.replace('\u2019', "'")  # Right single quote
    text = text.replace('\u201C', '"')  # Left double quote
    text = text.replace('\u201D', '"')  # Right double quote
    
    # Replace other common Unicode characters
    text = text.replace('\u2013', '-')  # En dash
    text = text.replace('\u2014', '-')  # Em dash
    text = text.replace('\u2026', '...') # Ellipsis
    
    return text.strip()

def process_with_openai(content, max_retries=3):
    config = load_config()
    client = OpenAI(api_key=config['openai_api_key'])
    
    # Read prompt from file
    prompt_path = Path(__file__).parent / 'prompt.txt'
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt = f.read()
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ],
                temperature=0.1,
                max_tokens=16384
            )
            
            output = response.choices[0].message.content
            
            # Validate and sort the response
            try:
                json_obj = json.loads(output)
                if validate_json_structure(json_obj):
                    # Clean text content in each category
                    for category in json_obj:
                        for item in json_obj[category]:
                            item["content"] = clean_text(item["content"])
                    
                    # Sort each category by votes
                    for category in json_obj:
                        json_obj[category].sort(key=lambda x: x["votes"], reverse=True)
                    
                    return json.dumps(json_obj, ensure_ascii=False)
                else:
                    print(f"Invalid JSON structure (attempt {attempt + 1})")
                    continue
            except json.JSONDecodeError as e:
                print(f"JSON parsing error (attempt {attempt + 1}): {str(e)}")
                continue

        except Exception as e:
            print(f"OpenAI API error (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))
            continue
    
    return json.dumps({
        "tutorial_ideas": [],
        "use_cases": [],
        "technical_questions": [],
        "problem_statements": []
    }, ensure_ascii=False)

# Process files with delay to prevent overload
for filename in os.listdir(json_directory):
    if filename.endswith('.json'):
        try:
            file_path = os.path.join(json_directory, filename)
            print(f"\nProcessing {filename}...")
            
            # Load JSON content
            with open(file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
            
            # Extract comments with text and author
            comments_data = []
            for comment in json_data.get("comments", []):
                comments_data.append({
                    "text": clean_text(comment['text']),
                    "author": comment['author'],
                    "votes": comment.get('votes', '0'),
                    "heart": comment.get('heart', False),
                    "replies": bool(comment.get('replies', ''))
                })
            
            # Convert to formatted string for OpenAI
            comments_text = "\n\n".join(
                f"Comment by {c['author']}:\n{c['text']}\nVotes: {c['votes']}\nHearted: {c['heart']}\nHas replies: {c['replies']}"
                for c in comments_data
            )
            
            # Process with OpenAI
            openai_output = process_with_openai(comments_text)
            
            # Parse the output to check if all arrays are empty
            processed_data = json.loads(openai_output)
            if all(len(processed_data[key]) == 0 for key in processed_data):
                print(f"Skipping {filename} - no relevant content found")
                continue
            
            # Save results only if there's relevant content
            output_path = os.path.join(output_directory, f'processed_{filename}')
            with open(output_path, 'w', encoding='utf-8') as output_file:
                json.dump(processed_data, output_file, indent=4, ensure_ascii=False)
            
            print(f"Successfully processed {filename}")
            
            # Add a small delay between files to prevent rate limiting
            time.sleep(2)
            
        except Exception as e:
            print(f"Error processing file {filename}: {str(e)}")
            continue
