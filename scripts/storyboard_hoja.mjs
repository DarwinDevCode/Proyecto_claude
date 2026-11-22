#!/usr/bin/env node
// Monta la hoja de storyboard: cada fotograma clave (capas escena + agua sobre el fondo)
// con su id, tiempo, narración, etiqueta y nota debajo.
// Uso: node scripts/storyboard_hoja.mjs "<carpeta del proyecto>"
// Lee 03_storyboard/planos.json, 03_storyboard/capas/*.png y 05_audio/voz_borrador.palabras.json.
// Escribe 03_storyboard/storyboard.png y 03_storyboard/storyboard.md.

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";

const proyecto = process.argv[2];
const sb = join(proyecto, "03_storyboard");
const { planos } = JSON.parse(readFileSync(join(sb, "planos.json"), "utf8"));
const palabras = JSON.parse(readFileSync(join(proyecto, "05_audio", "voz_borrador.palabras.json"), "utf8")).palabras;
const finVoz = palabras.at(-1).fin_ms;
const tmp = join(tmpdir(), `storyboard_${Date.now()}`);
mkdirSync(tmp, { recursive: true });

const W = 432, H = 768, PIE = 300, FUENTE = "C\\:/Windows/Fonts/arial.ttf", FUENTE_B = "C\\:/Windows/Fonts/arialbd.ttf";
const mmss = (ms) => `${Math.floor(ms / 60000)}:${String(Math.floor((ms % 60000) / 1000)).padStart(2, "0")}.${Math.floor((ms % 1000) / 100)}`;
const envolver = (t, n) => {
  const out = [];
  let linea = "";
  for (const w of t.split(" ")) {
    if ((linea + " " + w).trim().length > n) { out.push(linea.trim()); linea = w; } else linea += " " + w;
  }
  if (linea.trim()) out.push(linea.trim());
  return out.join("\n");
};
const ff = (args) => {
  const r = spawnSync("ffmpeg", ["-v", "error", "-y", ...args], { encoding: "utf8" });
  if (r.status !== 0) throw new Error(r.stderr);
};

// tiempos de inicio por plano
const inicios = planos.map((p) => {
  let n = 0;
  const w = palabras.find((x) => x.texto.startsWith(p.desde) && ++n === p.n);
  if (!w) throw new Error(`No encuentro "${p.desde}" (${p.n}) para ${p.id}`);
  return w.inicio_ms;
});

const paneles = [];
planos.forEach((p, i) => {
  const ini = i === 0 ? 0 : inicios[i];
  const fin = i + 1 < planos.length ? inicios[i + 1] : finVoz + 1000;
  p.tiempo = `${mmss(ini)}–${mmss(fin)}`;
  const esc = join(sb, "capas", `${p.id}_escena.png`);
  const agua = join(sb, "capas", `${p.id}_agua.png`);
  const fT = join(tmp, `t${i}.txt`), fN = join(tmp, `n${i}.txt`), fE = join(tmp, `e${i}.txt`);
  writeFileSync(fT, `${p.id} · ${p.escena} · ${p.tiempo}`);
  writeFileSync(fN, envolver(`«${p.narracion}»`, 40));
  writeFileSync(fE, envolver([p.etiqueta && `Etiqueta: ${p.etiqueta}`, p.nota].filter(Boolean).join(" — "), 46));
  const esc_f = (s) => s.replace(/\\/g, "/").replace(/:/g, "\\:");
  const entradas = ["-f", "lavfi", "-i", `color=c=0xF3F0EA:s=${W}x${H}`, "-i", esc];
  let filtro = `[1]scale=${W}:${H}[e];[0][e]overlay[b0]`;
  if (existsSync(agua)) { entradas.push("-i", agua); filtro += `;[2]scale=${W}:${H}[w];[b0][w]overlay[b1]`; } else filtro += `;[b0]null[b1]`;
  filtro += `;[b1]pad=${W}:${H + PIE}:0:0:color=white,` +
    `drawtext=fontfile='${FUENTE_B}':textfile='${esc_f(fT)}':expansion=none:x=12:y=${H + 10}:fontsize=22:fontcolor=0x2B3150,` +
    `drawtext=fontfile='${FUENTE}':textfile='${esc_f(fN)}':expansion=none:x=12:y=${H + 44}:fontsize=19:fontcolor=0x222222:line_spacing=4,` +
    `drawtext=fontfile='${FUENTE}':textfile='${esc_f(fE)}':expansion=none:x=12:y=${H + 170}:fontsize=16:fontcolor=0x5B5F73:line_spacing=3`;
  const panel = join(tmp, `p${String(i).padStart(2, "0")}.png`);
  ff([...entradas, "-filter_complex", filtro, "-frames:v", "1", panel]);
  paneles.push(panel);
});
ff(["-i", join(tmp, "p%02d.png"), "-vf", "tile=5x2:padding=8:margin=8:color=white", "-frames:v", "1", join(sb, "storyboard.png")]);

const md = [
  "# 03 · Storyboard (puerta humana 2, D-004)",
  "",
  `Voz de borrador: la última palabra termina en ${(finVoz / 1000).toFixed(2)} s; video de ${((finVoz + 1000) / 1000).toFixed(2)} s.`,
  "Hoja: `storyboard.png`. Fotogramas en `capas/` (fuera de git; se regeneran con `scripts/escena_cable_v3.py -- --storyboard`).",
  "",
  "| Plano | Escena | Tiempo | Narración | Etiqueta | Nota |",
  "|---|---|---|---|---|---|",
  ...planos.map((p) => `| ${p.id} | ${p.escena} | ${p.tiempo} | ${p.narracion} | ${p.etiqueta || "—"} | ${p.nota} |`),
  "",
].join("\n");
writeFileSync(join(sb, "storyboard.md"), md);
rmSync(tmp, { recursive: true, force: true });
console.log(`HOJA_OK ${paneles.length} paneles -> ${join(sb, "storyboard.png")}`);
