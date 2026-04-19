import sys
import json
import subprocess
import os

def run():
    if len(sys.argv) < 3:
        print("Usage: python run_harvester_with_file.py <script_root_relative_path> <json_file_path>")
        return

    script_path = sys.argv[1]
    json_file = sys.argv[2]

    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = f.read()

    # Pass JSON string as single argument
    subprocess.run(["python", script_path, json_data])

if __name__ == "__main__":
    run()
