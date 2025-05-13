from flask import Flask, render_template, request, redirect, url_for
from PIL import Image, ImageChops
import os

app = Flask(__name__)

STATIC_FOLDER = 'static'
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
    rotation = request.form.get('rotation', type=int, default=0)
    dpi = 300  # 固定DPI
    trim = request.form.get('trim') == 'on'

    # グレースケール化
    image = Image.open(image_file.stream).convert('L')

    # 回転（時計回りに変換されるようにマイナスをつける）
    if rotation:
        image = image.rotate(-rotation, expand=True)

    # カラーモードの変更
    if mode == 'binary':
        image = image.point(lambda x: 255 if x > 128 else 0, '1')
    elif mode == 'halftone':
        image = image.convert('1', dither=Image.FLOYDSTEINBERG)
    elif mode == 'grayscale':
        pass  # すでにグレースケールにしてある

    # 余白トリミング（白に近い部分をカット）
    if trim:
        bg = Image.new('L', image.size, 255)
        diff = ImageChops.difference(image, bg)
        diff = Image.eval(diff, lambda x: 0 if x < 15 else 255)
        bbox = diff.getbbox()
        if bbox:
            image = image.crop(bbox)

    # サイズ調整（mm → px に変換してリサイズ）
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

        MAX_SIZE = 10000
        width_px = min(width_px, MAX_SIZE)
        height_px = min(height_px, MAX_SIZE)

        image = image.resize((width_px, height_px), Image.LANCZOS)

    # 保存
    result_path = os.path.join(STATIC_FOLDER, 'output.png')
    image.save(result_path, dpi=(300, 300), optimize=True)

    return redirect(url_for('result'))

@app.route('/result')
def result():
    return render_template('result.html', result_url=url_for('static', filename='output.png'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
