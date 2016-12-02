# ACM Spider 2.0

> [第一版地址](https://github.com/Raynxxx/CUIT-ACM-Spider) 第一版采用了多线程优化爬虫速度，个人觉得代码不够优雅。

第二版改造了程序运行方式，以异步协程为主


## 主要依赖

* Python 3.5
* Tornado 4.4
* BeautifulSoup
* PyMySQL, SQLAlchemy

## 进度
- [X] 全局日志
- [X] 生产者/消费者队列
- [X] HTTP 接口可开关 Spider
- [X] HDU OJ Spider
- [X] BNU OJ Spider
- [X] Codeforces Spider
- [X] PKU OJ Spider
- [X] HUST Virtual Judge Spider
- [ ] BestCoder Spider
- [ ] 成就触发器