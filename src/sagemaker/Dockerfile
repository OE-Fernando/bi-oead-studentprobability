# Use the official SageMaker Scikit-learn inference image as the base.
# Replace the base image account and region if you use a different region.
# FROM 683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.2-1
FROM 683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1

# Copy inference code and Python dependency list into the image.
COPY src/model/inference.py /opt/program/inference.py
COPY src/model/requirements.txt /opt/program/requirements.txt

WORKDIR /opt/program

# Install Python dependencies needed for our custom inference code.
RUN pip install --no-cache-dir -r /opt/program/requirements.txt

# Configure SageMaker entrypoint for the custom image.
ENV SAGEMAKER_PROGRAM=inference.py
ENV SAGEMAKER_SUBMIT_DIRECTORY=/opt/program
