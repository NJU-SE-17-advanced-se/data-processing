# 合并（非同源数据合并）

## 目标结果

1. 不同源的文章合并
2. 有重叠文章的作者合并
3. publication 统一以年份来分，即合并同年的 issue
4. 不同源的 publication 合并
5. affiliation 合并（需要额外数据）

## 假设依赖

1. 同源的 paper 不存在重复。

   最多只可能有两篇文章合并，不可能有三或以上的文章的合并；paper 的合并一定是非同源的。

2. 只考虑两个源的合并（不考虑拓展性）

3. domain 简单的认为是单词

## 一些问题

1. ACM paper id 是 doi，不符合 id 规范

2. ACM paper 的 id 可能是 doi，但是目前难以判断是否是（可能没注册），因此某文章存在 doi，但是 ACM 的 id 不是这个doi，只是“内部 id”

   所以说，对应同一个 doi 的一定是同一文章，有不同 doi 的却未必不是一篇文章（可能其中一个 doi 是假的）

3. 可能需要记录合并状况

4. affiliation 的合并可能需要额外信息

   如果通过重复文章的对应作者的affiliation合并，现在没有affiliation 和 paper 的关系，只有作者的某时间 affiliation。需要添加表象进行合并
   
5. 可能需要对 domain 进一步清洗，例如 “software”和“Software”应该是一个（大小写），再如有无复数等。

## 额外表项

#### publication_mapping

id_main 为主 id

#### paper_mapping

记录两个 paper（一定是非同源得）的合并

id_main: 主id（这里是 IEEE paper id）

id: 原 id

src： （acm 或 ieee）来源于哪

#### researcher_mapping

id_main

id

src： （acm 或 ieee）

#### researcher_all

所有的 researcher，可能含有需要合并的。通过 researcher_merge 表进行记录

## 合并计划

1. publication 处理

   1. 名字一样，publication_date 一样的进行合并，记录于 publication_merge 中

2. paper 表处理

   1. （所有入库时修改 publication id）

   2. 所有 IEEE paper 入库，id 加 IEEE 前缀，然后 encode。记录于mapping表

   3. 遍历 ACM paper，判断合并库是否存在对应的paper

      判断方式：doi + title + publication year（优先 doi，如果doi一样一定可以合并，否则的话判断 title 和 publication year）

      1. 存在：
      2. 在 paper_merge 中记录合并
      3. 将可能的额外信息加入合并库的 paper 表中
      4. 不存在：将此文章，id 加 ACM 前缀，encode，之后插入合并库

3. domain 和 paper_domain 处理

   1. IEEE ACM domain 先后入库，重新计算 id，仍使用 hash

   2. 对照 paper_merge 表将两个库的 paper_domain 简单合并

      由于目前 domain 的 id 就是做 hash，因此合并完全不需要处理。

4. affiliation 处理

   1. 所有的 affiliation 统一入库。
   2. 之后可能对 affiliation 进行清洗，注意同时修改 researcher_affiliation 表

5. researcher 处理

   1. 两个数据库的 researcher 表全部入合并库 researcher_all，主要是修改 id，对应的分库 paper_researcher 也入合并库 paper_researcher_all ，同时修改 id
   2. 对 paper_merge 表中的所有文章，如果在 paper_researcher_all 有 order 相同，pid 在 paper_merge 中的，记录于 researcher_merge 中。这一步需要保证选取了“主 id”，避免之后还需要做图的遍历。把主 id 的paper_researcher 入合并库 paper_researcher 中
   3. 通过 researcher_merge 对 researcher_all 合并（修改id），结果加入合并库的 researcher 表中
   4. researcher_affiliation 把 researcher id 修改为主 id（如果有），然后入合并库

