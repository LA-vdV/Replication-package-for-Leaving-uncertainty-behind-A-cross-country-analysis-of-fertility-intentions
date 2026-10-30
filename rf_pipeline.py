"""
Random Forest Pipeline v2: Config-Driven Data Preparation, Hyperparameter Tuning, and Model Training
Uses sklearn Pipeline with OneHotEncoder and YAML configuration files.

"""

import pandas as pd
import numpy as np
import pickle
import os
import sys
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from scipy.stats import randint, uniform

import config_utils
import data_processor

def create_pipeline(categorical_features, continuous_features, model_type='rf'):

    
    # Preprocessing for categorical features
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    # Preprocessing for numerical features
    numerical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='mean'))
        # Note: No scaling for tree-based models
    ])
    
    # Combine preprocessing steps
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_transformer, continuous_features),
            ('cat', categorical_transformer, categorical_features)
        ],
        remainder='drop'  # Drop other columns
    )
    
    # Create classifier based on model type
    classifier = RandomForestClassifier(random_state=42)
    
    # Create the full pipeline
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', classifier)
    ])
    
    return pipeline

def hyperparameter_tuning(df, config):
    """Perform hyperparameter tuning using randomized search with pipeline"""
    
    # Get config parameters
    model_type = config_utils.get_model_type(config)
    all_features, categorical_features, continuous_features = config_utils.get_features(config)
    y_column = config_utils.get_target_column(config)
    n_iterations = config_utils.get_training_param(config, 'hyperparameter_tuning', 'n_iterations', 10)
    n_iter_search = config_utils.get_training_param(config, 'hyperparameter_tuning', 'n_iter_search', 50)
    scoring_metric = config_utils.get_training_param(config, 'hyperparameter_tuning', 'scoring_metric', 'f1_macro')
    random_state = config_utils.get_training_param(config, 'hyperparameter_tuning', 'random_state', 1500)
    
    np.random.seed(random_state)
    
    print(f"   Model type: {model_type.upper()}")
    print(f"   Scoring metric: {scoring_metric}")
    print(f"   Number of iterations: {n_iterations}")
    print(f"   Search iterations per run: {n_iter_search}")
    print(f"   Categorical features: {len(categorical_features)}")
    print(f"   Continuous features: {len(continuous_features)}")
    
    # Define hyperparameter search space for the pipeline
    param_dist = {
            'classifier__n_estimators': randint(50, 300),
            'classifier__max_depth': randint(70, 150),
            'classifier__min_samples_leaf': randint(1, 5),
            'classifier__min_samples_split': randint(2, 8)
        }

    results = []
    errors = []

    for i in range(n_iterations):
        try:
            # Create new random train/test split
            train_mask = np.random.uniform(size=len(df)) < 0.90
            df_train = df[train_mask].copy()
            
            # Remove rows with missing values in outcome
            df_train = df_train.dropna(subset=[y_column])
            
            if len(df_train) == 0:
                print(f"   Warning: Iteration {i+1} skipped - no training data after removing missing values")
                continue
            
            X_train = df_train[all_features]
            y_train = df_train[y_column]
            
            # Create pipeline for this iteration
            pipeline = create_pipeline(categorical_features, continuous_features, model_type)
            
            # Randomized search
            rand_search = RandomizedSearchCV(
                pipeline, param_distributions=param_dist, n_iter=n_iter_search, 
                cv=5, scoring=scoring_metric, random_state=42, n_jobs=-1
            )
            rand_search.fit(X_train, y_train)
            
            # Store results
            result = {
                    'iteration': i + 1,
                    'score': rand_search.best_score_,
                    'max_depth': rand_search.best_params_['classifier__max_depth'],
                    'min_samples_leaf': rand_search.best_params_['classifier__min_samples_leaf'],
                    'min_samples_split': rand_search.best_params_['classifier__min_samples_split'],
                    'n_estimators': rand_search.best_params_['classifier__n_estimators']
                }
            results.append(result)
            
    
        except Exception as e:
            print(f"   Warning: Iteration {i+1} failed with error: {type(e).__name__}: {e}")
            errors.append(e)
            continue

    # Stop with the real error if every iteration failed
    if not results:
        raise RuntimeError(
            f"All {n_iterations} tuning iterations failed. Last error: "
            f"{type(errors[-1]).__name__}: {errors[-1]}" if errors else
            f"No tuning iterations ran (check the data and sample filters)."
        ) from (errors[-1] if errors else None)

    results_df = pd.DataFrame(results)
    print(f"   Successfully completed {len(results)}/{n_iterations} iterations")
    
    print(f"\n[3/3] Best parameters (based on highest score):")
    best_idx = results_df['score'].idxmax()
    best_params = results_df.iloc[best_idx]
    print(f"   Score: {best_params['score']:.4f}")
    
    print(f"   Max Depth: {best_params['max_depth']:.0f}")
    print(f"   Min Samples Leaf: {best_params['min_samples_leaf']:.0f}")
    print(f"   Min Samples Split: {best_params['min_samples_split']:.0f}")
    print(f"   N Estimators: {best_params['n_estimators']:.0f}")
    best_params_dict = {
            'max_depth': int(best_params['max_depth']),
            'min_samples_leaf': int(best_params['min_samples_leaf']),
            'min_samples_split': int(best_params['min_samples_split']),
            'n_estimators': int(best_params['n_estimators'])
        }
    
    return results_df, best_params_dict

