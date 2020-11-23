# Data Crawler

## Requirements

python 3.6.9

8.0.20 MySQL Community Server - GPL

other python packages in requirements.txt

## 项目结构

```shell
.
├── data_crawler
│   ├── fake_agents.json
│   ├── __init__.py
│   ├── items.py # 用与定义所爬下数据的结构
│   ├── middlewares.py # 中间件
│   ├── pipelines.py # pipelines，用于数据的清理、保存
│   ├── settings.py # scrapy项目配置文件
│   └── spiders # 各爬虫
│       ├── acm_spider.py # ACM paper in search result crawler
│       ├── acm_paper_parser.py # 用于处理ACM paper页面的静态方法
│       ├── acm_proceeding_spider.py # ACM proceeding crawler
│       ├── ieee_spider.py # IEEE conferences crawler
│       ├── ieee_author_spider.py
│       ├── ieee_paper_spider.py # IEEE random paper crawler
│       ├── __init__.py
│       └── utils.py # 爬虫所使用的工具
├── fake_agents.json
├── README.md
├── requirements.txt # 配置要求
├── scrapy.cfg
├── scrapy_logs
├── proxies.txt # http代理地址
└── test_files # 暂时存储爬取结果
```

## 运行爬虫

### ACM paper in search result crawler

```shell
scrapy crawl ACM_Search
```

爬取data_crawler/settings.py中ACM_URL中的所有页面。这里要求这些页面是ACM的搜索结果页面。爬虫会爬取搜索出的所有文章的相关信息保存于文件。

### IEEE crawler

#### command

```shell
scrapy crawl IEEE_Conferences_Journals
```

#### settings

/data_crawler/settings.py

```python
# IEEE
# IEEE conferences
IEEE_CONF_URLS = [
    'https://ieeexplore.ieee.org/xpl/conhome/1000064/all-proceedings'
]
# 需要的年份(including 'from' and 'to')
IEEE_YEAR = {
    'from': 2019,
    'to': 2019
}
# IEEE journal
# journal 主页的 url。事实上只需要 punumber
IEEE_JOURNAL_URLS = [
    # 'https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=32'
]
IEEE_JOURNAL_YEAR = {
    'from': 2020,
    'to': 2020
}
```

#### result

爬取 IEEE_CONF_URLS 中所有会议在 IEEE_YEAR 范围内的所有文章

爬取 IEEE_JOURNAL_URLS 中所有期刊在 IEEE_JOURNAL_YEAR 范围内的所有文章

### ACM crawler

#### command

```shell
scrapy crawl ACM_Proceedings_Journals
```

#### settings

/data_crawler/settings.py

```python
### ACM conference proceeding urls
ACM_PROCEEDING_URLS = [
    'https://dl.acm.org/doi/proceedings/10.1145/3238147'
]
### ACM journals
ACM_JOURNAL_URLS = [
    'https://dl.acm.org/loi/tosem'
]
### 需要的年份(including 'from' and 'to')
ACM_JOURNAL_YEAR = {
    'from': 2019,
    'to': 2019
}
```

可以是多个proceeding

#### result

爬取 ACM_PROCEEDING_URLS 中的所有文章

爬取 ACM_JOURNAL_URLS 中 journal 在 ACM_JOURNAL_YEAR 范围内的所有文章

### DEBUG crawler

为了节约时间，模拟spider向pipeline发送数据，用于对pipeline的debug。直接读取之前爬取的内容，然后作为item传给pipeline处理。

#### command

```shell
scrapy crawl debug
```

#### settings

在test_files/crawled_items_debug.json 中放入之前爬的 raw json 结果

#### result

等于不实际发送请求，而是把之前的结果再次发送给pipeline处理


## 结果查看

### Raw Json File

存储结果保存在 /test_files/crawled_items.json中。其中是没有经过处理的所有spider传回的item

### Database

总共有三个数据库：`data_processing`, `data_processing_IEEE`, `data_processing_ACM`

`data_processing_IEEE`, `data_processing_ACM`可以认为分别是 IEEE ACM 数据库的一个子集，具有一样的性质。关键在于，第一，paper id 分别采用其内部 id；第二，reference 的存储采用 1 对 n 关系表来存，只要求 pid（文章 id）和 order（引用的顺序），其他的属性（doi title 等）都作为可为空的属性进行保存，最大程度得保留信息。

