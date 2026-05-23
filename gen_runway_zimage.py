import random
import os
import argparse
import re
import uuid
from datetime import datetime
import time

from comfy_api import (
    connect_websocket,
    get_images,
    save_image,
    load_workflow,
    clean_prompt_weights
)

MODEL_NAME = "z-image-turbo-q8_0.gguf"

# --- プロンプト用データセット（Z-Image-Turbo向け・自然文形式） ---
PROMPT_DATA = {
    # 1. 主題・ベース
    "base": [
        "japanese 1girl, solo, full body, wide shot"
    ],
    # 2. 名前指定による「顔の固定化・多様化」
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
        "20-year-old, young woman",
        "25-year-old, elegant woman",
        "30-year-old, sophisticated woman"
    ],
    # 4. ポーズ（全て「直立・歩行」を明示 → しゃがみ・座りポーズを防止）
    "pose": [
        "walking gracefully on a fashion runway, standing upright",
        "striking an elegant high fashion pose, standing tall",
        "standing upright with one hand on her hip, confident stance",
        "turning around dynamically, standing tall",
        "walking forward confidently, standing upright, with a dynamic stride"
    ],
    # 5. 体型・身体的特徴
    "body": [
        # 1. 【王道・しっとり発汗】
        "tall and slender with long legs and model proportions, medium-sized breasts, lightly sweating with glowing moist skin",
        # 2. 【可憐＆上品・すべすべ美肌スレンダー】
        "slender elegant figure with model proportions, medium-sized breasts, smooth flawless silky skin with a soft natural glow",
        # 3. 【ふっくら美乳・発汗】
        "tall and slender with long legs and model proportions, medium-sized breasts, covered in sweat with glistening luminous skin"
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
        "black hair with subtle blue highlights",
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
        "with a serious and fierce expression, confident gaze toward the viewer",
        "with a confident and seductive smile, looking directly at the viewer",
        "with a stoic and intense expression, gazing at the viewer with desire",
        "with a confident expression, seductive bedroom eyes and slightly parted lips",
        "with a captivating fierce runway expression, looking intensely at the viewer"
    ],
    # 10. ほくろ
    "mole": [
        "",
        "",
        "",
        "a subtle beauty mark under her eye",
        "a delicate mole near the corner of her mouth",
        "a charming beauty mark on her cheek"
    ],
    # 11. 服装（{color}/{bra_color} は generate_prompt 内で動的置換）
    "outfit": [
        # === 1. ハイファッション＆ドレス系 ===
        # アヴァンギャルドなオートクチュールドレス ✕ 高級レースブラ
        "wearing a daring avant-garde haute couture mini dress, wearing a luxury lace {bra_color} bra underneath",
        # シックなデザイナーブレザー ✕ タイトなブラレット
        "wearing a chic {color} designer blazer, wearing a tight {bra_color} bralette",
        # エレガントなスリット入りイブニングドレス ✕ 胸元カバー
        "wearing an elegant {color} evening gown with an extremely high slit, with cleavage and securely covered breasts",
        # メタリックマイクロミニスカート ✕ クロップトップ ✕ スポブラ
        "wearing a sexy {color} metallic micro mini skirt and a tight crop top, wearing a sports bra",
        # シースルーレースドレス ✕ 高級インナーランジェリー
        "wearing an elegant translucent lace runway dress, wearing beautiful {bra_color} lingerie underneath",
        # オープンデザイナージャケット ✕ レザーミニ ✕ ブラレット
        "wearing a stylish open {color} designer jacket over a tight {bra_color} bralette, with a leather mini skirt",
        # タイトなラテックスドレス ✕ 深い谷間
        "wearing a provocative tight {color} latex fashion dress, with elegant cleavage",
        # コルセット風ランウェイ衣装 ✕ ガーターストラップ ✕ レースブラ
        "wearing a {color} corset-style high fashion outfit with garter straps, wearing a sexy lace bra",
        # シアージャケット ✕ マイクロビキニトップ ✕ デニムショート
        "wearing an incredibly tiny micro bikini top under a sheer {color} designer jacket, with ultra short denim cutoffs and cleavage",
        # ウェットルック・レザーキャットスーツ ✕ ジッパー前開 ✕ プッシュアップブラ
        "wearing a skin-tight wet look leather catsuit, front zipper open, wearing a sexy {bra_color} push-up bra",
        # スキャンダラスなサイドカットアウトドレス ✕ 横乳カバー
        "wearing a scandalous high fashion gown with extreme side cutouts, with sideboob and wearing an invisible bra",
        # 透明PVCレインコート ✕ セクシーシースルーランジェリー
        "wearing a transparent PVC {color} raincoat over a sexy sheer lingerie set, in a high fashion rainy look",
        # スクールガール風プリーツミニ ✕ シャツ開 ✕ レースブラ
        "wearing an ultra-short schoolgirl inspired luxury {color} plaid skirt with thigh highs, open shirt with a sexy lace {bra_color} bra",
        # 背中が大きく開いたバックレスシルクドレス ✕ バスト完全防御
        "wearing a dangerously low-cut backless {color} silk dress, with sideboob and fully covered breasts",
        # メタルチェーン＆レザーハーネス衣装 ✕ レザービキニトップ
        "wearing a heavy metal chain and leather harness high fashion outfit, wearing a tiny leather {bra_color} bikini top",
        # シースルーメッシュトップ（刺繍カバー） ✕ エッジーランウェイ
        "wearing a sheer mesh top with strategic solid embroidery covering the chest, in a high fashion edgy look",
        # 深いVネックのハイレグ競泳水着風ボディスーツ
        "wearing a deep V-neck {color} swimsuit-style bodysuit with extreme high-cut hips, in a runway look",
        # クラッシュデニムジャケット ✕ マイクロミニ ✕ スポブラ
        "wearing a shredded post-apocalyptic {color} denim jacket, with heavy cleavage and a tight sports bra, and a micro mini denim skirt",

        # === 2. 超タイト・ボディコン系 ===
        # エレスティックバンデージドレス ✕ 全身のカーブが完全露出
        "wearing an ultra-tight {color} bandage mini dress that tightly outlines every curve of her body, with an extreme body-con silhouette and high heels",
        # ミラーシークインマイクロドレス ✕ 極限露出シルエット
        "wearing a {color} mirror sequin micro mini dress, skin-tight and clinging to every curve, with a plunging V-neckline and ultra short hemline",

        # === 3. ボディチェーン・極小系 ===
        # ゴールドボディチェーン ✕ 極小シルクビキニトップ ✕ シアースカート
        "wearing a cascading gold body chain over an extremely tiny {color} silk bikini top, with a sheer wrapping skirt, in a high fashion jewelry showcase",
        # メタリックリンクチェーンドレス ✕ 虹色ホログラムビキニ ✕ シアーフリルスカート
        "wearing an avant-garde metallic link chain dress over a shining holographic micro bikini, with a sheer frilled skirt, in a futuristic high fashion runway look",
        # ダイヤモンドボディジュエリー ✕ ハイカットメタリックモノキニ
        "wearing draped diamond body jewelry over a daring high-cut {color} metallic monokini, in a runway styling with cleavage",
        # シルバーチェーンハーネス ✕ レザーブラレット ✕ マイクロミニ
        "wearing a complex silver chain harness over a tiny {color} leather bralette, with an ultra micro skirt, in a fierce runway styling with cleavage",

        # === 4. セクシーコスプレ系 ===
        # セクシーポリス制服 ✕ 超ミニスカート ✕ ネクタイ
        "wearing a sexy {color} police officer uniform with an extremely short mini skirt, a police cap and necktie, and high heels",
        # ポリスブレザージャケット ✕ マイクロミニ ✕ サイハイストッキング
        "wearing a chic fitted {color} police uniform blazer with a micro mini police skirt, a police cap, thigh-high stockings, and high heels",
        # ポリスジャケット前全開 ✕ 高級レースブラ ✕ マイクロミニポリス
        "wearing a completely unbuttoned tailored {color} police jacket, wearing a luxury lace {bra_color} bra, a micro mini police skirt, and a police cap",
        # セクシーCA制服 ✕ マイクロミニ ✕ シルクブラウス ✕ スカーフ
        "wearing a chic {color} airline stewardess uniform with a micro mini skirt, cleavage, a silk blouse, an elegant scarf, and high heels",
        # セクシー教師ブレザー前開 ✕ 高級レースブラ ✕ タイトミニ
        "wearing a completely unbuttoned sexy {color} teacher blazer, wearing a luxury lace {bra_color} bra, and a micro mini pencil skirt with high heels",
        # 高級メイド服 ✕ 極短ミニ ✕ 白エプロン ✕ サイハイ
        "wearing an elegant luxury {color} maid uniform with an extremely short skirt, cleavage, a white apron, and thigh-high stockings",
        # ダークファンタジー魔女ドレス ✕ 黒レース ✕ とんがり帽子
        "wearing a dark fantasy {color} witch haute couture dress with dramatic black lace, a deep plunging neckline, a pointed hat, and sheer sleeves",
        # ゴシックデビル衣装 ✕ 黒シースルーミニ ✕ 小悪魔角＆尻尾 ✕ サイハイブーツ
        "wearing a gothic {color} devil fashion show costume, an extremely revealing black lace mini dress, small devil horns, a long devil tail, and thigh-high boots",
        # ハイファッション・セクシーナース制服 ✕ 前全開ショートジャケット ✕ 極限ウルトラマイクロミニ ✕ ナースキャップ
        "wearing a tiny open {color} cropped nurse jacket completely unbuttoned, wearing a tight lace {bra_color} bra, a microscopic micro skirt showing matching {bra_color} lace panties, visible sexy garter straps and thigh highs, and a stylized nurse cap",
        # ハイファッション・セクシー巫女 ✕ 極限サイドカットアウト ✕ ハイスリット
        "wearing a high-fashion modernized shrine maiden outfit with extreme side cutouts, a cropped red wide-sleeve top, and an ultra-high slit white skirt",
        # 高級サテンバニーガール ✕ 深いVネック ✕ タキシードカラー
        "wearing a luxury {color} satin bunny girl bodysuit with a plunging neckline, elegant tuxedo collar and cuffs, matching bunny ears, in a fierce runway styling with cleavage"
    ],
    # 12. アクセサリー
    "accessory": [
        "bold statement earrings",
        "oversized designer sunglasses",
        "a luxury designer handbag",
        "a stylish wide-brim hat",
        "layered gold necklaces"
    ],
    # 13. 背景
    "background": [
        "a neon-lit fashion stage with a dark background and dramatic spotlights",
        "a grand fashion show stage with elegant stage decorations",
        "a sleek catwalk stage with dramatic and cinematic stage lighting"
    ]
}


