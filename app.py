import os, subprocess, uuid, json
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
from vosk import Model, KaldiRecognizer
import wave

UPLOAD_FOLDER = "uploads"
MODEL_DIR = "model"
ALLOWED_EXT = {"wav", "mp3", "m4a", "ogg", "webm"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app = Flask(__name__, static_folder='../frontend', static_url_path='/')
CORS(app)

if not os.path.isdir(MODEL_DIR):
    print('Vosk model not found in', MODEL_DIR)
    # We'll still start; Dockerfile should place model in /app/model on Render
model = Model(MODEL_DIR) if os.path.isdir(MODEL_DIR) else None

def allowed_file(filename):
    return "." in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

def convert_to_wav(input_path, out_path):
    cmd = ["ffmpeg","-y","-i",input_path,"-ar","16000","-ac","1","-f","wav",out_path]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError('ffmpeg conversion failed: ' + proc.stderr.decode('utf-8', errors='ignore'))

def transcribe_file(wav_path):
    wf = wave.open(wav_path, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
        raise RuntimeError('WAV must be PCM16 mono 16kHz')
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(False)
    results = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            part = json.loads(rec.Result())
            results.append(part.get('text',''))
    final = json.loads(rec.FinalResult())
    results.append(final.get('text',''))
    return ' '.join([r for r in results if r]).strip()

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({'error':'no file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error':'no selected file'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error':'file type not allowed'}), 400
    filename = secure_filename(file.filename)
    uid = str(uuid.uuid4())[:8]
    in_path = os.path.join(UPLOAD_FOLDER, f"{uid}_{filename}")
    file.save(in_path)
    wav_path = os.path.join(UPLOAD_FOLDER, f"{uid}_converted.wav")
    try:
        convert_to_wav(in_path, wav_path)
        text = transcribe_file(wav_path)
        return jsonify({'text': text})
    except Exception as e:
        print('error', e)
        return jsonify({'error': str(e)}), 500
    finally:
        for p in [in_path, wav_path]:
            try:
                if os.path.exists(p): os.remove(p)
            except: pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)