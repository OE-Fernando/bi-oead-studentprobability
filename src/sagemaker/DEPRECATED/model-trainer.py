import boto3
import pandas as pd
import xgboost as xgb
import sklearn
from pathlib import Path
import sys
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
import joblib
from io import BytesIO
import tarfile

# Make repository root importable when running this file directly.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from services.data_contracts import (
    TRAINING_CATEGORICAL_FEATURES,
    TRAINING_INTEGER_FEATURES,
    build_training_data,
)
from project_paths import PATHS, s3_uri


def _build_requirements_text() -> str:
    # Pin training-time package versions so inference can install matching deps.
    return "\n".join(
        [
            f"scikit-learn=={sklearn.__version__}",
            f"xgboost=={xgb.__version__}",
            f"pandas=={pd.__version__}",
            f"joblib=={joblib.__version__}",
        ]
    ) + "\n"


def _build_model_artifact(pipeline) -> BytesIO:
    model_buffer = BytesIO()
    joblib.dump(pipeline, model_buffer)
    model_buffer.seek(0)

    inference_script_path = Path(__file__).with_name("inference.py")
    if not inference_script_path.exists():
        raise FileNotFoundError(f"Missing inference script: {inference_script_path}")

    requirements_text = _build_requirements_text()

    tar_buffer = BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
        model_tarinfo = tarfile.TarInfo(name="model.pkl")
        model_bytes = model_buffer.getvalue()
        model_tarinfo.size = len(model_bytes)
        tar.addfile(model_tarinfo, BytesIO(model_bytes))

        inference_bytes = inference_script_path.read_bytes()
        inference_tarinfo = tarfile.TarInfo(name="code/inference.py")
        inference_tarinfo.size = len(inference_bytes)
        tar.addfile(inference_tarinfo, BytesIO(inference_bytes))

        requirements_bytes = requirements_text.encode("utf-8")
        requirements_tarinfo = tarfile.TarInfo(name="code/requirements.txt")
        requirements_tarinfo.size = len(requirements_bytes)
        tar.addfile(requirements_tarinfo, BytesIO(requirements_bytes))

    tar_buffer.seek(0)
    return tar_buffer


def train_xgboost_model(target_column: str = "y"):
    # Initialize S3 client
    s3_client = boto3.client("s3")

    # Download data from S3 to memory
    data_buffer = BytesIO()
    s3_client.download_fileobj(PATHS.bucket_name, PATHS.training_data_key, data_buffer)
    data_buffer.seek(0)

    df = pd.read_csv(data_buffer)

    # Enforce data contract for model inputs.
    training_data = build_training_data(df, target_column=target_column)
    X = training_data.X
    y = training_data.y

    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Create preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", TRAINING_INTEGER_FEATURES),
            ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), TRAINING_CATEGORICAL_FEATURES),
        ]
    )

    # Create XGBoost model
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
    )

    # Create pipeline with preprocessing and model
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", model),
    ])

    # Train the pipeline
    pipeline.fit(X_train, y_train)

    # Evaluate the model
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    model_artifact = _build_model_artifact(pipeline)

    # Upload model.tar.gz artifact to S3
    s3_client.upload_fileobj(model_artifact, PATHS.bucket_name, PATHS.pipeline_output_key)

    print(f"Model artifact uploaded to S3: {s3_uri(PATHS.pipeline_output_key)}")
    print(
        "Pinned runtime versions:",
        {
            "scikit-learn": sklearn.__version__,
            "xgboost": xgb.__version__,
            "pandas": pd.__version__,
            "joblib": joblib.__version__,
        },
    )

    return s3_uri(PATHS.pipeline_output_key)


if __name__ == "__main__":
    model_s3_path = train_xgboost_model()
    print(f"Training completed. Model available at: {model_s3_path}")
