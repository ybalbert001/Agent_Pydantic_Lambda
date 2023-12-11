## 部署方式

## 部署Lambda
- 在cdk部署所在的Ec2中，执行如下命令部署
```bash
sh deploy.sh {region} {agent_tool_name} #for example agent_tool_name = 'get_contact'
```

## 数据摄入脚本

- 连接QAChatDeployStack/Ec2Stack/ProxyInstance, 执行如下脚本进行进行数据摄入。
  + 连接mysql，连接参数请从上一步部署的Lambda的环境变量中进行获取
  + 需要指定本地数据文件，需要上传到这个ec2上
```bash
sudo yum -y install python-pip
pip3 install pymysql pandas sqlalchemy
curl -LJO https://raw.githubusercontent.com/ybalbert001/Agent_Pydantic_Lambda/main/lambda/get_contact/init_mock_data.py
curl -LJO https://raw.githubusercontent.com/ybalbert001/Agent_Pydantic_Lambda/main/lambda/get_contact/data.csv

#注入数据
bash init_mock_data.sh ${region} 
#如何想要清空数据，可以执行如下语句
bash init_mock_data.sh ${region} "truncate"
```

## 测试
```bash
#case 1
{"param" : { "employee" : "Jane" }, "query" : "Jane 负责哪部份？"}

#case 2
{"param" : { "scope" : "SageMaker" }, "query" : "SageMaker 的问题谁负责？"}

#case 3
{"param" : { "scope" : "Lex" , "role" : "Product Manager"}, "query": "Lex的产品经理是谁"}

#case 4 
#测试目的：自动生成建议的问题，把Jene替换成Jane
{"param" : { "employee" : "Jene" }, "query":"Jene负责什么的？"}

#case 5
#测试目的：自动生成建议的问题，把SageMaker Studio替换成SageMaker
{"param" : { "scope" : "SageMaker Studio" }, "query" : "SageMaker Studio的问题联系谁？"}

#case 6
#测试目的：自动生成建议的问题，把Iex替换成Lex
{"param" : { "scope" : "Iex" }, "query" : "Iex的问题该找谁？"}

#case 7
#测试目的：如果没有相似的信息，放弃生成suggested_question
{"param" : { "scope" : "CleanRoom" }, "query" : "CleanRoom的SSA是谁？"}

#case 7
#测试目的：如果没有相似的信息，放弃生成suggested_question
{"param" : { "scope" : "Glue" }, "query" : "Glue的SSA是谁？"}
```