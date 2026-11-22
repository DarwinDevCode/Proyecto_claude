import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import datosVoz from "../../proyectos/2026-11-21_prueba-3d/05_audio/voz_borrador.palabras.json";

// Esta composición se renderiza con --public-dir "proyectos/2026-11-21_prueba-3d":
// staticFile() apunta a la carpeta del proyecto (04_blender/, 05_audio/).

export const PRUEBA3D_FRAMES = 450;
const INICIO_VOZ = 90; // 3,0 s: "cables como este" coincide con el plano del cable
const ETIQUETA = { desde: 205, hasta: 284 }; // pausa del acercamiento al cable (Blender 207-282)
// Centro del cable en ese plano, medido sobre el fotograma 250 renderizado
// (el borde superior coincide con la proyección calculada en Blender: ~650, 830).
const PUNTO_CABLE = { x: 550, y: 925 };

const C = {
  texto: "#FFFFFF",
  contorno: "#2B3150",
  capsula: "#2B3150",
  acento: "#5ED3B5",
};
const FUENTE = "'Segoe UI Black', 'Arial Black', 'Segoe UI', sans-serif";

type Palabra = { texto: string; inicio_ms: number; fin_ms: number };

// edge-tts agrupa "del 99" y deja "%" suelto: separa grupos y une "%" al número.
const palabrasSubtitulo = (lista: Palabra[]): Palabra[] => {
  const sep: Palabra[] = [];
  for (const p of lista) {
    const partes = p.texto.split(" ");
    const paso = (p.fin_ms - p.inicio_ms) / partes.length;
    partes.forEach((t, i) =>
      sep.push({
        texto: t,
        inicio_ms: Math.round(p.inicio_ms + i * paso),
        fin_ms: Math.round(p.inicio_ms + (i + 1) * paso),
      }),
    );
  }
  const unidas: Palabra[] = [];
  for (const p of sep) {
    const prev = unidas[unidas.length - 1];
    if (prev && /^[%.,;:!?]+$/.test(p.texto)) {
      prev.texto = `${prev.texto} ${p.texto}`;
      prev.fin_ms = p.fin_ms;
    } else {
      unidas.push({ ...p });
    }
  }
  return unidas;
};

const PALABRAS = palabrasSubtitulo(datosVoz.palabras as Palabra[]);

const Fondo3D: React.FC = () => {
  const frame = useCurrentFrame();
  const n = String(Math.min(frame + 1, PRUEBA3D_FRAMES)).padStart(4, "0");
  return <Img src={staticFile(`04_blender/frames/f_${n}.png`)} style={{ width: "100%", height: "100%" }} />;
};

const Subtitulos: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ms = ((frame - INICIO_VOZ) / fps) * 1000;
  const i = PALABRAS.findIndex((p, k) => {
    const siguiente = PALABRAS[k + 1];
    const fin = siguiente && siguiente.inicio_ms - p.fin_ms < 400 ? siguiente.inicio_ms : p.fin_ms + 250;
    return ms >= p.inicio_ms && ms < fin;
  });
  if (i < 0) return null;
  const p = PALABRAS[i];
  const entrada = spring({
    frame: frame - (INICIO_VOZ + Math.round((p.inicio_ms / 1000) * fps)),
    fps,
    config: { damping: 14, stiffness: 260, mass: 0.6 },
  });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", top: 1430 }}>
      <div
        style={{
          fontFamily: FUENTE,
          fontWeight: 900,
          fontSize: 104,
          letterSpacing: 1,
          color: C.texto,
          WebkitTextStroke: `14px ${C.contorno}`,
          paintOrder: "stroke fill",
          textTransform: "uppercase",
          transform: `scale(${0.8 + 0.2 * entrada})`,
          textShadow: `0 8px 0 ${C.contorno}`,
        }}
      >
        {p.texto.toLocaleUpperCase("es")}
      </div>
    </AbsoluteFill>
  );
};

const Etiqueta: React.FC = () => {
  const frame = useCurrentFrame(); // relativo al inicio de la Sequence
  const { fps } = useVideoConfig();
  const dur = ETIQUETA.hasta - ETIQUETA.desde;
  const caja = spring({ frame, fps, config: { damping: 13, stiffness: 180 } });
  const trazo = interpolate(frame, [6, 20], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const salida = interpolate(frame, [dur - 8, dur], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Flecha: del borde inferior de la cápsula al cable, con una curva suave
  const ini = { x: 360, y: 640 };
  const fin = { x: PUNTO_CABLE.x, y: PUNTO_CABLE.y };
  const ctrl = { x: ini.x - 10, y: fin.y - 60 };
  const ruta = `M ${ini.x} ${ini.y} Q ${ctrl.x} ${ctrl.y} ${fin.x} ${fin.y}`;
  const angulo = (Math.atan2(fin.y - ctrl.y, fin.x - ctrl.x) * 180) / Math.PI;
  const largo = 420;
  const punta = interpolate(frame, [18, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ opacity: salida }}>
      <svg width={1080} height={1920} style={{ position: "absolute" }}>
        <path
          d={ruta}
          fill="none"
          stroke={C.contorno}
          strokeWidth={14}
          strokeLinecap="round"
          strokeDasharray={largo}
          strokeDashoffset={largo * trazo}
        />
        <path
          d={ruta}
          fill="none"
          stroke={C.texto}
          strokeWidth={6}
          strokeLinecap="round"
          strokeDasharray={largo}
          strokeDashoffset={largo * trazo}
        />
        <g transform={`translate(${fin.x} ${fin.y}) rotate(${angulo}) scale(${punta})`}>
          <path d="M 0 0 L -34 -18 L -26 0 L -34 18 Z" fill={C.texto} stroke={C.contorno} strokeWidth={5} strokeLinejoin="round" />
        </g>
      </svg>
      <div
        style={{
          position: "absolute",
          left: 90,
          top: 540,
          padding: "22px 34px",
          borderRadius: 999,
          background: C.capsula,
          color: C.texto,
          fontFamily: FUENTE,
          fontWeight: 900,
          fontSize: 46,
          letterSpacing: 1,
          display: "flex",
          alignItems: "center",
          gap: 18,
          transform: `scale(${caja})`,
          transformOrigin: "30% 100%",
        }}
      >
        <span style={{ width: 22, height: 22, borderRadius: 999, background: C.acento, display: "inline-block" }} />
        CABLE DE FIBRA ÓPTICA
      </div>
    </AbsoluteFill>
  );
};

export const Prueba3D: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#F3F0EA" }}>
      <Fondo3D />
      <Sequence from={ETIQUETA.desde} durationInFrames={ETIQUETA.hasta - ETIQUETA.desde} layout="none">
        <Etiqueta />
      </Sequence>
      <Subtitulos />
      <Sequence from={INICIO_VOZ} layout="none">
        <Audio src={staticFile("05_audio/voz_borrador.mp3")} />
      </Sequence>
    </AbsoluteFill>
  );
};
