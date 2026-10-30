"""
Random Forest Evaluation v2: Config-Driven Model Quality and Feature Importance

This script evaluates the trained model and computes feature importance using configuration files.
"""

import pandas as pd
import numpy as np
import pickle
import sys
from pathlib import Path
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, f1_score
from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
import pandas as pd

import config_utils
import data_processor

def load_model_and_data(config):
    """Load the trained model and processed data using config"""
    print("=" * 80)
    print("RANDOM FOREST EVALUATION V2")
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
    
    return df_filtered, model, data.get('variable_labels', {})

def evaluate_model_quality(df, model, config):
    """Evaluate model on train and test sets"""
    print("\n" + "=" * 80)
    print("PART 1: MODEL QUALITY ASSESSMENT")
    print("=" * 80)
    
    all_features, categorical_features, continuous_features = config_utils.get_features(config)
    y_column = config_utils.get_target_column(config)
    
    def eval_subset(df_subset, subset_name):
        df_clean = df_subset.dropna(subset=all_features + [y_column])
        if len(df_clean) == 0:
            return None, None, None, None, None, None, None
        
        X = df_clean[all_features]
        y_true = df_clean[y_column].values
        y_pred = model.predict(X)
        
        cm = confusion_matrix(y_true, y_pred)
        accuracy = accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred, average='macro')
        
        # Per-class metrics
        unique_labels = sorted(y_true)
        n_classes = len(np.unique(y_true))
        precision_per_class = []
        recall_per_class = []
        f1_per_class = []
        
        for i in range(n_classes):
            tp = cm[i, i] if i < len(cm) else 0
            fp = cm[:, i].sum() - tp if i < cm.shape[1] else 0
            fn = cm[i, :].sum() - tp if i < cm.shape[0] else 0
            
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1_class = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0
            
            precision_per_class.append(prec)
            recall_per_class.append(rec)
            f1_per_class.append(f1_class)
        
        return cm, accuracy, f1, precision_per_class, recall_per_class, f1_per_class, df_clean
    
    # Evaluate train and test
    print("\n  Evaluating on training data...")
    results_train = eval_subset(df[df['train'] == 1], "train")
    if results_train[0] is not None:
        cm_train, acc_train, f1_train, prec_train, rec_train, f1_class_train, df_train_clean = results_train
        print(f"   Accuracy: {acc_train:.3f}, F1: {f1_train:.3f}")
    else:
        print("   No training data available")
        return
    
    print("\n  Evaluating on test data...")
    results_test = eval_subset(df[df['tests'] == 1], "test")
    if results_test[0] is not None:
        cm_test, acc_test, f1_test, prec_test, rec_test, f1_class_test, df_test_clean = results_test
        print(f"   Accuracy: {acc_test:.3f}, F1: {f1_test:.3f}")
    else:
        print("   No test data available")
        return
    
    # Create results DataFrames
    class_labels = ["No", "Uncertain", "Yes"]
    
    # Ensure confusion matrices are 3x3
    def ensure_3x3_cm(cm):
        if cm.shape == (3, 3):
            return cm
        elif cm.shape == (2, 2):
            # Extend to 3x3 if needed
            new_cm = np.zeros((3, 3))
            new_cm[:2, :2] = cm
            return new_cm
        else:
            return cm
    
    cm_train = ensure_3x3_cm(cm_train)
    cm_test = ensure_3x3_cm(cm_test)
    
    cm_train_df = pd.DataFrame(
        cm_train, index=class_labels, 
        columns=[f"hat({label})" for label in class_labels]
    )
    
    cm_test_df = pd.DataFrame(
        cm_test, index=class_labels,
        columns=[f"hat({label})" for label in class_labels]
    )
    
    # Ensure we have metrics for all classes
    while len(prec_test) < 3:
        prec_test.append(0.0)
    while len(rec_test) < 3:
        rec_test.append(0.0)
    
    stats_df = pd.DataFrame({
        'Average': [acc_test, np.mean(rec_test), np.mean(prec_test), f1_test],
        'No': [np.nan, rec_test[0], prec_test[0], np.nan],
        'Uncertain': [np.nan, rec_test[1] if len(rec_test) > 1 else 0, prec_test[1] if len(prec_test) > 1 else 0, np.nan],
        'Yes': [np.nan, rec_test[2] if len(rec_test) > 2 else 0, prec_test[2] if len(prec_test) > 2 else 0, np.nan]
    }, index=['Accuracy', 'Recall', 'Precision', 'F1 Score'])
    
    print("\n Creating merged dataset with train/test indicator...")
    
    # Create merged dataset with train/test indicator
    df_train_clean_copy = df_train_clean.copy()
    df_test_clean_copy = df_test_clean.copy()
    
    # Add test column
    df_train_clean_copy['test'] = False
    df_test_clean_copy['test'] = True
    
    # Merge datasets
    df_merged = pd.concat([df_train_clean_copy, df_test_clean_copy], ignore_index=True)
    
    # Save merged dataset
    merged_path = config_utils.get_output_dir(config) / 'merged_train_test_data.csv'
    df_merged.to_csv(merged_path, index=False)
    print(f"   ✓ Saved merged dataset: {merged_path}")
    
    print("\n Exporting confusion matrices and fit statistics...")
    
    # Create confusion matrix DataFrames for CSV export
    cm_train_df_csv = pd.DataFrame(
        cm_train, index=class_labels, 
        columns=[f"hat_{label}" for label in class_labels]
    )
    cm_train_df_csv['sample'] = 'train'
    cm_train_df_csv['actual_class'] = class_labels
    
    cm_test_df_csv = pd.DataFrame(
        cm_test, index=class_labels,
        columns=[f"hat_{label}" for label in class_labels]
    )
    cm_test_df_csv['sample'] = 'test'
    cm_test_df_csv['actual_class'] = class_labels
    
    # Merge confusion matrices for CSV export
    cm_combined_df = pd.concat([cm_train_df_csv, cm_test_df_csv], ignore_index=True)
    # Reorganize columns
    cols = ['sample', 'actual_class'] + [f"hat_{label}" for label in class_labels]
    cm_combined_df = cm_combined_df[cols]
    
    # Save confusion matrices as CSV
    cm_path = config_utils.get_output_dir(config) / 'confusion_matrices.csv'
    cm_combined_df.to_csv(cm_path, index=False)
    print(f"   ✓ Saved confusion matrices: {cm_path}")
    
    # Ensure we have metrics for all classes (fill missing with 0)
    while len(f1_class_train) < 3:
        f1_class_train.append(0.0)
    while len(f1_class_test) < 3:
        f1_class_test.append(0.0)
    
    # Create fit statistics DataFrame in long format
    fit_stats_list = []
    
    # Add overall metrics
    fit_stats_list.extend([
        {'name': 'accuracy', 'sample': 'train', 'statistic': acc_train},
        {'name': 'accuracy', 'sample': 'test', 'statistic': acc_test},
        {'name': 'f1_macro', 'sample': 'train', 'statistic': f1_train},
        {'name': 'f1_macro', 'sample': 'test', 'statistic': f1_test},
        {'name': 'precision_macro', 'sample': 'train', 'statistic': np.mean(prec_train)},
        {'name': 'precision_macro', 'sample': 'test', 'statistic': np.mean(prec_test)},
        {'name': 'recall_macro', 'sample': 'train', 'statistic': np.mean(rec_train)},
        {'name': 'recall_macro', 'sample': 'test', 'statistic': np.mean(rec_test)}
    ])
    
    # Add per-class metrics
    for i, class_name in enumerate(class_labels):
        fit_stats_list.extend([
            {'name': f'precision_{class_name.lower()}', 'sample': 'train', 'statistic': prec_train[i] if i < len(prec_train) else 0.0},
            {'name': f'precision_{class_name.lower()}', 'sample': 'test', 'statistic': prec_test[i] if i < len(prec_test) else 0.0},
            {'name': f'recall_{class_name.lower()}', 'sample': 'train', 'statistic': rec_train[i] if i < len(rec_train) else 0.0},
            {'name': f'recall_{class_name.lower()}', 'sample': 'test', 'statistic': rec_test[i] if i < len(rec_test) else 0.0},
            {'name': f'f1_{class_name.lower()}', 'sample': 'train', 'statistic': f1_class_train[i] if i < len(f1_class_train) else 0.0},
            {'name': f'f1_{class_name.lower()}', 'sample': 'test', 'statistic': f1_class_test[i] if i < len(f1_class_test) else 0.0}
        ])
    
    fit_stats_df = pd.DataFrame(fit_stats_list)
    
    # Save fit statistics as CSV
    fit_stats_path = config_utils.get_output_dir(config) / 'fit_statistics.csv'
    fit_stats_df.to_csv(fit_stats_path, index=False)
    print(f"   ✓ Saved fit statistics: {fit_stats_path}")
    
    # Display results
    print("\n" + "=" * 80)
    print("CONFUSION MATRIX - TEST DATA")
    print("=" * 80)
    print(cm_test_df.round(3))
    print("\n" + "=" * 80)
    print("FIT STATISTICS - TEST DATA")
    print("=" * 80)
    print(stats_df.round(3))
 

