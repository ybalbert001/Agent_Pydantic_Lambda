#!/bin/bash

# Check if jq is installed
if ! command -v jq &> /dev/null ;then
    echo "jq could not be found. Please install jq [sudo yum install jq or sudo apt install jq] at first." 
    exit 1
fi

region=$1
agent_name=$2
agent_id=$RANDOM
db_subnet_group_name="db_subnet_group_name_${agent_id}"

db_instance_name="db-instance-agent"
db_name="simple_info_db"
db_table_name='employee'
lambda_function_name="agent_tool_$agent_name"
policy_name="policy$agent_id"
role_name="role$agent_id"

stack_name="QAChatDeployStack"
db_az="${region}a"

echo "<Configurations>"
echo "region=$region"
echo "db_subnet_group_name=$db_subnet_group_name"
echo "db_username=$db_username"
echo "db_password=$db_password"
echo "db_instance_name=$db_instance_name"
echo "db_name=$db_name"
echo "db_table_name=$db_table_name"
echo "lambda_function_name=$lambda_function_name"
echo "policy_name=$policy_name"
echo "role_name=$role_name"
echo "</Configurations>"
echo 

echo "Step1. Creating Database instance of RDS(Mysql).."
vpc_id=$(aws cloudformation describe-stacks --stack-name "QAChatDeployStack" --region "${region}" --query 'Stacks[0].Outputs[?OutputKey==`VPC`].{OutputValue: OutputValue}' | jq ".[].OutputValue")
echo "vpc_id: $vpc_id"

sg_id=$(aws ec2 describe-security-groups --filters Name=vpc-id,Values=$vpc_id | jq '.SecurityGroups[] | select(.GroupName | contains("lambdasecuritygroup")) | .GroupId')
sg_id=${sg_id//\"}
echo "sg_id: $sg_id"

subnet_ids=$(aws ec2 describe-subnets --filters Name=vpc-id,Values=$vpc_id | jq -r '.Subnets | map(.SubnetId) | join(" ")')
echo "subnet_ids: $subnet_ids"

subnet_ids_list=$(aws ec2 describe-subnets --filters Name=vpc-id,Values=$vpc_id | jq -r '.Subnets | map(.SubnetId) | join(",")')
echo "subnet_ids_list: $subnet_ids_list"

aws rds describe-db-instances --db-instance-identifier $db_instance_name --region ${region}

if [ $? -ne 0 ]; then  
    echo "There is no database instance existed."
    echo

    db_username="username${agent_id}"                   
    db_password="password${agent_id}"

    aws rds create-db-subnet-group \
        --db-subnet-group-name $db_subnet_group_name \
        --db-subnet-group-description "DB Subnet Group For Agent" \
        --subnet-ids $subnet_ids

    aws rds create-db-instance \
        --db-instance-identifier $db_instance_name \
        --allocated-storage 50 \
        --db-instance-class db.r6g.large \
        --engine mysql \
        --master-username $db_username \
        --master-user-password $db_password \
        --vpc-security-group-ids $sg_id \
        --availability-zone $db_az \
        --db-subnet-group-name $db_subnet_group_name

    echo "write username/password to ssm"
    aws ssm put-parameter --name "agent_db_username" --value "$db_username" --type String --overwrite
    aws ssm put-parameter --name "agent_db_password" --value "$db_password" --type String --overwrite
else
    echo "read username/password from ssm"
    db_username=$(aws ssm get-parameter --name "agent_db_username" | jq '.Parameter.Value')
    db_username=${db_username//\"}
    db_password=$(aws ssm get-parameter --name "agent_db_password" | jq '.Parameter.Value')
    db_password=${db_password//\"}
fi


db_host=""
db_port=3306
while true; do
    ret=$(aws rds describe-db-instances --db-instance-identifier $db_instance_name)
    db_status=$(echo $ret | jq '.DBInstances[0].DBInstanceStatus')
    if [ "$db_status" = "\"available\"" ]; then
        echo "db instnace launched."
        db_host=$(echo $ret | jq '.DBInstances[0].Endpoint.Address')
        db_host=${db_host//\"}
        db_port=$(echo $ret | jq '.DBInstances[0].Endpoint.Port')
        echo "db_host: $db_host"
        echo "db_port: $db_port"
        break
    else
        echo "Waiting for db instnace launch..."
        sleep 3
    fi
done

echo
echo "Step2. Creating Lambda assets(zip, iamrole).."
#prepare lambda code zip
sudo yum -y install python-pip
mkdir -p lambda_code/package

pip install \
--platform manylinux2014_x86_64 \
--target=./lambda_code/package \
--implementation cp \
--python-version 3.10 \
--only-binary=:all: --upgrade sqlalchemy pymysql pydantic pandas cryptography

cd lambda_code/package/
zip -r ../my_deployment_package.zip .
cd ..
zip my_deployment_package.zip ../lambda_function.py
cd ..

bucket_name=$(aws cloudformation describe-stacks --stack-name "QAChatDeployStack" --region "${region}" --query 'Stacks[0].Outputs[?OutputKey==`UPLOADBUCKET`].{OutputValue: OutputValue}' | jq ".[].OutputValue")
bucket_name=${bucket_name//\"}
s3_bucket_path="s3://$bucket_name/lambda_code/"
aws s3 cp ./lambda_code/my_deployment_package.zip $s3_bucket_path

policy_name="policy$agent_id"
role_name="role$agent_id"
#prepare lambda iam role
policy=$(aws iam create-policy --policy-name $policy_name --policy-document file://lambda_role_policy.json)
policy_arn=$(echo $policy | jq '.Policy.Arn')
policy_arn=${policy_arn//\"}

iam_role=$(aws iam create-role \
    --role-name $role_name \
    --assume-role-policy-document '{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"},"Action": "sts:AssumeRole"}]}')
role_arn=$(echo $iam_role | jq '.Role.Arn')
role_arn=${role_arn//\"}

aws iam attach-role-policy --role-name $role_name \
    --policy-arn $policy_arn

echo "role_arn: $role_arn"
echo "policy_arn: $policy_arn"
sleep 15

echo
echo "Step3. Creating Lambda and setup its configuration."
aws lambda create-function --function-name $lambda_function_name \
    --code S3Bucket=$bucket_name,S3Key=lambda_code/my_deployment_package.zip \
    --runtime python3.10 \
    --handler lambda_function.lambda_handler --timeout 10 --region $region \
    --role $role_arn \
    --vpc-config SubnetIds=$subnet_ids_list,SecurityGroupIds=$sg_id

while true; do
    ret=$(aws lambda get-function --function-name $lambda_function_name | jq '.Configuration.State')
    if [ "$ret" = "\"Active\"" ]; then
        break
    else
        echo "Waiting for lambda launch..."
        sleep 3
    fi
done

env_list="{db_username='${db_username}',db_password='${db_password}',db_host='${db_host}',db_port='${db_port}',db_name='${db_name}',db_table_name='${db_table_name}'}"

aws lambda update-function-configuration --function-name $lambda_function_name \
    --environment Variables=$env_list

echo "step3: register all agent tool lambdas into Chat_Agent env"
all_agent_lambdas=$(aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'agent_tool')].FunctionName" --output text | tr '\t' ',')

python3 add_lambda_env.py "agent_tools" "${all_agent_lambdas}"

