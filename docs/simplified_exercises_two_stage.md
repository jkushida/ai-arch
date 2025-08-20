# 建築AI設計・2段階演習（基礎観察 → PSO最適化）

本演習は2段階構成です。Stage 1で設計パラメータと評価値の関係を体感し、Stage 2でPSO（粒子群最適化）を使って制約を満たす最適案を探索します。

---

## Stage 1: 基礎観察（手動パラメータ調整）

### 目的
- 設計パラメータ（寸法・材料・形状）と、評価指標（安全率・コスト・CO2・快適性・施工性）の関係を理解する。

### 前提
- 作業フォルダに移動：
```bash
cd /Users/kushida2/Library/CloudStorage/GoogleDrive-kushida2008@gmail.com/マイドライブ/2025code/AI_arch
```
- 単一評価スクリプト実行（FreeCADコマンドライン）：
```bash
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/test_generate_building.py
```
- 出力：`test_results.csv`（追記）と `.FCStd`（3Dモデル）

### 共通記録テンプレート（各実験で記入）
```
試行名: ________
変更パラメータ: 例) Lx=10→12, bc=300→500
結果: safety=____, cost=____ 円/m², co2=____ kg-CO2/m², comfort=____/10, constructability=____/10
所見: ________________________________________________
```

### 課題1: 建物サイズの影響（Lx, Ly）
1) `code/test_generate_building.py` の初期パラメータで実行し基準値を記録。
2) Lx, Ly を以下の3通りに変更してそれぞれ実行・記録：

   - パターンA: Lx=8.0, Ly=8.0
   - パターンB: Lx=10.0, Ly=10.0
   - パターンC: Lx=12.0, Ly=12.0
   - 
3) 観察：建物が大きくなると「安全率」「コスト/m²」「最大変位」はどう変化するか？

### 課題2: 柱断面の影響（bc, hc）
- bc, hc を [300, 400, 500, 600] mm に段階的変更し実行。
- 目標安全率2.0を満たす最小寸法を特定。コスト増加とのトレードオフを簡潔に考察。

### 課題3: 材料構成の影響（0=RC, 1=木材）
- 3ケースを比較：
  - RC一括: すべて0
  - 木造一括: すべて1
  - ハイブリッド: 柱=0、床1=0、床2=1、屋根=1、壁=1、バルコニー=0
- CO2、コスト、安全率の差を表でまとめる。

### 課題4: 快適性と形状（H1/H2, window_ratio_2f）
- H1, H2 ∈ {2.6, 3.0, 3.5}、`window_ratio_2f` ∈ {0.2, 0.4, 0.6} を組み合わせ、快適性と安全率への影響を確認。

### Stage 1 成果物
- `test_results.csv`（試行を最低8回以上追加）
- 代表 `.FCStd` 3件（小規模・中規模・ハイブリッド推奨）
- 1ページの所見（最重要パラメータ・基本トレードオフ）

---

## Stage 2: PSOによる最適化

### 目的
- 現実的制約を満たしつつ、重み付き目的を最小化する設計をPSOで探索する。

### 事前確認
- 設定ファイル：`code/pso_config.py`
- 実行：
```bash
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/pso_algorithm.py
```
- 監視（別ターミナル任意）：
```bash
python3 code/monitor_pso_mac.py
# ブラウザ: http://localhost:5001
```

### 制約・目的（本演習用）
- 制約（全て満たすこと）
  - 安全率 ≥ 2.0
  - コスト ≤ 350,000 円/m²
  - CO2 ≤ 500 kg-CO2/m²
- 目的（最小化）
  - 重み付き総合指標： 0.4*cost_norm + 0.3*co2_norm + 0.3*(1-comfort_norm)
  - 正規化の例：cost/350000, co2/500, comfort/10
  - 制約未達は大きなペナルティを加算

### 推奨の軽量設定（学習用）
`code/pso_config.py` の一部を以下の目安に調整：
```python
N_PARTICLES = 6
MAX_ITER = 6
W, C1, C2 = 0.7, 1.5, 1.5

# 主要変数の範囲（例）
variable_ranges.update({
    'Lx': (8.0, 12.0),
    'Ly': (8.0, 12.0),
    'bc': (300, 700),
    'hc': (300, 700),
    'tf': (350, 550),
    'tr': (350, 550),
    'material_columns': (0, 1),
    'material_walls': (0, 1),
    'material_roof': (0, 1),
    'window_ratio_2f': (0.2, 0.8),
})

# 目的関数の例
def calculate_fitness(cost, safety, co2, comfort, constructability):
    # 制約違反に強いペナルティ
    penalty = 0.0
    if safety < 2.0:
        penalty += (2.0 - safety) * 1e5
    if cost > 350000:
        penalty += (cost - 350000) * 0.5
    if co2 > 500:
        penalty += (co2 - 500) * 50

    cost_n = cost / 350000
    co2_n = co2 / 500
    comfort_n = comfort / 10.0

    fitness = 0.4*cost_n + 0.3*co2_n + 0.3*(1.0 - comfort_n)
    return fitness + penalty
```

