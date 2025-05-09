from flask import Flask, render_template, request, send_file, redirect, url_for
from PIL import Image, ImageOps
import os
import io

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
STATIC_FOLDER = 'static'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    image_file = request.files['image']
    mode = request.form['mode']
    width_mm = request.form.get('width', type=float)
    height_mm = request.form.get('height', type=float)
    dpi = request.form.get('dpi', type=int, default=300)

    image = Image.open(image_file.stream).convert('L')  # グレースケール化

    # サイズ調整
    if width_mm or height_mm:
        orig_w, orig_h = image.size
        if width_mm and not height_mm:
            width_px = int(width_mm / 25.4 * dpi)
            height_px = int(orig_h * (width_px / orig_w))
        elif height_mm and not width_mm:
            height_px = int(height_mm / 25.4 * dpi)
            width_px = int(orig_w * (height_px / orig_h))
        else:
            width_px = int(width_mm / 25.4 * dpi)
            height_px = int(height_mm / 25.4 * dpi)
        image = image.resize((width_px, height_px), Image.LANCZOS)

    # 処理モード
    if mode == 'binary':
        image = image.point(lambda x: 255 if x > 128 else 0, '1')
    elif mode == 'halftone':
        image = image.convert('1', dither=Image.FLOYDSTEINBERG)

    # 処理後画像保存（DPIを指定）
    result_path = os.path.join(STATIC_FOLDER, 'output.png')
    image.save(result_path, dpi=(dpi, dpi))  # ← ここでDPIを指定

    # 変換後プレビュー表示ページへ遷移
    return redirect(url_for('result'))

@app.route('/result')
def result():
    return render_template('result.html', result_url=url_for('static', filename='output.png'))

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
