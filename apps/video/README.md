# AlertaBOE · plantilla de vídeo (Remotion)

Compone los vídeos verticales (1080×1920) para TikTok/Reels/Shorts a partir de
las **props que emite el pipeline** de contenido (`boe/content/video/render.py`).

## Flujo end-to-end

```
Guionista (LLM)  ─►  TikTokScript (hook, points, cta, narration)
        │
        ▼
render.build_props ─►  props.json  (hook/points/cta + cues con tiempos + fps + frames)
render_assets      ─►  <id>.mp3    (narración edge-tts, extra [video])
        │
        ▼
node render.mjs props.json salida.mp4   ─►  vídeo final con subtítulos y voz
```

Los subtítulos salen del propio guion (sin ASR): `build_cues` reparte la
narración en fragmentos con tiempos estimados por ritmo de locución.

## Uso

```bash
cd apps/video
npm install

# Previsualizar en el estudio de Remotion (con las props por defecto):
npm run studio

# Renderizar un vídeo concreto a partir de las props del pipeline:
#   (props.json y el mp3 los deja render_assets en su out_dir)
npm run render -- /ruta/al/<id>.props.json ./out/<id>.mp4
```

Si `props.json` incluye `audioFile`, el script copia ese mp3 a `public/` para
que `staticFile()` lo encuentre y lo sincronice con el vídeo.

## Composición

`src/BoeShort.tsx` renderiza: etiqueta de fuente (`boe_id`), hook con entrada
animada, los puntos apareciendo escalonados, el CTA al final, subtítulos karaoke
por cue y un disclaimer permanente. La duración real y el fps vienen en las props
(`calculateMetadata`), así que el vídeo dura lo que dura la narración.

> Requiere Chromium (lo instala Remotion). El render no se ejecuta en CI por peso;
> `npm run typecheck` valida la plantilla.
