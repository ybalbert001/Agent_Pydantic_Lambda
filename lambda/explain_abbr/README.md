## 部署方式

## 部署Lambda
- 在cdk部署所在的Ec2中，执行如下命令部署
```bash
sh deploy.sh {region} {agent_tool_name} #for example agent_tool_name = 'explain_abbr'
```

## 数据摄入脚本

- 连接QAChatDeployStack/Ec2Stack/ProxyInstance, 执行如下脚本进行进行数据摄入。
  + 连接mysql，连接参数请从上一步部署的Lambda的环境变量中进行获取
  + 需要指定本地数据文件，需要上传到这个ec2上
```bash
sudo yum -y install python-pip
pip3 install pymysql pandas sqlalchemy openpyxl
curl -LJO https://raw.githubusercontent.com/ybalbert001/Agent_Pydantic_Lambda/main/lambda/explain_abbr/ingest_data.py
curl -LJO https://raw.githubusercontent.com/ybalbert001/Agent_Pydantic_Lambda/main/lambda/explain_abbr/ingest_data.sh
curl -LJO https://raw.githubusercontent.com/ybalbert001/Agent_Pydantic_Lambda/main/lambda/explain_abbr/abbr.xlsx

#注入数据
bash ingest_data.sh ${region} 
#如何想要清空数据，可以执行如下语句
bash ingest_data.sh ${region} "truncate"
```

## 连接mysql
```
sudo yum install mysql -y
mysql --host=<host> --port=3306 --user=<username> --password=<pwd> simple_info_db
```
:



## 测试
```bash
#case 1
{"param" : { "abbr" : "WWSO" }, "query" : "WWSO是什么意思"}

#case 2
{"param" : { "abbr" : "WBR" }, "query" : "WBR是啥意思"}

#case 3
{"param" : { "abbr" : "YOY"}, "query": "YOY"}

#case 4
{"param" : { "abbr" : "ADBC" }, "query" : "ADBC是什么意思"}

#case 5
{"param" : { "abbr" : "MDU" }, "query" : "缩写MDU"}
```