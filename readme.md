# API de Transcripción de Audio

Una API REST construida con FastAPI para transcribir archivos de audio usando el modelo Whisper de OpenAI.

## Características

- Transcripción de archivos de audio subidos directamente
- Transcripción de archivos de audio desde URLs
- Soporte para múltiples formatos de audio (MP3, WAV, M4A)
- Interfaz REST API con documentación automática

## Requisitos

- Docker y Docker Compose

## Inicio Rápido

1. Clonar el repositorio:
```bash
git clone https://github.com/TU_USUARIO/transcription-api.git
cd transcription-api
```

2. Iniciar con Docker Compose:
```bash
docker-compose up -d
```

3. La API estará disponible en: http://localhost:8000

## Uso

### Documentación de la API
Visita http://localhost:8000/docs para ver la documentación interactiva de la API.

### Transcribir archivo de audio
```bash
curl -X POST http://localhost:8000/transcribe/ \
  --data-binary @tuarchivo.mp3
```

### Transcribir desde URL
```bash
curl -X POST http://localhost:8000/transcribe/url/ \
  -H "Content-Type: application/json" \
  -d '{"url":"http://ejemplo.com/audio.mp3"}'
```

## Configuración

Puedes configurar el tamaño del modelo Whisper en el `docker-compose.yml`:
- `base` (default): Buen balance entre precisión y velocidad
- `small`: Más rápido, menos preciso
- `medium`: Más preciso, más lento
- `large`: La mayor precisión, pero requiere más recursos


## Licencia
Este proyecto está licenciado bajo los términos de la licencia Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0).  
Para más detalles, consulta el archivo LICENSE.md o visita [https://creativecommons.org/licenses/by-nc-sa/4.0/](https://creativecommons.org/licenses/by-nc-sa/4.0/).


## Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request