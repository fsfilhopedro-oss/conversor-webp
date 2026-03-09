from flask import Flask, render_template, request, send_file
from PIL import Image
import io
import os
import zipfile

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def compress_image(image, target_size_kb=30, max_fallback_kb=60):
    img_io = io.BytesIO()
    quality = 90
    working_image = image.copy()
    while True:
        img_io = io.BytesIO()
        working_image.save(img_io, 'WEBP', quality=quality)
        if img_io.tell() / 1024 <= target_size_kb: break
        if img_io.tell() / 1024 <= max_fallback_kb and quality <= 75: break
        if quality > 75: quality -= 5
        else:
            new_width = int(working_image.width * 0.9)
            new_height = int(working_image.height * 0.9)
            working_image = working_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            if new_width < 200: break
    img_io.seek(0)
    return img_io

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return "Nenhum arquivo enviado"

        memory_zip = io.BytesIO()
        with zipfile.ZipFile(memory_zip, 'w') as zf:
            for file in files:
                if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
                    img = Image.open(file.stream).convert("RGB")
                    filename = os.path.splitext(file.filename)[0] + ".webp"
                    processed_img = compress_image(img)
                    zf.writestr(filename, processed_img.getvalue())
        
        memory_zip.seek(0)
        return send_file(memory_zip, mimetype='application/zip', as_attachment=True, download_name='imagens_convertidas.zip')
    return render_template('index.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)