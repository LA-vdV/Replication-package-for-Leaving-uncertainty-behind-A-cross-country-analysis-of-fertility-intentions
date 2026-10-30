"""
Random Forest Interpretation:  Partial Dependence and Interaction Analysis

This script computes partial dependence plots and interaction effects.
"""

import pandas as pd
import numpy as np

import pickle
import sys
from pathlib import Path
from itertools import combinations
from collections import Counter
import warnings
warnings.filterwarnings('ignore')
from sklearn.tree import export_text

import config_utils
import data_processor

def load_model_and_data(config):
    """Load the trained model and processed data using config"""
    print("=" * 80)
    print("RANDOM FOREST INTERPRETATION V2")
    print("=" * 80)
    
    model_name = config_utils.get_model_name(config)
    print(f"Model: {model_name}")
    
    print("\n[1/2] Loading model and data...")
    
    # Load processed data
    data = data_processor.load_or_process_data(config)
    df = data['df']
    
    # Filter data for this model
    df_filtered = data_processor.filter_data_for_model(df, config)
    
    # Load trained model
    model_path = config_utils.get_output_path(config, 'model')
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    print(f"   ✓ Model loaded: {model_path.name}")
    print(f"   ✓ Data shape: {df_filtered.shape}")
    
    return df_filtered, model, data

def get_pipeline_feature_names(pipeline, config):
    """Load transformed feature names from disk or derive them from the preprocessor."""
    feature_names_path = config_utils.get_output_dir(config) / 'pipeline_feature_names.pkl'

    if feature_names_path.exists():
        with open(feature_names_path, 'rb') as f:
            feature_names = pickle.load(f)
    else:
        feature_names = pipeline.named_steps['preprocessor'].get_feature_names_out()

    return list(feature_names)

def parse_transformed_feature_name(transformed_feature, categorical_features, continuous_features):
    """Map a transformed sklearn feature name back to the original variable."""
    if transformed_feature.startswith('num__'):
        raw_feature = transformed_feature.split('num__', 1)[1]
        return {
            'raw_feature': raw_feature,
            'feature_type': 'continuous',
            'category': None,
            'readable_name': raw_feature
        }

    if transformed_feature.startswith('cat__'):
        encoded_name = transformed_feature.split('cat__', 1)[1]
        matching_features = [
            feature for feature in categorical_features
            if encoded_name == feature or encoded_name.startswith(f'{feature}_')
        ]

        if matching_features:
            raw_feature = max(matching_features, key=len)
            category = None
            if encoded_name != raw_feature:
                category = encoded_name[len(raw_feature) + 1:]

            readable_name = raw_feature if category is None else f'{raw_feature} [{category}]'
            return {
                'raw_feature': raw_feature,
                'feature_type': 'categorical',
                'category': category,
                'readable_name': readable_name
            }

    feature_type = 'continuous' if transformed_feature in continuous_features else 'unknown'
    return {
        'raw_feature': transformed_feature,
        'feature_type': feature_type,
        'category': None,
        'readable_name': transformed_feature
    }

def categorical_pdp_pipeline(pipeline, X_raw, feature_name, categories=None):
    """Compute partial dependence for categorical variables using pipeline"""
    if categories is None:
        categories = X_raw[feature_name].dropna().unique()
        # Sort categories to ensure consistent ordering
        categories = sorted(categories)
    
    results = []
    
    for cat in categories:
        X_temp = X_raw.copy()
        X_temp[feature_name] = cat
        
        try:
            preds = pipeline.predict_proba(X_temp)
            # Multi-class (no=0, uncertain=1, yes=2)
            results.append((cat, preds[:, 0].mean(), preds[:, 1].mean(), preds[:, 2].mean()))
        except Exception as e:
            print(f"   Warning: Failed to compute PDP for {feature_name}={cat}: {e}")
            continue
    
    if len(results) == 0:
        return None
    
    # Check if binary or multi-class based on first result
    return pd.DataFrame(results, columns=[feature_name, "no_pdp", "uncertain_pdp", "yes_pdp"])

