"""Step 2: Train final model using best hyperparameters."""

import os
import sys
import importlib.util
import json
from pathlib import Path

import joblib

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

# Load get_dynamodb_item (needed by student_srv_lambda)
dynamo_spec = importlib.util.spec_from_file_location(
    "get_dynamodb_item",
    lambda_dir / "get_dynamodb_item.py"
)
get_dynamodb_item = importlib.util.module_from_spec(dynamo_spec)
sys.modules["get_dynamodb_item"] = get_dynamodb_item
dynamo_spec.loader.exec_module(get_dynamodb_item)

# Load time_srv_lambda
time_spec = importlib.util.spec_from_file_location(
    "time_srv_lambda",
    lambda_dir / "time_srv_lambda.py"
)
time_srv_lambda = importlib.util.module_from_spec(time_spec)
sys.modules["time_srv_lambda"] = time_srv_lambda
time_spec.loader.exec_module(time_srv_lambda)

# Load student_srv_lambda (depends on get_dynamodb_item)
student_spec = importlib.util.spec_from_file_location(
    "student_srv_lambda",
    lambda_dir / "student_srv_lambda.py"
)
student_srv_lambda = importlib.util.module_from_spec(student_spec)
sys.modules["student_srv_lambda"] = student_srv_lambda
student_spec.loader.exec_module(student_srv_lambda)

# Load data_srv_lambda (now that all its dependencies are available)
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
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, classification_report, log_loss, roc_auc_score

# Get SageMaker paths
base_path = Path(__file__).resolve().parent

# Path to training data.
data_path = base_path.parent.parent / "data"
train_path = os.environ.get("SM_CHANNEL_TRAIN", str(data_path))

# Path to save the trained model.
model_dir = os.environ.get("SM_MODEL_DIR", base_path)

# Path to best hyperparameters file
hyperparams_file = base_path / "best_hyperparameters.json"


def evaluate_model(pipeline, X_train, y_train, X_test, y_test):
    """Print model quality indicators after training."""
    y_train_pred = pipeline.predict(X_train)
    y_test_pred = pipeline.predict(X_test)

    train_accuracy = accuracy_score(y_train, y_train_pred)
    test_accuracy = accuracy_score(y_test, y_test_pred)

    print("\nModel quality indicators:")
    print(f"  Training accuracy: {train_accuracy:.4f}")
    print(f"  Test accuracy:     {test_accuracy:.4f}")

    try:
        y_test_proba = pipeline.predict_proba(X_test)[:, 1]
        roc_auc = roc_auc_score(y_test, y_test_proba)
        ll = log_loss(y_test, pipeline.predict_proba(X_test))
        print(f"  Test ROC AUC:      {roc_auc:.4f}")
        print(f"  Test log loss:     {ll:.4f}")
    except Exception as exc:
        print(f"  Skipping probability-based metrics: {exc}")

    print("\nClassification report (test set):")
    print(classification_report(y_test, y_test_pred, digits=4))


def main():
    """Train model using best hyperparameters and save it."""
    print("="*60)
    print("STEP 2: TRAIN WITH BEST HYPERPARAMETERS")
    print("="*60)
    
    # Load best hyperparameters
    if not hyperparams_file.exists():
        raise FileNotFoundError(
            f"Best hyperparameters file not found: {hyperparams_file}\n"
            "Please run search_hyperparameters.py first."
        )
    
    with open(hyperparams_file, 'r') as f:
        best_params = json.load(f)
    
    print(f"Loaded best hyperparameters from: {hyperparams_file}")
    print("Best parameters:")
    for key, value in best_params.items():
        print(f"  {key}: {value}")

    # Load data
    file_path = os.path.join(train_path, "students_prob_show_up_to_lc_data.csv")
    print(f"\nLoading training data from: {file_path}")

    data = pd.read_csv(file_path)
    target_column = 'didGoToClass'

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

    # Create XGBoost classifier with best hyperparameters
    model = xgb.XGBClassifier(random_state=42, **best_params)

    # Create pipeline with preprocessing and model
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', model)
    ])

    # Train the model
    print("\nTraining model with best hyperparameters...")
    pipeline.fit(X_train, y_train)

    # Evaluate model
    evaluate_model(pipeline, X_train, y_train, X_test, y_test)

    # Save the trained model
    output_path = os.path.join(model_dir, "pipeline.joblib")
    joblib.dump(pipeline, output_path)
    print(f"\nSaved trained pipeline to: {output_path}")


if __name__ == "__main__":
    main()