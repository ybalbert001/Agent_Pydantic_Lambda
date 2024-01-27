import boto3
import json
import sys

new_env_key = sys.argv[1]
new_env_value = sys.argv[2]
# 创建 Lambda 客户端
lambda_client = boto3.client('lambda')

# 定义函数名称和新的环境变量
function_name = 'Chat_Agent'

response = lambda_client.get_function_configuration(FunctionName=function_name)
old_env = response['Environment']['Variables']

env_vars = {**old_env}
env_vars[new_env_key] = new_env_value
print(f"env_vars:{env_vars}")

response = lambda_client.update_function_configuration(
                FunctionName=function_name, Environment={"Variables": env_vars}
            )
print(response)