def compute_1d_pdp_pipeline(df_subset, pipeline, feature_name, categorical_features, continuous_features, 
                          is_categorical=False, grid_resolution=10):
    """Compute 1D partial dependence for pipeline models"""
    
    all_features = categorical_features + continuous_features
    df_clean = df_subset.dropna(subset=[feature_name])
    if len(df_clean) == 0:
        return None
    
    results = []
    
    if is_categorical:
        # Use categorical PDP for pipeline
        X_for_prediction = df_clean[all_features]
        
        if len(X_for_prediction) == 0:
            return None
            
        pdp_result = categorical_pdp_pipeline(pipeline, X_for_prediction, feature_name)
        
        if pdp_result is None:
            return None
        
        categories = pdp_result[feature_name].values
        
        for i, cat in enumerate(categories):
            row = pdp_result[pdp_result[feature_name] == cat].iloc[0]
            results.append({
                    'feature1': feature_name, 'f1_value': cat, 'f1_idx': i,
                    'no_pdp': row['no_pdp'],
                    'uncertain_pdp': row['uncertain_pdp'],
                    'yes_pdp': row['yes_pdp']
                })
        return results
        
    else:
        X_for_prediction = df_clean[all_features]
        
        if len(X_for_prediction) == 0:
            return None
        
        try:
            # Create grid for continuous variable - ensure it's numeric
            feature_values = df_clean[feature_name].dropna()
            
            # Convert to numeric and handle non-numeric values
            feature_values = pd.to_numeric(feature_values, errors='coerce').dropna()
            
            if len(feature_values) == 0:
                print(f"   Warning: No valid numeric values for {feature_name}")
                return None
            
            if feature_name in ['std_tv_deaths', 'std_deaths']:
                grid_values = np.array([-0.75, 0, 0.75, 1.5, 2.25, 3.0])
            elif feature_name in ['age', 'age_partner']:
                grid_values = np.array([20, 24, 28, 32, 36, 40, 44, 48])    
            else:
                # Ensure feature_values is a numpy array of floats
                feature_values_array = np.array(feature_values, dtype=float)
                grid_values = np.percentile(feature_values_array, [5, 15, 25, 35, 45, 55, 65, 75, 85, 95])
            
            # Manual partial dependence for continuous variables
            for i, grid_val in enumerate(grid_values):
                X_temp = X_for_prediction.copy()
                X_temp[feature_name] = float(grid_val)  # Ensure numeric
                
                preds = pipeline.predict_proba(X_temp)
                results.append({
                    'feature1': feature_name,
                    'f1_value': grid_val,
                    'f1_idx': i,
                    'no_pdp': preds[:, 0].mean(),
                    'uncertain_pdp': preds[:, 1].mean(),
                    'yes_pdp': preds[:, 2].mean()
                    })
            
        except Exception as e:
            print(f"   Warning: Manual PDP failed for {feature_name}: {e}")
            return None
    
    return results

def partial_dependence_analysis_pipeline(df, pipeline, config, suffix=''):
    """Compute partial dependence plots using pipeline and config"""
    subset_label = f" ({suffix})" if suffix else ""
    print("\n" + "=" * 80)
    print(f"PARTIAL DEPENDENCE ANALYSIS{subset_label}")
    print("=" * 80)
    
    all_features, categorical_features, continuous_features = config_utils.get_features(config)
    
    df_full = df[df['full'] == 1].copy()
    
    print(f"\nComputing PDP for continuous variables...")
    pdp_results = []
    
    for var in continuous_features:
        # Use higher resolution for continuous variables
        grid_resolution = 10 if var != 'std_deaths' else 6  # Custom for std_deaths
        results = compute_1d_pdp_pipeline(df_full, pipeline, var, categorical_features, 
                                        continuous_features, False, grid_resolution)
        if results:
            pdp_results.extend(results)
    
    print(f"Computing PDP for categorical variables...")
    for var in categorical_features:
        results = compute_1d_pdp_pipeline(df_full, pipeline, var, categorical_features, 
                                        continuous_features, True)
        if results:
            pdp_results.extend(results)
    
    pdp_df = pd.DataFrame(pdp_results)
    
    # Save results
    print(f"\nSaving partial dependence results...")
    
    # Create filename with suffix if provided
    filename = 'pdp'
    if suffix:
        filename += f'_{suffix.lower().replace(" ", "_").replace(",", "")}'
    filename += '.csv'
    
    pdp_path = config_utils.get_output_dir(config) / filename
    pdp_df.to_csv(pdp_path, index=False)
    print(f" Saved: {pdp_path}")
   
    return pdp_df

