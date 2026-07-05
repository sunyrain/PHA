# PHA 专家核心整合版：检索关键词、字段与反向设计结构

日期：2026-07-01

定位：以专家意见为核心，将 PHA 从“蛋白-水凝胶吸附事实库”升级为“生物界面、多蛋白竞争吸附、protein corona、工艺匹配和 AI 反向设计”一体化数据框架。

## 一、核心目标

| 层面 | 目标 |
| --- | --- |
| 文献数据 | 系统抽取不同水凝胶对不同蛋白的动态吸附、竞争吸附、选择性吸附、低吸附和抗污染行为。 |
| 生物界面 | 覆盖血液接触材料、创面敷料、抗污染表面、炎症/补体/血小板等界面响应。 |
| 多蛋白体系 | 支持 serum/plasma/混合蛋白、protein corona、Vroman 效应和蛋白交换数据。 |
| 反向设计 | 面向“吸附一批蛋白、不吸附一批蛋白”的约束，输出候选水凝胶、制备路线和使用工艺。 |
| AI 建模 | 为分类、容量预测、选择性排序、机制标签和工艺推荐提供可训练数据。 |

## 二、专家核心检索组

| 检索组 | 主题 | 核心关键词方向 | WOS | Scopus | 数据用途 |
| ---: | --- | --- | ---: | ---: | --- |
| Q1 | 定量吸附与物性关联 | protein adsorption/binding、capacity、isotherm、kinetic、zeta potential、swelling、pore/mesh size、modulus、contact angle | 902 | 878 | 容量预测、物性-吸附关系 |
| Q2 | 命名模型蛋白 | BSA、HSA、albumin、lysozyme、fibrinogen、hemoglobin、IgG、antibody、transferrin、ferritin 等 | 3,169 | 3,099 | 蛋白描述符和模型蛋白响应 |
| Q3 | 生物界面与血液接触水凝胶 | blood-contacting、hemocompatibility、biointerface、platelet adhesion、complement activation、foreign body response | 1,081 | 731 | 血液接触、抗炎、界面响应 |
| Q4 | 选择性亲和/印迹/螯合/适配体/离子交换 | molecularly imprinted、affinity、ion-exchange、boronate、metal chelate、Ni-NTA、aptamer | 141 | 135 | 选择性吸附和机制规则 |
| Q5 | 低吸附/抗污染 | low/reduced/minimal protein adsorption、protein resistant、biofouling、antifouling、zwitterionic、PEGylated | 3,831 | 4,283 | 不吸附/弱吸附负样本 |
| Q6 | 多蛋白竞争吸附与 protein corona | competitive adsorption、multi-protein adsorption、protein corona、protein exchange、serum/plasma adsorption、Vroman effect | 761 | 511 | 多蛋白吸附向量和竞争选择性 |
| Q7 | 机理和物性驱动吸附 | electrostatic、hydrophobic、hydrogen bonding、size exclusion、pI、protein unfolding、hydration layer、corona | 2,003 | 1,949 | 机制标签和可解释设计 |
| Q8 | 分离/纯化水凝胶吸附剂 | protein separation/purification/capture、affinity chromatography、ion exchange、dynamic binding capacity、elution | 1,871 | 1,375 | 分离纯化和工艺匹配 |
| Q9 | 配方/制备/工艺窗口 | formulation、fabrication、crosslinking density、gelation、cryopolymerization、grafting、coating、regeneration、scale-up | 972 | 953 | 可复现实验和制备工艺 |
| Q10 | 水凝胶库/高通量/数据驱动设计 | hydrogel library、combinatorial、high-throughput、hydrogel array、machine learning、inverse design、binding profile | 53 | 67 | AI-ready 数据集和材料 panel |

## 三、记录粒度

| 原则 | 定义 |
| --- | --- |
| 基础记录 | 一条记录 = 论文 + 水凝胶材料 + 蛋白靶标 + 实验条件 + 测量结果。 |
| 多蛋白记录 | 血清、血浆、混合蛋白、protein corona 或竞争吸附体系应保留蛋白 panel、蛋白排序和竞争结果。 |
| 反向设计视图 | 将单条记录进一步汇总成“水凝胶-条件-蛋白响应矩阵”，用于表达吸附集合和排斥集合。 |
| 工艺视图 | 制备方法、交联/接枝/涂覆、洗脱、再生、灭菌、保存和放大风险应能从记录中独立检索。 |

## 四、字段模块

| 模块 | 核心字段 |
| --- | --- |
| 来源和证据 | 记录编号、DOI、题名、年份、期刊、检索组、来源章节/图表、证据文本、提取方式、置信度、审核状态 |
| 文献相关性 | 纳入/待定/排除、研究类型、是否定量、是否有对照、是否适合训练 |
| 水凝胶组成和制备 | 水凝胶形态、骨架、单体、比例、交联剂、引发剂、合成方法、溶剂、制备 pH/温度、官能团、配体、金属桥联、模板、复合组分、基底、后处理 |
| 水凝胶物性 | 电荷类型、响应类型、LCST、溶胀、含水量、孔隙率、孔径、网孔尺寸、粒径、ζ 电位、接触角、模量、黏附能、渗透性、稳定性、形貌方法 |
| 蛋白性质 | 蛋白名称、简称、来源、角色、分子量、等电点、实验 pH 下电荷、初始浓度、基质、竞争蛋白、标记方式、蛋白类别、血液相关、炎症相关 |
| 实验条件 | 批量/柱/表面/流动/QCM/SPR 等模式、水凝胶用量、溶液体积、pH、缓冲液、盐、温度、时间、流速、洗涤、洗脱、再生、检测方法、重复数、吸附类型、竞争体系、是否做脱附 |
| 吸附和分离结果 | 吸附/选择性吸附/弱吸附/不吸附/抗污染标签、原始指标、归一化容量、表面吸附量、去除率、回收率、纯度、动态结合容量、选择性因子、印迹因子、结合/解离常数、等温/动力学模型 |
| 多蛋白和 corona 结果 | protein corona 组成、竞争吸附结果、蛋白交换、Vroman-like 行为、吸附可逆性、目标/非目标蛋白排序 |
| 机理和对照 | 静电、疏水、氢键、水化层、尺寸排阻、孔扩散、印迹、金属配位、离子交换、配体亲和、pH/温度/盐响应、蛋白构象变化、protein unfolding、corona 证据、对照材料和倍数变化 |
| 生物界面响应 | 血小板黏附、血小板激活、巨噬细胞极化、补体激活、细胞黏附、血液相容性、异物反应 |
| AI 建模标签 | 应用场景、预测目标、正/负/弱/混合样本、重要性评分、是否可用于训练 |
| 反向设计和工艺匹配 | 目标吸附蛋白集合、目标排斥蛋白集合、性能阈值、允许工艺窗口、候选水凝胶、推荐制备路线、洗脱/再生方案、放大风险、验证实验 |

## 五、实施判断

| 结论 | 执行动作 |
| --- | --- |
| 专家新增的 Q3/Q6 是核心方向，不应只作为候选。 | 已写入 `PHA/configs/config.yaml` 并完成 count-only 探测。 |
| 旧 Q3 分离纯化不应被覆盖。 | 保留为 Q8，服务分离纯化和工艺匹配。 |
| 旧 Q6 高通量筛选不应丢失。 | 升级为 Q10，服务 AI-ready 数据集。 |
| 低吸附/抗污染是负样本来源。 | Q5 保留为核心，后续靠 triage 控制噪声。 |
| 设计空间过大，不能穷举。 | 采用“机制规则缩小空间 + 数据模型排序 + 文献证据回溯”的反向设计路线。 |

