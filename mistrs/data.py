import json
import pandas as pd
from prettytable import PrettyTable
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime

def jprint(data):
    #Prints JSON in an easy to ready format
    print(json.dumps(data, indent=2, sort_keys=True))

def read_xlsx(file):
    #convert xlsx into an array
    df = pd.read_excel(file)
    result = df.to_json(orient="records")
    parsed = json.loads(result)
    return parsed

def create_xlsx(data, file):
    # creates an xlsx file from an array
    df = pd.DataFrame(data)
    df.to_excel(file, index=False)

def read_csv(file):
    #convert csv into an array
    df = pd.read_csv(file)
    result = df.to_json(orient="records")
    parsed = json.loads(result)
    return parsed

def create_csv(data, file):
    # creates a csv file from an array
    df = pd.DataFrame(data)
    df.to_csv(file, index=False)

def list_ids(data):
    #creates a list of IDs to iterate over
    result = [item['id'] for item in data]
    return result


def print_table(array, headers=None):
    '''
    Create PrettyTable object and return
    example usage print(print_table(data))
    '''
    table = PrettyTable()
    single_column_header = 'value'
    try:
        # Check if the array is a list of dictionaries
        if isinstance(array[0], dict):
            # Use dictionary keys as headers if no headers are provided
            if headers:
                table.field_names = headers
            else:
                table.field_names = list(array[0].keys())
            # Add rows using dictionary values
            for row in array:
                table.add_row([row.get(key, '') for key in table.field_names])
        # Check if the array is a 2D array (list of lists/tuples)
        elif isinstance(array[0], (list, tuple)) and not isinstance(array[0], str):
            if headers:
                table.field_names = headers
            else:
                table.field_names = [f'Column {i+1}' for i in range(len(array[0]))]

            for row in array:
                table.add_row(row)
        # Handle 1D array
        else:
            table.field_names = [single_column_header]
            for item in array:
                table.add_row([item])
        return table
    except Exception as e:
        print(f"Error creating table: {str(e)}")

def clean_mac(mac_address: str):
    # Remove all dots and colons and convert to lowercase
    normalized = mac_address.replace('.', '').replace(':', '').lower()
    return normalized

def edittime(epoch_timestamp):
    """
    Convert epoch timestamp to standard datetime format.

    Args:
        epoch_timestamp (int): Unix epoch timestamp in seconds

    Returns:
        str: Formatted datetime string in the format 'YYYY-MM-DD HH:MM:SS'

    Example:
        epoch_to_standard_time(1683936000)
        '2023-05-13 00:00:00'
    """
    try:
        # Convert epoch to datetime object
        dt = datetime.fromtimestamp(epoch_timestamp)

        # Format the datetime as string
        standard_time = dt.strftime('%Y-%m-%d %H:%M:%S')

        return standard_time
    except (ValueError, TypeError) as e:
        return f"Error converting timestamp: {str(e)}"

def print_unique(items, value: str):
    # cycles through an array and returns the unique values
    unique_values = set()
    for item in items:
        v = item.get(value)
        if v:
            unique_values.add(v)
    for v in unique_values:
        return(v)

def analyze_errors(data, site_array=None, error='Error ', group_by='site', top_n=None, save_path=None):
    """
    Analyze AP disconnection data and create a time series visualization.

    Parameters:
    - error = str of error name
    - config: API configuration
    - data: List of events pulled from API
    - site_array: List of site information for lookups. items are a dict {'id': '12345', 'name':'site1'}
    - group_by: 'site' or 'ap' to determine grouping method
    - top_n: Optional integer to limit display to top N sites/APs with most errors
    - save_path: Optional path to save the figure

    Returns:
    - DataFrame with processed data
    """
    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Convert timestamps to datetime
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')

    # Add site name if grouping by site if site_array is provided
    if group_by == 'site':
        if site_array:  # Only map if site_array is provided and not empty
            site_lookup = {site['id']: site['name'] for site in site_array}
            df['site_name'] = df['site_id'].map(site_lookup)
            group_column = 'site_name'
        else:
            group_column = 'site_id'
        title = f'{error} by Site'
    else:
        group_column = 'ap'
        title = f'{error} by Access Point'

    # Group by selected column and date
    grouped = df.groupby([df['datetime'].dt.date, group_column]).size().unstack().fillna(0)

    # If top_n is specified, filter to show only the top N sites/APs with most errors
    if top_n and top_n < len(grouped.columns):
        # Calculate total errors for each site/AP
        totals = grouped.sum().sort_values(ascending=False)
        top_columns = totals.head(top_n).index
        grouped = grouped[top_columns]
        title += f" (Top {top_n})"

    # Plot the data
    plt.figure(figsize=(12, 8))

    # Use seaborn for better aesthetics
    sns.set_style("whitegrid")

    # Plot each group as a line
    for column in grouped.columns:
        plt.plot(grouped.index, grouped[column], marker='o', linewidth=2, label=column)

    # Add labels and title
    plt.xlabel('Date')
    plt.ylabel('Number of Errors')
    plt.title(title)
    plt.legend(title=group_by.capitalize(), bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    # Save the figure if a path is provided
    if save_path:
        # Ensure the directory exists
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to {save_path}")

    plt.show()

    return df
