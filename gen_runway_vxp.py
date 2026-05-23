import random
import os
import argparse
import uuid
from datetime import datetime
import time

from comfy_api import (
    connect_websocket,
    get_images,
    save_image,
    load_workflow,
    get_aspect_dimensions
)

MODEL_NAME = "SDXL\\vxpILBaseNSFW_v10.safetensors"

# --- KSampler設定（ベース用：ノード4） ---
BASE_SAMPLER_CONFIG = {
    "steps": 25,
    "cfg": 5.0,
    "sampler_name": "euler_ancestral",
    "scheduler": "normal",
    "denoise": 1.0
}

# --- KSampler設定（アップスケール用：ノード19） ---
UPSCALE_SAMPLER_CONFIG = {
    "steps": 15,
    "cfg": 4.5,
    "sampler_name": "euler_ancestral",
    "scheduler": "normal",
    "denoise": 0.32
}

PROMPT_DATA = {
    # 1. 主題・ベース（ワークフロー側で品質タグが付与されるため、被写体の指定のみ）
    "base": [
        "japanese 1girl, solo, full body, wide shot"
    ],
    # 2.5 名前指定による「顔の固定化・多様化」
    "model_name": [
        "",                 # 名前を指定しない（純粋なプロンプト依存）
        "face of Haruka",   # ハルカの顔
        "face of Risa",     # リサの顔
        "face of Yuki",     # ユキの顔
        "face of Rina",     # リナの顔
        "face of Mei",      # メイの顔
        "face of Kanna",    # カンナの顔
        "face of Yuna",     # ユナの顔
        "face of Mio"       # ミオの顔
    ],
    # 3. 年齢
    "age": [
        "20-year-old young woman",
        "25-year-old elegant woman",
        "30-year-old sophisticated woman"
    ],
    # 4. ポーズ（全て「立位」を明示 → しゃがみ・座りポーズを防止）
    "pose": [
        # ランウェイを歩く（直立歩行）
        "walking on runway, standing upright",
        # ハイファッションポーズを決める（直立・エレガント）
        "standing tall, striking an elegant upright high fashion pose",
        # 腰に手を当て、自信あふれるスタンス（直立）
        "standing upright, hand on hip, confident stance",
        # ダイナミックに振り返る（直立）
        "standing, turning around dynamically",
        # 前に向かって堂々と歩く（直立歩行）
        "walking forward confidently, standing tall, dynamic walking pose"
    ],
    # 5. 体型・身体的特徴（公開用・上品な質感バリエーション）
    "body": [
        # 1. 【王道・しっとり発汗】
        "tall and slender, long legs, model proportions, (medium breasts:1.2), (lightly sweating:1.1), glowing moist skin",

        # 2. 【可憐＆上品・すべすべ美肌スレンダー】
        "(slender body:1.3), model proportions, (medium breasts:1.2), smooth skin, flawless silky skin, soft glowing skin",

        # 3. 【合格！限界ふっくら美乳（ミディアム上限）】
        "tall and slender, long legs, model proportions, (medium breasts:1.5), (covered in sweat:1.2), glistening skin, sweaty body"
    ],
    # 6. 髪型
    "hair_style": [
        "sleek straight hair",
        "elegant updo",
        "tight ponytail",
        "chic bob cut",
        "voluminous runway hair"
    ],
    # 7. 髪色
    "hair_color": [
        # --- シック・大人カラー ---
        "black hair",
        "dark brown hair",
        "chestnut brown hair",

        # --- 洗練アッシュ系 ---
        "ash blonde hair",
        "ash gray hair",
        "lavender ash hair",

        # --- お洒落ハイライト・メッシュ系 ---
        "black hair with blue highlights",
        "black hair with pink highlights",
        "brown hair with blonde highlights",
        "dark hair with silver highlights"
    ],
    # 8. 顔立ち・メイク
    "face_features": [
        "round face, big round eyes, natural makeup",
        "sharp jawline, fierce runway makeup, high cheekbones",
        "almond eyes, glossy lips, heavy makeup",
        "droopy eyes, thick eyebrows, light makeup",
        "cat eyes, pouty lips, smokey eyes",
        "oval face, clear skin, minimal makeup",
        "elegant facial features, striking makeup",
        "asian beauty, natural elegant makeup, cute cheeks"
    ],
    # 9. 表情（凛としたハイファッション仕様）
    "expression": [
        "serious expression, fierce look, confident gaze",
        "confident seductive smile, looking at viewer",
        "stoic face, looking at viewer intensely with desire",
        "confident expression, seductive bedroom eyes, parted lips",
        "captivating gaze, fierce runway expression, looking at viewer"
    ],
    # 10. ほくろ
    "mole": [
        "",
        "",
        "",
        "beauty mark under eye",
        "(mole near the corner of the mouth:1.2)",
        "beauty mark on cheek"
    ],
    # 11. 服装（公開用・露出事故を防ぎつつセクシーなハイファッション）
    "outfit": [
        # === 1. ハイファッション＆ドレス系 ===
        # アヴァンギャルドなオートクチュールドレス ✕ 高級レースブラ
        "wearing a daring avant-garde haute couture mini dress, (wearing a luxury lace {bra_color} bra:1.3)",
        # シックなデザイナーブレザー ✕ タイトなブラレット
        "wearing a chic {color} designer blazer, (wearing a tight {bra_color} bralette:1.3)",
        # エレガントなスリット入りイブニングドレス ✕ 胸元カバー
        "wearing an elegant {color} evening gown with extremely high slit, (cleavage, securely covered breasts:1.3)",
        # メタリックマイクロミニスカート ✕ クロップトップ ✕ スポブラ
        "wearing a sexy {color} metallic micro mini skirt and tight crop top, (wearing a sports bra:1.2)",
        # シースルーレースドレス ✕ 高級インナーランジェリー
        "wearing an elegant translucent lace runway dress, (wearing beautiful {bra_color} lingerie underneath:1.4)",
        # オープンデザイナージャケット ✕ レザーミニ ✕ ブラレット
        "wearing a stylish open {color} designer jacket over a (tight {bra_color} bralette:1.4), leather mini skirt",
        # タイトなラテックスドレス ✕ 深い谷間
        "wearing a provocative tight {color} latex fashion dress, (cleavage:1.2)",
        # コルセット風ランウェイ衣装 ✕ ガーターストラップ ✕ レースブラ
        "wearing a {color} corset-style high fashion outfit, (garter straps:1.2), (wearing a sexy lace bra:1.3)",
        # シアージャケット ✕ マイクロビキニトップ ✕ デニムショート
        "wearing an incredibly tiny micro bikini top under a sheer {color} designer jacket, ultra short denim cutoffs, (cleavage:1.4)",
        # ウェットルック・レザーキャットスーツ ✕ ジッパー前開 ✕ プッシュアップブラ
        "wearing a skin-tight wet look leather catsuit, front zipper open, (wearing a sexy {bra_color} push-up bra:1.4)",
        # スキャンダラスなサイドカットアウトドレス ✕ 横乳カバー
        "wearing a scandalous high fashion gown with extreme side cutouts, (sideboob, wearing invisible bra:1.4)",
        # 透明PVCレインコート ✕ セクシーシースルーランジェリー
        "wearing a transparent PVC {color} raincoat over a (sexy sheer lingerie set:1.3), high fashion rainy look",
        # スクールガール風プリーツミニ ✕ シャツ開 ✕ レースブラ
        "wearing an ultra-short schoolgirl inspired luxury {color} plaid skirt, (thigh highs:1.2), open shirt with (sexy lace {bra_color} bra:1.3)",
        # 背中が大きく開いたバックレスシルクドレス ✕ バスト完全防御
        "wearing a dangerously low-cut backless {color} silk dress, (sideboob, but breasts fully covered:1.2)",
        # メタルチェーン＆レザーハーネス衣装 ✕ レザービキニトップ
        "wearing a heavy metal chains and leather harness high fashion outfit, (wearing a tiny leather {bra_color} bikini top:1.4)",
        # シースルーメッシュトップ（刺繍カバー） ✕ エッジーランウェイ
        "wearing a sheer mesh top with strategic solid embroidery covering the chest, high fashion edgy look, (no nipple, breasts covered:1.5)",
        # 深いVネックのハイレグ競泳水着風ボディスーツ
        "wearing a deep V-neck {color} swimsuit as a bodysuit, extreme high cut hips, runway look",
        # クラッシュデニムジャケット ✕ マイクロミニ ✕ スポブラ
        "wearing a shredded post-apocalyptic {color} denim jacket, (heavy cleavage, wearing a tight sports bra:1.3), (micro mini denim skirt:1.3)",

        # === 2. 超タイト・ボディコン系 ===
        # エレスティックバンデージドレス ✕ 全身のカーブが完全露出
        "wearing an ultra-tight {color} bandage mini dress, (every curve of her body tightly outlined:1.4), extreme body-con silhouette, high heels",
        # ミラーシークインマイクロドレス ✕ 極限露出シルエット
        "wearing a {color} mirror sequin micro mini dress, (skin-tight clinging to every curve:1.3), plunging V-neckline, ultra short hemline, runway look",

        # === 3. ボディチェーン・極小系 ===
        # ゴールドボディチェーン ✕ 極小シルクビキニトップ ✕ シアースカート
        "wearing a cascading gold body chain over an extremely tiny {color} silk bikini top, sheer wrapping skirt, high fashion jewelry showcase, (cleavage:1.4)",
        # メタリックリンクチェーンドレス ✕ 虹色ホログラムビキニ ✕ シアーフリルスカート
        "wearing an avant-garde metallic link chain dress over a (shining holographic micro bikini:1.4), sheer wrapping frilled skirt, futuristic high fashion runway look",
        # ダイヤモンドボディジュエリー ✕ ハイカットメタリックモノキニ
        "wearing draped diamond body jewelry over a daring high-cut {color} metallic monokini, runway styling, (cleavage:1.4)",
        # シルバーチェーンハーネス ✕ レザーブラレット ✕ マイクロミニ
        "wearing a complex silver chain harness over a tiny {color} leather bralette, ultra micro skirt, fierce runway styling, (cleavage:1.3)",

        # === 4. セクシーコスプレ系 ===
        # セクシーポリス制服 ✕ 超ミニスカート ✕ ネクタイ
        "wearing a sexy {color} police officer uniform, (extremely short mini skirt:1.3), police cap, necktie, wearing high heels",
        # ポリスブレザージャケット ✕ マイクロミニ ✕ サイハイストッキング
        "wearing a chic fitted {color} police uniform blazer, (micro mini police skirt:1.3), police cap, thigh-high stockings, wearing high heels",
        # ポリスジャケット前全開 ✕ 高級レースブラ ✕ マイクロミニポリス
        "(wearing a tailored {color} police jacket completely unbuttoned:1.3), (wearing a luxury lace {bra_color} bra:1.3), (micro mini police skirt:1.4), police cap",
        # セクシーCA制服 ✕ マイクロミニ ✕ シルクブラウス ✕ スカーフ
        "wearing a chic {color} airline stewardess uniform, (micro mini skirt:1.3), (cleavage:1.2), silk blouse, elegant scarf, high heels, runway look",
        # セクシー教師ブレザー前開 ✕ 高級レースブラ ✕ タイトミニ
        "wearing a sexy {color} teacher blazer completely unbuttoned, (wearing a luxury lace {bra_color} bra:1.3), (micro mini pencil skirt:1.3), high heels",
        # 高級メイド服 ✕ 極短ミニ ✕ 白エプロン ✕ サイハイ
        "wearing an elegant luxury {color} maid uniform with an extremely short skirt, (cleavage:1.2), white apron, thigh-high stockings",
        # ダークファンタジー魔女ドレス ✕ 黒レース ✕ とんがり帽子
        "wearing a dark fantasy {color} witch haute couture dress, dramatic black lace, (deep plunging neckline:1.3), pointed hat, sheer sleeves, runway look",
        # ゴシックデビル衣装 ✕ 黒シースルーミニ ✕ 小悪魔角＆尻尾 ✕ サイハイブーツ
        "wearing a gothic {color} devil fashion show costume, (extremely revealing black lace mini dress:1.3), small devil horns, long devil tail, thigh-high boots",
        # ハイファッション・セクシーナース制服 ✕ 前全開ショートジャケット ✕ 極限ウルトラマイクロミニ（パンティ露出） ✕ ナースキャップ
        "wearing a tiny open {color} cropped nurse jacket completely unbuttoned, (wearing a tight lace {bra_color} bra:1.4), (microscopic micro skirt, showing matching {bra_color} lace panties:1.5), (visible sexy garter straps and thigh highs:1.3), stylized nurse cap",
        # ハイファッション・セクシー巫女 ✕ 極限サイドカットアウト ✕ ハイスリット
        "wearing a high-fashion modernized miko (shrine maiden) outfit with extreme side cutouts, cropped red wide-sleeve top, ultra-high slit white skirt, (cleavage:1.3)",
        # 高級サテンバニーガール ✕ 深いVネック ✕ タキシードカラー
        "wearing a luxury {color} satin bunny girl bodysuit with a plunging neckline, elegant tuxedo collar and cuffs, matching bunny ears, fierce runway styling, (cleavage:1.4)"
    ],
    # 12. アクセサリー
    "accessory": [
        # 大胆で存在感のあるステートメントイヤリング
        "wearing bold statement earrings",
        # オーバーサイズのデザイナーサングラス
        "wearing oversized designer sunglasses",
        # 高級デザイナーハンドバッグ所持
        "holding a luxury designer handbag",
        # スタイリッシュなつば広ハット
        "wearing a stylish wide-brim hat",
        # レイヤード（重ね付け）ゴールドネックレス
        "wearing layered gold necklaces"
    ],
    # 13. 背景
    "background": [
        # ネオン輝くファッションステージ ✕ ダーク背景 ✕ スポットライト
        "(neon lit fashion stage:1.3), (dark background:1.2), (spotlight:1.1)",
        # 壮大なファッションショーステージ ✕ 優雅なステージ装飾
        "(grand fashion show stage:1.3), (elegant stage decorations:1.2)",
        # キャットウォーク ✕ ドラマチックなライティング
        "(catwalk stage:1.3), (dramatic stage lighting:1.2)"
    ]
}


