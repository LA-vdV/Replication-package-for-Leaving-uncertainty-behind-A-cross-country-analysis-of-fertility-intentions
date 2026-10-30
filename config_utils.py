"""
Configuration utilities for the RF pipeline v2
Functional approach for YAML config loading, validation, and path management
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load and validate YAML configuration file
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        Dictionary with validated configuration
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    # Load YAML
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file: {e}")
    
    # Validate config structure
    _validate_config(config)
    
    # Resolve relative paths
    config = _resolve_paths(config, config_path.parent)
    
    return config

def _validate_config(config: Dict[str, Any]):
    """Validate required config sections and fields"""
    required_sections = ['model', 'features', 'target', 'data', 'output']
    
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required section: {section}")
    
    # Validate model section
    model = config['model']
    if 'name' not in model:
        raise ValueError("Missing model.name")
    if 'model_type' not in model:
        raise ValueError("Missing model.model_type")
        
    # Validate features
    features = config['features']
    if 'categorical' not in features or 'continuous' not in features:
        raise ValueError("Missing categorical or continuous features")
        
    # Validate target
    target = config['target']
    if 'column' not in target:
        raise ValueError("Missing target.column")
        
    # Validate output folder matches model name
    model_name = model['name']
    output_folder = config['output'].get('model_folder')
    if output_folder != model_name:
        raise ValueError(f"Output folder '{output_folder}' must match model name '{model_name}'")

def _resolve_paths(config: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
    """Convert relative paths to absolute paths"""
    config = config.copy()  # Don't modify original
    
    # Resolve data paths
    data_section = config['data']
    for key, path in data_section.items():
        if isinstance(path, str) and ('/' in path or '\\' in path):
            resolved_path = (base_dir / path).resolve()
            data_section[key] = str(resolved_path)
    
    # Resolve output base path
    output_section = config['output']
    if 'base_path' in output_section:
        base_path = output_section['base_path']
        resolved_base = (base_dir / base_path).resolve()
        output_section['base_path'] = str(resolved_base)
    
    return config

def get_model_name(config: Dict[str, Any]) -> str:
    """Get model name from config"""
    return config['model']['name']

def get_model_type(config: Dict[str, Any]) -> str:
    """Get model type from config"""
    return config['model']['model_type']

def get_features(config: Dict[str, Any]) -> Tuple[List[str], List[str], List[str]]:
    """
    Get feature lists from config
    
    Returns:
        Tuple of (all_features, categorical_features, continuous_features)
    """
    categorical = config['features']['categorical']
    continuous = config['features']['continuous']
    all_features = categorical + continuous
    return all_features, categorical, continuous

def get_target_column(config: Dict[str, Any]) -> str:
    """Get target column name from config"""
    return config['target']['column']

def get_sample_filters(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get sample filtering criteria from config"""
    return config.get('sample', {}).get('filters', {})

def get_additional_filters(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get additional filtering criteria from config"""
    return config.get('sample', {}).get('additional_filters', {})

def get_output_dir(config: Dict[str, Any]) -> Path:
    """Get output directory path for model"""
    base_path = config['output']['base_path']
    model_folder = config['output']['model_folder']
    return Path(base_path) / model_folder

def get_processed_data_path(config: Dict[str, Any]) -> Path:
    """Get path to processed data file"""
    return Path(config['data']['processed_data'])

def get_output_path(config: Dict[str, Any], file_key: str) -> Path:
    """Get full output path for a specific file"""
    if file_key not in config['output']['files']:
        raise ValueError(f"Unknown output file key: {file_key}")
    
    filename = config['output']['files'][file_key]
    return get_output_dir(config) / filename

def get_training_param(config: Dict[str, Any], section: str, param: str, default=None):
    """Get training parameter with fallback to default"""
    return config.get('training', {}).get(section, {}).get(param, default)

def get_analysis_param(config: Dict[str, Any], section: str, param: str, default=None):
    """Get analysis parameter with fallback to default"""
    return config.get('analysis', {}).get(section, {}).get(param, default)

def save_config(config: Dict[str, Any], output_path: str):
    """Save config to specified path"""
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
