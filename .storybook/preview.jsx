import '../docs/analysis-plain.css';
import '../docs/analysis-satisfaction.css';
import '../docs/analysis-satisfaction-v2.css';
import './preview.css';

import { mswLoader } from 'msw-storybook-addon/csf3';

import { mswHandlers } from './msw-handlers';
import carouselStyle from '../docs/carousel-style.json';

/** @type { import('@storybook/html-vite').Preview } */
const preview = {
  initialGlobals: {
    carouselControlStyle: carouselStyle.controls,
    carouselHeaderStyle: carouselStyle.header,
  },
  globalTypes: {
    carouselControlStyle: {
      description: 'Selected carousel control-bar treatment',
    },
    carouselHeaderStyle: {
      description: 'Selected carousel header treatment',
    },
  },
  decorators: [
    (Story) => {
      document.body.classList.add('satisfaction-preview');
      return Story();
    },
  ],
  loaders: [mswLoader()],
  async beforeEach({ msw }) {
    msw.use(...mswHandlers);
  },
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    a11y: {
      test: 'todo',
    },
  },
};

export default preview;
