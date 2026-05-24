# gen_runway 🎨

ComfyUI を使ったランウェイ風ハイファッション女性画像の自動生成スクリプトです。
モデルごとに特性が異なる2つのジェネレーター、および生成した画像を美しく鑑賞するスライドショーシステムを収録しています。

---

## スクリプト・ツール一覧

### `gen_runway_vxp.py` ｜ SDXL + vxpILBase
- **モデル**: `SDXL/vxpILBaseNSFW_v10.safetensors`
- **ワークフロー**: `workflows/vxpILBase_v10.json`
- **特徴**:
  - ランダムプロンプト生成（顔・ポーズ・髪型・服装など10以上のカテゴリ）
  - 動的カラーシステム（服装やブラカラーをランダムに変化）
  - アップスケール付き高品質出力（SDXL + Hi-res fix）

### `gen_runway_zimage.py` ｜ Z-Image-Turbo (GGUF)
- **モデル**: `z-image-turbo-q8_0.gguf`
- **ワークフロー**: `workflows/z-image.json`
- **特徴**:
  - 自然な英語段落形式のプロンプト自動生成！Z-Image-Turbo向け最適化！
  - ステップ数・CFGスケールをコマンドラインで調整可能
  - カスタムプロンプトの直接入力オプション（`-p`）

### `runway_show.html` & `update_slideshow.py` ｜ スライドショービューア [NEW]
生成した画像を、まるでファッションショーのランウェイ（Lookbook）のように美しく、ドラマチックに自動再生するローカルHTMLビューアです。
- **特徴**:
  - **ハイブランド風デザイン**: 漆黒の背景に、モデルを照らす上品なにじみゴールドシャドウと背面スポットライト。
  - **優雅なフェード遷移**: 3秒間隔（1秒〜10秒で調整可能）で優雅にクロスフェードします。
  - **HUDコントロール**: キーボードショートカット（Spaceで再生/停止、左右キーで手動送り、Fキーでフルスクリーン）や再生速度スライダーを完備。
  - **マルチフォルダ対応**: 引数指定によって、zimageモデルやvxpモデルの画像を簡単に切り替えてスライドショー再生可能。
  - **※Git安全設計**: `runway_show.html` は画像リストを内包するため、プライバシー保護の観点から `.gitignore` に追加されており、コミット時に余計な差分やファイル名がGitHubにアップされる心配はありません。

---

## 共通仕様
- **アスペクト比指定対応**: `square` (1:1) / `portrait` (3:4) / `landscape` (16:9) に対応。
- **バッチ生成対応**: `-n` オプションで複数枚の一括生成が可能。
- **自動化**: ComfyUI WebSocket API経由で生成・保存まで完全自動化。

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

### 1. 画像の生成

#### `gen_runway_vxp.py`
```bash
# 1枚生成（デフォルト square）
python gen_runway_vxp.py

# 10枚バッチ生成
python gen_runway_vxp.py -n 10

# portrait（縦長）で5枚生成
python gen_runway_vxp.py -n 5 --aspect portrait
```

#### `gen_runway_zimage.py`
```bash
# 1枚生成（デフォルト square）
python gen_runway_zimage.py

# 5枚バッチ生成、portrait
python gen_runway_zimage.py -n 5 --aspect portrait

# ステップ数・CFGを調整して生成
python gen_runway_zimage.py -n 3 --steps 12 --cfg 2.0

# カスタムプロンプトを直接指定して生成
python gen_runway_zimage.py -p "A young Japanese woman walking on a grand fashion runway..."
```

---

### 2. スライドショーの鑑賞

画像生成後、スキャンスクリプトを実行してビューアを最新の画像リストに更新します。

```bash
# 1. デフォルト (output_runway_zimage) の画像をスキャンする場合
python update_slideshow.py

# 2. vxp版 (output_runway_vxp) など別のフォルダを指定してスキャンする場合
python update_slideshow.py output_runway_vxp
```

スキャンが成功したら、**`runway_show.html` をダブルクリックしてブラウザで開くだけ**で、スライドショーが自動で開始されます！

> [!TIP]
> HTMLファイルを直接ブラウザで開き、画像ファイルをまとめて**ドラッグ＆ドロップ**することでも手軽に再生を開始できます。

---

## ファイル構成

```
gen_runway/
├── gen_runway_vxp.py       # SDXL vxpILBase ランウェイジェネレーター
├── gen_runway_zimage.py    # Z-Image-Turbo ランウェイジェネレーター
├── comfy_api.py            # ComfyUI WebSocket APIユーティリティ
├── runway_show.html        # ランウェイ・スライドショービューア (Git除外)
├── update_slideshow.py     # スライドショー画像リスト自動更新スクリプト
├── workflows/
│   ├── vxpILBase_v10.json  # vxpILBase用ワークフロー
│   └── z-image.json        # Z-Image-Turbo用ワークフロー
├── .gitignore              # Git管理除外設定
└── README.md               # 本ドキュメント
```

---

## ライセンス

MIT
