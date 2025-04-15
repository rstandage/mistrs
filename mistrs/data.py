import json
import pandas as pd

def pprint(data):
    #Prints JSON in an easy to ready format
    print(json.dumps(data, indent=2, sort_keys=True))

def read_xlsx(file):
    #convert xlsx into an array
    df = pd.read_xslx(file)
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

