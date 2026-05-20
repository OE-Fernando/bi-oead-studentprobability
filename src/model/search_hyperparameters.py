"""Step 1: Search for best hyperparameters and save them."""

import os
import sys
import importlib.util
import json
from pathlib import Path

# Set up imports from lambda directory using importlib to handle hyphenated directory name
lambda_dir = Path(__file__).resolve().parent.parent / "lambda" / "bi_ml_oead-prob-v2"

# Load holiday_service_lambda first since data_srv_lambda depends on it
holiday_spec = importlib.util.spec_from_file_location(
    "holiday_service_lambda",
    lambda_dir / "holiday_service_lambda.py"
)
holiday_service_lambda = importlib.util.module_from_spec(holiday_spec)
sys.modules["holiday_service_lambda"] = holiday_service_lambda
holiday_spec.loader.exec_module(holiday_service_lambda)

# Load data_contracts_lambda
contracts_spec = importlib.util.spec_from_file_location(
    "data_contracts_lambda",
    lambda_dir / "data_contracts_lambda.py"
)
data_contracts_lambda = importlib.util.module_from_spec(contracts_spec)
sys.modules["data_contracts_lambda"] = data_contracts_lambda
contracts_spec.loader.exec_module(data_contracts_lambda)

# Load data_srv_lambda (now that its dependency holiday_service_lambda is available)
srv_spec = importlib.util.spec_from_file_location(
    "data_srv_lambda",
    lambda_dir / "data_srv_lambda.py"
)
data_srv_lambda = importlib.util.module_from_spec(srv_spec)
sys.modules["data_srv_lambda"] = data_srv_lambda
srv_spec.loader.exec_module(data_srv_lambda)

# Extract the symbols for use in this module
TRAINING_CATEGORICAL_FEATURES = data_contracts_lambda.TRAINING_CATEGORICAL_FEATURES
TRAINING_INTEGER_FEATURES = data_contracts_lambda.TRAINING_INTEGER_FEATURES
build_historical_data = data_contracts_lambda.build_historical_data
DataService = data_srv_lambda.DataService

import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer

# Get SageMaker paths
base_path = Path(__file__).resolve().parent

# Path to training data.
data_path = base_path.parent.parent / "data"
train_path = os.environ.get("SM_CHANNEL_TRAIN", str(data_path))

# Path to model directory.
model_dir = os.environ.get("SM_MODEL_DIR", base_path)

# Path to save best hyperparameters
hyperparams_file = base_path / "best_hyperparameters.json"


def main():
    """Search for best hyperparameters using RandomizedSearchCV."""
    # Load data
    file_path = os.path.join(train_path, "students_prob_show_up_to_lc_data.csv")
    print(f"Loading training data from: {file_path}")

    data = pd.read_csv(file_path)
    target_column = 'J'

    # Enforce data contract for model inputs.
    historical_data = build_historical_data(data, target_column=target_column)

    service = DataService()
    training_data = service.historical_to_training(historical_data)

    X = training_data.X
    y = training_data.y

    print(f"Dataset shape: X={X.shape}, y={y.shape}")

    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"Train/test split: {X_train.shape[0]} / {X_test.shape[0]}")

    # Create preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', TRAINING_INTEGER_FEATURES),
            ('cat', OneHotEncoder(drop='first', handle_unknown='ignore'), TRAINING_CATEGORICAL_FEATURES),
        ]
    )

    model = xgb.XGBClassifier(random_state=42)

    # Create pipeline with preprocessing and model
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', model)
    ])

    # Define hyperparameter search space
    param_distributions = {
        'classifier__n_estimators': [50, 100, 200, 300],
        'classifier__max_depth': [3, 6, 9, 12],
        'classifier__learning_rate': [0.01, 0.05, 0.1, 0.2],
        'classifier__subsample': [0.6, 0.8, 1.0],
        'classifier__colsample_bytree': [0.6, 0.8, 1.0],
        'classifier__gamma': [0, 0.1, 0.2, 0.5],
        'classifier__min_child_weight': [1, 3, 5],
        'classifier__reg_alpha': [0, 0.01, 0.1, 1],
        'classifier__reg_lambda': [0.1, 1, 10],
    }

    # Perform randomized search with cross-validation
    print("\n" + "="*60)
    print("STEP 1: HYPERPARAMETER SEARCH")
    print("="*60)
    search = RandomizedSearchCV(
        pipeline,
        param_distributions=param_distributions,
        n_iter=50,  # Number of parameter settings sampled
        cv=3,  # 3-fold cross-validation
        scoring='roc_auc',  # Optimize for ROC AUC
        random_state=42,
        n_jobs=-1,  # Use all available cores
        verbose=1
    )

    print("Starting hyperparameter search...")
    search.fit(X_train, y_train)

    best_params = search.best_params_
    best_score = search.best_score_

    print(f"\nBest parameters found:")
    for key, value in best_params.items():
        print(f"  {key}: {value}")
    print(f"Best cross-validation score (ROC AUC): {best_score:.4f}")

    # Save best hyperparameters to file
    with open(hyperparams_file, 'w') as f:
        json.dump(best_params, f, indent=2)
    print(f"\nSaved best hyperparameters to: {hyperparams_file}")


if __name__ == "__main__":
    main()