### 実行と結果確認
- 実行後、以下を確認：
  - `pso_output/csv/pso_gbest_history.csv`（gbest履歴）
  - `pso_output/images/`（収束曲線）
- 最良解のモデル生成（任意）：
```bash
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/gbest_generate_building.py
```

### 課題A: 収束と設定感度
- N_PARTICLES を 4→8、MAX_ITER を 6→12 に変更した2条件を比較。
- 収束速度、最終fitnessの差、探索の安定性を簡潔に考察。

### 課題B: 重み変更の影響
- 重みを3通り設定して実行し、コスト・CO2・快適性のバランス変化を比較：
  - 経済性重視：w = (0.6, 0.2, 0.2)
  - 環境性重視：w = (0.2, 0.6, 0.2)
  - 快適性重視：w = (0.2, 0.2, 0.6)

### 課題C: 最終案の妥当性チェック
- gbest案を `.FCStd` で確認し、構造的に不自然な形状や極端値がないかをレビュー。

### Stage 2 成果物
- `pso_output/csv/` の主要CSV（履歴・設定）
- 収束グラフ1枚（またはスクリーンショット）
- 1-2ページの要約（最良案の指標値、採用理由、重み・設定の影響）

---

## レポート提出（全体）
- 分量目安：A4 5-7ページ
- 構成：目的/方法（Stage1/2）→結果→考察→結論
- 図表：`test_results.csv`から1枚、PSO収束グラフ1枚、代表3D形状のスクショ1-2枚

## 参考
- `docs/simplified_exercises.md`（基礎演習の詳細）
- `docs/PSO_usage.md` / `docs/pso_summary.md`（PSOの使い方と背景）
- `docs/random_sampling_guide.md`（変数範囲の目安）

---

## 付録: 演習パターン集（選択・組合せ自由）

以下のパターンを Stage 1 → Stage 2 の流れで実施できます。いくつか選んで比較し、最終案を選定してください。

### P1. 経済性重視（コスト最小）
- 目的: 制約を満たしつつコスト最小化
- 主要変数: Lx, Ly, bc, hc, tf, tr, material_*
- 重み例（Stage 2）: (cost, co2, comfort) = (0.6, 0.2, 0.2)
- Stage 1ポイント: Lx/Ly と bc/hc の2軸で「安全率2.0の最小柱寸法」を確認

### P2. 低炭素重視（CO2最小）
- 目的: CO2削減と安全性の両立
- 主要変数: material_*（離散）, tf/tr, roof_morph, window_ratio_2f
- 重み例: (0.2, 0.6, 0.2)
- Stage 1: RC→木造→ハイブリッドの3比較（CO2と安全率の差）

### P3. 快適性重視（ユーザー体験）
- 目的: 快適性を高めつつ制約を満たす
- 主要変数: H1/H2, window_ratio_2f, roof_morph/shift, balcony_depth
- 重み例: (0.2, 0.2, 0.6)
- Stage 1: H1/H2×window比の3×3格子探索

### P4. ハイブリッド構造の適材適所
- 目的: 柱=RC、他=木材基調でコストとCO2を削減
- 主要変数: material_*（柱固定0、他0/1）, bc/hc, tf/tr
- 重み例: (0.4, 0.3, 0.3)
- Stage 1: RC/木/ハイブリッドを比較し、柱断面の最小化を検討

### P5. 形状最適化（壁傾斜と屋根）
- 目的: 形状で安全性・快適性の両立を狙う
- 主要変数: wall_tilt_angle, roof_morph, roof_shift, window_ratio_2f
- 重み例: 0.3*cost + 0.2*co2 + 0.5*(1−comfort)
- Stage 1: tilt∈{-15,0,15} × 屋根3種の9通り比較

### P6. 軽量化（重量の代理最小）
- 目的: 最小重量（体積）で安全率2.0を確保
- 主要変数: bc/hc, tf/tr, tw_ext
- 目的例: 体積最小 + 制約ペナルティ（PSO側で実装）
- Stage 1: bc/hcを段階増やして安全率2.0の閾値を把握

### P7. 施工性×コストのトレードオフ
- 目的: コスト低減と施工性確保の最適バランス
- 主要変数: tf/tr, wall_tilt_angle（施工性に影響）
- 実施: (cost重視)と(施工性重視)の重みで2回最適化しレーダー比較

### P8. ロバスト設計（ばらつき耐性）
- 目的: 小さな条件変動に対して性能が落ちにくい設計
- アプローチ: gbest近傍の擬似サンプルで期待値+分散ペナルティ（近似）
- Stage 1: 同一設計で Lx±0.5m 等の再評価で感度確認

