#!/usr/bin/env node
// Diagnóstico del entorno: npm run doctor
// Imprime una tabla OK/FALLA (y AVISO para lo que no impide trabajar) con la solución sugerida.
// Sale con código 1 si hay alguna FALLA.

import { spawnSync, execFileSync } from "node:child_process";
import { existsSync, readFileSync, statSync, readdirSync } from "node:fs";
import { createConnection } from "node:net";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), "..");
const resultados = [];

const anotar = (nombre, estado, detalle, solucion = "") =>
  resultados.push({ nombre, estado, detalle, solucion: estado === "OK" ? "" : solucion });

// Ejecuta un comando a través de la shell (necesario en Windows para npm/uvx .cmd).
function ejecutar(comando) {
  const r = spawnSync(comando, { shell: true, encoding: "utf8", timeout: 30000, cwd: RAIZ });
  if (r.error || r.status !== 0) return null;
  return `${r.stdout || ""}${r.stderr || ""}`.trim();
}

const primeraLinea = (s) => (s || "").split(/\r?\n/)[0].trim();
const leerJson = (ruta) => JSON.parse(readFileSync(ruta, "utf8").replace(/^﻿/, ""));

function versionMinima(actual, minima) {
  const a = actual.split(".").map(Number);
  const m = minima.split(".").map(Number);
  for (let i = 0; i < m.length; i++) {
    if ((a[i] || 0) > m[i]) return true;
    if ((a[i] || 0) < m[i]) return false;
  }
  return true;
}

// --- Node y npm -----------------------------------------------------------
{
  const v = process.versions.node;
  const ok = versionMinima(v, "20.19.0");
  anotar("Node.js", ok ? "OK" : "FALLA", `v${v}`, "Instala Node LTS >= 20.19 (fnm install --lts)");
  const npm = ejecutar("npm --version");
  anotar("npm", npm ? "OK" : "FALLA", npm ? primeraLinea(npm) : "no responde", "Reinstala Node.js (npm viene incluido)");
}

// --- FFmpeg / ffprobe -----------------------------------------------------
for (const herramienta of ["ffmpeg", "ffprobe"]) {
  const s = ejecutar(`${herramienta} -version`);
  const m = s && s.match(/version (\S+)/);
  anotar(herramienta, s ? "OK" : "FALLA", m ? m[1] : "no responde", "winget install Gyan.FFmpeg y reinicia la terminal");
}

// --- Python y uv ----------------------------------------------------------
{
  const s = ejecutar("python --version") || ejecutar("py --version");
  const m = s && s.match(/Python (\d+\.\d+\.\d+)/);
  const ok = m && versionMinima(m[1], "3.11.0");
  anotar("Python >= 3.11", ok ? "OK" : "FALLA", m ? m[1] : "no responde", "winget install Python.Python.3.12");
  const uv = ejecutar("uv --version");
  anotar("uv", uv ? "OK" : "FALLA", uv ? primeraLinea(uv).replace(/^uv /, "") : "no responde",
    "winget install astral-sh.uv y reinicia la terminal / la app de Claude");
  const uvx = ejecutar("uvx --version");
  anotar("uvx", uvx ? "OK" : "FALLA", uvx ? primeraLinea(uvx).replace(/^uvx /, "") : "no responde",
    "Viene con uv; reinicia la terminal para recargar el PATH");
}

// --- Blender (ruta única en scripts/config.json) --------------------------
let config = null;
{
  const rutaConfig = join(RAIZ, "scripts", "config.json");
  try {
    config = leerJson(rutaConfig);
  } catch (e) {
    anotar("scripts/config.json", "FALLA", "no existe o no es JSON válido", "Restaura scripts/config.json desde git");
  }
  if (config) {
    const exe = config.blender?.exe;
    if (!exe || !existsSync(exe)) {
      anotar("Blender", "FALLA", `no existe: ${exe}`, "Instala Blender o corrige blender.exe en scripts/config.json");
    } else {
      try {
        const s = execFileSync(exe, ["-b", "--factory-startup", "--version"], { encoding: "utf8", timeout: 60000 });
        const m = s.match(/Blender (\d+\.\d+(?:\.\d+)?)(\s+LTS)?/);
        const ver = m ? `${m[1]}${m[2] || ""}` : "?";
        const esperada = config.blender.version_esperada;
        const coincide = !esperada || (m && m[1].startsWith(esperada));
        anotar("Blender", coincide ? "OK" : "FALLA", `${ver} — ${exe}`,
          `Se esperaba ${esperada}; actualiza version_esperada o la ruta en scripts/config.json`);
      } catch {
        anotar("Blender", "FALLA", `no responde: ${exe}`, "Abre Blender una vez a mano o reinstálalo");
      }
    }
  }
}

// --- GPU ------------------------------------------------------------------
{
  const s = ejecutar("nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader");
  anotar("GPU (nvidia-smi)", s ? "OK" : "FALLA", s ? primeraLinea(s) : "no responde",
    "Instala/actualiza el driver de NVIDIA");
}

