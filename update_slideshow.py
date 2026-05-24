import os
import glob
import re
import sys

def update_slideshow():
    # デフォルトの画像フォルダ名
    default_folder = "output_runway_zimage"
    
    # 1. ターゲット画像ディレクトリとフォルダ名のパース
    if len(sys.argv) > 1:
        target_input = sys.argv[1].rstrip("\\/")
        if os.path.isabs(target_input):
            # 絶対パスが指定された場合 (例: D:\gen_runway\output_runway_vxp)
            image_dir = target_input
            folder_name = os.path.basename(target_input)
        else:
            # 相対的なフォルダ名が指定された場合 (例: output_runway_vxp)
            folder_name = target_input
            image_dir = os.path.join(r"d:\gen_runway", folder_name)
    else:
        # 引数なしの場合はデフォルトを使用
        folder_name = default_folder
        image_dir = os.path.join(r"d:\gen_runway", folder_name)

    # ターゲットとなるHTML
    html_path = r"d:\gen_runway\runway_show.html"

    print("=== Runway Slideshow Auto-Updater ===")
    print(f"Targeting Folder: {folder_name}")
    print(f"Directory Path:   {image_dir}")
    
    # ファイルとフォルダの存在確認
    if not os.path.exists(html_path):
        print(f"Error: runway_show.html が見つかりません: {html_path}")
        return
        
    if not os.path.exists(image_dir):
        print(f"Error: 指定された画像フォルダが見つかりません: {image_dir}")
        return

    # 2. PNG画像のリストを取得して日付順にソート
    search_pattern = os.path.join(image_dir, "*.png")
    png_files = glob.glob(search_pattern)
    
    if not png_files:
        print(f"Warning: {image_dir} 内にPNG画像が見つかりませんでした。")
        relative_paths = []
    else:
        # ファイル名でソート (日付順)
        png_files.sort(key=lambda x: os.path.basename(x))
        
        # HTMLから見た相対パスに変換
        # Windowsの区切り文字 '\' は、ブラウザで正しく動くように、かつ Pythonの置換エラーを防止するために '/' に統一します
        relative_paths = []
        for f in png_files:
            filename = os.path.basename(f)
            # URL互換のスラッシュに統一
            rel_path = f"{folder_name}/{filename}".replace("\\", "/")
            relative_paths.append(rel_path)
            
        print(f"Found {len(relative_paths)} PNG images in {image_dir}.")

    # 3. HTMLの読み込み
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # 4. JS配列ブロックの生成
    if relative_paths:
        js_items = ",\n".join([f'            "{path}"' for path in relative_paths])
        new_preset_block = f"const PRESET_IMAGES = [\n{js_items}\n        ];"
    else:
        new_preset_block = "const PRESET_IMAGES = [\n            /*IMAGE_LIST_PLACEHOLDER*/\n        ];"

    # 5. 安全な置換処理
    # re.sub は置換テキスト内の '\' を正規表現エスケープとして解釈してしまうため、
    # 検索だけ re.search で行い、置換は Pythonの標準文字列関数 .replace() を使って安全に実行します。
    pattern = r"const PRESET_IMAGES = \[\s*[\s\S]*?\s*\];"
    match = re.search(pattern, html_content)
    
    if match:
        target_string = match.group(0)
        updated_content = html_content.replace(target_string, new_preset_block)
        print(f"Updated the image array in runway_show.html with images from '{folder_name}'.")
    else:
        print("Error: HTML内の PRESET_IMAGES 配列の検出に失敗しました。")
        return

    # 6. 上書き保存
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(updated_content)
        
    print(f"Success! d:\\gen_runway\\runway_show.html を更新しました。")
    print("このファイルをダブルクリックしてブラウザで開くだけで、自動的にスライドショーが始まります！")
    print("=====================================")

if __name__ == "__main__":
    update_slideshow()
