# Transformer 改进实验与作业说明材料

## 1. 问题诊断

原 notebook 中 Transformer 的测试集 Empty AUPRC 为 0.7621，低于 Historical average、LightGBM 和 Random forest。训练日志显示 Transformer 的训练损失持续下降，但验证损失在第 2-4 轮后开始反弹，说明该数据集下纯序列 Transformer 容易过拟合；同时占用行为具有强日周期和周周期，简单历史周期先验本身已经很强。

## 2. 改进思路

本次快速改进采用“季节先验 + 判别模型 + Transformer”的轻量融合结构：

1. **Seasonal-Transformer blend**：用验证集搜索 Transformer 与历史周期先验的线性融合权重，只使用验证集选权，测试集不参与调参。
2. **Hybrid Seasonal-GBDT-Transformer**：在 Seasonal-Transformer 的基础上加入 LightGBM 的非线性表格特征表达，固定权重为 `Historical average=0.15, LightGBM=0.60, Transformer=0.25`。这个结构保留 Transformer 的多步时序信息，同时用季节先验稳定周期模式，用 GBDT 捕获小样本传感器/日历特征的非线性关系。
3. **Hybrid balanced tree-deep**：作为补充消融，加入少量 Random forest 并降低 LightGBM 权重，用于检验树模型集成是否还能进一步改善排序能力。
4. **训练策略解释**：原 Transformer 已出现早停前过拟合，因此本轮不继续堆深模型，而是采用验证集调权的集成正则化，相当于对 Transformer 输出做先验校准和模型平均。

## 3. 验证集选权结果

| candidate | weights | validation_auprc_empty | test_auprc_empty |
| --- | --- | --- | --- |
| Hybrid Seasonal-GBDT-Transformer | Historical average=0.15; LightGBM=0.60; Transformer=0.25 | 0.7286 | 0.8514 |
| Hybrid balanced tree-deep | Historical average=0.20; LightGBM=0.50; Random forest=0.10; Transformer=0.20 | 0.7273 | 0.8554 |
| LightGBM | LightGBM=1.00 | 0.7228 | 0.8382 |
| Hybrid tree-seasonal | Historical average=0.25; LightGBM=0.55; Random forest=0.20 | 0.7186 | 0.8544 |
| Seasonal-Transformer blend | Historical average=0.54; Transformer=0.46 | 0.7168 | 0.8490 |
| Transformer | Transformer=1.00 | 0.6904 | 0.7621 |
| Historical average | Historical average=1.00 | 0.6701 | 0.8497 |

## 4. 模型级测试对比

| model | auprc_empty | auroc_empty | f1_empty | brier_empty | log_loss_empty |
| --- | --- | --- | --- | --- | --- |
| Hybrid balanced tree-deep | 0.8554 | 0.9349 | 0.7654 | 0.0922 | 0.2978 |
| Hybrid tree-seasonal | 0.8544 | 0.9352 | 0.7687 | 0.0917 | 0.2964 |
| Hybrid Seasonal-GBDT-Transformer | 0.8514 | 0.9333 | 0.7616 | 0.0928 | 0.2984 |
| Historical average | 0.8497 | 0.9262 | 0.7621 | 0.0974 | 0.3237 |
| Seasonal-Transformer blend | 0.8490 | 0.9295 | 0.7436 | 0.0981 | 0.3174 |
| LightGBM | 0.8382 | 0.9291 | 0.7601 | 0.0956 | 0.3058 |
| Transformer | 0.7621 | 0.9034 | 0.6581 | 0.1136 | 0.3510 |

相对原 Transformer，Seasonal-Transformer blend 的 Empty AUPRC 从 0.7621 提升到 0.8490，提升 0.0869。按验证集 AUPRC 选择的主方案为 **Hybrid Seasonal-GBDT-Transformer**，测试 AUPRC 为 0.8514；测试集中最高的补充候选为 **Hybrid balanced tree-deep**，AUPRC 为 0.8554。后者可作为消融结果展示，但严格模型选择应以验证集排序为准。

## 5. 10% 风险约束推荐对比

| model | empty_probability_threshold | occupancy_conflict_rate | safe_shiftable_load_opportunity_kwh | kwh_per_day | recommendation_count |
| --- | --- | --- | --- | --- | --- |
| LightGBM | 0.9500 | 0.0415 | 493.9232 | 11.4866 | 265 |
| Hybrid Seasonal-GBDT-Transformer | 0.8750 | 0.0000 | 490.1464 | 11.3988 | 259 |
| Seasonal-Transformer blend | 0.8000 | 0.0000 | 457.8952 | 10.6487 | 249 |
| Hybrid balanced tree-deep | 0.8750 | 0.0000 | 446.5471 | 10.3848 | 256 |
| Hybrid tree-seasonal | 0.9500 | 0.0000 | 116.7878 | 2.7160 | 86 |
| Transformer | 0.9000 | 0.0968 | 97.4392 | 2.2660 | 31 |
| Historical average | 0.9500 | 0.0000 | 94.6230 | 2.2005 | 66 |

在 10% 验证集风险约束下，原 Transformer 的测试安全可调负荷机会为 97.4 kWh；Seasonal-Transformer blend 提升到 457.9 kWh；验证集选出的主方案 **Hybrid Seasonal-GBDT-Transformer** 达到 490.1 kWh，测试占用冲突率为 0.00%。测试 AUPRC 最高的补充候选 **Hybrid balanced tree-deep** 在同一 10% 约束下为 446.5 kWh，冲突率为 0.00%。

## 6. 可写入作业的创新点

- **面向建筑占用预测的周期先验融合**：不是直接替换 Transformer，而是把强日周期/周周期先验作为可解释基线，与 Transformer 输出进行验证集校准。
- **小数据稳健化策略**：针对 Transformer 过拟合，引入模型平均和先验校准，降低单个深度模型在短时间跨度数据上的方差。
- **风险约束目标一致**：模型选择不仅看 AUPRC，还继续沿用 notebook 中的“最大化安全可调负荷机会，同时限制占用冲突率”的业务指标。
- **不使用未来传感器或负荷泄漏**：融合只使用已有模型的合法预测输出；HVAC/lighting 仍只用于机会评估，不作为预测输入。

## 7. 文件输出

- `results/improved_transformer_candidate_scores.csv`
- `results/improved_transformer_model_metrics.csv`
- `results/improved_transformer_selected_thresholds.csv`
- `results/improved_transformer_policy_results_test.csv`
- `predictions/hybrid_transformer_test_predictions.csv`
