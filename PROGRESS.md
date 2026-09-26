# 毕设项目进度

> 题目：Agent-based Automated Design and Optimization of Approximation Algorithms for Set Cover
>
> 最近更新：2026-09-26

## 当前阶段

**Phase 1：Set Cover 实验环境和初步实验协议已建立。** 继续校准实例分布，再进入 LLM 算法搜索。阶段划分以可运行、可复现的交付物为准。

## 已完成

- [x] 建立 unweighted Set Cover 的实例结构、结构校验、可行性检查和解校验。
- [x] 实现经典贪心算法，并预留评分函数接口。
- [x] 实现 random、sparse、dense、high_overlap、low_overlap 五类带 seed 的生成器。
- [x] 用 SciPy MILP 计算已证明最优的 OPT；未证明最优时不报告近似比。
- [x] 实现单实例评估和 `python -m experiments.run_benchmark`；结果可保存为 JSON。
- [x] 编写 README 和单元测试。最近验证：**33 项测试通过**。
- [x] 运行默认 10 个实例的快速检查：10/10 个贪心解有效且 OPT 已证最优，平均经验比值约 1.0811。
- [x] 初始化 Git 仓库，并将 Phase 1 代码提交到 `merewinds/Graduation-thesis` 的 `main` 分支（提交 `5da69e6`）。
- [x] 加入版本化 smoke、搜索、验证、保留测试集配置，并验证三组 pilot 种子互不重叠。
- [x] 给 OPT 设置单实例 20 秒上限与零 MIP gap；超限时保留 ALG、记录状态、不报告 `ALG/OPT`。
- [x] 记录 Python/SciPy 版本、实例结构统计、ALG 与 OPT 分别的运行时间、P90 经验比值。
- [x] 改善 `low_overlap` 在 `m > n` 时的大量近单元素集合问题。
- [x] 运行 pilot 搜索集 25 个实例：25/25 解有效且 OPT 已证最优，平均经验比值约 1.0526。
- [x] 加入 `greedy_trap` 受控诊断实例族；5/5 个实例均为 Greedy=18、OPT=12，经验比值 1.5。
- [x] 建立按完整实例指纹索引的 OPT 缓存，只写入已证明最优解；重复运行诊断配置时命中 5/5。
- [x] 在 benchmark 汇总中加入按实例类型统计的经验比值、密度和平均两两 Jaccard。

## 下一步：实例校准与正式协议

- [ ] 继续校准随机生成器的难度。当前 pilot 中 dense 与 low_overlap 的贪心结果均等于 OPT；`greedy_trap` 是固定结构的诊断用例，不能代替有多样性的正式实验实例族。
- [ ] 在完整实验前确定总运行预算、重复次数和最终样本量；当前配置是 pilot，不是论文最终统计方案。
- [x] Phase 2 前预计算并复用固定实例的 OPT，避免每次评价候选评分函数时重复求解整数规划。
- [ ] 保留测试集仅用于最终评估，不向未来 Agent 的设计或反馈环节泄露。

## 后续里程碑

### Phase 2：自动算法搜索

- [ ] 在固定贪心框架内让 LLM 设计评分函数，建立 one-shot 与性能反馈基线。
- [ ] 限制候选函数的执行环境，记录候选、评价结果和失败原因。

### Phase 3：反例引导搜索

- [ ] 搜索高经验比值实例，保存 ALG/OPT 解与决策轨迹。
- [ ] 比较性能反馈、反例反馈、反思与记忆等方法，并在保留测试集上评估泛化。

## 更新规则

完成一项任务后，勾选对应条目，写明验证结果；新增实验设计决策时记录其参数、理由和日期。实验观察到的 `ALG/OPT` 始终称为**经验近似比**，不等同于理论近似保证。
