#!/bin/bash

mkdir lambda_code/package

pip install sqlalchemy pymysql pydantic pandas -t ./lambda_code/package

cd lambda_code/package/
zip -r ../my_deployment_package.zip .

cd ..
zip my_deployment_package.zip lambda_function.py