from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import whisper
import tempfile
import os
from typing import List
import requests
from pydantic import BaseModel, HttpUrl

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the Whisper model
model = whisper.load_model("base")

class AudioURL(BaseModel):
    url: HttpUrl

@app.post("/transcribe/")
async def transcribe_audio(request: Request):
    temp_file = None
    try:
        # Leer el contenido binario directamente
        content = await request.body()
        
        # Validar que el archivo no esté vacío
        if len(content) == 0:
            raise HTTPException(status_code=400, detail={
                "error": "El archivo está vacío",
                "tip": "Asegúrate de que el archivo de audio contenga datos"
            })
            
        # Crear archivo temporal con extensión .mp3
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.write(content)
        temp_file.close()
        
        try:
            # Transcribe the audio file
            result = model.transcribe(temp_file.name)
            
            return {
                "success": True,
                "text": result["text"],
                "language": result.get("language", "unknown"),
                "file_size": len(content)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail={
                "error": "Error al transcribir el audio",
                "detail": str(e),
                "tip": "Asegúrate de que el archivo de audio no esté corrupto y sea válido"
            })
            
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "Error al procesar el archivo",
            "detail": str(e),
            "tip": "Verifica que el archivo sea válido y pueda ser leído correctamente"
        })
    finally:
        # Clean up: close the file if it's still open
        if temp_file is not None:
            try:
                os.unlink(temp_file.name)
            except Exception:
                pass  # Ignore errors during cleanup

@app.post("/transcribe/url")
async def transcribe_from_url(audio: AudioURL):
    temp_file = None
    try:
        # Descargar el archivo de audio
        response = requests.get(str(audio.url), stream=True)
        response.raise_for_status()  # Verificar si la descarga fue exitosa
        
        # Crear archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        
        # Guardar el contenido descargado
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
        
        temp_file.close()
        
        try:
            # Transcribir el archivo
            result = model.transcribe(temp_file.name)
            
            return {
                "success": True,
                "text": result["text"],
                "language": result.get("language", "unknown"),
                "source_url": str(audio.url)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail={
                "error": "Error al transcribir el audio",
                "detail": str(e),
                "tip": "Asegúrate de que la URL corresponda a un archivo de audio válido"
            })
            
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail={
            "error": "Error al descargar el archivo",
            "detail": str(e),
            "tip": "Verifica que la URL sea accesible y corresponda a un archivo de audio"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "Error al procesar el archivo",
            "detail": str(e),
            "tip": "Verifica que la URL sea válida y corresponda a un archivo de audio"
        })
    finally:
        # Limpieza del archivo temporal
        if temp_file is not None:
            try:
                os.unlink(temp_file.name)
            except Exception:
                pass

@app.get("/")
async def root():
    return {
        "message": "API de Transcripción de Audio",
        "endpoints": {
            "/transcribe": "POST - Transcribe un archivo de audio enviado directamente",
            "/transcribe/url": "POST - Transcribe un archivo de audio desde una URL",
            "/": "GET - Esta información"
        },
        "instrucciones": {
            "archivo_directo": "Envía el archivo de audio directamente como binary data en el body del request",
            "desde_url": "Envía un JSON con el formato: {'url': 'http://ejemplo.com/audio.mp3'}"
        }
    }