def compute_permutation_importance_pipeline(df, model, config, variable_labels):
    """Compute permutation feature importance for pipeline models"""
    print("\n" + "=" * 80)
    print("PART 2: PERMUTATION FEATURE IMPORTANCE")
    print("=" * 80)
    
    all_features, categorical_features, continuous_features = config_utils.get_features(config)
    y_column = config_utils.get_target_column(config)
    
    # Get config parameters
    n_repeats = config_utils.get_analysis_param(config, 'evaluation', 'permutation_importance', {}).get('n_repeats', 10)
    random_state = config_utils.get_analysis_param(config, 'evaluation', 'permutation_importance', {}).get('random_state', 42)
    
    # Prepare data
    df_full = df[df['full'] == 1].dropna(subset=all_features + [y_column])
    X_full = df_full[all_features]
    y_full = df_full[y_column].values
    
    print(f"\n[1/3] Computing sklearn permutation importance...")
    print(f"   Sample size: {len(df_full):,}")
    print(f"   Features: {len(all_features)}")
    print(f"   Repeats: {n_repeats}")
    
    # Use sklearn's permutation_importance
    perm_result = permutation_importance(
        model, X_full, y_full, 
        n_repeats=n_repeats, 
        random_state=random_state, 
        scoring={'accuracy': 'accuracy', 
                'precision': 'precision_macro',
                'recall': 'recall_macro',
                'f1': 'f1_macro'},
        n_jobs=-1  # Use all available cores
    )
    
    print(f"\n[2/3] Processing results...")
    
    # Create results dataframe with individual feature importance
    individual_results = []
    for i, feature in enumerate(all_features):
        individual_results.append({
            'feature': feature,
            'accuracy_mean': perm_result['accuracy'].importances_mean[i],
            'accuracy_std': perm_result['accuracy'].importances_std[i],
            'precision_mean': perm_result['precision'].importances_mean[i],
            'precision_std': perm_result['precision'].importances_std[i],
            'recall_mean': perm_result['recall'].importances_mean[i],
            'recall_std': perm_result['recall'].importances_std[i],
            'f1_mean': perm_result['f1'].importances_mean[i],
            'f1_std': perm_result['f1'].importances_std[i]
        })
    
    individual_df = pd.DataFrame(individual_results)
    
    # Add variable type and labels
    individual_df['variable_type'] = individual_df['feature'].apply(
        lambda x: 'categorical' if x in categorical_features else 'continuous'
    )
    
    # Add variable labels
    individual_df['labels'] = individual_df['feature'].apply(
        lambda x: variable_labels.get(x, x.replace('_', ' ').title())
    )
    
    print(f"\n[3/3] Saving permutation importance...")
    
    # Save individual results
    individual_path = config_utils.get_output_path(config, 'permutation_importance')
    individual_df.to_csv(individual_path, index=False)
    print(f"   ✓ Saved: {individual_path}")
    
    return individual_df