def compute_2d_pdp_pipeline(df, pipeline, feature1, feature2, categorical_features, 
                           continuous_features, grid_size=20):
    """Compute 2D partial dependence for pipeline models"""
    print(f"\n[2D PDP] Computing 2D partial dependence: {feature1} x {feature2}...")
    
    all_features = categorical_features + continuous_features
    df_full = df[df['full'] == 1].dropna(subset=all_features)
    
    if len(df_full) == 0:
        print(f"   No data available for {feature1} x {feature2}")
        return None
    
    X_base = df_full[all_features].copy()
    
    # Determine if features are categorical
    f1_categorical = feature1 in categorical_features
    f2_categorical = feature2 in categorical_features
    
    results = []
    
    # Create grids for each feature
    if f1_categorical:
        f1_values = sorted(df_full[feature1].unique())
    else:
        # Use predefined grids for specific variables
        if feature1 in ['std_tv_deaths', 'std_deaths']:
            f1_values = np.array([-0.75, 0, 0.75, 1.5, 2.25, 3.0])
        elif feature1 in ['age', 'age_partner']:
            f1_values = np.array([20, 24, 28, 32, 36, 40, 44, 48])
        else:
            f1_min, f1_max = df_full[feature1].quantile([0.05, 0.95])
            f1_values = np.linspace(f1_min, f1_max, grid_size)
    
    if f2_categorical:
        f2_values = sorted(df_full[feature2].unique())
    else:
        # Use predefined grids for specific variables
        if feature2 in ['std_tv_deaths', 'std_deaths']:
            f2_values = np.array([-0.75, 0, 0.75, 1.5, 2.25, 3.0])
        elif feature2 in ['age', 'age_partner']:
            f2_values = np.array([20, 24, 28, 32, 36, 40, 44, 48])
        else:
            f2_min, f2_max = df_full[feature2].quantile([0.05, 0.95])
            f2_values = np.linspace(f2_min, f2_max, grid_size)
    
    # Compute 2D PDP
    total_combinations = len(f1_values) * len(f2_values)
    combo_count = 0
    
    for i, f1_val in enumerate(f1_values):
        for j, f2_val in enumerate(f2_values):
            combo_count += 1
            if combo_count % 50 == 0:
                print(f"   Progress: {combo_count}/{total_combinations}")
            
            X_temp = X_base.copy()
            X_temp[feature1] = f1_val
            X_temp[feature2] = f2_val
            
            try:
                y_pred = pipeline.predict_proba(X_temp)
                results.append({
                    'feature1': feature1,
                    'feature2': feature2,
                    'f1_value': f1_val,
                    'f2_value': f2_val,
                    'f1_idx': i,
                    'f2_idx': j,
                    'pdp_no': y_pred[:, 0].mean(),
                    'pdp_uncertain': y_pred[:, 1].mean(),
                    'pdp_yes': y_pred[:, 2].mean()
                    })
            except Exception as e:
                print(f"   Warning: Failed for {feature1}={f1_val}, {feature2}={f2_val}: {e}")
                continue
    
    if not results:
        print(f"   No valid results for {feature1} x {feature2}")
        return None
    
    return pd.DataFrame(results)

def compute_2d_pdp_pairs(df, pipeline, config):
    """Compute 2D partial dependence for a limited set of feature pairs."""
    analysis_params = config_utils.get_analysis_param(config, 'interpretation', 'interaction_analysis', {})
    max_features = analysis_params.get('max_features', 12)
    grid_size = analysis_params.get('grid_size_2d', 15)

    all_features, categorical_features, continuous_features = config_utils.get_features(config)
    all_available_features = categorical_features + continuous_features

    priority_features = [
        'child_few', 'age', 'educ_own', 'partner',
        'earnings', 'isowner', 'cn', 'std_tv_deaths',
        'age_partner', 'empl_lv', 'subj_health', 'educ_partner'
    ]

    priority_available = [f for f in priority_features if f in all_available_features]
    other_features = [f for f in all_available_features if f not in priority_available]
    features_for_analysis = (priority_available + other_features)[:max_features]

    pdp_2d_frames = []
    for f1, f2 in combinations(features_for_analysis, 2):
        pdp_2d = compute_2d_pdp_pipeline(
            df, pipeline, f1, f2, categorical_features, continuous_features, grid_size=grid_size
        )
        if pdp_2d is not None:
            pdp_2d_frames.append(pdp_2d)

    if not pdp_2d_frames:
        return None

    pdp_2d_df = pd.concat(pdp_2d_frames, ignore_index=True)
    output_path = config_utils.get_output_dir(config) / 'pdp_2d.csv'
    pdp_2d_df.to_csv(output_path, index=False)
    print(f"   ✓ Saved 2D PDP: {output_path}")
    return pdp_2d_df

