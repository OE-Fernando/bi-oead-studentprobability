# inference.py

import os
import json
import joblib
import numpy as np
import pandas as pd
from io import StringIO


def model_fn(model_dir):
    """Load model from the model directory."""
    model_path = os.path.join(model_dir, "pipeline.joblib")
    model = joblib.load(model_path)
    return model


def input_fn(request_body, request_content_type):
    if request_content_type == "application/json":

        if isinstance(request_body, bytes):
            request_body = request_body.decode("utf-8")

        data = json.loads(request_body)
        df = pd.DataFrame([data])
        return df

    elif request_content_type == "text/csv":

        if isinstance(request_body, bytes):
            request_body = request_body.decode("utf-8")

        return pd.read_csv(StringIO(request_body))

    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")


def predict_fn(input_data, model):
    """Return probability of positive class."""

    probabilities = model.predict_proba(input_data)

    # probability of class 1
    positive_class_probs = probabilities[:, 1]

    return positive_class_probs


def output_fn(prediction, content_type):
    """Format prediction output."""

    if content_type == "application/json":
        return json.dumps(prediction.tolist())

    elif content_type == "text/csv":
        return ",".join(map(str, prediction))

    else:
        raise ValueError(f"Unsupported content type: {content_type}")