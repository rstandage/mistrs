import json
import pandas as pd
from prettytable import PrettyTable

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