import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
// public/ contiene los audios (mp3) que referencia staticFile(audioFile).
Config.setPublicDir("public");
