import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const PALABRAS = ["Estudio", "de", "producción", "listo"];

export const Prueba: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const salida = interpolate(
    frame,
    [durationInFrames - 15, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#F4EFE6",
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
        gap: 24,
        fontFamily: "Segoe UI, Arial, sans-serif",
        opacity: salida,
      }}
    >
      {PALABRAS.map((palabra, i) => {
        const entrada = spring({
          frame: frame - i * 8,
          fps,
          config: { damping: 12, stiffness: 120 },
        });
        return (
          <div
            key={palabra}
            style={{
              fontSize: 120,
              fontWeight: 800,
              color: i === PALABRAS.length - 1 ? "#E4572E" : "#1F2A44",
              transform: `translateY(${(1 - entrada) * 200}px) scale(${entrada})`,
              opacity: entrada,
            }}
          >
            {palabra}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
