import os
import cv2
import torch.version
from yomitoku import DocumentAnalyzer
from yomitoku.data.functions import load_image
from yomitoku import TextRecognizer
from yomitoku import OCR
import torch
import glob

configs = {
        "text_detector": {
                "device": "cuda",
            },
            "text_recognizer": {
                "device": "cuda",
            },
}

IMG_DIR = "D:/notoa/Pictures/kindle_ss/jinkouchinou_"
if __name__ == "__main__":
    ocr = OCR(configs=configs, visualize=False, device="cuda")
    # 画像ファイルの拡張子を必要に応じて追加
    img_files = glob.glob(os.path.join(IMG_DIR, "*.png")) + \
                glob.glob(os.path.join(IMG_DIR, "*.jpg")) + \
                glob.glob(os.path.join(IMG_DIR, "*.jpeg"))
    for img_path in img_files:
        filename = os.path.splitext(os.path.basename(img_path))[0]
        json_name = f"{filename}_output.json"
        json_path = os.path.join(IMG_DIR, json_name)
        if os.path.exists(json_path):
            print(f"Skipping {img_path}, already processed.")
            continue
        img = cv2.imread(img_path)
        results, ocr_vis = ocr(img)
        # 画像ごとにファイル名を変えて保存
        results.to_json(json_path)