### P9. 限定予算下の最大快適性
- 目的: コスト上限固定で快適性最大化
- 重み例: (0.6, 0.1, 0.3) を (penalty強) と併用
- Stage 1: コスト天井付近で快適性敏感度を把握

### P10. 2段階最適化（サンプリング→PSO）
- 目的: 先に粗い全体像→PSOで絞り込み
- Stage 1: 10〜20点のランダムサンプリングで良好領域を把握
- Stage 2: その領域に範囲を狭めてPSO再実行（例: 粒子8, 反復10）

---

## 付録: 目的関数プリセット（差し替え候補）

以下は `code/pso_config.py` の `calculate_fitness` にそのまま差し替え可能な候補です（既存シグネチャ互換）。目的に応じて選択・比較してください。どれも基本の共通基準値を前提にしています。

- 基本設定（共通の基準値）
  - コスト基準: 350000 円/m²
  - CO2基準: 500 kg-CO2/m²
  - 安全率閾値: 2.0

### 1) 経済性重視（安全率ペナルティ付き）

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    SAFETY_THRESHOLD = 2.0
    fitness = cost
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 100000
    return fitness
```

### 2) 重み付き合成（バランス型）
- コスト0.4、CO2 0.3、快適性0.3（最大化なので 1−comfort/10）

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    SAFETY_THRESHOLD = 2.0
    COST_BASE, CO2_BASE, COMFORT_BASE = 350000.0, 500.0, 10.0
    cost_n = cost / COST_BASE
    co2_n = co2 / CO2_BASE
    comfort_n = max(0.0, min(1.0, comfort / COMFORT_BASE))
    fitness = 0.4*cost_n + 0.3*co2_n + 0.3*(1.0 - comfort_n)
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 100
    return fitness
```

### 3) 低炭素重視（CO2最小 + 制約ペナルティ）

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    SAFETY_TH, COST_CAP, CO2_CAP = 2.0, 350000.0, 500.0
    fitness = co2 / CO2_CAP
    if safety < SAFETY_TH:
        fitness += (SAFETY_TH - safety) * 100
    if cost > COST_CAP:
        fitness += (cost - COST_CAP) * 0.5 / COST_CAP
    return fitness
```

### 4) 快適性重視（予算内最大快適）

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    SAFETY_TH, COST_CAP, CO2_CAP = 2.0, 350000.0, 500.0
    comfort_n = max(0.0, min(1.0, comfort/10.0))
    fitness = (1.0 - comfort_n)  # 快適性最大化 → 1−comfort
    if safety < SAFETY_TH:
        fitness += (SAFETY_TH - safety) * 100
    if cost > COST_CAP:
        fitness += (cost - COST_CAP) * 0.5 / COST_CAP
    if co2 > CO2_CAP:
        fitness += (co2 - CO2_CAP) * 0.1 / CO2_CAP
    return fitness
```

### 5) ロバスト安全余裕（目標2.2を緩く推奨）

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    SAFETY_TH = 2.0
    TARGET_SAFETY = 2.2  # 余裕目標
    fitness = cost / 350000.0 + co2 / 500.0
    if safety < SAFETY_TH:
        fitness += (SAFETY_TH - safety) * 100
    if safety < TARGET_SAFETY:
        fitness += (TARGET_SAFETY - safety) * 10
    return fitness
```

### 6) 施工性トレードオフ（厚すぎ/形状難の抑制を代理）

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    SAFETY_TH = 2.0
    # 施工性は10が良い想定 → (1−constructability/10)を最小化に加える
    construct_n = max(0.0, min(1.0, constructability/10.0))
    fitness = 0.5*(cost/350000.0) + 0.2*(co2/500.0) + 0.3*(1.0 - construct_n)
    if safety < SAFETY_TH:
        fitness += (SAFETY_TH - safety) * 100
    return fitness
```

### 7) 辞書式（安全性最優先 → コスト → CO2）

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    SAFETY_TH = 2.0
    if safety < SAFETY_TH:
        return 1e9 + (SAFETY_TH - safety) * 1e7  # 安全性最優先で巨大化
    # 安全満たしたらコスト主、CO2は微小重みでタイブレーク
    return cost + 100.0 * (co2 / 500.0)
```

### 8) 体積（軽量化）志向 + 安全ペナルティ（コストが体積近似の場合に有効）

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    SAFETY_TH = 2.0
    fitness = cost/350000.0  # 体積近似としてコストを代理
    if safety < SAFETY_TH:
        fitness += (SAFETY_TH - safety) * 100
    # 快適性を少しだけ維持（過度な薄肉/極端形状の抑制）
    fitness += 0.1 * (1.0 - max(0.0, min(1.0, comfort/10.0)))
    return fitness
```

補足: これらは `code/fitness_presets.py` にも収録されており、`code/pso_config.py` の `FITNESS_PRESET` を切り替えることで編集なしに選択できます。
