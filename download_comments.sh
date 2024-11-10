#!/bin/bash

# Define the subfolder where comments will be saved
OUTPUT_DIR="comments"

# Create the subfolder if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Activate virtual environment if needed
# source /path/to/your/venv/bin/activate

# Loop through each line (video ID) in video-ids.txt
while IFS= read -r video_id; do
    # Check if video_id is not empty
    if [ -n "$video_id" ]; then
        # Run youtube-comment-downloader for each video ID, sorting by popular and pretty-printing JSON
        youtube-comment-downloader --youtubeid "$video_id" --output "${OUTPUT_DIR}/${video_id}.json" --pretty --sort 0
        echo "Downloaded and formatted popular comments for video ID: $video_id"
    fi
done < video-ids.txt
