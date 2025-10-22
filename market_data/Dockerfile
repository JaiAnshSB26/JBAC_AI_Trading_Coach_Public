# Dockerfile for building Lambda package with yfinance on Linux
FROM public.ecr.aws/lambda/python:3.11

# Install zip utility
RUN yum install -y zip

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt -t /tmp/lambda_package/

# Copy handler
COPY handler.py /tmp/lambda_package/

# Create the zip file
WORKDIR /tmp/lambda_package
RUN zip -r /tmp/lambda_package.zip .

# Output instructions
CMD ["echo", "Package built at /tmp/lambda_package.zip"]
