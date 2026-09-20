import asyncio
import uuid
from pathlib import Path

import edge_tts
from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Folder jaha temporary MP3 files save hongi
OUTPUT_DIR = Path(__file__).parent / "generated"
OUTPUT_DIR.mkdir(exist_ok=True)

# Available voices - yaha aur bhi add kar sakte ho
VOICES = {
    "Hindi Male": "hi-IN-MadhurNeural",
    "Hindi Female": "hi-IN-SwaraNeural",
    "English Male (US)": "en-US-GuyNeural",
    "English Female (US)": "en-US-JennyNeural",
    "English Male (UK)": "en-GB-RyanNeural",
    "English Female (UK)": "en-GB-SoniaNeural",
}


@app.get("/", response_class=HTMLResponse)
async def home():
    html_path = Path(__file__).parent / "index.html"
    return html_path.read_text(encoding="utf-8")


@app.get("/voices")
async def get_voices():
    return {"voices": list(VOICES.keys())}


@app.get("/history")
async def get_history():
    files = sorted(OUTPUT_DIR.glob("*.mp3"), key=lambda f: f.stat().st_mtime, reverse=True)
    return {"files": [f.name for f in files[:20]]}


@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = OUTPUT_DIR / filename
    return FileResponse(path=file_path, media_type="audio/mpeg", filename=filename)


@app.post("/generate")
async def generate(
    text: str = Form(...),
    voice: str = Form(...),
    filename: str = Form("output"),
    speed: str = Form("+0%"),
):
    voice_id = VOICES.get(voice, "hi-IN-MadhurNeural")

    # Safe filename banao
    safe_name = "".join(c for c in filename if c.isalnum() or c in ("-", "_")) or "output"
    unique_name = f"{safe_name}_{uuid.uuid4().hex[:6]}.mp3"
    output_path = OUTPUT_DIR / unique_name

    tts = edge_tts.Communicate(text, voice_id, rate=speed)
    await tts.save(str(output_path))

    return FileResponse(
        path=output_path,
        media_type="audio/mpeg",
        filename=f"{safe_name}.mp3",
    )


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)