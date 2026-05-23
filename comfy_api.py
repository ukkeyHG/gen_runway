import websocket
import urllib.request
import urllib.parse
import json
import uuid
import random
import os
import re
import time
from datetime import datetime

# ComfyUIの接続デフォルト設定（環境変数経由の指定も可能）
COMFYUI_HOST = os.environ.get("COMFYUI_HOST", "localhost")
COMFYUI_PORT = int(os.environ.get("COMFYUI_PORT", 8188))


def clean_prompt_weights(text: str) -> str:
    """
    SDXLスタイルのウェイト表記 (単語:1.5) や (単語) を取り除き、
    DiTモデル（Z-Image-Turbo等）に最適なクリーンなテキストに変換します。
    """
    if not text:
        return ""
    # (word:weight) -> word
    text = re.sub(r'\(([^)]+):[0-9.]+\)', r'\1', text)
    # (word) -> word
    text = re.sub(r'\(([^)]+)\)', r'\1', text)
    return text


def connect_websocket(client_id: str, host: str = COMFYUI_HOST, port: int = COMFYUI_PORT) -> websocket.WebSocket:
    """ComfyUIサーバーのWebSocketに接続し、接続オブジェクトを返します。"""
    ws = websocket.WebSocket()
    ws.connect(f"ws://{host}:{port}/ws?clientId={client_id}")
    return ws


def queue_prompt(prompt: dict, client_id: str, prompt_id: str, host: str = COMFYUI_HOST, port: int = COMFYUI_PORT) -> str:
    """ワークフローJSONをComfyUIのAPIに送信します。"""
    url = f"http://{host}:{port}/prompt"
    payload = json.dumps({
        "prompt": prompt,
        "client_id": client_id,
        "prompt_id": prompt_id,
    })
    data = payload.encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        urllib.request.urlopen(req).read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        print(f"ComfyUI APIエラー ({e.code}): {body}")
        raise
    return prompt_id


def get_history(prompt_id: str, host: str = COMFYUI_HOST, port: int = COMFYUI_PORT) -> dict:
    """指定したprompt_idの完了履歴を取得します。"""
    url = f"http://{host}:{port}/history/{prompt_id}"
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())


def get_image(image_info: dict, host: str = COMFYUI_HOST, port: int = COMFYUI_PORT) -> bytes:
    """ComfyUIサーバーから生成された画像のバイナリデータをダウンロードします。"""
    url = f"http://{host}:{port}/view"
    params = urllib.parse.urlencode({
        "filename": image_info["filename"],
        "subfolder": image_info["subfolder"],
        "type": image_info["type"],
    })
    with urllib.request.urlopen(f"{url}?{params}") as response:
        return response.read()


def get_images(ws: websocket.WebSocket, prompt: dict, client_id: str, host: str = COMFYUI_HOST, port: int = COMFYUI_PORT) -> list:
    """WebSocketを監視し、ワークフロー完了を検知したあと、全画像をダウンロードして返します。"""
    prompt_id = str(uuid.uuid4())
    queue_prompt(prompt, client_id, prompt_id, host, port)
    output_images = []

    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message["type"] == "executing":
                data = message["data"]
                if data["node"] is None and data["prompt_id"] == prompt_id:
                    break  # 実行完了
        else:
            continue  # プレビュー画像等のバイナリデータはスキップ

    history = get_history(prompt_id, host, port)
    outputs = history[prompt_id].get("outputs", {})

    for node_id, output_data in outputs.items():
        images = output_data.get("images", [])
        for image_info in images:
            image_data = get_image(image_info, host, port)
            output_images.append(image_data)

    return output_images


def save_image(image_data: bytes, filename: str, output_dir: str = "output"):
    """画像バイナリをファイルとしてローカルディスクに保存します。"""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, "wb") as f:
        f.write(image_data)
    print(f"Saved: {path}")
    print("-" * 50)
    print()


def get_aspect_dimensions(aspect: str, is_sdxl: bool = True):
    """
    アスペクト比（square, portrait, landscape）に応じて、
    ベース画像サイズと最終アップスケール画像サイズを計算して返します。
    """
    if aspect == "portrait":
        # 縦長：ベースはSDXL最適（4:7）、最終出力はYouTube Shortsジャスト（9:16）
        img_width, img_height = 768, 1344
        target_width, target_height = 1080, 1920
    elif aspect == "landscape":
        # 横長：最終出力はYouTubeフルHDジャスト（16:9）
        img_width, img_height = 1344, 768
        target_width, target_height = 1920, 1080
    else:  # square
        # 正方形
        if is_sdxl:
            img_width, img_height = 1024, 1024
            target_width, target_height = 1536, 1536
        else:
            img_width, img_height = 1024, 1024
            target_width, target_height = 1024, 1024

    return img_width, img_height, target_width, target_height


def load_workflow(workflow_name: str) -> dict:
    """workflows/ フォルダから指定されたワークフローJSONを読み込みます。"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    workflow_path = os.path.join(base_dir, "workflows", workflow_name)
    with open(workflow_path, "r", encoding="utf-8") as f:
        return json.load(f)
