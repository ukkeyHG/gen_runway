# gen_runway 🎨

ComfyUI を使ったランウェイ風ハイファッション女性画像の自動生成スクリプト集です。  
モデルごとに特性が異なる2つのジェネレーターを収録しています。

---

## スクリプト一覧

### `gen_runway_vxp.py` — SDXL + vxpILBase
- **モデル**: `SDXL/vxpILBaseNSFW_v10.safetensors`
- **ワークフロー**: `workflows/vxpILBase_v10.json`
- **特徴**:
  - ランダムプロンプト生成（顔・ポーズ・髪型・服装など10以上のカテゴリ）
  - 動的カラーシステム（衣装・ブラカラーをランダムに変化）
  - アップスケール付き高品質出力（SDXL + Hi-res fix）

### `gen_runway_zimage.py` — Z-Image-Turbo (GGUF)
- **モデル**: `z-image-turbo-q8_0.gguf`
- **ワークフロー**: `workflows/z-image.json`
- **特徴**:
  - 自然な英語段落形式のプロンプト自動生成（Z-Image-Turbo向け最適化）
  - ステップ数・CFGスケールをコマンドラインで調整可能
  - カスタムプロンプトの直接指定オプション（`-p`）

---

## 共通仕様

- ✅ アスペクト比指定対応（`square` / `portrait` / `landscape`）
- ✅ バッチ生成対応（`-n` オプションで複数枚一括生成）
- ✅ ComfyUI WebSocket API経由で生成・保存まで自動化

---

## 必要環境

- Python 3.10 以上
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) がローカルで起動していること
- 各スクリプトが参照するモデルファイルが ComfyUI の `models/` 以下に配置済みであること

---

## セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/ukkeyHG/gen_runway.git
cd gen_runway
```

---

## 使い方

### `gen_runway_vxp.py`

```bash
# 1枚生成（デフォルト: square）
python gen_runway_vxp.py

# 10枚バッチ生成
python gen_runway_vxp.py -n 10

# portrait（縦長）で5枚生成
python gen_runway_vxp.py -n 5 --aspect portrait

# 出力先ディレクトリを指定
python gen_runway_vxp.py -n 3 -o my_output
```

| オプション | 短縮形 | デフォルト | 説明 |
|---|---|---|---|
| `--num` | `-n` | `1` | 生成枚数 |
| `--output-dir` | `-o` | `output_runway_vxp` | 出力先ディレクトリ |
| `--aspect` | - | `square` | アスペクト比（`square` / `portrait` / `landscape`） |

### `gen_runway_zimage.py`

```bash
# 1枚生成（デフォルト: square）
python gen_runway_zimage.py

# 5枚バッチ生成、portrait
python gen_runway_zimage.py -n 5 --aspect portrait

# ステップ数・CFGを調整
python gen_runway_zimage.py -n 3 --steps 12 --cfg 2.0

# カスタムプロンプトを直接指定
python gen_runway_zimage.py -p "A young Japanese woman walking on a grand fashion runway..."
```

| オプション | 短縮形 | デフォルト | 説明 |
|---|---|---|---|
| `--num` | `-n` | `1` | 生成枚数 |
| `--output-dir` | `-o` | `output_runway_zimage` | 出力先ディレクトリ |
| `--aspect` | - | `square` | アスペクト比（`square` / `portrait` / `landscape`） |
| `--steps` | - | `8` | KSamplerのステップ数 |
| `--cfg` | - | `1.5` | KSamplerのCFGスケール |
| `--prompt` | `-p` | _(自動生成)_ | カスタムプロンプトを直接指定 |

---

## ファイル構成

```
gen_runway/
├── gen_runway_vxp.py       # SDXL vxpILBase ランウェイジェネレーター
├── gen_runway_zimage.py    # Z-Image-Turbo ランウェイジェネレーター
├── comfy_api.py            # ComfyUI WebSocket APIユーティリティ
├── workflows/
│   ├── vxpILBase_v10.json  # vxpILBase用ワークフロー
│   └── z-image.json        # Z-Image-Turbo用ワークフロー
└── README.md
```

---

## ライセンス

MIT
