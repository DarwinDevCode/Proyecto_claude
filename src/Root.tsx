import React from "react";
import { Composition } from "remotion";
import { Prueba } from "./Prueba";
import { Prueba3D, PRUEBA3D_FRAMES } from "./prueba3d/Prueba3D";
import { Prueba3Dv2, PRUEBA3D_V2_FRAMES } from "./prueba3d/Prueba3Dv2";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Prueba"
        component={Prueba}
        durationInFrames={150}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="Prueba3D"
        component={Prueba3D}
        durationInFrames={PRUEBA3D_FRAMES}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="Prueba3Dv2"
        component={Prueba3Dv2}
        durationInFrames={PRUEBA3D_V2_FRAMES}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
