// Renderiza un vídeo del BOE a partir de las props emitidas por el pipeline.
//
//   node render.mjs <props.json> <salida.mp4>
//
// Si las props incluyen `audioFile`, se espera el mp3 junto al props.json y se
// copia a public/ para que staticFile() lo encuentre.

import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { cpSync, mkdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

async function main() {
  const [propsPath, outPath] = process.argv.slice(2);
  if (!propsPath || !outPath) {
    console.error("Uso: node render.mjs <props.json> <salida.mp4>");
    process.exit(1);
  }

  const props = JSON.parse(readFileSync(propsPath, "utf-8"));

  // Copia el audio al public dir para staticFile().
  if (props.audioFile) {
    const publicDir = join(__dirname, "public");
    mkdirSync(publicDir, { recursive: true });
    cpSync(join(dirname(propsPath), props.audioFile), join(publicDir, props.audioFile));
  }

  const serveUrl = await bundle({ entryPoint: resolve(__dirname, "src/index.ts") });
  const composition = await selectComposition({
    serveUrl,
    id: "BoeShort",
    inputProps: props,
  });

  await renderMedia({
    composition,
    serveUrl,
    codec: "h264",
    outputLocation: outPath,
    inputProps: props,
  });

  console.log(`✅ Vídeo renderizado en ${outPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
