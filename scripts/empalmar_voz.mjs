#!/usr/bin/env node
// Sustituye UNA escena de una voz de borrador por otra grabación, sin regenerar el resto.
// Corta el original en el centro de las pausas que rodean la escena, inserta la nueva
// (con media pausa antes y después) y desplaza los tiempos por palabra posteriores.
//
// Uso: node scripts/empalmar_voz.mjs <original_base> <nueva_base> <salida_base> <ini_ms_escena> <fin_ms_escena>
//   *_base = ruta sin extensión de un par .mp3 + .palabras.json (formato de scripts/tts_borrador.py)
//   ini_ms/fin_ms = inicio de la primera palabra y fin de la última de la escena en el original.

import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";

const [, , orig, nueva, salida, iniS, finS] = process.argv;
const ini = Number(iniS), fin = Number(finS);
const po = JSON.parse(readFileSync(`${orig}.palabras.json`, "utf8"));
const pn = JSON.parse(readFileSync(`${nueva}.palabras.json`, "utf8"));
const antes = po.palabras.filter((w) => w.fin_ms <= ini);
const despues = po.palabras.filter((w) => w.inicio_ms >= fin);
const corteA = (antes.at(-1).fin_ms + ini) / 2;            // centro de la pausa previa
const corteC = (fin + despues[0].inicio_ms) / 2;           // centro de la pausa siguiente
const mediaA = ini - corteA, mediaC = corteC - fin;
const nIni = pn.palabras[0].inicio_ms, nFin = pn.palabras.at(-1).fin_ms;
const relleno = Math.max(0, mediaA - nIni);                // silencio a añadir antes de la nueva
const durB = relleno + nFin + mediaC;                      // duración del bloque nuevo
const s = (ms) => (ms / 1000).toFixed(3);

const filtro =
  `[0:a]atrim=0:${s(corteA)},asetpts=PTS-STARTPTS[a];` +
  `[1:a]atrim=0:${s(nFin + mediaC)},asetpts=PTS-STARTPTS,adelay=${Math.round(relleno)}:all=1,apad=whole_dur=${s(durB)}[b];` +
  `[0:a]atrim=start=${s(corteC)},asetpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=0:a=1[o]`;
const r = spawnSync("ffmpeg", ["-v", "error", "-y", "-i", `${orig}.mp3`, "-i", `${nueva}.mp3`, "-filter_complex", filtro,
  "-map", "[o]", "-ar", "24000", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "64k", `${salida}.mp3`], { encoding: "utf8" });
if (r.status !== 0) { console.error(r.stderr); process.exit(1); }

const desfaseB = corteA + relleno;
const desfaseC = corteA + durB - corteC;
const palabras = [
  ...antes,
  ...pn.palabras.map((w) => ({ ...w, inicio_ms: Math.round(w.inicio_ms + desfaseB), fin_ms: Math.round(w.fin_ms + desfaseB) })),
  ...despues.map((w) => ({ ...w, inicio_ms: Math.round(w.inicio_ms + desfaseC), fin_ms: Math.round(w.fin_ms + desfaseC) })),
];
writeFileSync(`${salida}.palabras.json`, JSON.stringify({ ...po, texto: null, empalme: { escena_ini_ms: ini, escena_fin_ms: fin, desfase_posterior_ms: Math.round(desfaseC) }, palabras }, null, 2));
console.log(`EMPALME_OK corteA=${s(corteA)}s corteC=${s(corteC)}s desfase posterior=${s(desfaseC)}s ultima=${s(palabras.at(-1).fin_ms)}s`);
