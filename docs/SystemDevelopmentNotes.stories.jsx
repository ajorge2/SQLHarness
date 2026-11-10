import { expect } from 'storybook/test';

import pageMarkup from './index.html?raw';

const controlBarMarkup = {
  utility: `
    <span class="system-details-status" data-carousel-status aria-live="polite" aria-atomic="true"></span>
    <div class="system-details-buttons">
      <button type="button" data-carousel-previous aria-label="Show previous page">←</button>
      <button type="button" data-carousel-next aria-label="Show next page">→</button>
    </div>`,
  chapters: `
    <span class="system-details-status system-details-status--sr" data-carousel-status aria-live="polite" aria-atomic="true"></span>
    <button class="system-details-chapter" type="button" data-carousel-slide-to="0"><span>01</span><strong>MODEL</strong></button>
    <button class="system-details-chapter" type="button" data-carousel-slide-to="1"><span>02</span><strong>SQL FRAGMENTS</strong></button>`,
  rail: `
    <span class="system-details-status system-details-status--sr" data-carousel-status aria-live="polite" aria-atomic="true"></span>
    <div class="system-details-rail-label"><strong data-carousel-current>02</strong><span>/ 02</span></div>
    <div class="system-details-rail" aria-label="Carousel pages">
      <button type="button" data-carousel-slide-to="0" aria-label="Show model page"></button>
      <button type="button" data-carousel-slide-to="1" aria-label="Show SQL fragments page"></button>
    </div>
    <div class="system-details-buttons">
      <button type="button" data-carousel-previous aria-label="Show previous page">←</button>
      <button type="button" data-carousel-next aria-label="Show next page">→</button>
    </div>`,
  folio: `
    <span class="system-details-status system-details-status--sr" data-carousel-status aria-live="polite" aria-atomic="true"></span>
    <button class="system-details-folio-arrow" type="button" data-carousel-previous aria-label="Show previous page">←</button>
    <div class="system-details-folio-number" aria-hidden="true"><span data-carousel-current>02</span><i></i><span data-carousel-total>02</span></div>
    <button class="system-details-folio-arrow" type="button" data-carousel-next aria-label="Show next page">→</button>`,
  split: `
    <span class="system-details-status system-details-status--sr" data-carousel-status aria-live="polite" aria-atomic="true"></span>
    <button class="system-details-split-command" type="button" data-carousel-previous aria-label="Show previous page">←</button>
    <div class="system-details-split-status" aria-hidden="true"><strong data-carousel-current>02</strong><span>OF</span><strong data-carousel-total>02</strong></div>
    <button class="system-details-split-command" type="button" data-carousel-next aria-label="Show next page">→</button>`,
};

const renderSystemDevelopmentNotes = ({ initialSlide }, { globals }) => {
  const source = new DOMParser().parseFromString(pageMarkup, 'text/html');
  const carousel = source.querySelector('[data-system-carousel]');
  const controls = carousel.querySelector('.system-details-controls');
  const stage = document.createElement('main');
  const controlStyle = controlBarMarkup[globals.carouselControlStyle]
    ? globals.carouselControlStyle
    : 'utility';
  const headerStyle = ['signal', 'indexed', 'bracket', 'overline', 'masthead'].includes(globals.carouselHeaderStyle)
    ? globals.carouselHeaderStyle
    : 'signal';

  stage.className = 'storybook-component-stage';
  carousel.dataset.headerStyle = headerStyle;
  controls.dataset.controlsStyle = controlStyle;
  controls.innerHTML = controlBarMarkup[controlStyle];
  stage.append(carousel);

  const slides = [...carousel.querySelectorAll('[data-carousel-slide]')];
  const status = carousel.querySelector('[data-carousel-status]');
  const visualCurrent = carousel.querySelector('[data-carousel-current]');
  const visualTotal = carousel.querySelector('[data-carousel-total]');
  const previous = carousel.querySelector('[data-carousel-previous]');
  const next = carousel.querySelector('[data-carousel-next]');
  const directButtons = [...carousel.querySelectorAll('[data-carousel-slide-to]')];
  let current = Math.min(Math.max(initialSlide - 1, 0), slides.length - 1);

  const update = () => {
    slides.forEach((slide, index) => {
      slide.hidden = index !== current;
    });
    status.textContent = `${current + 1} / ${slides.length}`;
    if (visualCurrent) visualCurrent.textContent = String(current + 1).padStart(2, '0');
    if (visualTotal) visualTotal.textContent = String(slides.length).padStart(2, '0');
    if (previous) previous.disabled = current === 0;
    if (next) next.disabled = current === slides.length - 1;
    directButtons.forEach((button) => {
      const selected = Number(button.dataset.carouselSlideTo) === current;
      button.setAttribute('aria-current', selected ? 'page' : 'false');
    });
  };

  previous?.addEventListener('click', () => {
    current = Math.max(0, current - 1);
    update();
  });
  next?.addEventListener('click', () => {
    current = Math.min(slides.length - 1, current + 1);
    update();
  });
  directButtons.forEach((button) => {
    button.addEventListener('click', () => {
      current = Number(button.dataset.carouselSlideTo);
      update();
    });
  });
  update();

  return stage;
};

