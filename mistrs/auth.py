import json
import requests
from typing import Dict, List
from pathlib import Path
from prettytable import PrettyTable
from datetime import datetime
import re

# Available Mist cloud environments
ENVIRONMENTS = {
    'global01': {'name': 'Mist Global 01', 'api_url': 'https://api.mist.com/api/v1/'},
    'global02': {'name': 'Mist Global 02', 'api_url': 'https://api.gc1.mist.com/api/v1/'},
    'global03': {'name': 'Mist Global 03', 'api_url': 'https://api.ac2.mist.com/api/v1/'},
    'global04': {'name': 'Mist Global 04', 'api_url': 'https://api.gc2.mist.com/api/v1/'},
    'global05': {'name': 'Mist Global 05', 'api_url': 'https://api.gc4.mist.com/api/v1/'},
    'emea01':   {'name': 'Mist EMEA 01',   'api_url': 'https://api.eu.mist.com/api/v1/'},
    'emea02':   {'name': 'Mist EMEA 02',   'api_url': 'https://api.gc3.mist.com/api/v1/'},
    'emea03':   {'name': 'Mist EMEA 03',   'api_url': 'https://api.ac6.mist.com/api/v1/'},
    'apac01':   {'name': 'Mist APAC 01',   'api_url': 'https://api.ac5.mist.com/api/v1/'},
}


def get_headers(token: str) -> Dict:
    """Build standard Mist API request headers from a token.

    Args:
        token (str): API token (from credentials dict or org token)

    Returns:
        dict: Headers ready to pass to any api.py function
    """
    return {
        'Content-Type': 'application/json',
        'Authorization': f'Token {token}'
    }


