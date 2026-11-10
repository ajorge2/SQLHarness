

/** @type { import('@storybook/html-vite').StorybookConfig } */
const config = {
  "stories": [
    "../docs/**/*.stories.@(js|jsx|mjs|ts|tsx)"
  ],
  "addons": [
    "@chromatic-com/storybook",
    "@storybook/addon-vitest",
    "@storybook/addon-a11y",
    "@storybook/addon-docs",
    "@storybook/addon-mcp",
    "msw-storybook-addon"
  ],
  "framework": "@storybook/html-vite",
  "staticDirs": ["../public"],
  viteFinal(viteConfig) {
    viteConfig.plugins = [...(viteConfig.plugins ?? []), persistCarouselStylePlugin];
    return viteConfig;
  }
};
export default config;
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const carouselStyleScript = fileURLToPath(new URL('../docs/carousel-style.js', import.meta.url));
const carouselStyleData = fileURLToPath(new URL('../docs/carousel-style.json', import.meta.url));
const allowedCarouselStyles = new Set(['utility', 'chapters', 'rail', 'folio', 'split']);
const allowedCarouselHeaderStyles = new Set(['signal', 'indexed', 'bracket', 'overline', 'masthead']);

const persistCarouselStylePlugin = {
  name: 'persist-carousel-style',
  configureServer(server) {
    server.middlewares.use('/__sqlharness/apply-carousel-style', (request, response) => {
      if (request.method !== 'POST') {
        response.statusCode = 405;
        response.end('Method not allowed');
        return;
      }

      let body = '';
      request.on('data', (chunk) => { body += chunk; });
      request.on('end', async () => {
        try {
          const request = JSON.parse(body);
          const stored = JSON.parse(await readFile(carouselStyleData, 'utf8'));
          const controls = request.controls ?? request.style ?? stored.controls ?? stored.style ?? 'utility';
          const header = request.header ?? stored.header ?? 'signal';
          if (!allowedCarouselStyles.has(controls)) throw new Error('Unknown carousel control style');
          if (!allowedCarouselHeaderStyles.has(header)) throw new Error('Unknown carousel header style');
          const selection = { controls, header };
          await Promise.all([
            writeFile(carouselStyleScript, `window.SQLHARNESS_CAROUSEL_STYLE = ${JSON.stringify(selection)};\n`, 'utf8'),
            writeFile(carouselStyleData, `${JSON.stringify(selection, null, 2)}\n`, 'utf8'),
          ]);
          response.setHeader('Content-Type', 'application/json');
          response.end(JSON.stringify(selection));
        } catch (error) {
          response.statusCode = 400;
          response.end(error.message);
        }
      });
    });
  },
};

