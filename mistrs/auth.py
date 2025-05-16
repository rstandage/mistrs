import json
import requests
from typing import Dict, List
from pathlib import Path
from prettytable import PrettyTable
from datetime import datetime
import re

# Define available environments with their corresponding API URLs at module level
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

def get_headers(token):
    '''
    This will build the required headers for API interation.
    example usage once credentials are obtained:
    headers = get_headers(credentials["api_token"])
    '''
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {token}'
    }
    return headers

def validate_credentials(api_url: str, api_token: str) -> Dict:
    """
    Validate credentials by making a request to the /self endpoint
    Args:
        api_url (str): API URL
        api_token (str): API token
    Returns:
        dict: User information if successful
    """
    try:
        headers = {'Authorization': f'Token {api_token}'}
        response = requests.get(f"{api_url.rstrip('/')}/self", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to validate credentials: {str(e)}")

def display_user_info(user_data: Dict):
    """
    Display user information using PrettyTable
    Args:
        user_data (dict): User information from /self endpoint
    """
    table = PrettyTable()
    table.field_names = ["Key Name", "Organization", "Role", "Org ID"]
    for privilege in user_data.get('privileges', []):
        table.add_row([
            user_data.get('name', 'N/A'),
            privilege.get('name', 'N/A'),
            privilege.get('role', 'N/A'),
            privilege.get('org_id', 'N/A')
        ])
    print("\nUser Information:")
    print(table)

def get_existing_tokens(config_dir: Path, token_type: str = "otp") -> List[Dict]:
    """
    Get list of existing tokens and their details
    Args:
        config_dir (Path): Directory containing token files
        token_type (str): Type of token to look for ("otp" or "regular")
    Returns:
        list: List of dictionaries containing token details
    """
    tokens = []
    pattern = "*_otp.env" if token_type == "otp" else "*.env"
    for file in config_dir.glob(pattern):
        # Skip regular env files when looking for OTP tokens
        if token_type == "otp" and not file.name.endswith("_otp.env"):
            continue
        # Skip OTP env files when looking for regular tokens
        if token_type == "regular" and file.name.endswith("_otp.env"):
            continue

        try:
            data = json.loads(file.read_text())
            if all(key in data for key in ["api_token", "api_url"]):
                tokens.append({
                    "filename": file.name,
                    "org_name": data.get("org_name", "N/A"),
                    "api_url": data["api_url"],
                    "environment": data.get("environment", "Unknown"),
                    "created": data.get("created", "Unknown")
                })
        except Exception:
            continue
    return tokens

def get_credentials(environment: str = None, interactive: bool = True, otp: bool = False) -> Dict[str, str]:
    """
    Get API credentials from the environment file. Files are stored in .mistrs file at user home

    Args:
        environment (str, optional): Environment name ('emea01', 'global01', etc.)
        interactive (bool): If True, allows user input for missing credentials.
        otp (bool): If True, handles OTP/one-time token flow

    Returns:
        dict: Dictionary containing 'api_url', 'api_token', and additional metadata
    """
    # Set up paths
    config_dir = Path.home() / ".mistrs"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Validate environment if provided
    if environment and environment.lower() not in ENVIRONMENTS:
        raise ValueError(f"Invalid environment. Choose from: {', '.join(ENVIRONMENTS.keys())}")

    # Handle OTP/one-time token flow
    if otp and interactive:
        existing_tokens = get_existing_tokens(config_dir, "otp")

        # Display existing OTP tokens
        if existing_tokens:
            print("\nExisting OTP tokens:")
            table = PrettyTable()
            table.field_names = ["#", "Organization", "Environment", "Created"]
            for i, token in enumerate(existing_tokens, 1):
                table.add_row([
                    i,
                    token['org_name'],
                    token['environment'],
                    token['created']
                ])
            print(table)

        # Display options
        print("\nOptions:")
        print("0. Create new OTP token")
        if existing_tokens:
            print(f"1-{len(existing_tokens)}: Use existing token")

        while True:
            try:
                selection = int(input("\nSelect option: "))
                if selection == 0:
                    # Environment selection if not provided
                    if not environment:
                        print("\nAvailable environments:")
                        for i, (env_key, env_data) in enumerate(ENVIRONMENTS.items(), 1):
                            print(f"{i}. {env_data['name']}")
                            print(f"   API: {env_data['api_url']}")

                        while True:
                            try:
                                env_selection = int(input("\nSelect environment number: "))
                                if 1 <= env_selection <= len(ENVIRONMENTS):
                                    environment = list(ENVIRONMENTS.keys())[env_selection - 1]
                                    break
                                print("Invalid selection. Please try again.")
                            except ValueError:
                                print("Invalid input. Please enter a number.")

                    print(f"\nCreating new OTP token for {ENVIRONMENTS[environment]['name']}")
                    print(f"API URL: {ENVIRONMENTS[environment]['api_url']}")

                    # Get token and validate
                    while True:
                        api_token = input("Enter OTP token: ").strip()
                        if api_token:
                            break
                        print("Token cannot be empty. Please try again.")

                    credentials = {
                        "api_token": api_token,
                        "api_url": ENVIRONMENTS[environment]['api_url'],
                        "environment": environment,
                        "created": datetime.now().isoformat()
                    }

                    # Validate and get org info
                    try:
                        user_info = validate_credentials(credentials['api_url'], credentials['api_token'])
                        display_user_info(user_info)

                        if user_info.get('privileges'):
                            org_privilege = user_info['privileges'][0]
                            credentials.update({
                                "org_id": org_privilege.get('org_id'),
                                "org_name": org_privilege.get('name')
                            })

                        # Ask if user wants to store the token
                        store = input("\nWould you like to store this token? (yes/no): ").lower().strip()
                        if store in ['y', 'yes']:
                            safe_org_name = re.sub(r'[^a-zA-Z0-9]', '_', credentials['org_name'].lower())
                            env_file = config_dir / f"{safe_org_name}_{environment}_otp.env"
                            env_file.write_text(json.dumps(credentials, indent=4))
                            print(f"OTP token saved at: {env_file}")

                        return credentials

                    except Exception as e:
                        raise ValueError(f"Failed to validate OTP token: {str(e)}")

                elif 1 <= selection <= len(existing_tokens):
                    # Use existing token
                    selected_token = existing_tokens[selection - 1]
                    env_file = config_dir / selected_token["filename"]
                    credentials = json.loads(env_file.read_text())

                    # Validate existing token
                    try:
                        user_info = validate_credentials(credentials['api_url'], credentials['api_token'])
                        display_user_info(user_info)
                        return credentials
                    except ValueError as e:
                        print(f"Token validation failed: {e}")
                        print("Please create a new token.")
                        continue

                print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    # Handle regular token flow
    if not otp:
        # Interactive environment selection if not specified
        if not environment and interactive:
            print("\nAvailable environments:")
            for i, (env_key, env_data) in enumerate(ENVIRONMENTS.items(), 1):
                env_file = config_dir / f"{env_key}.env"
                status = "✓" if env_file.exists() else "✗"
                print(f"{i}. {env_data['name']} [{status}]")
                print(f"   API: {env_data['api_url']}")

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
                    # Validate existing credentials
                    try:
                        user_info = validate_credentials(data['api_url'], data['api_token'])
                        display_user_info(user_info)
                        return data
                    except ValueError:
                        if not interactive:
                            raise
                        print("Stored credentials are invalid. Please enter new credentials.")
        except Exception as e:
            if not interactive:
                raise Exception(f"Failed to load credentials: {str(e)}")

        # Interactive credential creation
        print(f"\nCreating/Updating credentials for {ENVIRONMENTS[environment]['name']}")
        print(f"API URL: {ENVIRONMENTS[environment]['api_url']}")

        while True:
            api_token = input("Enter API token: ").strip()
            if api_token:
                break
            print("API token cannot be empty. Please try again.")

        credentials = {
            "api_token": api_token,
            "api_url": ENVIRONMENTS[environment]['api_url']
        }

        # Validate and save credentials
        try:
            user_info = validate_credentials(credentials['api_url'], credentials['api_token'])
            display_user_info(user_info)

            env_file.write_text(json.dumps(credentials, indent=4))
            print(f"Credentials saved at: {env_file}")

        except Exception as e:
            raise Exception(f"Failed to validate or save credentials: {str(e)}")

        return credentials

# Example usage
if __name__ == "__main__":
    try:
        # For OTP/one-time token
        credentials = get_credentials(otp=True)

        # For regular token
        # credentials = get_credentials()

        print("\nCredentials retrieved successfully!")
        print(f"API URL: {credentials['api_url']}")
        print(f"API Token: {'*' * len(credentials['api_token'])}")
        if 'org_id' in credentials:
            print(f"Organization ID: {credentials['org_id']}")
            print(f"Organization Name: {credentials['org_name']}")

    except Exception as e:
        print(f"Error: {e}")