# --- 動的カラーリスト ---
_OUTFIT_COLORS = [
    "white", "black", "pastel pink", "crimson red", "pale blue",
    "lavender purple", "lemon yellow", "tangerine orange", "beige",
    "gold", "silver", "hot pink", "burgundy", "deep navy"
]
_BRA_COLORS = [
    "white", "black", "red", "pink", "purple", "emerald green",
    "light blue", "nude-colored", "navy blue", "canary yellow",
    "orange", "gold", "silver", "hot pink", "lavender"
]


def generate_prompt() -> str:
    """各カテゴリからランダムにパーツを選択し、Z-Image-Turbo向けに自然な英語の段落を構築する"""
    model_name    = random.choice(PROMPT_DATA["model_name"]).strip()
    age           = random.choice(PROMPT_DATA["age"]).strip()
    pose          = random.choice(PROMPT_DATA["pose"]).strip()
    body          = random.choice(PROMPT_DATA["body"]).strip()
    hair_style    = random.choice(PROMPT_DATA["hair_style"]).strip()
    hair_color    = random.choice(PROMPT_DATA["hair_color"]).strip()
    face_features = random.choice(PROMPT_DATA["face_features"]).strip()
    expression    = random.choice(PROMPT_DATA["expression"]).strip()
    mole          = random.choice(PROMPT_DATA["mole"]).strip()
    accessory     = random.choice(PROMPT_DATA["accessory"]).strip()
    background    = random.choice(PROMPT_DATA["background"]).strip()

    # --- 動的カラーシステム（衣装の色・ブラカラーをランダムに変化） ---
    outfit_raw       = random.choice(PROMPT_DATA["outfit"]).strip()
    chosen_color     = random.choice(_OUTFIT_COLORS)
    chosen_bra_color = random.choice(_BRA_COLORS)
    outfit = outfit_raw.replace("{color}", chosen_color).replace("{bra_color}", chosen_bra_color)

    # --- ウェイト構文を除去（Z-Image-Turboは自然文が最適） ---
    age           = clean_prompt_weights(age)
    pose          = clean_prompt_weights(pose)
    body          = clean_prompt_weights(body)
    hair_style    = clean_prompt_weights(hair_style)
    hair_color    = clean_prompt_weights(hair_color)
    face_features = clean_prompt_weights(face_features)
    expression    = clean_prompt_weights(expression)
    mole          = clean_prompt_weights(mole)
    outfit        = clean_prompt_weights(outfit)
    accessory     = clean_prompt_weights(accessory)
    background    = clean_prompt_weights(background)

    # 年齢の重複表現の防止（"20-year-old, young woman" -> "20-year-old"）
    cleaned_age = age
    if "woman" in cleaned_age:
        cleaned_age = cleaned_age.split(",")[0].strip()

    # --- 自然文としての組み立て ---
    # 1. 基本設定（モデル・年齢・体型）
    subject_details = []
    if cleaned_age:
        subject_details.append(cleaned_age)
    if model_name:
        subject_details.append(f"with the {model_name}")

    if subject_details:
        subject_sentence = f"She is an elegant young Japanese model, {', '.join(subject_details)}."
    else:
        subject_sentence = "She is an elegant young Japanese model."

    if body:
        subject_sentence += f" She has {body}."

    # 2. 髪型と髪色
    hair_sentence = ""
    if hair_style and hair_color:
        hair_sentence = f"Her hair is beautifully styled in a {hair_style} with {hair_color}."
    elif hair_style:
        hair_sentence = f"Her hair is beautifully styled in a {hair_style}."
    elif hair_color:
        hair_sentence = f"She has beautiful {hair_color}."

    # 3. 顔立ち・表情・ほくろ
    face_parts = []
    if face_features:
        face_parts.append(face_features)
    if expression:
        face_parts.append(expression)
    if mole:
        face_parts.append(mole)

    face_sentence = ""
    if face_parts:
        face_sentence = f"Her face features {', '.join(face_parts)}."

    # 4. ポーズ・衣装・アクセサリー
    pose_part = f"She is {pose}" if pose else "She is standing confidently"

    outfit_part = ""
    if outfit:
        if outfit.lower().startswith("wearing"):
            outfit_part = f"she is {outfit}"
        else:
            outfit_part = f"she is wearing {outfit}"

    acc_part = f"adorned with {accessory}" if accessory else ""

    clothing_parts = [pose_part]
    if outfit_part:
        clothing_parts.append(outfit_part)
    if acc_part:
        clothing_parts.append(acc_part)

    clothing_sentence = ", ".join(clothing_parts) + "."

    # 5. 背景
    bg_sentence = f"The scene is set on {background}." if background else ""

    # 段落として結合
    sentences = [subject_sentence, hair_sentence, face_sentence, clothing_sentence, bg_sentence]
    full_prompt = " ".join([s for s in sentences if s.strip()])

    # 整形
    full_prompt = re.sub(r',\s*,', ',', full_prompt)
    full_prompt = re.sub(r'\s+', ' ', full_prompt).strip()

    return full_prompt


