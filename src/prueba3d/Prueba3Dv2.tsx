import React from "react";
import {
  AbsoluteFill,
  Audio,
  cancelRender,
  continueRender,
  delayRender,
  Img,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import datosVoz from "../../proyectos/2026-11-21_prueba-3d/05_audio/voz_borrador_v2.palabras.json";
import urlLilita from "../../biblioteca/fuentes/LilitaOne/LilitaOne-Regular.ttf";

// Render con --public-dir "proyectos/2026-11-21_prueba-3d" (04_blender/, 05_audio/).
// La escena llega en dos capas PNG con alfa: "escena" (con contorno) y "agua" (bloque
// semitransparente con el resto en holdout). Se componen sobre el fondo.

// Voz a velocidad normal: la última palabra termina a 7,85 s -> 1 s más = 266 fotogramas.
export const PRUEBA3D_V2_FRAMES = 266;
const ETIQUETA = { desde: 137, hasta: 180 }; // aparece en "este" (f137) y sale con el mov. 3 (f178)
const PUNTO_CABLE = { x: 512, y: 990 }; // centro del cable en ese plano (proyección desde Blender)

const C = { texto: "#FFFFFF", contorno: "#2B3150", capsula: "#2B3150", acento: "#5ED3B5", fondo: "#F3F0EA" };
const FUENTE = "'Lilita One', sans-serif";

// Fuente OFL local (biblioteca/fuentes): el render espera a que cargue
const espera = delayRender("Cargando Lilita One");
const fuente = new FontFace("Lilita One", `url(${urlLilita}) format("truetype")`);
fuente
  .load()
  .then(() => {
    document.fonts.add(fuente);
    continueRender(espera);
  })
  .catch((e) => cancelRender(e));

type Palabra = { texto: string; inicio_ms: number; fin_ms: number };

// edge-tts agrupa "del 99" y deja "%" suelto: separa grupos y une "%" al número.
const palabrasSubtitulo = (lista: Palabra[]): Palabra[] => {
  const sep: Palabra[] = [];
  for (const p of lista) {
    const partes = p.texto.split(" ");
    const paso = (p.fin_ms - p.inicio_ms) / partes.length;
    partes.forEach((t, i) =>
      sep.push({ texto: t, inicio_ms: Math.round(p.inicio_ms + i * paso), fin_ms: Math.round(p.inicio_ms + (i + 1) * paso) }),
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

const Capa: React.FC<{ nombre: "escena" | "agua" }> = ({ nombre }) => {
  const frame = useCurrentFrame();
  const n = String(Math.min(frame + 1, PRUEBA3D_V2_FRAMES)).padStart(4, "0");
  return (
    <Img
      src={staticFile(`04_blender/frames_v2_${nombre}/f_${n}.png`)}
      style={{ position: "absolute", width: "100%", height: "100%" }}
    />
  );
};

const Subtitulos: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ms = (frame / fps) * 1000;
  const i = PALABRAS.findIndex((p, k) => {
    const sig = PALABRAS[k + 1];
    const fin = sig && sig.inicio_ms - p.fin_ms < 400 ? sig.inicio_ms : p.fin_ms + 250;
    return ms >= p.inicio_ms && ms < fin;
  });
  if (i < 0) return null;
  const p = PALABRAS[i];
  const entrada = spring({
    frame: frame - Math.round((p.inicio_ms / 1000) * fps),
    fps,
    config: { damping: 14, stiffness: 260, mass: 0.6 },
  });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", top: 1420 }}>
      <div
        style={{
          fontFamily: FUENTE,
          fontSize: 118,
          letterSpacing: 2,
          color: C.texto,
          WebkitTextStroke: `16px ${C.contorno}`,
          paintOrder: "stroke fill",
          transform: `scale(${0.8 + 0.2 * entrada})`,
          textShadow: `0 9px 0 ${C.contorno}`,
        }}
      >
        {p.texto.toLocaleUpperCase("es")}
      </div>
    </AbsoluteFill>
  );
};

const Etiqueta: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = ETIQUETA.hasta - ETIQUETA.desde;
  const caja = spring({ frame, fps, config: { damping: 13, stiffness: 200 } });
  const trazo = interpolate(frame, [4, 14], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const punta = interpolate(frame, [12, 17], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const salida = interpolate(frame, [dur - 6, dur], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const ini = { x: 330, y: 650 };
  const fin = PUNTO_CABLE;
  const ctrl = { x: ini.x - 20, y: fin.y - 70 };
  const ruta = `M ${ini.x} ${ini.y} Q ${ctrl.x} ${ctrl.y} ${fin.x} ${fin.y}`;
  const angulo = (Math.atan2(fin.y - ctrl.y, fin.x - ctrl.x) * 180) / Math.PI;
  const largo = 520;

  return (
    <AbsoluteFill style={{ opacity: salida }}>
      <svg width={1080} height={1920} style={{ position: "absolute" }}>
        {[{ c: C.contorno, w: 14 }, { c: C.texto, w: 6 }].map((s) => (
          <path
            key={s.c}
            d={ruta}
            fill="none"
            stroke={s.c}
            strokeWidth={s.w}
            strokeLinecap="round"
            strokeDasharray={largo}
            strokeDashoffset={largo * trazo}
          />
        ))}
        <g transform={`translate(${fin.x} ${fin.y}) rotate(${angulo}) scale(${punta})`}>
          <path d="M 0 0 L -34 -18 L -26 0 L -34 18 Z" fill={C.texto} stroke={C.contorno} strokeWidth={5} strokeLinejoin="round" />
        </g>
      </svg>
      <div
        style={{
          position: "absolute",
          left: 80,
          top: 548,
          padding: "20px 34px",
          borderRadius: 999,
          background: C.capsula,
          color: C.texto,
          fontFamily: FUENTE,
          fontSize: 52,
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

export const Prueba3Dv2: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: C.fondo }}>
      <Capa nombre="escena" />
      <Capa nombre="agua" />
      <Sequence from={ETIQUETA.desde} durationInFrames={ETIQUETA.hasta - ETIQUETA.desde} layout="none">
        <Etiqueta />
      </Sequence>
      <Subtitulos />
      <Audio src={staticFile("05_audio/voz_borrador_v2.mp3")} />
    </AbsoluteFill>
  );
};
