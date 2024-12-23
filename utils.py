import json

def load_json(filename):
    """Load JSON data from a file."""
    with open(filename, "r") as file:
        return json.load(file)

def save_json(data, filename):
    """Save data to a JSON file."""
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
