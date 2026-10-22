import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

// Fon OFL dalam public/fonts (salinan dari broll/fonts)
loadFont({ family: "Bebas Neue", url: staticFile("fonts/BebasNeue-Regular.ttf") });
loadFont({ family: "Amiri", url: staticFile("fonts/Amiri-Bold.ttf"), weight: "700" });
