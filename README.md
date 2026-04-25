# Infinitum Tattoo Studio — Backend Flask

Proyecto armado manteniendo la versión visual original, pero sirviendo assets desde `/static` con cache y compresión.

## Ejecutar local

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Abrir: http://127.0.0.1:5000

## Qué se optimizó

- Se mantiene el HTML, CSS y JS original.
- Las imágenes base64 del HTML fueron extraídas a archivos dentro de `static/img`.
- Se agregaron `loading="lazy"` y `decoding="async"` en imágenes extraídas.
- Se configuró Flask con compresión Gzip/Brotli usando `Flask-Compress`.
- Se agregaron headers de cache para CSS, JS e imágenes.
- El JavaScript principal se carga con `defer`.
- Se agregaron `preconnect` para Google Fonts y `preload` para el logo principal.

## Deploy

Funciona en Render, Railway, Fly.io, Heroku o cualquier servidor compatible con Python.
Comando de producción:

```bash
gunicorn app:app
```


## Performance Mode aplicado
Se mantiene el diseño/base original, pero la carga inicial desactiva loader, cursor personalizado, partículas y ruido animado. Spotify ahora carga recién cuando se abre el reproductor. Esto apunta a mejorar Lighthouse sin cambiar la identidad visual principal.
