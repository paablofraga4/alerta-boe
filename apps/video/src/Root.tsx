import React from "react";
import { Composition } from "remotion";
import { BoeShort } from "./BoeShort";
import { DEFAULT_PROPS, type BoeShortProps } from "./types";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="BoeShort"
      component={BoeShort}
      durationInFrames={DEFAULT_PROPS.durationInFrames}
      fps={DEFAULT_PROPS.fps}
      width={1080}
      height={1920}
      defaultProps={DEFAULT_PROPS}
      // La duración y el fps reales vienen en las props emitidas por el pipeline.
      calculateMetadata={({ props }: { props: BoeShortProps }) => ({
        durationInFrames: props.durationInFrames,
        fps: props.fps,
      })}
    />
  );
};
