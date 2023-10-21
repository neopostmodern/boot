import json
import os
from json import JSONDecodeError

config_file_path = os.path.join(os.path.dirname(__file__), "config.json")


def load_config():
    try:
        with open(config_file_path) as config_json_file:
            global config
            config = json.load(config_json_file)
    except FileNotFoundError as file_not_found_error:
        print(f"Config file {config_file_path} not found:")
        print(file_not_found_error)
    except JSONDecodeError as json_decode_error:
        print(f"Failed to load {config_file_path} due to invalid JSON:")
        print(json_decode_error)
    except Exception as exception:
        print(
            f"Unexpected exception ({type(exception).__name__}) occurred when reading JSON config:"
        )
        print(exception)


config = None
load_config()
if config is None:
    print("")
    print("Config failed to load (see details above), aborting.")
    exit(1)

if __name__ == "__main__":
    print("Dry run to test configuration:")
    print(config)
