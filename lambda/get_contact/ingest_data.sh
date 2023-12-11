#!/bin/bash

# Check if jq is installed
if ! command -v jq &> /dev/null ;then
    echo "jq could not be found. Please install jq [sudo yum install jq or sudo apt install jq] at first." 
    exit 1
fi

region=$1
flag=$2

db_table_name=$(aws lambda get-function-configuration --function-name agent_tool_get_contact --region ${region} | jq '.Environment.Variables.db_table_name')
db_table_name=${db_table_name//\"}
echo $db_table_name

db_password=$(aws lambda get-function-configuration --function-name agent_tool_get_contact --region ${region} | jq '.Environment.Variables.db_password')
db_password=${db_password//\"}
echo $db_password

db_port=$(aws lambda get-function-configuration --function-name agent_tool_get_contact --region ${region} | jq '.Environment.Variables.db_port')
db_port=${db_port//\"}
echo $db_port

db_name=$(aws lambda get-function-configuration --function-name agent_tool_get_contact --region ${region} | jq '.Environment.Variables.db_name')
db_name=${db_name//\"}
echo $db_name

db_username=$(aws lambda get-function-configuration --function-name agent_tool_get_contact --region ${region} | jq '.Environment.Variables.db_username')
db_username=${db_username//\"}
echo $db_username

db_host=$(aws lambda get-function-configuration --function-name agent_tool_get_contact --region ${region} | jq '.Environment.Variables.db_host')
db_host=${db_host//\"}
echo $db_host

python3 ingest_data.py --host ${db_host} --username ${db_username} --password ${db_password} --db_name ${db_name} --csv_file "./data.csv" --flag "$flag" 