def validate_credentials(api_url: str, api_token: str) -> Dict:
    """Validate an API token against the /self endpoint.

    Args:
        api_url (str): Base API URL (e.g. 'https://api.mist.com/api/v1/')
        api_token (str): API token to validate

    Returns:
        dict: User/org data from /self if valid

    Raises:
        ValueError: If the token is invalid or the request fails
    """
    try:
        headers = get_headers(api_token)
        response = requests.get(f"{api_url.rstrip('/')}/self", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to validate credentials: {e}")


def display_user_info(user_data: Dict):
    """Print a PrettyTable of the authenticated user's org privileges.

    Args:
        user_data (dict): Response from /self endpoint
    """
    table = PrettyTable()
    table.field_names = ["Name", "Organization", "Role", "Org ID"]
    for privilege in user_data.get('privileges', []):
        table.add_row([
            user_data.get('name', 'N/A'),
            privilege.get('name', 'N/A'),
            privilege.get('role', 'N/A'),
            privilege.get('org_id', 'N/A')
        ])
    print("\nAuthenticated User:")
    print(table)


def _get_existing_tokens(config_dir: Path, token_type: str = "org_token") -> List[Dict]:
    """List stored credential files from ~/.mistrs/

    Args:
        config_dir (Path): The ~/.mistrs directory
        token_type (str): 'org_token' for *_org.env files, 'regular' for *.env files

    Returns:
        list: Token metadata dicts (filename, org_name, api_url, environment, created)
    """
    tokens = []
    pattern = "*_org.env" if token_type == "org_token" else "*.env"
    for file in config_dir.glob(pattern):
        if token_type == "org_token" and not file.name.endswith("_org.env"):
            continue
        if token_type == "regular" and file.name.endswith("_org.env"):
            continue
        try:
            data = json.loads(file.read_text())
            if all(k in data for k in ("api_token", "api_url")):
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


def _select_environment() -> str:
    """Interactively prompt the user to choose a Mist environment.

    Returns:
        str: Environment key (e.g. 'emea01')
    """
    print("\nAvailable environments:")
    env_keys = list(ENVIRONMENTS.keys())
    for i, key in enumerate(env_keys, 1):
        env = ENVIRONMENTS[key]
        print(f"  {i}. {env['name']}  ({env['api_url']})")
    while True:
        try:
            sel = int(input("\nSelect environment number: "))
            if 1 <= sel <= len(env_keys):
                return env_keys[sel - 1]
            print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")


def _org_token_interactive(config_dir: Path, environment: str) -> Dict:
    """Interactive flow: select or create an org token.

    Args:
        config_dir (Path): ~/.mistrs directory
        environment (str): Pre-selected environment key, or None to prompt

    Returns:
        dict: Credentials dict (api_token, api_url, environment, org_id, org_name, created)
    """
    existing = _get_existing_tokens(config_dir, "org_token")

    if existing:
        print("\nStored org tokens:")
        table = PrettyTable()
        table.field_names = ["#", "Organization", "Environment", "Created"]
        for i, t in enumerate(existing, 1):
            table.add_row([i, t['org_name'], t['environment'], t['created']])
        print(table)

    print("\nOptions:")
    print("  0. Create / enter new org token")
    if existing:
        print(f"  1-{len(existing)}. Use stored token")

    while True:
        try:
            selection = int(input("\nSelect option: "))
        except ValueError:
            print("Please enter a number.")
            continue

        if selection == 0:
            # New org token
            if not environment:
                environment = _select_environment()

            print(f"\nEnvironment: {ENVIRONMENTS[environment]['name']}")
            print(f"API URL:     {ENVIRONMENTS[environment]['api_url']}")

            while True:
                api_token = input("Enter org token: ").strip()
                if api_token:
                    break
                print("Token cannot be empty.")

            credentials = {
                "api_token": api_token,
                "api_url": ENVIRONMENTS[environment]['api_url'],
                "environment": environment,
                "created": datetime.now().isoformat()
            }

            user_info = validate_credentials(credentials['api_url'], credentials['api_token'])
            display_user_info(user_info)

            if user_info.get('privileges'):
                priv = user_info['privileges'][0]
                credentials.update({
                    "org_id": priv.get('org_id'),
                    "org_name": priv.get('name')
                })

            store = input("\nStore this token for future use? (y/n): ").lower().strip()
            if store in ('y', 'yes'):
                safe_name = re.sub(r'[^a-zA-Z0-9]', '_', credentials.get('org_name', 'unknown').lower())
                env_file = config_dir / f"{safe_name}_{environment}_org.env"
                env_file.write_text(json.dumps(credentials, indent=4))
                print(f"Token saved: {env_file}")

            return credentials

        elif 1 <= selection <= len(existing):
            selected = existing[selection - 1]
            env_file = config_dir / selected["filename"]
            credentials = json.loads(env_file.read_text())
            user_info = validate_credentials(credentials['api_url'], credentials['api_token'])
            display_user_info(user_info)
            return credentials

        print("Invalid selection.")


def _org_token_non_interactive(config_dir: Path, environment: str) -> Dict:
    """Non-interactive flow: load and validate a stored org token.

    Args:
        config_dir (Path): ~/.mistrs directory
        environment (str): Environment key to match stored token against

    Returns:
        dict: Credentials dict

    Raises:
        ValueError: If no matching stored token exists or validation fails
    """
    existing = _get_existing_tokens(config_dir, "org_token")
    matches = [t for t in existing if t['environment'] == environment]
    if not matches:
        raise ValueError(
            f"No stored org token for environment '{environment}'. "
            "Run interactively first to store a token."
        )
    env_file = config_dir / matches[0]["filename"]
    credentials = json.loads(env_file.read_text())
    user_info = validate_credentials(credentials['api_url'], credentials['api_token'])
    display_user_info(user_info)
    return credentials


def _regular_token_interactive(config_dir: Path, environment: str) -> Dict:
    """Interactive flow for a regular (non-org) API token.

    Args:
        config_dir (Path): ~/.mistrs directory
        environment (str): Pre-selected environment key, or None to prompt

    Returns:
        dict: Credentials dict (api_token, api_url)
    """
    if not environment:
        environment = _select_environment()

    env_file = config_dir / f"{environment}.env"

    # Try stored credentials first
    if env_file.exists():
        try:
            data = json.loads(env_file.read_text())
            if all(k in data for k in ("api_token", "api_url")):
                user_info = validate_credentials(data['api_url'], data['api_token'])
                display_user_info(user_info)
                return data
        except ValueError:
            print("Stored credentials are invalid. Please enter new ones.")

    print(f"\nEnvironment: {ENVIRONMENTS[environment]['name']}")
    print(f"API URL:     {ENVIRONMENTS[environment]['api_url']}")

    while True:
        api_token = input("Enter API token: ").strip()
        if api_token:
            break
        print("Token cannot be empty.")

    credentials = {
        "api_token": api_token,
        "api_url": ENVIRONMENTS[environment]['api_url']
    }

    user_info = validate_credentials(credentials['api_url'], credentials['api_token'])
    display_user_info(user_info)
    env_file.write_text(json.dumps(credentials, indent=4))
    print(f"Credentials saved: {env_file}")

    return credentials


def _regular_token_non_interactive(config_dir: Path, environment: str) -> Dict:
    """Non-interactive flow for a regular API token.

    Args:
        config_dir (Path): ~/.mistrs directory
        environment (str): Environment key

    Returns:
        dict: Credentials dict

    Raises:
        ValueError: If no stored credentials exist or validation fails
    """
    env_file = config_dir / f"{environment}.env"
    if not env_file.exists():
        raise ValueError(
            f"No stored credentials for environment '{environment}'. "
            "Run interactively first."
        )
    data = json.loads(env_file.read_text())
    user_info = validate_credentials(data['api_url'], data['api_token'])
    display_user_info(user_info)
    return data


def get_credentials(
    environment: str = None,
    interactive: bool = True,
    org_token: bool = True,
    otp: bool = None
) -> Dict:
    """Authenticate to the Mist API and return a credentials dict.

    Credentials are stored in ~/.mistrs/ and re-used on subsequent calls.
    The returned dict includes a pre-built 'headers' key so you can pass
    it directly into an APIConfig dataclass without calling get_headers() separately.

    Args:
        environment (str, optional): Environment key ('emea01', 'global01', etc.).
            Required for non-interactive mode.
        interactive (bool): Prompt the user if no stored credentials exist (default: True).
        org_token (bool): Use org-level token flow, recommended (default: True).
        otp (bool): Deprecated alias for org_token; kept for backward compatibility.

    Returns:
        dict: {
            'api_token': str,
            'api_url': str,
            'environment': str,
            'org_id': str,       # org_token flow only
            'org_name': str,     # org_token flow only
            'created': str,      # org_token flow only
            'headers': dict      # pre-built for immediate use in API calls
        }

    Raises:
        ValueError: If environment is invalid, or non-interactive with no stored token.
    """
    config_dir = Path.home() / ".mistrs"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Backward compatibility: otp param overrides org_token when supplied
    use_org_token = org_token if otp is None else otp

    if environment and environment.lower() not in ENVIRONMENTS:
        raise ValueError(f"Invalid environment. Choose from: {', '.join(ENVIRONMENTS.keys())}")

    if use_org_token:
        if interactive:
            credentials = _org_token_interactive(config_dir, environment)
        else:
            if not environment:
                raise ValueError("'environment' is required for non-interactive org token auth.")
            credentials = _org_token_non_interactive(config_dir, environment)
    else:
        if interactive:
            credentials = _regular_token_interactive(config_dir, environment)
        else:
            if not environment:
                raise ValueError("'environment' is required for non-interactive auth.")
            credentials = _regular_token_non_interactive(config_dir, environment)

    # Attach pre-built headers so scripts don't need a separate get_headers() call
    credentials['headers'] = get_headers(credentials['api_token'])
    return credentials


if __name__ == "__main__":
    try:
        creds = get_credentials()
        print("\nCredentials retrieved successfully!")
        print(f"API URL: {creds['api_url']}")
        print(f"Token:   {'*' * len(creds['api_token'])}")
        if 'org_id' in creds:
            print(f"Org:     {creds['org_name']} ({creds['org_id']})")
    except Exception as e:
        print(f"Error: {e}")