其中`data_processing`用与给后端提供数据，我认为类似一个数据仓库的意义。最主要的区别，第一， paper id 是自行设定的，统一两个内部 id；第二，reference 可能不一样，相当于 paper 表内部得有向关系（n 对 n 关系），也就是说只考虑在爬取范围内得 paper 被引用的状况。当然这个 reference 得定义如果有所区别，之后也可以改。另外这一部分还没有完成。

#### setting

如要启动数据库保存，需要在/data_crawler/settings中设置:

1. 配置数据库用户名密码等

   ```python
   # Database
   MYSQL_HOST = 'localhost'
   MYSQL_DBNAME = 'data_processing'
   MYSQL_USER = 'root'
   MYSQL_PASSWORD = 'root'
   MYSQL_PORT = 3306
   ```

2. 启动MysqlPipeline(确保'data_crawler.pipelines.MysqlPipeline': 889的最后这个数字不是None)

   ```python
   ITEM_PIPELINES = {
       'data_crawler.pipelines.RemoveEmptyItemPipeline': 500,
    	'data_crawler.pipelines.JsonWriterPipeline': 888 if not DEBUG else None,
       'data_crawler.pipelines.MysqlPipeline': 889,
   }
   ```
   

#### 数据库初始化

进入Mysql之后运行 source /absolute/path/data_processing.sql (或者在data_processing根目录下进入mysql，可以写相对路径)

**注意此操作会将原名为data_processing的数据库删库**

#### 数据库基本结构（ `data_processing_IEEE`, `data_processing_ACM`）

##### 1. affiliation

TODO: 目前来看，ieee没有affliation的页面，因此也似乎没有内部id，怎么处理暂时不清楚。暂时用name来作为IEEE affiliation的id

| 序号 |     名称      |           描述            |     类型      |  键  | 为空 | 额外 | 默认值 |
| :--: | :-----------: | :-----------------------: | :-----------: | :--: | :--: | :--: | :----: |
|  1   |     `id`      | {ACM内部id}或{IEEE内部id} | varchar(255)  | PRI  |  NO  |      |        |
|  2   |    `name`     |                           | varchar(255)  |      |  NO  |      |        |
|  3   | `description` |                           | varchar(4095) |      | YES  |      |        |

##### 2. domain

| 序号 |  名称  |        描述        |     类型     |  键  | 为空 | 额外 | 默认值 |
| :--: | :----: | :----------------: | :----------: | :--: | :--: | :--: | :----: |
|  1   |  `id`  |                  | varchar(255) | PRI  |  NO  |      |        |
|  2   |  `name`  |  | varchar(255) |   |  NO  |      |        |
|  3   | `url` | 如果是ACM则有url | varchar(255) |      | YES |      |        |

##### 3. paper

| 序号 |        名称        |        描述        |     类型      |  键  | 为空 | 额外 | 默认值 |
| :--: | :----------------: | :----------------: | :-----------: | :--: | :--: | :--: | :----: |
|  1   |        `id`        | IEEE, ACM inner id | varchar(255)  | PRI  |  NO  |      |        |
|  2   |      `title`       |                    | varchar(255)  |      |  NO  |      |        |
|  3   |       `abs`        |      abstract      | varchar(4095) |      |  NO  |      |        |
|  4   |  `publication_id`  |  发表的会议的id  | varchar(255)  |      |  NO  |      |        |
|  5   | `publication_date` | 发表年份，事实上和 publication表冗余，但是为了方便还是直接存了 | varchar(255)  |      |  NO  |      |        |
|  6   |       `link`       | 事实上是 `doi.org/{paper_doi}` | varchar(255)  |      |  YES  |      |        |
|  7   |       `doi`       | 文章 doi | varchar(255)  |      |  YES  |      |        |
|  8  |       `citation`       | 被引量 | int(11) |      |  NO  |      |        |


##### 4. researcher

