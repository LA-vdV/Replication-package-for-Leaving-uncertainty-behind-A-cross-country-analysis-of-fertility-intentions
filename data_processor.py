"""
Data processing functions for RF pipeline v2
Handles one-time data processing that is shared across all models
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple
import config_utils

def load_raw_data(source_path: str) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Load raw data from Stata file and extract variable labels
    
    Args:
        source_path: Path to raw Stata data file
        
    Returns:
        Tuple of (dataframe, variable_labels_dict)
    """
    source_path = Path(source_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Source data not found: {source_path}")
    
    print("Loading raw data...")
    df = pd.read_stata(source_path)
    
    # Extract variable labels for later use
    try:
        # Try to get variable labels from Stata file if available
        with pd.io.stata.StataReader(source_path) as reader:
            variable_labels = reader.variable_labels()
    except:
        # Fallback: create basic labels
        variable_labels = {col: col.replace('_', ' ').title() for col in df.columns}
    
    return df, variable_labels

def apply_basic_preprocessing(df: pd.DataFrame) -> pd.DataFrame:
    """Apply basic data preprocessing shared across all models"""
    print("Applying basic preprocessing...")
    df = df.copy()
    
    # Basic data type optimization
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                # Convert string categoricals to category type for memory efficiency
                df[col] = df[col].astype('category') 
            except:
                pass
    
    # Add helper variables used across models
    df['young'] = ((df['age'] >= 20) & (df['age'] <= 39)).astype(int)
    df['child_1'] = df['child_few'].isin(['Childless','One']).astype(int)
    
    # Apply age_partner filtering (common across models)
    df.loc[df['age_partner'] >= 50, 'age_partner'] = np.nan
    df.loc[df['age_partner'] < 20, 'age_partner'] = np.nan
    
    # Create train/test split identifier (consistent across models)
    np.random.seed(1000)
    df['train'] = (np.random.uniform(size=len(df)) < 0.90).astype(int)
    df['tests'] = 1 - df['train']
    df['full'] = 1

    return df

def create_target_variable(df: pd.DataFrame) -> pd.DataFrame:
    """Create the target variable fer_short2"""
    print("Creating target variable...")
    df = df.copy()
    
    # Create fer_short2 following Stata
    target_mapping = {
        "Definitely not": 1, 
        "Probably not": 1,
        "Unsure": 2, 
        "Probably yes": 3, 
        "Definitely yes": 3,
        "Currently expecting a child": np.nan
    }
        
    # Use map instead of replace to avoid warnings
    df['fer_short2'] = df['fer14'].map(target_mapping)

    return df

def save_processed_data(df: pd.DataFrame, variable_labels: Dict[str, str], 
                       output_path: str, source_path: str):
    """Save processed data to shared location"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    processed_data = {
        'df': df,
        'variable_labels': variable_labels,
        'processing_info': {
            'source_file': str(source_path),
            'processed_date': pd.Timestamp.now().isoformat(),
            'n_observations': len(df),
            'n_variables': len(df.columns)
        }
    }
    
    with open(output_path, 'wb') as f:
        pickle.dump(processed_data, f)
    
    print(f"   ✓ Saved processed data: {output_path}")
    print(f"   ✓ Data shape: {df.shape}")
    
    return processed_data

def process_data(source_path: str, output_path: str) -> Dict[str, Any]:
    """
    Complete data processing pipeline
    
    Args:
        source_path: Path to raw Stata file
        output_path: Where to save processed data
        
    Returns:
        Dictionary with processed data and metadata
    """
    df, variable_labels = load_raw_data(source_path)
    df = apply_basic_preprocessing(df)
    df = create_target_variable(df)
    processed_data = save_processed_data(df, variable_labels, output_path, source_path)
    
    return processed_data

def load_or_process_data(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load processed data if it exists, otherwise process it
    
    Args:
        config: Model configuration dictionary
        
    Returns:
        Dictionary with processed data and metadata
    """
    processed_path = config_utils.get_processed_data_path(config)
    
    if processed_path.exists():
        print(f"Loading existing processed data: {processed_path}")
        with open(processed_path, 'rb') as f:
            return pickle.load(f)
    else:
        print(f"Processed data not found, creating: {processed_path}")
        source_file = config['data']['source_file']
        return process_data(source_file, processed_path)

def filter_data_for_model(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Apply model-specific filtering to the processed data
    
    Args:
        df: Processed dataframe
        config: Model configuration dictionary
        
    Returns:
        Filtered dataframe for the specific model
    """
    model_name = config_utils.get_model_name(config)
    print(f"Applying {model_name} sample filters...")
    initial_n = len(df)
    
    # Apply base filters
    df_filtered = df.copy()
    
    sample_filters = config_utils.get_sample_filters(config)
    for filter_col, filter_val in sample_filters.items():
        if filter_col in df_filtered.columns:
            if isinstance(filter_val, list):
                df_filtered = df_filtered[df_filtered[filter_col].isin(filter_val)]
            else:
                df_filtered = df_filtered[df_filtered[filter_col] == filter_val]
    
    # Apply additional filters
    additional_filters = config_utils.get_additional_filters(config)
    for filter_col, filter_val in additional_filters.items():
        if filter_col in df_filtered.columns:
            if isinstance(filter_val, list):
                df_filtered = df_filtered[df_filtered[filter_col].isin(filter_val)]
            else:
                df_filtered = df_filtered[df_filtered[filter_col] == filter_val]
    
    print(f"   ✓ Filtered from {initial_n:,} to {len(df_filtered):,} observations")
    
    return df_filtered