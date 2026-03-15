/**
 * Record a GIF-ready video of the portfolio page by scrolling through sections.
 * Usage: node scripts/record_portfolio.mjs
 *
 * Outputs: assets/portfolio-preview.webm
 */

import { chromium } from "playwright";
import { mkdirSync, renameSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const outputDir = resolve(__dirname, "..", "assets");
mkdirSync(outputDir, { recursive: true });

const URL = "https://yancheng-go.github.io";
const WIDTH = 1280;
const HEIGHT = 720;

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: WIDTH, height: HEIGHT },
    recordVideo: {
      dir: outputDir,
      size: { width: WIDTH, height: HEIGHT },
    },
    // Use light mode so GIF colors are visible
    colorScheme: "light",
  });

  const page = await context.newPage();
  await page.goto(URL, { waitUntil: "networkidle" });

  // Wait for page JS to fully render (particles, stats, etc.)
  await page.waitForTimeout(3000);

  // Take a debug screenshot to verify rendering
  await page.screenshot({ path: resolve(outputDir, "debug-screenshot.png") });
  console.log("Debug screenshot saved");

  // Scroll through sections smoothly
  const scrollSteps = [400, 800, 1200, 1800, 2400, 3000, 3600, 4200];
  for (const y of scrollSteps) {
    await page.evaluate((scrollY) => {
      window.scrollTo({ top: scrollY, behavior: "smooth" });
    }, y);
    await page.waitForTimeout(1200);
  }

  // Scroll back to top
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "smooth" }));
  await page.waitForTimeout(1500);

  // Close context to finalize video
  const video = page.video();
  await context.close();

  // Rename the video file
  if (video) {
    const videoPath = await video.path();
    const targetPath = resolve(outputDir, "portfolio-preview.webm");
    renameSync(videoPath, targetPath);
    console.log(`Video saved: ${targetPath}`);
  }

  await browser.close();
}

main().catch(console.error);