def main(config_path):
    """Main interpretation execution"""
    print(f"Loading configuration: {config_path}")
    config = config_utils.load_config(config_path)
    model_name = config_utils.get_model_name(config)
    
    print(f"   ✓ Model: {model_name}")
    print(f"   ✓ Output: {config_utils.get_output_dir(config)}")
    
    # Load data and model
    df, model, data = load_model_and_data(config)
    all_features, categorical_features, continuous_features = config_utils.get_features(config)
    
    # Part 1: Partial dependence (pipeline method) - Full sample
    pdp_pipeline = partial_dependence_analysis_pipeline(
        df, model, config
    )
    
    # Partial dependence for young and childless subsample (if configured)
    analysis_params = config_utils.get_analysis_param(config, 'interpretation', 'subsamples', {})
    if analysis_params.get('young_childless', False):
        print("\n" + "=" * 80)
        print("CREATING YOUNG & CHILDLESS SUBSAMPLE")
        print("=" * 80)
        
        # Create young (age 20-39) and childless (0-1 children) variables if they don't exist
        if 'young' not in df.columns:
            df['young'] = ((df['age'] >= 20) & (df['age'] <= 39)).astype(int)
            print("   ✓ Created 'young' variable (age 20-39)")
        
        if 'child_1' not in df.columns:
            df['child_1'] = df['child_few'].isin([0, 1]).astype(int)
            print("   ✓ Created 'child_1' variable (0-1 children)")
        
        # Create subset for young and childless individuals
        df_young_childless = df[
            (df['young'] == 1) & 
            (df['child_1'] == 1)
        ].copy()
        
        print(f"     Young & childless subset: {len(df_young_childless)} observations")
        print(f"     (Original full sample: {len(df[df['full'] == 1])} observations)")
        
        if len(df_young_childless) > 0:
            # Create a temporary dataframe with the subset marked as 'full'
            df_temp = df.copy()
            df_temp['full'] = 0  # Reset all to 0
            df_temp.loc[df_young_childless.index, 'full'] = 1  # Mark subset as full
            
            pdp_young_childless = partial_dependence_analysis_pipeline(
                df_temp, model, config, suffix='young_childless'
            )
        else:
            print("    No observations in young & childless subset - skipping analysis")
            pdp_young_childless = None

    # Part 2: 2D partial dependence analysis (without H-statistics)
    pdp_2d = compute_2d_pdp_pairs(df, model, config)
    
    print("\n" + "=" * 80)
    print("INTERPRETATION COMPLETE!")
    print("=" * 80)
    print(f"✓ Configuration: {config_path}")
    print(f"✓ Output folder: {config_utils.get_output_dir(config)}")
    print(f"✓ Processed {len(categorical_features)} categorical + {len(continuous_features)} continuous features")
    print(f"✓ 1D partial dependence analysis saved")
    if analysis_params.get('young_childless', False) and 'pdp_young_childless' in locals():
        if pdp_young_childless is not None:
            print(f"✓ Young & childless subsample analysis saved")
    if pdp_2d is not None:
        print(f"✓ 2D partial dependence computed for {len(pdp_2d.groupby(['feature1', 'feature2']))} feature pairs")
 
    print("\nFiles generated:")
    print(f"  - 1D partial dependence: pdp.csv")
    if analysis_params.get('young_childless', False):
        print(f"  - Young & childless 1D PDP: pdp_young_childless.csv") 
    if pdp_2d is not None:
        print(f"  - 2D partial dependence: pdp_2d.csv")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python rf_interpretation.py <config_file>")
        print("Example: python rf_interpretation.py model_configs/full_sample.yaml")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    # Check if config file exists
    if not Path(config_file).exists():
        print(f"Error: Config file not found: {config_file}")
        print("\nAvailable configs in model_configs/:")
        config_dir = Path("model_configs")
        if config_dir.exists():
            for config_path in config_dir.glob("*.yaml"):
                print(f"   - {config_path}")
        sys.exit(1)
    
    print(f"Running interpretation with config: {config_file}")
    main(config_file)