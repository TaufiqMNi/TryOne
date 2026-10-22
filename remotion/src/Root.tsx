import { Composition } from "remotion";
import { Main } from "./Main";
import { Card, CardProps, calculateCardMetadata } from "./card/Card";

// Lalai neutral (sama seperti card.html) — Remotion gabung --props atas defaultProps,
// jadi medan pilihan mesti ada nilai lalai supaya tak "bocor" dari contoh.
const cardDefaults: CardProps = {
  kind: "title",
  lines: ["Tajuk", "kad"],
  highlight: "",
  arabic: [],
  source: "",
  duration: 2.5,
  full: false,
  instant: false,
};

// Ikut CLAUDE.md: 1080x1920, 30fps
export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Main"
      component={Main}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={150}
    />
    <Composition
      id="Card"
      component={Card}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={75}
      defaultProps={cardDefaults}
      calculateMetadata={calculateCardMetadata}
    />
  </>
);
