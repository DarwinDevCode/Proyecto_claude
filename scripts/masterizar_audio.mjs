#!/usr/bin/env node
// Masteriza el audio de un MP4 a -14 LUFS integrados con pico verdadero <= -1,5 dBTP,
// medido DESPUÉS de codificar (AAC). El video se copia sin recodificar.
//
// Uso: node scripts/masterizar_audio.mjs "<entrada.mp4>" "<salida.mp4>" [--lufs -14] [--tp -1.5]
//
// Pasos: loudnorm en dos pasadas (medir + aplicar en modo lineal) -> AAC 48 kHz ->
// medición con ebur128 (peak=true). Si el pico verdadero medido supera el límite, baja el
// objetivo de pico 0,5 dB y repite (máximo 3 intentos).

import { spawnSync } from "node:child_process";
import { existsSync, renameSync, rmSync } from "node:fs";

const [, , entrada, salida, ...resto] = process.argv;
const opt = (n, d) => {
  const i = resto.indexOf(n);
  return i >= 0 ? Number(resto[i + 1]) : d;
};
const LUFS = opt("--lufs", -14);
const TP_MAX = opt("--tp", -1.5);
if (!entrada || !salida || !existsSync(entrada)) {
  console.error('Uso: node scripts/masterizar_audio.mjs "<entrada.mp4>" "<salida.mp4>" [--lufs -14] [--tp -1.5]');
  process.exit(2);
}

const ffmpeg = (args) => {
  const r = spawnSync("ffmpeg", ["-hide_banner", "-nostats", ...args], { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  if (r.status !== 0) throw new Error(`ffmpeg falló (${r.status}):\n${r.stderr.slice(-2000)}`);
  return r.stderr;
};

const medirLoudnorm = (archivo, tpObjetivo) => {
  const err = ffmpeg(["-i", archivo, "-vn", "-af", `loudnorm=I=${LUFS}:TP=${tpObjetivo}:LRA=11:print_format=json`, "-f", "null", "-"]);
  const json = err.slice(err.lastIndexOf("{"), err.lastIndexOf("}") + 1);
  return JSON.parse(json);
};

const medirEbur128 = (archivo) => {
  const err = ffmpeg(["-i", archivo, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"]);
  const resumen = err.slice(err.lastIndexOf("Summary:"));
  const I = Number(/I:\s+(-?[\d.]+) LUFS/.exec(resumen)?.[1]);
  const TP = Number(/Peak:\s+(-?[\d.]+) dBFS/.exec(resumen)?.[1]);
  return { I, TP };
};

const tmp = `${salida}.tmp.mp4`;
let tpObjetivo = TP_MAX - 0.5;
let resultado = null;
for (let intento = 1; intento <= 3; intento++) {
  const m = medirLoudnorm(entrada, tpObjetivo);
  const filtro =
    `loudnorm=I=${LUFS}:TP=${tpObjetivo}:LRA=11:` +
    `measured_I=${m.input_i}:measured_TP=${m.input_tp}:measured_LRA=${m.input_lra}:` +
    `measured_thresh=${m.input_thresh}:offset=${m.target_offset}:linear=true:print_format=summary`;
  ffmpeg(["-y", "-i", entrada, "-map", "0:v", "-map", "0:a", "-c:v", "copy", "-af", filtro,
    "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp]);
  const final = medirEbur128(tmp);
  resultado = { intento, tpObjetivo, entrada: { I: Number(m.input_i), TP: Number(m.input_tp) }, final };
  console.log(`intento ${intento}: objetivo TP ${tpObjetivo} dBTP -> medido tras codificar: ${final.I} LUFS, ${final.TP} dBTP`);
  if (final.TP <= TP_MAX && Math.abs(final.I - LUFS) <= 0.5) break;
  tpObjetivo -= 0.5;
}
if (existsSync(salida)) rmSync(salida);
renameSync(tmp, salida);
const ok = resultado.final.TP <= TP_MAX && Math.abs(resultado.final.I - LUFS) <= 0.5;
console.log(JSON.stringify({ ok, objetivo: { LUFS, TP_MAX }, ...resultado }, null, 2));
process.exit(ok ? 0 : 1);
