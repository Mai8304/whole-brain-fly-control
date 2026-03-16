# True ROI Mesh First Design

**Goal:** Define a scientifically honest `True ROI mesh（真实脑区网格）` route for the neural console so the brain panel can move from `whole-brain shell（整脑外壳）` to real region geometry instead of heuristic glow markers.

**Scope:** This design refines the existing neural console work. It does not replace the current `FlyWire brain mesh（FlyWire 果蝇脑网格）` shell pipeline; it adds the missing anatomical asset chain required for real `ROI activity glow（脑区活动发光）`.

**Relationship to existing plans:** This design extends:
- `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-neural-console-ui-design.md`
- `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-neural-console-ui-refinement-design.md`

---

## 1. Problem Statement

The project already has:
- real `FlyWire（果蝇连接组平台）` whole-brain shell geometry
- real `whole-brain rate model（全脑速率模型）` node activity
- real `flybody（果蝇身体与 MuJoCo 物理环境）` closed-loop rollout video

The project does **not** yet have:
- real `ROI mesh（脑区网格）`
- real `node -> ROI mapping（节点到脑区映射）`

This is why the current brain panel can render the shell but cannot yet render anatomically correct ROI glow.

---

## 2. Best-Practice Asset Chain

The recommended industry/scientific best practice is:

`ROI SoT（脑区单一事实来源）`
`-> annotation volume（脑区标注体数据）`
`-> ROI mesh（脑区网格）`
`-> node -> ROI mapping（节点到脑区映射）`
`-> runtime aggregation（运行时活动聚合）`
`-> UI rendering（界面渲染）`

Key rule:
- heavy geometry and anatomical mapping happen **offline**
- runtime only updates `activity_value（活动值）` and render attributes

This avoids fake front-end-only glow and keeps anatomy, labels, and activity consistent.

---

## 3. Single Source of Truth Policy

### 3.1 ROI naming and ontology SoT

`VFB/FBbt（Virtual Fly Brain / Drosophila Anatomy Ontology，果蝇虚拟脑平台 / 果蝇解剖本体）` should be the `ROI SoT（脑区单一事实来源）` for:
- ROI names
- ROI hierarchy
- ROI identity
- ROI explanatory text

Why:
- It is a stable anatomy-first naming system.
- It separates anatomical truth from project-specific UI concerns.
- It avoids inventing an ad-hoc ROI vocabulary inside the UI.

### 3.2 Runtime activity source

`FlyWire-derived whole-brain model（基于 FlyWire 的全脑模型）` remains the SoT for:
- node identities
- node activity values
- whole-brain graph structure

### 3.3 Derived project assets

The project should generate and own three derived runtime assets:
- `roi_manifest.json`
- `roi_mesh/<roi_id>.glb`
- `node_roi_map.parquet`

These are project-local compiled assets, not anatomy SoT.

---

## 4. Geometry Strategy

### 4.1 Recommended route

Use an `atlas-first geometry（图谱优先几何）` workflow:
- obtain or generate ROI geometry from `annotation volume（脑区标注体数据）`
- convert each ROI into its own mesh
- align/export meshes into a stable UI asset directory

This is preferred over:
- trying to split the current whole-brain shell into ROI pieces
- painting fake regions directly in the front end

### 4.2 Runtime rendering policy

The brain panel should eventually render three layers:
- `whole-brain shell（整脑外壳）`
- `ROI activity glow（脑区活动发光）`
- `top active neurons overlay（最活跃神经元叠加）`

The shell remains context.
The ROI layer is the main explanatory layer.
The top-neuron layer remains secondary evidence.

---

## 5. Node-to-ROI Mapping Policy

### 5.1 Why this is the real blocker

Even with ROI meshes, the UI cannot be anatomically truthful without a stable `node -> ROI mapping（节点到脑区映射）`.

The mapping asset should be produced offline and versioned.

### 5.2 Recommended mapping table shape

Minimum columns:
- `source_id`
- `node_idx`
- `roi_id`

Optional future columns:
- `coverage_fraction`
- `mapping_method`
- `mapping_version`

### 5.3 Runtime rule

At runtime:
- per-node activity stays in model space
- backend aggregates node activity into ROI activity using `node_roi_map`
- front end never guesses anatomy

---

## 6. V1 Representative ROI Set

V1 should freeze the first real ROI set to **8 representative ROIs**:

- `AL — antennal lobe（触角叶）`
- `LH — lateral horn（外侧角）`
- `PB — protocerebral bridge（前大脑桥）`
- `FB — fan-shaped body（扇形体）`
- `EB — ellipsoid body（椭圆体）`
- `NO — noduli（节球）`
- `LAL — lateral accessory lobe（外侧附属叶）`
- `GNG — gnathal ganglion（颚神经节）`

Grouping:
- `input-associated（输入相关）`: `AL`, `LH`
- `core-processing（核心处理）`: `PB`, `FB`, `EB`, `NO`
- `output-associated（输出相关）`: `LAL`, `GNG`

This is a representative explanatory set, not a claim of complete walking circuitry coverage.

---

## 7. Visual Priority Policy

### 7.1 Display tiers

- `Tier A`: current top `3` active ROIs
- `Tier B`: remaining `5` ROIs
- `Tier C`: shell context

### 7.2 Color logic

Use grouped hues by information-flow role:
- input-associated: `blue / cyan（蓝 / 青）`
- core-processing: `gold / amber（金 / 琥珀）`
- output-associated: `coral / red-orange（珊瑚 / 橙红）`

Rule:
- color communicates role
- brightness communicates current activity

### 7.3 Naming/display policy

Use a configuration-driven `roi_manifest` with:
- `roi_id`
- `short_label`
- `display_name`
- `display_name_zh`
- `group`
- `description_zh`
- `default_color`
- `priority`

3D view:
- short label only

Explanation panel / tooltip:
- short label
- English full name
- Chinese explanation
- activity
- delta
- mapped node count

---

## 8. Output Artifacts

The `True ROI mesh first` pipeline should produce:

- `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/ui-assets/<asset_id>/roi_manifest.json`
- `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/ui-assets/<asset_id>/brain_shell.glb`
- `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/ui-assets/<asset_id>/roi_mesh/<roi_id>.glb`
- `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/ui-assets/<asset_id>/node_roi_map.parquet`
- `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/ui-assets/<asset_id>/source_info.json`

The API layer should later expose:
- brain shell metadata
- ROI mesh metadata
- ROI manifest
- ROI activity payload
- mapping coverage summary

---

## 9. Non-Goals for This Phase

This phase should **not** attempt to do all of the following:
- all-brain ROI coverage
- full neuron morphology rendering
- hand-authored artistic glow regions
- direct front-end-only region painting
- turning / flight task-specific ROI expansions

The goal is anatomical correctness for a representative ROI set, not final completeness.

---

## 10. Acceptance Criteria

This design is considered implemented when:

1. The project has a formal `ROI SoT（脑区单一事实来源）` policy using `VFB/FBbt`.
2. A representative ROI asset pack exists with:
   - manifest
   - real ROI meshes
   - node-to-ROI map
3. The backend can aggregate node activity into ROI activity using the compiled map.
4. The front end can load and render:
   - real shell
   - real ROI meshes
   - real ROI activity glow
5. The UI remains honest about coverage by displaying `mapping coverage（映射覆盖度）`.

---

## 11. Recommended Next Step

The next implementation milestone is **not** front-end polish.

It is:
- freeze the ROI manifest for the 8 V1 ROIs
- create the first real `node_roi_map`
- wire the resulting assets into the UI backend

