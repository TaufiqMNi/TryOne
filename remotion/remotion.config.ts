import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setCodec("h264");
// Guna Chromium yang dah terpasang dalam container (elak muat turun)
if (process.env.PLAYWRIGHT_BROWSERS_PATH) {
  Config.setBrowserExecutable(
    `${process.env.PLAYWRIGHT_BROWSERS_PATH}/chromium_headless_shell-1194/chrome-linux/headless_shell`,
  );
}
