# Este archivo está bajo la licencia Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International.
# Para más información, visita: https://creativecommons.org/licenses/by-nc-sa/4.0/
# Autor: [Ronald Schneider Hamann](https://github.com/skarious)
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import whisper
import tempfile
import os
from typing import List, Dict, Any
import requests
from pydantic import BaseModel, HttpUrl
from fastapi.responses import JSONResponse

class AudioURL(BaseModel):
    url: HttpUrl

    class Config:
        schema_extra = {
            "example": {
                "url": "https://ejemplo.com/audio.mp3"
            }
        }

class TranscriptionResponse(BaseModel):
    success: bool
    text: str
    language: str
    file_size: int = None
    source_url: str = None

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "text": "Este es el texto transcrito del audio.",
                "language": "es",
                "file_size": 1024576,
                "source_url": None
            }
        }

app = FastAPI(
    title="API de Transcripción de Audio",
    description="""
    Esta API permite transcribir archivos de audio a texto utilizando el modelo Whisper de OpenAI.
    
    ## Características
    
    * Transcripción de archivos de audio subidos directamente
    * Transcripción de archivos de audio desde URLs
    * Soporte para múltiples formatos (MP3, WAV, M4A)
    * Detección automática del idioma
    
    ## Formatos Soportados
    
    * MP3 (.mp3)
    * WAV (.wav)
    * M4A (.m4a)
    * Y otros formatos de audio compatibles con ffmpeg
    """,
    version="1.0.0",
    contact={
        "name": "Tu Nombre",
        "url": "https://github.com/TU_USUARIO/transcription-api",
    },
)

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

@app.post("/transcribe/",
    response_model=TranscriptionResponse,
    summary="Transcribir archivo de audio",
    description="""
    Transcribe un archivo de audio a texto.
    
    ## Cómo usar
    
    1. Selecciona un archivo de audio (MP3, WAV, M4A)
    2. Envía el archivo como datos binarios en el cuerpo de la solicitud
    3. Recibirás la transcripción en formato texto
    
    ## Ejemplo con curl
    ```bash
    curl -X POST http://localhost:8000/transcribe/ \\
      -F "file=@tuarchivo.mp3"
    ```
    
    ## Ejemplo con Python
    ```python
    import requests
    
    with open('audio.mp3', 'rb') as f:
        files = {'file': ('audio.mp3', f, 'audio/mpeg')}
        response = requests.post('http://localhost:8000/transcribe/', 
                               files=files)
        print(response.json())
    ```
    """)
async def transcribe_audio(file: UploadFile = File(..., description="Archivo de audio a transcribir (MP3, WAV, M4A)")):
    temp_file = None
    try:
        # Leer el contenido del archivo
        content = await file.read()
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail={
                "error": "El archivo está vacío",
                "tip": "Asegúrate de que el archivo de audio contenga datos"
            })
            
        # Crear archivo temporal con la extensión original
        suffix = os.path.splitext(file.filename)[1] or '.mp3'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(content)
        temp_file.close()
        
        try:
            result = model.transcribe(temp_file.name)
            
            return TranscriptionResponse(
                success=True,
                text=result["text"],
                language=result.get("language", "unknown"),
                file_size=len(content)
            )
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
        if temp_file is not None:
            try:
                os.unlink(temp_file.name)
            except Exception:
                pass

@app.post("/transcribe/url",
    response_model=TranscriptionResponse,
    summary="Transcribir audio desde URL",
    description="""
    Transcribe un archivo de audio desde una URL.
    
    ## Cómo usar
    
    1. Proporciona la URL de un archivo de audio en formato JSON
    2. La API descargará y transcribirá el audio
    3. Recibirás la transcripción en formato texto
    
    ## Ejemplo con curl
    ```bash
    curl -X POST http://localhost:8000/transcribe/url/ \\
      -H "Content-Type: application/json" \\
      -d '{"url":"http://ejemplo.com/audio.mp3"}'
    ```
    
    ## Ejemplo con Python
    ```python
    import requests
    
    response = requests.post('http://localhost:8000/transcribe/url/',
                           json={'url': 'http://ejemplo.com/audio.mp3'})
    print(response.json())
    ```
    """)
async def transcribe_from_url(audio: AudioURL):
    temp_file = None
    try:
        response = requests.get(str(audio.url), stream=True)
        response.raise_for_status()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
        
        temp_file.close()
        
        try:
            result = model.transcribe(temp_file.name)
            
            return TranscriptionResponse(
                success=True,
                text=result["text"],
                language=result.get("language", "unknown"),
                source_url=str(audio.url)
            )
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
        if temp_file is not None:
            try:
                os.unlink(temp_file.name)
            except Exception:
                pass

@app.get("/",
    summary="Información de la API",
    description="Retorna información sobre los endpoints disponibles y cómo usar la API.")
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