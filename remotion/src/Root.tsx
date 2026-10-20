import { Composition } from "remotion";
import { Main } from "./Main";

// Ikut CLAUDE.md: 1080x1920, 30fps
export const RemotionRoot: React.FC = () => (
  <Composition
    id="Main"
    component={Main}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={150}
  />
);
