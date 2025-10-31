const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const clearBtn = document.getElementById('clearBtn');
const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');
const output = document.getElementById('output');
const statusEl = document.getElementById('status');

let recognition;
let listening = false;

function supportsSpeechRecognition(){
  return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
}

if(!supportsSpeechRecognition()){
  statusEl.textContent = 'Status: Your browser does not support Web Speech API. Use Chrome or Edge.';
  startBtn.disabled = true;
  stopBtn.disabled = true;
} else {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onstart = () => {
    listening = true;statusEl.textContent = 'Status: Listening...';
    startBtn.classList.add('listening');
  };

  recognition.onend = () => {
    listening = false;statusEl.textContent = 'Status: Idle';
    startBtn.classList.remove('listening');
  };

  recognition.onerror = (e) => {
    console.error('Speech recognition error', e);
    statusEl.textContent = 'Status: Error — ' + (e.error || 'unknown');
  };

  let finalTranscript = '';

  recognition.onresult = (event) => {
    let interim = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += transcript + '\n';
      } else {
        interim += transcript;
      }
    }
    output.value = finalTranscript + interim;
    downloadBtn.href = makeDownloadHref(output.value);
  };
}

function makeDownloadHref(text){
  const blob = new Blob([text], {type: 'text/plain'});
  return URL.createObjectURL(blob);
}

startBtn.addEventListener('click', () => {
  if(!recognition) return;
  if(listening){
    recognition.stop();
  } else {
    try{ recognition.start(); } catch(e){ console.warn(e); }
  }
});

stopBtn.addEventListener('click', () => {
  if(recognition && listening) recognition.stop();
});

clearBtn.addEventListener('click', () => {
  output.value = '';
  downloadBtn.href = makeDownloadHref('');
});

copyBtn.addEventListener('click', async () => {
  try{
    await navigator.clipboard.writeText(output.value);
    statusEl.textContent = 'Status: Copied text to clipboard';
    setTimeout(()=> statusEl.textContent = 'Status: Idle', 1200);
  } catch(e){
    console.error(e);
    statusEl.textContent = 'Status: Copy failed';
  }
});

downloadBtn.href = makeDownloadHref('');