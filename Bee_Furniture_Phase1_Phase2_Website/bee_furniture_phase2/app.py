import os, io, base64, uuid, ipaddress, socket
from urllib.parse import urlparse
from pathlib import Path
import requests
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / '.env')
app = Flask(__name__, static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 12 * 1024 * 1024
GENERATED = BASE / 'static' / 'generated'
GENERATED.mkdir(parents=True, exist_ok=True)

@app.get('/')
def home():
    return send_from_directory(BASE, 'index.html')

@app.get('/health')
def health():
    return jsonify({'ok': True, 'ai_configured': bool(os.getenv('OPENAI_API_KEY'))})

def safe_remote_image(url):
    parsed = urlparse(url or '')
    if parsed.scheme != 'https' or not parsed.hostname:
        raise ValueError('The product image must be a public HTTPS image URL.')
    host = parsed.hostname.lower()
    if host in {'localhost', '127.0.0.1'} or host.endswith('.local'):
        raise ValueError('Private image hosts are not allowed.')
    try:
        for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM):
            ip = ipaddress.ip_address(item[4][0])
            if not ip.is_global:
                raise ValueError('Private image hosts are not allowed.')
    except socket.gaierror as exc:
        raise ValueError('Could not resolve the product image host.') from exc
    r = requests.get(url, timeout=25, stream=True, headers={'User-Agent':'BeeFurniturePreview/1.0'})
    r.raise_for_status()
    content_type = r.headers.get('Content-Type','').split(';')[0].lower()
    if content_type not in {'image/jpeg','image/png','image/webp'}:
        raise ValueError('The product reference URL did not return a supported image.')
    data = r.content
    if len(data) > 12 * 1024 * 1024:
        raise ValueError('The product image is too large.')
    ext = {'image/jpeg':'jpg','image/png':'png','image/webp':'webp'}[content_type]
    return data, ext

@app.post('/api/visualise')
def visualise():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return jsonify({'error':'AI service is not configured yet. Add OPENAI_API_KEY to the .env file and restart the server.'}), 503
    room = request.files.get('room_image')
    if not room:
        return jsonify({'error':'Please upload a room photo.'}), 400
    if room.mimetype not in {'image/jpeg','image/png','image/webp'}:
        return jsonify({'error':'Room photo must be JPG, PNG or WebP.'}), 400
    room_bytes = room.read()
    if not room_bytes or len(room_bytes) > 12*1024*1024:
        return jsonify({'error':'Room photo is empty or exceeds 12 MB.'}), 400
    product_name = (request.form.get('product_name') or 'selected sofa')[:120]
    colour = (request.form.get('selected_colour') or 'selected colour')[:60]
    try:
        sofa_bytes, sofa_ext = safe_remote_image(request.form.get('sofa_image_url'))
        room_ext = {'image/jpeg':'jpg','image/png':'png','image/webp':'webp'}[room.mimetype]
        prompt = (
            'Create a photorealistic interior-design preview by editing the supplied room photograph. '
            f'Place the exact furniture item shown in the second reference image into a plausible open floor area: {product_name}. '
            f'The requested upholstery colour is {colour}. Preserve the sofa silhouette, arm shape, seat count, legs, cushions and overall construction from the product reference as closely as possible. '
            'Keep the original room architecture, windows, doors, flooring, walls and camera viewpoint. Match perspective, scale impression, ambient lighting and contact shadows. '
            'Do not add text, labels, extra furniture, people or decorations. This is an illustrative visual preview, not a dimensionally guaranteed AR placement.'
        )
        files = [
            ('image[]', ('room.'+room_ext, room_bytes, room.mimetype)),
            ('image[]', ('sofa.'+sofa_ext, sofa_bytes, 'image/'+('jpeg' if sofa_ext=='jpg' else sofa_ext)))
        ]
        response = requests.post(
            'https://api.openai.com/v1/images/edits',
            headers={'Authorization': f'Bearer {api_key}'},
            data={'model': os.getenv('OPENAI_IMAGE_MODEL','gpt-image-1'), 'prompt': prompt, 'size':'1536x1024'},
            files=files,
            timeout=180
        )
        if not response.ok:
            try: detail = response.json().get('error',{}).get('message', response.text[:500])
            except Exception: detail = response.text[:500]
            return jsonify({'error':f'AI image service error: {detail}'}), response.status_code
        payload = response.json()
        b64 = payload.get('data',[{}])[0].get('b64_json')
        if not b64:
            return jsonify({'error':'AI service returned no image. Please try again.'}), 502
        image_bytes = base64.b64decode(b64)
        filename = f'{uuid.uuid4().hex}.png'
        (GENERATED / filename).write_bytes(image_bytes)
        return jsonify({'image_url':f'/static/generated/{filename}'})
    except ValueError as exc:
        return jsonify({'error':str(exc)}), 400
    except requests.RequestException as exc:
        return jsonify({'error':f'Could not reach the image service: {exc}'}), 502
    except Exception as exc:
        app.logger.exception('Visualisation failed')
        return jsonify({'error':f'Visualisation failed: {exc}'}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT','5000')), debug=False)
