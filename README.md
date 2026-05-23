# gen_runway_vxp 🎨

ComfyUI + SDXL（`vxpILBase` モデル）を使用した、ランウェイ風ハイファッション女性画像の自動生成スクリプトです。

## 特徴

- ✅ ランダムプロンプト生成（顔・ポーズ・髪型・服装など10以上のカテゴリ）
- ✅ 動的カラーシステム（衣装・ブラカラーをランダムに変化）
- ✅ アップスケール付き高品質出力（SDXL + Hi-res fix）
- ✅ アスペクト比指定対応（square / portrait / landscape）
- ✅ バッチ生成対応（`-n` オプションで複数枚一括生成）

## 必要環境

- Python 3.10 以上
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) がローカルで起動していること
- モデル: `SDXL/vxpILBaseNSFW_v10.safetensors`
- ワークフロー: `workflows/vxpILBase_v10.json`

## セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/<your-username>/gen_runway_vxp.git
cd gen_runway_vxp
```

## 使い方

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

### オプション一覧

| オプション | 短縮形 | デフォルト | 説明 |
|---|---|---|---|
| `--num` | `-n` | `1` | 生成枚数 |
| `--output-dir` | `-o` | `output_runway_vxp` | 出力先ディレクトリ |
| `--aspect` | - | `square` | アスペクト比（`square` / `portrait` / `landscape`） |

## ファイル構成

```
gen_runway_vxp/
├── gen_runway_vxp.py   # メイン生成スクリプト
├── comfy_api.py        # ComfyUI WebSocket APIユーティリティ
├── workflows/
│   └── vxpILBase_v10.json  # ComfyUIワークフロー定義
└── README.md
```

## ライセンス

MIT
