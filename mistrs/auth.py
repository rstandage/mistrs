import json, requests
from typing import Dict
from pathlib import Path
from prettytable import PrettyTable



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

def get_credentials(environment: str = None, interactive: bool = True, one_time_token: bool = False) -> Dict[str, str]:
    """
    Get API credentials from the environment file. Files are stored in .mistrs file at user home

    Args:
        environment (str, optional): Environment name ('emea01', 'global01', etc.)
        interactive (bool): If True, allows user input for missing credentials.
        one_time_token (bool): If True, handles one-time org token flow

    Returns:
        dict: Dictionary containing 'api_url', 'api_token', and 'org_id' (for one-time tokens)
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

    # Handle one-time token flow
    if one_time_token:
        print(f"\nUsing one-time token for {ENVIRONMENTS[environment]['name']}")
        print(f"API URL: {ENVIRONMENTS[environment]['api_url']}")

        while True:
            api_token = input("Enter one-time org token: ").strip()
            if api_token:
                break
            print("Token cannot be empty. Please try again.")

        # Validate the token
        credentials = {
            "api_token": api_token,
            "api_url": ENVIRONMENTS[environment]['api_url']
        }

        try:
            user_info = validate_credentials(credentials['api_url'], credentials['api_token'])
            display_user_info(user_info)

            # Add org_id to credentials
            if user_info.get('privileges'):
                org_privilege = user_info['privileges'][0]  # Get first privilege
                credentials.update({
                    "org_id": org_privilege.get('org_id'),
                    "org_name": org_privilege.get('name')
                })

            # Ask if user wants to store the token
            if interactive:
                store = input("\nWould you like to store this token? (yes/no): ").lower().strip()
                if store in ['y', 'yes']:
                    org_name = credentials['org_name']
                    env_file = config_dir / f"{environment}_{org_name}.env"
                    env_file.write_text(json.dumps(credentials, indent=4))
                    print(f"Credentials saved at: {env_file}")

            return credentials
        except Exception as e:
            raise ValueError(f"Failed to validate one-time token: {str(e)}")

    # Try to load existing credentials
    try:
        if env_file.exists():
            data = json.loads(env_file.read_text())
            if all(key in data for key in ["api_token", "api_url"]):
                # Validate existing credentials
                try:
                    user_info = validate_credentials(data['api_url'], data['api_token'])
                    display_user_info(user_info)
                    # Update org_id if it exists in the response
                    if user_info.get('privileges'):
                        org_privilege = user_info['privileges'][0]
                        data.update({
                            "org_id": org_privilege.get('org_id'),
                            "org_name": org_privilege.get('name')
                        })
                        # Update the stored file with org_id
                        env_file.write_text(json.dumps(data, indent=4))
                    return data
                except ValueError:
                    if not interactive:
                        raise
                    print("Stored credentials are invalid. Please enter new credentials.")
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

    # Create credentials dictionary
    credentials = {
        "api_token": api_token,
        "api_url": ENVIRONMENTS[environment]['api_url']
    }

    # Validate new credentials
    try:
        user_info = validate_credentials(credentials['api_url'], credentials['api_token'])
        display_user_info(user_info)

        # Add org_id to credentials if available
        if user_info.get('privileges'):
            org_privilege = user_info['privileges'][0]
            credentials.update({
                "org_id": org_privilege.get('org_id'),
                "org_name": org_privilege.get('name')
            })

        # Save credentials
        env_file.write_text(json.dumps(credentials, indent=4))
        print(f"Credentials saved at: {env_file}")
    except Exception as e:
        raise Exception(f"Failed to validate or save credentials: {str(e)}")

    return credentials

# Example usage
if __name__ == "__main__":
    try:
        # For regular token
        credentials = get_credentials()
        print("\nCredentials retrieved successfully!")
        print(f"API URL: {credentials['api_url']}")
        print(f"API Token: {'*' * len(credentials['api_token'])}")
        if 'org_id' in credentials:
            print(f"Organization ID: {credentials['org_id']}")
            print(f"Organization Name: {credentials['org_name']}")

        # For one-time token
        # credentials = get_credentials(one_time_token=True)

    except Exception as e:
        print(f"Error: {e}")