const meta = {
  tags: ['ai-generated'],
  render: renderSystemDevelopmentNotes,
  args: {
    initialSlide: 1,
  },
  argTypes: {
    initialSlide: {
      control: { type: 'inline-radio' },
      options: [1, 2],
    },
  },
};

export default meta;

export const InteractiveCarousel = {
  parameters: {
    carouselExplorations: {
      figmaUrl:
        'https://www.figma.com/design/pnPZTwi0EpDg6JUbN3eXfm/SQLHarness-System-Notes-Explorations?node-id=13-65',
      variants: [
        {
          name: 'Swiss utility strip',
          lineage: 'Approved New Typography baseline',
          description: 'A quiet counter paired with compact, square commands.',
          theme: {
            key: 'swiss', controlsKey: 'utility', canvas: '#b9aaaa', body: '#c8bbbb', controls: '#685044',
            button: '#ebdede', ink: '#252222', accent: '#685044', rule: '#8a756b',
            controlsInk: '#f7f2ee', buttonInk: '#252222', radius: 0, bullet: '●',
            headingFont: 'IBM Plex Sans, sans-serif', bodyFont: 'IBM Plex Sans, sans-serif',
            labelFont: 'IBM Plex Mono, monospace', headingWeight: 600, showRule: false,
          },
        },
        {
          name: 'Indexed chapters',
          lineage: 'Editorial chapter tabs',
          description: 'The two slides become named destinations instead of an abstract count.',
          referenceUrl: 'https://www.designsystems.com/space-govuk-navigation/',
          theme: {
            key: 'swiss', controlsKey: 'chapters', canvas: '#b9aaaa', body: '#c8bbbb', controls: '#685044',
            button: '#ebdede', ink: '#252222', accent: '#685044', rule: '#8a756b',
            controlsInk: '#f7f2ee', buttonInk: '#252222', radius: 0, bullet: '●',
            headingFont: 'IBM Plex Sans, sans-serif', bodyFont: 'IBM Plex Sans, sans-serif',
            labelFont: 'IBM Plex Mono, monospace', headingWeight: 600, showRule: false,
          },
        },
        {
          name: 'Progress rail',
          lineage: 'Industrial wayfinding',
          description: 'A strong horizontal route makes position legible at a glance.',
          referenceUrl: 'https://www.moma.org/collection/works/7292',
          theme: {
            key: 'swiss', controlsKey: 'rail', canvas: '#b9aaaa', body: '#c8bbbb', controls: '#685044',
            button: '#ebdede', ink: '#252222', accent: '#685044', rule: '#8a756b',
            controlsInk: '#f7f2ee', buttonInk: '#252222', radius: 0, bullet: '●',
            headingFont: 'IBM Plex Sans, sans-serif', bodyFont: 'IBM Plex Sans, sans-serif',
            labelFont: 'IBM Plex Mono, monospace', headingWeight: 600, showRule: false,
          },
        },
        {
          name: 'Centered folio',
          lineage: 'Modernist book pagination',
          description: 'Navigation reads like a composed page folio rather than app chrome.',
          referenceUrl: 'https://www.moma.org/collection/works/7292',
          theme: {
            key: 'swiss', controlsKey: 'folio', canvas: '#b9aaaa', body: '#c8bbbb', controls: '#ebdede',
            button: '#685044', ink: '#252222', accent: '#685044', rule: '#8a756b',
            controlsInk: '#252222', buttonInk: '#f7f2ee', radius: 0, bullet: '●',
            headingFont: 'IBM Plex Sans, sans-serif', bodyFont: 'IBM Plex Sans, sans-serif',
            labelFont: 'IBM Plex Mono, monospace', headingWeight: 600, showRule: false,
          },
        },
        {
          name: 'Split command bar',
          lineage: 'Early digital control panels',
          description: 'Back, position, and forward each occupy a clear physical zone.',
          referenceUrl: 'https://www.ibm.com/design/language/',
          theme: {
            key: 'swiss', controlsKey: 'split', canvas: '#b9aaaa', body: '#c8bbbb', controls: '#685044',
            button: '#ebdede', ink: '#252222', accent: '#685044', rule: '#8a756b',
            controlsInk: '#f7f2ee', buttonInk: '#252222', radius: 0, bullet: '●',
            headingFont: 'IBM Plex Sans, sans-serif', bodyFont: 'IBM Plex Sans, sans-serif',
            labelFont: 'IBM Plex Mono, monospace', headingWeight: 600, showRule: false,
          },
        },
      ],
      headerVariants: [
        {
          name: 'Signal rule',
          lineage: 'Swiss grid / signal bar',
          description: 'The approved baseline: a single strong rule gives the title a clear starting signal.',
          theme: {
            key: 'swiss', headerKey: 'signal', controlsKey: 'chapters', canvas: '#b9aaaa', body: '#c8bbbb', controls: '#685044',
            button: '#ebdede', ink: '#252222', accent: '#685044', rule: '#8a756b',
            controlsInk: '#f7f2ee', buttonInk: '#252222', radius: 0, bullet: '●',
            headingFont: 'IBM Plex Sans, sans-serif', bodyFont: 'IBM Plex Sans, sans-serif',
            labelFont: 'IBM Plex Mono, monospace', headingWeight: 600, showRule: false,
          },
        },
        {
          name: 'Indexed header',
          lineage: 'Dutch editorial indexing',
          description: 'A compact system label and index make the card feel like part of a documented series.',
          theme: {
            key: 'swiss', headerKey: 'indexed', controlsKey: 'chapters', canvas: '#b9aaaa', body: '#c8bbbb', controls: '#685044',
            button: '#ebdede', ink: '#252222', accent: '#685044', rule: '#8a756b',
            controlsInk: '#f7f2ee', buttonInk: '#252222', radius: 0, bullet: '●',
            headingFont: 'IBM Plex Sans, sans-serif', bodyFont: 'IBM Plex Sans, sans-serif',
            labelFont: 'IBM Plex Mono, monospace', headingWeight: 600, showRule: false,
          },
        },
        {
          name: 'Bracket marker',
          lineage: 'Modular wayfinding systems',
          description: 'A vertical marker anchors the title without adding another horizontal divider.',
          theme: {
            key: 'swiss', headerKey: 'bracket', controlsKey: 'chapters', canvas: '#b9aaaa', body: '#c8bbbb', controls: '#685044',
            button: '#ebdede', ink: '#252222', accent: '#685044', rule: '#8a756b',
            controlsInk: '#f7f2ee', buttonInk: '#252222', radius: 0, bullet: '●',
            headingFont: 'IBM Plex Sans, sans-serif', bodyFont: 'IBM Plex Sans, sans-serif',
            labelFont: 'IBM Plex Mono, monospace', headingWeight: 600, showRule: false,
          },
        },
        {
          name: 'Editorial overline',
          lineage: 'Magazine section hierarchy',
          description: 'A small section name and short accent rule introduce the title with editorial rhythm.',
          theme: {
            key: 'swiss', headerKey: 'overline', controlsKey: 'chapters', canvas: '#b9aaaa', body: '#c8bbbb', controls: '#685044',
            button: '#ebdede', ink: '#252222', accent: '#685044', rule: '#8a756b',
            controlsInk: '#f7f2ee', buttonInk: '#252222', radius: 0, bullet: '●',
            headingFont: 'IBM Plex Sans, sans-serif', bodyFont: 'IBM Plex Sans, sans-serif',
            labelFont: 'IBM Plex Mono, monospace', headingWeight: 600, showRule: false,
          },
        },
        {
          name: 'Reversed masthead',
          lineage: 'International Typographic Style posters',
          description: 'A dark title band creates the strongest hierarchy while staying inside the page palette.',
          theme: {
            key: 'swiss', headerKey: 'masthead', controlsKey: 'chapters', canvas: '#b9aaaa', body: '#c8bbbb', controls: '#685044',
            button: '#ebdede', ink: '#252222', accent: '#685044', rule: '#8a756b',
            controlsInk: '#f7f2ee', buttonInk: '#252222', radius: 0, bullet: '●',
            headingFont: 'IBM Plex Sans, sans-serif', bodyFont: 'IBM Plex Sans, sans-serif',
            labelFont: 'IBM Plex Mono, monospace', headingWeight: 600, showRule: false,
          },
        },
      ],
    },
  },
  play: async ({ canvas, userEvent }) => {
    const carousel = canvas.getByRole('region', { name: 'System development notes' });
    const next = canvas.queryByRole('button', { name: 'Show next page' })
      ?? canvas.getByRole('button', { name: /SQL FRAGMENTS/ });

    await expect(carousel).toHaveAttribute('aria-roledescription', 'carousel');
    await userEvent.click(next);
    await expect(canvas.getByText('2 / 2')).toHaveTextContent('2 / 2');
    await expect(
      canvas.getByRole('group', { name: '2 of 2: How SQL fragments are selected' }),
    ).toBeVisible();
  },
};

export const SecondSlide = {
  args: {
    initialSlide: 2,
  },
};

export const CssCheck = {
  play: async ({ canvas }) => {
    const viewport = canvas.getByRole('group', {
      name: '1 of 2: How the semantic model was developed',
    }).parentElement;

    // .system-details-viewport uses --carousel-body: #c8bbbb.
    await expect(getComputedStyle(viewport).backgroundColor).toBe('rgb(200, 187, 187)');
  },
};