| 序号 |  名称  |                             描述                             |     类型     |  键  | 为空 | 额外 | 默认值 |
| :--: | :----: | :----------------------------------------------------------: | :----------: | :--: | :--: | :--: | :----: |
|  1   |  `id`  | ACM内部id}或{IEEE内部id}，如 IEEE 内 id 为37085628262，说明其主页是https://ieeexplore.ieee.org/author/37085628262 | varchar(255) | PRI  |  NO  |      |        |
|  2   | `name` |                                                              | varchar(255) |      |  NO  |      |        |

##### 5. publication

| 序号 |        名称        |                 描述                  |     类型     |  键  | 为空 | 额外 | 默认值 |
| :--: | :----------------: | :-----------------------------------: | :----------: | :--: | :--: | :--: | :----: |
|  1   |        `id`        |        使用对应数据库的内部 id        | varchar(255) | PRI  |  NO  |      |        |
|  2   |       `name`       |                                       | varchar(255) |      |  NO  |      |        |
|  3   | `publication_date` |              发表的年份               | varchar(255) |      |  NO  |      |        |
|  4   |      `impact`      | 影响力因子（TODO:目前不知道怎么获得） | varchar(255) |      |  NO  |      |        |


##### 6. paper_reference (in data_processing)

| 序号 | 名称  |        描述        |     类型     |  键  | 为空 | 额外 | 默认值 |
| :--: | :---: | :----------------: | :----------: | :--: | :--: | :--: | :----: |
|  1   | `pid` |      paper id      | varchar(255) | PRI  |  NO  |      |        |
|  2   | `rid` | reference paper id | varchar(255) | PRI  |  NO  |      |        |

##### 6. paper_reference (in data_processing_IEEE and data_processing_ACM)

这用与合并之后提供给 data_processing 库

| 序号 | 名称 | 描述 | 类型 | 键 | 为空 | 额外 | 默认值 |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| 1 | `pid` | paper id | varchar(255) | PRI | NO |  |  |
| 2 | `order` | 第几个引用 | int | PRI | NO |  |  |
| 3 | `r_doi` | reference doi | varchar(255) |  | YES |  |  |
| 4 | `r_title` | reference title | varchar(255) |  | YES |  |  |
| 5 | `r_document_id` | reference document id (如果是来自 IEEE 的文章，则可能有，即 IEEE 内部文章 id) | varchar(255) |  | YES |  |  |
| 6 | `r_citation` | reference citation string | varchar(4095) |  | YES |  |  |

##### 7. paper_researcher

| 序号 |  名称   |     描述      |     类型     |  键  | 为空 | 额外 | 默认值 |
| :--: | :-----: | :-----------: | :----------: | :--: | :--: | :--: | :----: |
|  1   |  `pid`  |   paper id    | varchar(255) | PRI  |  NO  |      |        |
|  2   |  `rid`  | researcher id | varchar(255) | PRI  |  NO  |      |        |
|  3   | `order` |   第几作者    | varchar(255) |      |  NO  |      |        |

##### 8. paper_domain

| 序号 | 名称  |   描述    |     类型     |  键  | 为空 | 额外 | 默认值 |
| :--: | :---: | :-------: | :----------: | :--: | :--: | :--: | :----: |
|  1   | `pid` | paper id  | varchar(255) | PRI  |  NO  |      |        |
|  2   | `did` | domain id | varchar(255) | PRI  |  NO  |      |        |

##### 9. researcher_affiliation

代表某学者在某年在某机构发表了文章

| 序号 |  名称  |       描述       |     类型     |  键  | 为空 | 额外 | 默认值 |
| :--: | :----: | :--------------: | :----------: | :--: | :--: | :--: | :----: |
|  1   | `rid`  |  researcher id   | varchar(255) | PRI  |  NO  |      |        |
|  2   | `aid`  |  affiliation id  | varchar(255) | PRI  |  NO  |      |        |
|  3   | `year` | 在某年发表了文章 | varchar(255) | PRI  |  NO  |      |        |

## 其他设置

### Log

log保存在 /scrapy_logs中

### Proxy

在proxies.txt中列出http代理的ip和端口号，自动随机切换代理。

格式为一行一个，ip:端口号

如果不需要代理则在settings中将rotating_proxies.middlewares.RotatingProxyMiddleware、rotating_proxies.middlewares.BanDetectionMiddleware两个中间件禁用

