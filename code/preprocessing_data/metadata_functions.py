import pandas as pd 
from pandas import json_normalize
import ast
import os 
import json

##########################################################################################
# Unpacking Raw Downloaded Metadata
##########################################################################################

def process_json(json_dir:str):

    dfs = []

    for file in os.listdir(json_dir):
        
        filepath = os.path.join(json_dir, file)
        with open (filepath, 'r') as file:
            data = json.load(file)

        df = json_normalize(data)

        dfs.append(df)

    all_bills_df = pd.concat(dfs, ignore_index=True)
    return(all_bills_df)

##########################################################################################

def create_sponsors_df(df, bill_id_col='bill_id',sponsor_col='metadata.sponsors'):

    all_rows = []

    for _, row in df.iterrows():
        bill_id = row[bill_id_col]
        sponsors_raw = row[sponsor_col]

        if not sponsors_raw or sponsors_raw == "[]":
            continue

        try:
            sponsors = ast.literal_eval(sponsors_raw)
            if isinstance(sponsors, list):
                for sponsor in sponsors:
                    if isinstance(sponsor, dict):
                        sponsor_copy = sponsor.copy()
                        sponsor_copy['bill_id'] = bill_id
                        all_rows.append(sponsor_copy)
        except (ValueError, SyntaxError):
            print(f"Error parsing sponsors for bill {bill_id}")
            continue

    sponsors_df = pd.DataFrame(all_rows)

    # Move 'bill_id' to the first column (if it exists)
    cols = ['bill_id'] + [c for c in sponsors_df.columns if c != 'bill_id']
    sponsors_df = sponsors_df[cols]
    
    return sponsors_df

##########################################################################################
# Working with Unpacked Metadata
##########################################################################################

def load_metadata(sessions, file_types, metadata_path):
    """
    """

    metadata_dict = {}

    for session in sessions:
        # Create a nested dict for each session
        metadata_dict[session] = {}

        # Load the main metadata file
        metadata_dict[session]['metadata'] = pd.read_csv(f"{metadata_path}{session}_metadata.csv")

        # Load each file type for that session
        for file_type in file_types:
            metadata_dict[session][file_type] = pd.read_csv(f"{metadata_path}{session}_{file_type}_metadata.csv")

    return metadata_dict

##########################################################################################

def extract_subject_names(cell):
    """
    For use on subject metadata - extract the subject names to a new column
    """

    if not cell or cell == "[]":
        return ""
    
    try:
        data = ast.literal_eval(cell)  # safely convert string to list of dicts
        subjects = [d.get("name") for d in data if isinstance(d, dict) and d.get("name")]
        return ", ".join(subjects)
    except (ValueError, SyntaxError):
        pass

    return ""

##########################################################################################

def count_subjects(df):

    df['subject_list'] = df['subject_names'].apply(lambda x: [s.strip() for s in x.split(',') if s.strip()])

    # Explode so each subject gets its own row
    exploded_df = df.explode('subject_list')

    # Group by subject and count how many bills each appears in
    subject_counts_df = (
        exploded_df
        .groupby('subject_list', as_index=False)
        .size()
        .rename(columns={'subject_list': 'subject', 'size': 'bill_count'})
        .sort_values('bill_count', ascending=False)
        .reset_index(drop=True)
    )

    return(subject_counts_df)

##########################################################################################