// --- MCP de Blender -------------------------------------------------------
{
  const ruta = join(RAIZ, ".mcp.json");
  let servidor = null;
  try {
    servidor = leerJson(ruta).mcpServers?.blender;
  } catch {
    /* se informa abajo */
  }
  const args = servidor?.args?.join(" ") || "";
  const okMcp = servidor && /mcp-for-blender/.test(args);
  anotar(".mcp.json (blender)", okMcp ? "OK" : "FALLA",
    okMcp ? `${servidor.command} ${args}` : "falta el servidor 'blender' con mcp-for-blender",
    'Restaura .mcp.json: { "mcpServers": { "blender": { "command": "uvx", "args": ["mcp-for-blender@<versión>"] } } }');

  let habilitado = false;
  try {
    const s = leerJson(join(RAIZ, ".claude", "settings.json"));
    habilitado = s.enableAllProjectMcpServers === true || (s.enabledMcpjsonServers || []).includes("blender");
  } catch {
    /* se informa abajo */
  }
  anotar("MCP habilitado en settings", habilitado ? "OK" : "FALLA",
    habilitado ? "enabledMcpjsonServers incluye blender" : "no habilitado",
    'Añade "blender" a enabledMcpjsonServers en .claude/settings.json');

  const puerto = Number(servidor?.env?.BLENDER_PORT || config?.blender?.mcp_puerto || 9876);
  const escucha = await new Promise((resolve) => {
    const sock = createConnection({ host: "127.0.0.1", port: puerto });
    const fin = (v) => { sock.destroy(); resolve(v); };
    sock.setTimeout(1000, () => fin(false));
    sock.once("connect", () => fin(true));
    sock.once("error", () => fin(false));
  });
  anotar(`Addon Blender (puerto ${puerto})`, escucha ? "OK" : "AVISO",
    escucha ? "Blender escuchando" : "Blender cerrado o addon detenido",
    "Abre Blender > N > pestaña MCP for Blender > Start MCP Server (solo necesario para usar el MCP)");
}

// --- Remotion -------------------------------------------------------------
{
  const pkg = join(RAIZ, "node_modules", "remotion", "package.json");
  const ver = existsSync(pkg) ? leerJson(pkg).version : null;
  anotar("Remotion", ver ? "OK" : "FALLA", ver ? `v${ver}` : "no instalado", "npm install (pide permiso antes)");

  const shell = join(RAIZ, "node_modules", ".remotion", "chrome-headless-shell");
  anotar("Remotion Chrome Headless Shell", existsSync(shell) ? "OK" : "FALLA",
    existsSync(shell) ? "descargado" : "no descargado",
    "npx remotion browser ensure (requiere acceso a remotion.media)");

  const dirSkills = join(RAIZ, ".claude", "skills");
  const skills = existsSync(dirSkills) ? readdirSync(dirSkills).filter((n) => n.startsWith("remotion-")) : [];
  const accesibles = skills.filter((n) => existsSync(join(dirSkills, n, "SKILL.md")));
  anotar("Skills de Remotion", accesibles.length > 0 ? "OK" : "FALLA",
    `${accesibles.length} en .claude/skills`, "npx remotion skills add");
}

// --- Documentación --------------------------------------------------------
{
  const ruta = join(RAIZ, "docs", "AUDITORIA_SISTEMA_VIDEO.md");
  const tam = existsSync(ruta) ? statSync(ruta).size : -1;
  anotar("docs/AUDITORIA_SISTEMA_VIDEO.md", tam > 0 ? "OK" : "FALLA",
    tam < 0 ? "no existe" : `${tam} bytes`, "Copia la versión completa de la auditoría en docs/");
}

// --- Tabla ----------------------------------------------------------------
const cols = [
  ["Comprobación", (r) => r.nombre],
  ["Estado", (r) => r.estado],
  ["Detalle", (r) => r.detalle],
  ["Solución sugerida", (r) => r.solucion],
];
const anchos = cols.map(([t, f]) => Math.max(t.length, ...resultados.map((r) => String(f(r)).length)));
const fila = (vals) => "| " + vals.map((v, i) => String(v).padEnd(anchos[i])).join(" | ") + " |";
const color = { OK: "\x1b[32m", FALLA: "\x1b[31m", AVISO: "\x1b[33m" };
const usarColor = process.stdout.isTTY;

console.log("\nDiagnóstico del estudio de producción\n");
console.log(fila(cols.map(([t]) => t)));
console.log("|" + anchos.map((a) => "-".repeat(a + 2)).join("|") + "|");
for (const r of resultados) {
  let linea = fila(cols.map(([, f]) => f(r)));
  if (usarColor) linea = linea.replace(` ${r.estado.padEnd(anchos[1])} `, ` ${color[r.estado]}${r.estado.padEnd(anchos[1])}\x1b[0m `);
  console.log(linea);
}
const fallas = resultados.filter((r) => r.estado === "FALLA").length;
const avisos = resultados.filter((r) => r.estado === "AVISO").length;
console.log(`\n${resultados.length - fallas - avisos} OK, ${fallas} FALLA, ${avisos} AVISO\n`);
process.exit(fallas > 0 ? 1 : 0);