def train_final_model(df, config, best_params):
    """Train the final model with best hyperparameters using pipeline"""
    
    # Get config parameters
    all_features, categorical_features, continuous_features = config_utils.get_features(config)
    y_column = config_utils.get_target_column(config)
    model_type = config_utils.get_model_type(config)
    final_random_state = config_utils.get_training_param(config, 'final_model', 'random_state', 42)
    
    # Prepare training data
    df_train = df[df['train'] == 1].copy()
    df_train = df_train.dropna(subset=[y_column])
    
    X_train = df_train[all_features]
    y_train = df_train[y_column]
    
    print(f"\nTraining on {len(X_train):,} observations with {len(all_features)} features...")
    
    # Create pipeline with best parameters
    pipeline = create_pipeline(categorical_features, continuous_features, model_type)
    
    # Set the best hyperparameters
    params_to_set = {f'classifier__{k}': v for k, v in best_params.items()}
    params_to_set['classifier__random_state'] = final_random_state
    pipeline.set_params(**params_to_set)
    
    pipeline.fit(X_train, y_train)
    print("Model training complete")
    
    return pipeline

def save_results(df, config, results_df, best_params, pipeline_model):
  
    print("\n" + "=" * 80)
    model_type = config_utils.get_model_type(config)
    print(f"STEP 4: SAVING RESULTS ({model_type.upper()})")
    print("=" * 80)
    
    # Create output directory
    output_dir = config_utils.get_output_dir(config)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_features, categorical_features, continuous_features = config_utils.get_features(config)
    
    # Save processed data (shared across all models) - only if it doesn't exist
    processed_data_path = config_utils.get_processed_data_path(config)
    if not processed_data_path.exists():
        processed_data = {
            'df': df,
            'variable_labels': {}  # Will be populated during data processing
        }
        with open(processed_data_path, 'wb') as f:
            pickle.dump(processed_data, f)
        print(f"Saved shared: {processed_data_path.name}")
    else:
        print(f"Using existing shared: {processed_data_path.name}")
    
    # Save configuration (copy of YAML config)  
    config_output_path = config_utils.get_output_path(config, 'config')
    config_utils.save_config(config, config_output_path)
    print(f"Saved: {config_output_path.name}")
    
    # Save feature information for evaluation (shared across all models)
    feature_info = {
        'categorical_features': categorical_features,
        'continuous_features': continuous_features,
        'all_features': all_features
    }
    
    feature_info_path = config_utils.get_output_path(config, 'feature_names')
    with open(feature_info_path, 'wb') as f:
        pickle.dump(feature_info, f)
    print(f"Saved: {feature_info_path.name}")
    
    # Save hyperparameter search results
    hyper_path = config_utils.get_output_path(config, 'hyperparameter_results')
    results_df.to_csv(hyper_path, index=False)
    print(f"Saved: {hyper_path}")
    
    # Save best parameters
    params_path = config_utils.get_output_path(config, 'hyperparameters')
    with open(params_path, 'wb') as f:
        pickle.dump(best_params, f)
    print(f"Saved: {params_path}")

    # Save trained pipeline model
    model_path = config_utils.get_output_path(config, 'model')
    with open(model_path, 'wb') as f:
        pickle.dump(pipeline_model, f)
    print(f"Saved: {model_path}")
    
    # Save feature names from the pipeline (useful for interpretation)
    try:
        # Get feature names after preprocessing
        feature_names = pipeline_model.named_steps['preprocessor'].get_feature_names_out()
        feature_names_path = output_dir / 'pipeline_feature_names.pkl'
        with open(feature_names_path, 'wb') as f:
            pickle.dump(feature_names, f)
        print(f"Saved: pipeline_feature_names.pkl")
    except Exception as e:
        print(f"Warning: Could not save feature names: {e}")

def main(config_path):
    """Main pipeline execution"""
    print("=" * 80)
    print("RANDOM FOREST")
    print("=" * 80)
    
    # Load configuration
    print(f"Loading configuration: {config_path}")
    config     = config_utils.load_config(config_path)
    model_name = config_utils.get_model_name(config)
    model_type = config_utils.get_model_type(config)
    

    print(f"   Model: {model_name} ({model_type})")
    print(f"   Output: {config_utils.get_output_dir(config)}")
    
    # Load or process data
    data = data_processor.load_or_process_data(config)
    df = data['df']
    
    # Filter data for this model
    df_filtered = data_processor.filter_data_for_model(df, config)
    
    # Hyperparameter tuning
    results_df, best_params = hyperparameter_tuning(df_filtered, config)

    # Train final model
    pipeline_model = train_final_model(df_filtered, config, best_params)
    
    # Save everything
    save_results(df_filtered, config, results_df, best_params, pipeline_model)
    
    print("\n" + "=" * 80)
    print(f"{model_name.upper()} PIPELINE COMPLETE!")
    print("=" * 80)
    print(f"Configuration: {config_path}")
    print(f"Output folder: {config_utils.get_output_dir(config)}")
    print(f"\nNext steps:")
    print(f"   - Run evaluation: python rf_evaluation.py {config_path}")
    print(f"   - Run interpretation: python rf_interpretation.py {config_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python rf_pipeline.py <config_file>")
        print("Example: python rf_pipeline.py model_configs/full_sample.yaml")
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
    
    print(f"Running pipeline with config: {config_file}")
    main(config_file)