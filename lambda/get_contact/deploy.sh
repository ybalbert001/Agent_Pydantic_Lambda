#!/bin/bash

# Check if jq is installed
if ! command -v jq &> /dev/null ;then
    echo "jq could not be found. Please install jq [sudo yum install jq or sudo apt install jq] at first." 
    exit 1
fi

db_subnet_group_name="test_subnet_group_name" #agent_db_group
db_username="db1username"                   #db_username
db_password="db1password"                   #db_password
db_instance_name="db-instance-name"         #agent-db-instance
db_name="simple_info_db"
db_table_name='employee'

region="us-west-2"
stack_name="QAChatDeployStack"
db_az="${region}a"

vpc_id=$(aws cloudformation describe-stacks --stack-name "QAChatDeployStack" --region "us-west-2" --query 'Stacks[0].Outputs[?OutputKey==`VPC`].{OutputValue: OutputValue}' | jq ".[].OutputValue")
echo $vpc_id

sg_id=$(aws ec2 describe-security-groups --filters Name=vpc-id,Values="$vpc_id" | jq ".SecurityGroups[0].GroupId")
sg_id=${sg_id//\"}
echo $sg_id

subnet_ids=$(aws ec2 describe-subnets --filters Name=vpc-id,Values="$vpc_id" | jq -r '.Subnets | map(.SubnetId) | join(" ")')
echo $subnet_ids

subnet_ids_list=$(aws ec2 describe-subnets --filters Name=vpc-id,Values="$vpc_id" | jq -r '.Subnets | map(.SubnetId) | join(",")')
echo $subnet_ids_list

aws rds create-db-subnet-group \
    --db-subnet-group-name $db_subnet_group_name \
    --db-subnet-group-description "DB Subnet Group For Agent" \
    --subnet-ids $subnet_ids

db_subnet_group_name="test_subnet_group_name"
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

#prepare lambda code zip
sudo yum -y install python-pip
mkdir -p lambda_code/package
pip install sqlalchemy pymysql pydantic pandas -t ./lambda_code/package

cd lambda_code/package/
zip -r ../my_deployment_package.zip .
cd ..
zip my_deployment_package.zip ../lambda_function.py
cd ..

#prepare lambda iam role
policy=$(aws iam create-policy --policy-name MyCustomPolicy2 --policy-document file://lambda_role_policy.json)
policy_arn=$(echo $policy | jq '.Policy.Arn')
policy_arn=${policy_arn//\"}

iam_role=$(aws iam create-role \
    --role-name AgentLambdaRole2 \
    --assume-role-policy-document '{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"},"Action": "sts:AssumeRole"}]}')
role_name=$(echo $iam_role | jq '.Role.RoleName')
role_name=${role_name//\"}
role_arn=$(echo $iam_role | jq '.Role.Arn')
role_arn=${role_arn//\"}

aws iam attach-role-policy --role-name $role_name \
    --policy-arn $policy_arn

aws lambda create-function --function-name agent_tool_get_contact \
    --zip-file fileb://lambda_code/my_deployment_package.zip --runtime python3.10 \
    --handler lambda_function.lambda_handler --timeout 10 --region $region \
    --role $role_arn \
    --vpc-config SubnetIds=$subnet_ids_list,SecurityGroupIds=$sg_id

env_list="{db_username='${db_username}',db_password='${db_password}',db_host='${db_host}',db_port='${db_port}',db_name='${db_name}',db_table_name='${db_table_name}'}"

aws lambda update-function-configuration --function-name agent_tool_get_contact \
    --environment Variables=$env_list

