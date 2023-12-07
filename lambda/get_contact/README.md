## 部署方式

## 部署Lambda
- 在cdk部署所在的Ec2中，执行如下命令部署
```bash
sh deploy.sh {region} {agent_tool_name} #for example agent_tool_name = 'get_contact'
```

## 数据摄入脚本

- 连接QAChatDeployStack/Ec2Stack/ProxyInstance, 执行如下脚本进行进行数据摄入。
  需要连接mysql，连接参数请从上一步部署的Lambda的环境变量中进行获取
```bash
sudo yum -y install python-pip
pip3 install pymysql pandas sqlalchemy
curl -LJO https://raw.githubusercontent.com/ybalbert001/Agent_Pydantic_Lambda/lambda/get_contact/init_mock_data.py
python3 init_mock_data.py --host db-instance-name.cd9gl0lywxoi.us-west-2.rds.amazonaws.com --username {db_username} --password {db_password} --db_name simple_info_db --csv_file "./data.csv"
```