def generate_prompt() -> str:
    """各カテゴリからランダムに1つを選び、カンマで繋げてプロンプトを生成"""
    parts = []
    for key, items in PROMPT_DATA.items():
        if items:
            chosen = random.choice(items)
            
            # --- 動的カラーシステムの移植（衣装の色やブラの色をランダムに変化） ---
            if key == "outfit":
                chosen_color     = random.choice(["white", "black", "pastel pink", "crimson red", "pale blue", "lavender purple", "lemon yellow", "tangerine orange", "beige", "gold", "silver", "hot pink", "burgundy", "deep navy"])
                chosen_bra_color = random.choice(["white", "black", "red", "pink", "purple", "emerald green", "light blue", "nude-colored", "navy blue", "canary yellow", "orange", "gold", "silver", "hot pink", "lavender"])
                chosen = chosen.replace("{color}", chosen_color).replace("{bra_color}", chosen_bra_color)
                    
            parts.append(chosen)
    cleaned = [p.strip().rstrip(",").strip() for p in parts if p.strip()]
    return ", ".join(cleaned)


def main():
    default_output_dir = "output_runway_vxp"

    parser = argparse.ArgumentParser(description="SDXL vxpILBase SFW Runway Generator")
    parser.add_argument("-n", "--num", type=int, default=1, help="生成数（デフォルト: 1）")
    parser.add_argument("-o", "--output-dir", default=default_output_dir, help="出力保存先ディレクトリ")
    parser.add_argument("--aspect", choices=["square", "portrait", "landscape"], default="square", help="画像の縦横比")
    args = parser.parse_args()

    # アスペクト比からサイズを決定
    img_width, img_height, target_width, target_height = get_aspect_dimensions(args.aspect, is_sdxl=True)

    # ワークフローJSONのロード (workflows/ から)
    try:
        prompt = load_workflow("vxpILBase_v10.json")
    except Exception as e:
        print(f"Error: vxpILBase_v10.json の読み込みに失敗しました: {e}")
        return

    client_id = str(uuid.uuid4())

    # WebSocket接続
    try:
        ws = connect_websocket(client_id)
        print("Connected to ComfyUI server")
    except Exception as e:
        print(f"ComfyUIへの接続に失敗しました: {e}")
        return

    total_start_time = time.time()
    for i in range(args.num):
        # 1. ランダムプロンプトを生成して設定（ノード2）
        positive_prompt = generate_prompt()
        combined_prompt = f"only one girl, solo, {positive_prompt}, (masterpiece, best quality:1.2), rating_safe, high fashion photography, cinematic lighting, perfect hands"
        if "2" in prompt:
            prompt["2"]["inputs"]["text"] = combined_prompt
        
        # シードの設定（ノード20）
        if "20" in prompt:
            prompt["20"]["inputs"]["seed"] = random.randint(0, 2**50 - 1)

        # モデルの上書き
        if "1" in prompt:
            prompt["1"]["inputs"]["ckpt_name"] = MODEL_NAME

        # ネガティブプロンプト部（ノード3）の上書き（※露出を徹底的に防ぐトリプルセーフ構造）
        if "3" in prompt:
            prompt["3"]["inputs"]["text"] = (
                "(worst quality:1.4), (monochrome:1.4), (grayscale:1.3), (noise:1.3), (deformed:1.3), "
                "(hands poor:1.2), (fingers poor:1.2), (bad anatomy:1.2), (inaccurate limb:1.2), (extra hands:1.2), "
                "(deformed fingers:1.2), (extra fingers:1.2), (extra arms:1.2), (extra legs:1.2), (ugly), (mosaic), "
                "naked, nude, bare breasts, exposed nipples, bare pussy, bottomless, no panties, "
                "(futa), (unnatural pose, color inconsistency, transparency issues, improper proportions, color scheme issues, image seams), "
                "(duplicate, morbid, mutilated, blurry, disfigured, cropped, signature, text, watermark), bad face, badeyes, dirty teeth, yellow teeth"
            )

        # サンプラー設定の上書き（ノード4: ベース用）
        if "4" in prompt:
            for k, v in BASE_SAMPLER_CONFIG.items():
                prompt["4"]["inputs"][k] = v
        
        # サンプラー設定の上書き（ノード19: アップスケール用）
        if "19" in prompt:
            for k, v in UPSCALE_SAMPLER_CONFIG.items():
                prompt["19"]["inputs"][k] = v

        # 出力サイズの上書き（ノード8: 空のLatent Image）
        if "8" in prompt:
            prompt["8"]["inputs"]["width"] = img_width
            prompt["8"]["inputs"]["height"] = img_height
            
        # アップスケールサイズの上書き（ノード17）※動画用ジャストサイズ
        if "17" in prompt:
            image_link = prompt["17"]["inputs"].get("image", ["16", 0])
            prompt["17"] = {
                "class_type": "ImageScale",
                "inputs": {
                    "upscale_method": "area",
                    "width": target_width,
                    "height": target_height,
                    "crop": "center",
                    "image": image_link
                }
            }

        # API呼び出し前に情報を出力
        print(f"[{i+1}/{args.num}] Positive Prompt:\n{positive_prompt}")
        if "20" in prompt:
            print(f"Seed: {prompt['20']['inputs']['seed']}")
        print("---")

        # 画像生成開始
        print("Starting generation...")
        loop_start_time = time.time()
        try:
            images = get_images(ws, prompt, client_id)
            loop_time = time.time() - loop_start_time
            
            m, s = divmod(loop_time, 60)
            h, m = divmod(m, 60)
            time_str = f"{int(h):02d}:{int(m):02d}:{s:05.2f}"
            
            print(f"Generated {len(images)} image(s)")
            print(f"[{i+1}/{args.num}] 生成完了! (所要時間: {time_str})")

            # 保存処理
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            for j, image_data in enumerate(images):
                suffix = f"_{j+1}" if len(images) > 1 else ""
                save_image(image_data, f"img_{ts}{suffix}.png", args.output_dir)
        except Exception as e:
            print(f"画像生成中にエラーが発生しました: {e}")
            break

    total_time = time.time() - total_start_time
    m, s = divmod(total_time, 60)
    h, m = divmod(m, 60)
    total_time_str = f"{int(h):02d}:{int(m):02d}:{s:05.2f}"
    
    print(f"すべての生成が完了しました！ (合計所要時間: {total_time_str})")
    ws.close()
    print("Done")

if __name__ == "__main__":
    main()
