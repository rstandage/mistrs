import json
from typing import Dict
from pathlib import Path

def get_credentials(environment: str = None, interactive: bool = True) -> Dict[str, str]:
    """
    Get API credentials from the environment file.

    Args:
        environment (str, optional): Environment name ('emea01', 'global01', etc.)
        interactive (bool): If True, allows user input for missing credentials.

    Returns:
        dict: Dictionary containing 'api_url' and 'api_token'
    """
    # Define available environments with their corresponding API URLs
    ENVIRONMENTS = {
        'global01': {
            'name': 'Mist Global 01',
            'api_url': 'https://api.mist.com/api/v1/'
        },
        'global02': {
            'name': 'Mist Global 02',
            'api_url': 'https://api.gc1.mist.com/api/v1/'
        },
        'global03': {
            'name': 'Mist Global 03',
            'api_url': 'https://api.ac2.mist.com/api/v1/'
        },
        'global04': {
            'name': 'Mist Global 04',
            'api_url': 'https://api.gc2.mist.com/api/v1/'
        },
        'global05': {
            'name': 'Mist Global 05',
            'api_url': 'https://api.gc4.mist.com/api/v1/'
        },
        'emea01': {
            'name': 'Mist EMEA 01',
            'api_url': 'https://api.eu.mist.com/api/v1/'
        },
        'emea02': {
            'name': 'Mist EMEA 02',
            'api_url': 'https://api.gc3.mist.com/api/v1/'
        },
        'emea03': {
            'name': 'Mist EMEA 03',
            'api_url': 'https://api.ac6.mist.com/api/v1/'
        },
        'apac01': {
            'name': 'Mist APAC 01',
            'api_url': 'https://api.ac5.mist.com/api/v1/'
        }
    }

    # Validate environment if provided
    if environment and environment.lower() not in ENVIRONMENTS:
        raise ValueError(f"Invalid environment. Choose from: {', '.join(ENVIRONMENTS.keys())}")

    # Set up paths
    config_dir = Path.home() / ".mistrs"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Interactive environment selection if not specified
    if not environment and interactive:
        print("\nAvailable environments:")
        for i, (env_key, env_data) in enumerate(ENVIRONMENTS.items(), 1):
            env_file = config_dir / f"{env_key}.env"
            status = "✓" if env_file.exists() else "✗"
            print(f"{i}. {env_data['name']} [{status}]")

        while True:
            try:
                selection = int(input("\nSelect environment number: "))
                if 1 <= selection <= len(ENVIRONMENTS):
                    environment = list(ENVIRONMENTS.keys())[selection - 1]
                    break
                print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")
    elif not environment and not interactive:
        raise ValueError("Environment must be specified when interactive mode is False")

    env_file = config_dir / f"{environment}.env"

    # Try to load existing credentials
    try:
        if env_file.exists():
            data = json.loads(env_file.read_text())
            if all(key in data for key in ["api_token", "api_url"]):
                return data
    except Exception as e:
        if not interactive:
            raise Exception(f"Failed to load credentials: {str(e)}")

    # If we reach here and interactive is False, raise an exception
    if not interactive:
        raise ValueError(f"No valid credentials found for environment: {environment}")

    # Interactive credential creation
    print(f"\nCreating/Updating credentials for {ENVIRONMENTS[environment]['name']}")
    print(f"API URL: {ENVIRONMENTS[environment]['api_url']}")

    while True:
        api_token = input("Enter API token: ").strip()
        if api_token:
            break
        print("API token cannot be empty. Please try again.")

    # Save credentials
    credentials = {
        "api_token": api_token,
        "api_url": ENVIRONMENTS[environment]['api_url']
    }

    try:
        env_file.write_text(json.dumps(credentials, indent=4))
        print(f"Credentials saved at: {env_file}")
    except Exception as e:
        raise Exception(f"Failed to save credentials: {str(e)}")

    return credentials

# Example usage
if __name__ == "__main__":
    try:
        # This will show an interactive menu to select environment
        credentials = get_credentials()

        print("\nCredentials retrieved successfully!")
        print(f"API URL: {credentials['api_url']}")
        print(f"API Token: {'*' * len(credentials['api_token'])}")

    except Exception as e:
        print(f"Error: {e}")


def get_headers(token):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {token}'
    }
    return headers