def main():
    default_output_dir = "output_runway_zimage"

    parser = argparse.ArgumentParser(description="Z-Image-Turbo Runway Generator")
    parser.add_argument("-n", "--num", type=int, default=1, help="生成枚数（デフォルト: 1）")
    parser.add_argument("-o", "--output-dir", default=default_output_dir, help="出力保存先ディレクトリ")
    parser.add_argument("--aspect", choices=["square", "portrait", "landscape"], default="square", help="画像のアスペクト比")
    parser.add_argument("--steps", type=int, default=8, help="KSamplerのステップ数（デフォルト: 8）")
    parser.add_argument("--cfg", type=float, default=1.5, help="KSamplerのCFGスケール（デフォルト: 1.5）")
    parser.add_argument("-p", "--prompt", type=str, default="", help="カスタムプロンプトを直接指定")
    args = parser.parse_args()

    # アスペクト比からサイズを決定
    if args.aspect == "portrait":
        img_width, img_height = 768, 1344
    elif args.aspect == "landscape":
        img_width, img_height = 1344, 768
    else:
        img_width, img_height = 1024, 1024

    # ワークフローJSONのロード
    try:
        prompt = load_workflow("z-image.json")
    except Exception as e:
        print(f"Error: z-image.json の読み込みに失敗しました: {e}")
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
        # 1. プロンプトを決定
        if args.prompt:
            dynamic_prompt = args.prompt
        else:
            dynamic_prompt = generate_prompt()

        # 2. ワークフローの書き換え

        # モデル名の上書き（ノード28）
        if "28" in prompt:
            prompt["28"]["inputs"]["gguf_name"] = MODEL_NAME

        # ポジティブプロンプト（ノード6）— 品質タグは自然文形式で末尾に追加
        fixed_text = (
            "highly detailed cinematic photograph, ideal body proportions, full-body shot, "
            "expressive eyes, fine hair texture, soft realistic cinematic lighting, natural shadows, "
            "perfectly in focus, shot on 35mm lens, DSLR, ultra photorealism"
        )
        combined_positive_prompt = f"{dynamic_prompt} {fixed_text}"
        if "6" in prompt:
            prompt["6"]["inputs"]["text"] = combined_positive_prompt

        # ネガティブプロンプト（ノード7）— Z-Image-Turbo向けシンプル自然文
        if "7" in prompt:
            prompt["7"]["inputs"]["text"] = (
                "low quality, blurry, out of focus, poorly rendered, distorted, bad anatomy, "
                "extra limbs, extra hands, extra fingers, deformed fingers, missing fingers, "
                "fused body parts, mutated, disfigured, ugly face, poorly drawn face, bad proportions, "
                "duplicate, cropped, watermark, text, signature, logo, grainy, noisy"
            )

        # KSampler設定（ノード3）
        if "3" in prompt:
            prompt["3"]["inputs"]["seed"]  = random.randint(0, 2**50 - 1)
            prompt["3"]["inputs"]["steps"] = args.steps
            prompt["3"]["inputs"]["cfg"]   = args.cfg

        # 画像サイズ（ノード13）
        if "13" in prompt:
            prompt["13"]["inputs"]["width"]  = img_width
            prompt["13"]["inputs"]["height"] = img_height

        print(f"[{i+1}/{args.num}] Dynamic Prompt:\n{dynamic_prompt}")
        print(f"Seed: {prompt['3']['inputs']['seed']} | Size: {img_width}x{img_height} | Steps: {args.steps} | CFG: {args.cfg}")
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