def main(config_path):
    """Main evaluation execution"""
    print(f"Loading configuration: {config_path}")
    config = config_utils.load_config(config_path)
    model_name = config_utils.get_model_name(config)
    
    print(f"   ✓ Model: {model_name}")
    print(f"   ✓ Output: {config_utils.get_output_dir(config)}")
    
    # Load model and data
    df, model, variable_labels = load_model_and_data(config)
    
    # Part 1: Model quality
    evaluate_model_quality(df, model, config)
    
    # Part 2: Permutation importance
    perm_df = compute_permutation_importance_pipeline(df, model, config, variable_labels)
    
    
    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE!")
    print("=" * 80)
    print(f"  Configuration: {config_path}")
    print(f"Output folder: {config_utils.get_output_dir(config)}")
    print("\nFiles generated:")    
    print(f"  - Merged train/test data: merged_train_test_data.csv")
    print(f"  - Confusion matrices: confusion_matrices.csv")
    print(f"  - Fit statistics: fit_statistics.csv")
    print(f"  - Permutation importance: {config_utils.get_output_path(config, 'permutation_importance').name}")
    print(f"\nNext step: Run 'python rf_interpretation.py {config_path}' for model interpretation")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python rf_evaluation.py <config_file>")
        print("Example: python rf_evaluation.py model_configs/full_sample.yaml")
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
    
    print(f"Running evaluation with config: {config_file}")
    main(config_file)