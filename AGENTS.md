# Fruitfly Agent Guidelines

> Scope: applies to this repository by default.
> Precedence: direct user instructions override this file.

## 1. Default Language
- MUST: 默认使用简体中文。
- SHOULD: 回答先给结论，再给必要解释。

## 2. Terminology Annotation
- MUST: 第一次出现的专有名称、论文术语、强化学习术语、神经科学术语，都要补中文注释。
- MUST: 优先使用 `英文术语（中文解释）` 格式。
- SHOULD: 如果术语是当前讨论核心，再补 1 句通俗解释，避免只给直译。

Examples:
- `imitation learning（模仿学习：先模仿 flybody 中已有的 expert MLP 控制器）`
- `PPO fine-tune（强化学习微调：模仿学习完成后，再用 PPO 继续优化策略）`
- `gait initiation（起步：从静止开始进入稳定步态）`
- `straight walking（稳定直行：按目标速度持续向前行走）`
- `turning（转向：维持行走同时按目标角速度改变方向）`
- `whole-brain rate model（全脑速率模型：用连续神经活动值近似全脑动态，而不是逐脉冲放电）`

## 3. Explanation Style
- MUST: 讨论架构或论文流程时，先给通俗版解释，再给工程版拆解。
- SHOULD: 当用户追问“这是什么意思”时，先回答概念差异，再回答实现差异。

## 4. Project Goal
- MUST: 本项目目标明确为 `fruit fly whole-brain research platform（果蝇全脑科研平台）`。
- MUST: 所有训练、评估、可视化、UI 和资产管线都应优先服务科研可复现性、数据可追溯性和结果可解释性。

## 5. Current Approved Project Defaults
- MUST: 当前具身环境默认使用 `flybody（果蝇身体与 MuJoCo 物理环境）`。
- MUST: connectome（连接组）数据默认使用 `本地快照`，训练和评估时不在线查询 `neuPrint（连接组查询服务）`。
- MUST: 第一阶段默认使用完整 `139,246` 神经元全图，不走“小图替身”主线。
- MUST: 第一阶段训练范围默认是 `IL-only walking（仅模仿学习的步行阶段）`。
- MUST NOT: 第一阶段默认不引入 `PPO fine-tune（强化学习微调）`、`flight（飞行）`、`Brian2（脉冲神经仿真框架）` 全脑版本，除非用户明确要求。

## 6. Data and Architecture Guardrails
- MUST: `flow_role（afferent / intrinsic / efferent，即输入 / 中间 / 输出标签）` 与 connectome 快照一起冻结。
- MUST: `normalized（标准化层）` 作为项目内部单一事实来源，`compiled（训练编译层）` 只保存训练直接可用的图结果。
- MUST: `flybody` 适配层与脑模型解耦；身体环境不应依赖脑模型内部实现。
- MUST: 所有科研数据链必须真实、准确、来源匹配；禁止编造数据、禁止混用不兼容数据源、禁止把代表性预览或占位结果伪装成真实科研结果。
- MUST: `UI（用户界面）` 默认运行在 `research strict mode（科研严格模式）`；禁止默认 `mock fallback（模拟回退）`。
- MUST: 当真实 `session / summary / brain-view / timeline / video / ROI activity（会话 / 摘要 / 脑图 / 时间轴 / 视频 / 脑区活动）` 数据不存在时，返回 `null`、空值或明确的 unavailable 状态，而不是伪造内容。
- MUST: 任何 representative preview（代表性预览）、占位 mesh（占位网格）、样例时间轴或 mock 数据，只能在显式开发模式下使用，并且必须明确标注为非科研数据。

## 7. FlyWire Official Route Guardrails
- MUST: ROI / 脑区可视化正式主线严格沿 `FlyWire official route（FlyWire 官方路线）` 构建，不把非 FlyWire 官方来源放入正式真值链。
- MUST: 在正式主线中，优先使用 `neuropil（神经纤维区）` 语义，而不是泛化 `ROI（脑区）` 语义。
- MUST: 当前 V1 脑区显示范围固定为 `8` 个官方 `neuropils（神经纤维区）`：`AL`、`LH`、`PB`、`FB`、`EB`、`NO`、`LAL`、`GNG`。
- MUST: `FlyWire 783` 官方发布文件是 neuropil 真值主数据源；正式主线应优先依赖官方发布文件，而不是在线 API 查询。
- MUST: 正式第一性真值层定义为 `synapse_neuropil_assignment.parquet（突触级神经纤维区归属表）`。
- MUST: 正式派生层定义为 `node_neuropil_occupancy.parquet（节点级神经纤维区占据表）`。
- MUST: 正式 `neuropil` 活动展示只能来自：
  - `FlyWire` 官方突触/神经纤维区数据
  - `FlyWire` 官方 neuropil mesh
  - 本地离线编译出的正式真值/派生产物
- MUST NOT: 不允许用 `dominant ROI evidence（主导脑区证据）`、预览数据、代表性示例或启发式推断替代正式 `neuropil occupancy truth（神经纤维区占据真值）`。
- MUST: 当 `synapse_neuropil_assignment.parquet` 或 `node_neuropil_occupancy.parquet` 缺失时，`UI/API` 必须返回 `null` 或 unavailable；允许显示整脑壳，但不允许显示正式 `neuropil glow（神经纤维区发光）`。

## 8. UI System Guardrails
- MUST: `Experiment Console（实验控制台）` 与 `Training Console（训练控制台）` 必须共享同一套设计系统、组件语义、间距规则、状态色规则和交互语言，不允许各自形成割裂风格。
- MUST: 两个控制台的 2D UI 统一使用 `shadcn/ui（组件体系）` 作为基础组件层；3D 脑图层可继续使用 `react-three-fiber（React 的 Three.js 3D 渲染层）`。
- MUST: 涉及界面结构、设计语言、交互样式的讨论与方案制定，必须按 `ui-ux-pro-max（界面设计技能）` 的设计思路执行；若该技能的本地脚本入口损坏，必须明确说明，不能伪装成已跑通其自动检索。
- MUST: 两个控制台都必须支持主题模式：
  - `light（亮色）`
  - `dark（暗色）`
  - `system（跟随系统）`
- MUST: 两个控制台都必须支持多语言：
  - `English（英文）`
  - `简体中文`
  - `繁體中文`
  - `日本語（日文）`
- MUST: UI 语言应优先跟随系统语言；若系统语言不可识别或不在支持列表内，默认回退到 `English`。
- MUST: 主题与语言切换必须在两个控制台之间保持一致，并共享同一状态来源，而不是每个页面单独维护一套不兼容开关。

## 9. Git Commit Guardrails
- MUST: `git commit（代码提交）` 必须原子化；一个 commit 只表达一个清晰、单一的意图。
- MUST NOT: 不要把无关改动、顺手修复、临时调试、生成产物或本地环境噪音混进同一个 commit。
- SHOULD: 同一功能对应的代码、测试、必要文档可放进同一个原子 commit；仓库规则或流程变更应单独提交。
- MUST: 提交前先明确这次 commit 的范围和目的；如果一句提交信息概括不了改动，就应拆分 commit。
