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

# --- プロンプト用データセット（公開用・SFW仕様） ---
PROMPT_DATA = {
    # 1. 主題・ベース
    "base": [
        "japanese 1girl, solo, full body, wide shot"
    ],
    # 2.5 名前指定による「顔の固定化・多様化」
    "model_name": [
        "",
        "face of Haruka",
        "face of Risa",
        "face of Yuki",
        "face of Rina",
        "face of Mei",
        "face of Kanna",
        "face of Yuna",
        "face of Mio"
    ],
    # 3. 年齢
    "age": [
        "20-year-old, young woman",
        "25-year-old, elegant woman",
        "30-year-old, sophisticated woman"
    ],
    # 4. ポーズ
    "pose": [
        "walking on runway",
        "striking a high fashion pose",
        "hand on hip, confident stance",
        "turning around dynamically",
        "walking forward confidently, dynamic walking pose"
    ],
    # 5. 体型・身体的特徴
    "body": [
        "tall and slender, long legs, model proportions, (medium breasts:1.2)",
        "elegant posture, beautiful collarbone, (medium breasts:1.2), sensual mood",
        "(medium breasts:1.2), (covered in sweat:1.1), tall and slender",
        "curvy model proportions, long legs, (medium breasts:1.2)"
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
        "black hair",
        "dark brown hair",
        "blonde hair",
        "silver hair",
        "ash brown hair"
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
    # 9. 表情
    "expression": [
        "serious expression, fierce look",
        "confident smile",
        "stoic face, looking at viewer intensely"
    ],
    # 10. ほくろ
    "mole": [
        "",
        "beauty mark under eye",
        "(mole near the corner of the mouth:1.2)",
        "beauty mark on cheek"
    ],
    # 11. 服装（公開用・露出事故を防ぎつつセクシーなハイファッション）
    "outfit": [
        "wearing a daring avant-garde haute couture mini dress, (wearing a luxury lace bra:1.3)",
        "wearing a chic designer blazer, (wearing a tight bralette:1.3)",
        "wearing an elegant evening gown with extremely high slit, (cleavage, securely covered breasts:1.3)",
        "wearing a sexy metallic micro mini skirt and tight crop top, (wearing a sports bra:1.2)",
        "wearing an elegant translucent lace runway dress, (wearing beautiful lingerie underneath:1.4)",
        "wearing a stylish open designer jacket over a (tight bralette:1.4), leather mini skirt",
        "wearing a provocative tight latex fashion dress, (cleavage:1.2)",
        "wearing a corset-style high fashion outfit, (garter straps:1.2), (wearing a sexy lace bra:1.3)",
        "wearing an incredibly tiny micro bikini top under a sheer designer jacket, ultra short denim cutoffs, (cleavage:1.4)",
        "wearing a skin-tight wet look leather catsuit, front zipper open, (wearing a sexy black push-up bra:1.4)",
        "wearing a scandalous high fashion gown with extreme side cutouts, (sideboob, wearing invisible bra:1.4)",
        "wearing a transparent PVC raincoat over a (sexy sheer lingerie set:1.3), high fashion rainy look",
        "wearing an ultra-short schoolgirl inspired luxury plaid skirt, (thigh highs:1.2), open shirt with (sexy lace bra:1.3)",
        "wearing a dangerously low-cut backless silk dress, (sideboob, but breasts fully covered:1.2)",
        "wearing a heavy metal chains and leather harness high fashion outfit, (wearing a tiny leather bikini top:1.4)",
        "wearing a sheer mesh top with strategic solid embroidery covering the chest, high fashion edgy look, (no nipple, breasts covered:1.5)",
        "wearing a deep V-neck swimsuit as a bodysuit, extreme high cut hips, runway look",
        "wearing a shredded post-apocalyptic denim jacket, (heavy cleavage, wearing a tight sports bra:1.3), (micro mini denim skirt:1.3)",
        "wearing a sexy police officer uniform, (extremely short mini skirt:1.3), police cap, necktie, wearing high heels",
        "wearing a chic fitted police uniform blazer, (micro mini police skirt:1.3), police cap, thigh-high stockings, wearing high heels",
        "(wearing a tailored police jacket completely unbuttoned:1.3), (wearing a luxury lace bra:1.3), (micro mini police skirt:1.4), police cap",
        "wearing a chic airline stewardess uniform, (micro mini skirt:1.3), (cleavage:1.2), silk blouse, elegant scarf, high heels, runway look",
        "wearing a sexy teacher blazer completely unbuttoned, (wearing a luxury lace bra:1.3), (micro mini pencil skirt:1.3), high heels",
        "wearing an elegant luxury maid uniform with an extremely short skirt, (cleavage:1.2), white apron, thigh-high stockings",
        "wearing a dark fantasy witch haute couture dress, dramatic black lace, (deep plunging neckline:1.3), pointed hat, sheer sleeves, runway look",
        "wearing a gothic devil fashion show costume, (extremely revealing black lace mini dress:1.3), small devil horns, long devil tail, thigh-high boots"
    ],
    # 12. アクセサリー
    "accessory": [
        "wearing bold statement earrings",
        "wearing oversized designer sunglasses",
        "holding a luxury designer handbag",
        "wearing a stylish wide-brim hat",
        "wearing layered gold necklaces"
    ],
    # 13. 背景
    "background": [
        "fashion show stage, brightly lit runway, crowd in background",
        "glamorous runway stage, flashing stage lights, audience",
        "neon lit fashion stage, dark background, spotlight",
        "grand fashion show stage, elegant stage decorations",
        "catwalk stage, dramatic stage lighting"
    ]
}


def generate_prompt() -> str:
    """各カテゴリからランダムにパーツを選択し、Z-Image-Turbo向けに自然な英語の段落を構築する"""
    model_name = random.choice(PROMPT_DATA["model_name"]).strip()
    age = random.choice(PROMPT_DATA["age"]).strip()
    pose = random.choice(PROMPT_DATA["pose"]).strip()
    body = random.choice(PROMPT_DATA["body"]).strip()
    hair_style = random.choice(PROMPT_DATA["hair_style"]).strip()
    hair_color = random.choice(PROMPT_DATA["hair_color"]).strip()
    face_features = random.choice(PROMPT_DATA["face_features"]).strip()
    expression = random.choice(PROMPT_DATA["expression"]).strip()
    mole = random.choice(PROMPT_DATA["mole"]).strip()
    outfit = random.choice(PROMPT_DATA["outfit"]).strip()
    accessory = random.choice(PROMPT_DATA["accessory"]).strip()
    background = random.choice(PROMPT_DATA["background"]).strip()

    # --- 各要素のクリーンアップ ---
    model_name = clean_prompt_weights(model_name)
    age = clean_prompt_weights(age)
    pose = clean_prompt_weights(pose)
    body = clean_prompt_weights(body)
    hair_style = clean_prompt_weights(hair_style)
    hair_color = clean_prompt_weights(hair_color)
    face_features = clean_prompt_weights(face_features)
    expression = clean_prompt_weights(expression)
    mole = clean_prompt_weights(mole)
    outfit = clean_prompt_weights(outfit)
    accessory = clean_prompt_weights(accessory)
    background = clean_prompt_weights(background)

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

    # 2. 髪型と髪色 (より自然な前置詞表現へ)
    hair_sentence = ""
    if hair_style and hair_color:
        hair_sentence = f"Her hair is beautiful, styled in a {hair_style} with {hair_color}."
    elif hair_style:
        hair_sentence = f"Her hair is beautiful, styled in a {hair_style}."
    elif hair_color:
        hair_sentence = f"She has beautiful {hair_color}."

    # 3. 顔立ち・表情・ほくろ
    face_details = []
    if face_features:
        face_details.append(face_features)
    if expression:
        face_details.append(expression)
    if mole:
        face_details.append(f"a {mole}")
        
    face_sentence = ""
    if face_details:
        face_sentence = f"She has a {', '.join(face_details)}."

    # 4. ポーズ・衣装・アクセサリー
    pose_part = f"She is confidently {pose}" if pose else "She is standing confidently"
    
    outfit_part = ""
    if outfit:
        if outfit.lower().startswith("wearing"):
            outfit_part = outfit
        else:
            outfit_part = f"wearing {outfit}"

    acc_part = ""
    if accessory:
        cleaned_acc = accessory
        if cleaned_acc.startswith("wearing "):
            cleaned_acc = cleaned_acc[8:]
        acc_part = f"adorned with {cleaned_acc}"
    
    clothing_parts = [pose_part]
    if outfit_part:
        clothing_parts.append(outfit_part)
    if acc_part:
        clothing_parts.append(acc_part)
        
    clothing_sentence = ", ".join(clothing_parts) + "."

    # 5. 背景
    bg_sentence = ""
    if background:
        bg_sentence = f"The entire scene is captured on a {background}."

    # 段落として結合
    sentences = [subject_sentence, hair_sentence, face_sentence, clothing_sentence, bg_sentence]
    full_prompt = " ".join([s for s in sentences if s.strip()])
    
    # 重複するスペース・記号の整形
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
    parser.add_argument("-p", "--prompt", type=str, default="", help="カスタムの精密なポジティブプロンプトを指定する")
    args = parser.parse_args()

    # アスペクト比からサイズを決定
    if args.aspect == "portrait":
        img_width, img_height = 768, 1344
    elif args.aspect == "landscape":
        img_width, img_height = 1344, 768
    else:
        img_width, img_height = 1024, 1024

    # ワークフローJSONのロード (workflows/ から)
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
        # 1. Z-Image向け自然プロンプトを決定
        if args.prompt:
            dynamic_prompt = args.prompt
        else:
            dynamic_prompt = generate_prompt()
        
        # 2. ワークフローJSONの書き換え
        # ポジティブプロンプトの完全統合（2体描写バグを根絶するため、ConditioningConcatを排除して1つのテキストにまとめます）
        # ※ fixed_text は「品質タグのみ」に限定します。"A young woman..." のような主語を再導入すると
        #   モデルが2人目の被写体として認識し、2体描写バグが再発します。
        fixed_text = "highly detailed cinematic photograph, pale glistening moist skin, ideal body proportions, full-body shot, expressive eyes, fine hair texture, soft realistic cinematic lighting, natural shadows, perfectly in focus, shot on 35mm lens, DSLR, 8k resolution, ultra photorealism"
        combined_positive_prompt = f"{dynamic_prompt}, {fixed_text}"

        # ノード「6」: 統合ポジティブプロンプト
        if "6" in prompt:
            prompt["6"]["inputs"]["text"] = combined_positive_prompt
            
        # ノード「3」: KSampler設定
        if "3" in prompt:
            prompt["3"]["inputs"]["seed"] = random.randint(0, 2**50 - 1)
            prompt["3"]["inputs"]["steps"] = args.steps
            prompt["3"]["inputs"]["cfg"] = args.cfg
            
        # ノード「13」: EmptySD3LatentImage設定
        if "13" in prompt:
            prompt["13"]["inputs"]["width"] = img_width
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
