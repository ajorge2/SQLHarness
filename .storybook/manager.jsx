import React, { useEffect, useState } from 'react';
import { AddonPanel } from 'storybook/internal/components';
import { addons, types, useGlobals, useParameter, useStorybookApi } from 'storybook/manager-api';

const ADDON_ID = 'sqlharness/carousel-explorations';
const PANEL_ID = `${ADDON_ID}/panel`;
const PARAM_KEY = 'carouselExplorations';

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Alegreya+Sans+SC:wght@700&family=Cormorant+Garamond:wght@400;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;600&family=Maitree:wght@400;600&display=swap');

  .sqlharness-explorations {
    box-sizing: border-box;
    position: absolute;
    inset: 0;
    display: grid;
    grid-template-rows: 52px minmax(0, 1fr) 34px;
    width: 100%;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    color: #251f1f;
    background: #f3eeea;
    font-family: Inter, ui-sans-serif, system-ui, sans-serif;
  }

  .sqlharness-explorations * { box-sizing: border-box; }

  .sqlharness-explorations__header {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
    padding: 8px 12px;
    border-bottom: 1px solid #d8cfca;
    background: #fffaf6;
  }

  .sqlharness-explorations__title {
    min-width: 0;
    flex: 1;
  }

  .sqlharness-explorations__title strong,
  .sqlharness-explorations__title span {
    display: block;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  .sqlharness-explorations__title strong { font-size: 13px; }
  .sqlharness-explorations__title span { color: #756762; font-size: 11px; }

  .sqlharness-explorations__modes {
    display: flex;
    gap: 3px;
    padding: 3px;
    border: 1px solid #d8cfca;
    background: #f3eeea;
  }

  .sqlharness-explorations__mode {
    height: 24px;
    padding: 0 8px;
    border: 0;
    color: #756762;
    background: transparent;
    font: 650 10px/1 Inter, ui-sans-serif, system-ui, sans-serif;
    cursor: pointer;
  }

  .sqlharness-explorations__mode[aria-pressed='true'] { color: #fffaf6; background: #6c4c3e; }

  .sqlharness-explorations__button,
  .sqlharness-explorations__link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 32px;
    border: 1px solid #cfc3bd;
    border-radius: 5px;
    color: #332a27;
    background: #fff;
    font: inherit;
    font-size: 12px;
    font-weight: 650;
    text-decoration: none;
    cursor: pointer;
  }

  .sqlharness-explorations__button { width: 34px; font-size: 18px; }
  .sqlharness-explorations__link { padding: 0 11px; }
  .sqlharness-explorations__button:hover,
  .sqlharness-explorations__link:hover { background: #eadfda; }
  .sqlharness-explorations__button:focus-visible,
  .sqlharness-explorations__link:focus-visible,
  .sqlharness-explorations__dot:focus-visible { outline: 2px solid #6c4c3e; outline-offset: 2px; }

  .sqlharness-explorations__stage {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 0;
    min-height: 0;
    overflow: hidden;
    padding: 10px 52px;
  }

  .sqlharness-explorations__image {
    display: block;
    width: 100%;
    height: 100%;
    min-width: 0;
    min-height: 0;
    object-fit: contain;
    object-position: center;
    user-select: none;
  }

  .sqlharness-style-preview {
    position: relative;
    display: grid;
    grid-template-rows: minmax(0, 1fr) 52px;
    height: 100%;
    max-width: 100%;
    aspect-ratio: 545 / 410;
    overflow: hidden;
    border: var(--preview-border, 0) solid var(--style-rule);
    border-radius: var(--style-radius);
    color: var(--style-ink);
    background: var(--style-body);
    box-shadow: 0 10px 30px rgba(31, 25, 22, 0.08);
  }

  .sqlharness-style-preview__body {
    min-height: 0;
    padding: 22px 24px 34px;
    overflow: hidden;
    background: var(--style-body);
    font-family: var(--body-font);
  }

  .sqlharness-style-preview[data-header='indexed'] .sqlharness-style-preview__body,
  .sqlharness-style-preview[data-header='bracket'] .sqlharness-style-preview__body,
  .sqlharness-style-preview[data-header='overline'] .sqlharness-style-preview__body,
  .sqlharness-style-preview[data-header='masthead'] .sqlharness-style-preview__body { padding-top: 28px; }

  .sqlharness-style-preview__signal {
    width: 100%;
    height: 8px;
    margin-bottom: 15px;
    background: var(--style-accent);
  }

  .sqlharness-style-preview h3 {
    margin: 0 0 17px;
    color: var(--style-ink);
    font-family: var(--heading-font);
    font-size: 24px;
    font-weight: var(--heading-weight);
    line-height: 1.18;
  }

  .sqlharness-style-preview[data-header='indexed'] h3::before {
    content: 'SYSTEM NOTE  /  INDEX 02';
    display: block;
    margin-bottom: 9px;
    color: var(--style-accent);
    font: 500 10px/1.2 var(--label-font);
    letter-spacing: 0.09em;
  }

  .sqlharness-style-preview[data-header='bracket'] h3 {
    padding: 5px 0 5px 18px;
    border-left: 8px solid var(--style-accent);
  }

  .sqlharness-style-preview[data-header='overline'] h3::before {
    content: 'SYSTEM DEVELOPMENT';
    display: block;
    margin-bottom: 8px;
    color: var(--style-accent);
    font: 500 10px/1.2 var(--label-font);
    letter-spacing: 0.12em;
  }

  .sqlharness-style-preview[data-header='overline'] h3::after {
    content: '';
    display: block;
    width: 54px;
    height: 2px;
    margin-top: 12px;
    background: var(--style-accent);
  }

  .sqlharness-style-preview[data-header='masthead'] h3 {
    margin: 0 -24px 20px;
    padding: 18px 24px;
    color: var(--controls-ink);
    background: var(--style-controls);
  }

  .sqlharness-style-preview__rule {
    height: 1px;
    margin: -6px 0 15px;
    background: var(--style-rule);
  }

  .sqlharness-style-preview ul {
    display: grid;
    gap: 13px;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .sqlharness-style-preview li {
    display: grid;
    grid-template-columns: 20px minmax(0, 1fr);
    gap: 10px;
    font-size: 15px;
    line-height: 1.43;
  }

  .sqlharness-style-preview__bullet {
    color: var(--style-accent);
    font-family: var(--label-font);
    font-size: 12px;
    line-height: 1.7;
  }

  .sqlharness-style-preview__controls {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-width: 0;
    padding: 8px 14px;
    color: var(--controls-ink);
    background: var(--style-controls);
    font-family: var(--label-font);
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.08em;
  }

  .sqlharness-style-preview__buttons { display: flex; gap: 8px; }

  .sqlharness-style-preview__buttons button {
    width: 36px;
    height: 36px;
    border: var(--button-border, 0) solid var(--style-accent);
    border-radius: var(--style-radius);
    color: var(--button-ink);
    background: var(--style-button);
    font: inherit;
    font-size: 16px;
  }

  .sqlharness-style-preview button { cursor: pointer; }
  .sqlharness-style-preview button:disabled { cursor: default; opacity: 0.36; }
  .sqlharness-style-preview button:focus-visible { outline: 2px solid var(--style-ink); outline-offset: -3px; }

  .sqlharness-style-preview__select {
    position: absolute;
    right: 14px;
    bottom: 66px;
    z-index: 2;
    min-height: 32px;
    padding: 0 11px;
    border: 1px solid var(--style-rule);
    color: var(--button-ink);
    background: var(--style-button);
    font: 500 11px/1 var(--label-font);
    letter-spacing: 0.03em;
    box-shadow: 0 3px 12px rgba(37, 34, 34, 0.12);
  }

  .sqlharness-style-preview__select[data-selected='true']::before { content: '✓  '; }

  .sqlharness-style-preview__controls[data-controls='chapters'] {
    gap: 0;
    padding: 0;
    background: var(--style-button);
  }

  .sqlharness-style-preview__chapter {
    display: flex;
    min-width: 0;
    height: 52px;
    flex: 1;
    align-items: center;
    gap: 8px;
    padding: 0 14px;
    border-right: 1px solid var(--style-rule);
    color: var(--style-ink);
    letter-spacing: 0;
    background: transparent;
    font: inherit;
    text-align: left;
  }

  .sqlharness-style-preview__chapter span { color: var(--style-rule); }
  .sqlharness-style-preview__chapter strong { overflow: hidden; font-weight: 500; white-space: nowrap; text-overflow: ellipsis; }
  .sqlharness-style-preview__chapter--active { color: var(--controls-ink); background: var(--style-controls); }
  .sqlharness-style-preview__chapter--active span { color: inherit; }

  .sqlharness-style-preview__controls[data-controls='rail'] {
    gap: 14px;
  }

  .sqlharness-style-preview__rail {
    display: grid;
    min-width: 0;
    flex: 1;
    grid-template-columns: 1fr 1fr;
    gap: 3px;
  }

  .sqlharness-style-preview__rail button {
    height: 6px;
    padding: 0;
    border: 0;
    background: color-mix(in srgb, var(--controls-ink) 38%, transparent);
  }

  .sqlharness-style-preview__rail button[aria-current='true'] { background: var(--controls-ink); }

  .sqlharness-style-preview__rail-label {
    display: flex;
    align-items: baseline;
    gap: 5px;
    white-space: nowrap;
  }

  .sqlharness-style-preview__rail-label strong { font-size: 16px; font-weight: 500; }

  .sqlharness-style-preview__controls[data-controls='folio'] {
    justify-content: center;
    gap: 20px;
    color: var(--controls-ink);
    border-top: 1px solid var(--style-rule);
  }

  .sqlharness-style-preview__folio-number {
    display: flex;
    align-items: center;
    gap: 9px;
    font-size: 13px;
    letter-spacing: 0;
  }

  .sqlharness-style-preview__folio-number i {
    display: block;
    width: 42px;
    height: 1px;
    background: var(--style-rule);
  }

  .sqlharness-style-preview__folio-arrow {
    border: 0;
    color: var(--style-accent);
    background: transparent;
    font: 500 18px/1 var(--label-font);
  }

  .sqlharness-style-preview__controls[data-controls='split'] {
    display: grid;
    grid-template-columns: 64px minmax(0, 1fr) 64px;
    padding: 0;
  }

  .sqlharness-style-preview__split-command {
    display: grid;
    height: 52px;
    place-items: center;
    border: 0;
    color: var(--button-ink);
    background: var(--style-button);
    font: 500 17px/1 var(--label-font);
  }

  .sqlharness-style-preview__split-status {
    display: flex;
    height: 52px;
    align-items: center;
    justify-content: center;
    gap: 10px;
    border-right: 1px solid color-mix(in srgb, var(--controls-ink) 28%, transparent);
    border-left: 1px solid color-mix(in srgb, var(--controls-ink) 28%, transparent);
    letter-spacing: 0;
  }

  .sqlharness-style-preview__split-status strong { font-size: 18px; font-weight: 500; }
  .sqlharness-style-preview__split-status span { opacity: 0.62; }

  .sqlharness-style-preview[data-style='aerospace'] h3 {
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .sqlharness-style-preview[data-style='swiss'] {
    --preview-border: 2px;
  }

  .sqlharness-style-preview[data-style='craft'] {
    --preview-border: 2px;
    --button-border: 1px;
  }

  .sqlharness-style-preview[data-style='craft'] h3 { font-size: 27px; }
  .sqlharness-style-preview[data-style='craft'] li { font-size: 16px; }
  .sqlharness-style-preview[data-style='carbon'] h3 { font-size: 22px; }
  .sqlharness-style-preview[data-style='carbon'] li { font-size: 14px; }

  .sqlharness-explorations__arrow {
    position: absolute;
    top: 50%;
    z-index: 1;
    width: 38px;
    height: 56px;
    transform: translateY(-50%);
    border: 1px solid #cfc3bd;
    border-radius: 6px;
    color: #332a27;
    background: rgba(255, 250, 246, 0.94);
    font-size: 21px;
    cursor: pointer;
  }

  .sqlharness-explorations__arrow:hover { background: #eadfda; }
  .sqlharness-explorations__arrow--previous { left: 10px; }
  .sqlharness-explorations__arrow--next { right: 10px; }

  .sqlharness-explorations__footer {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    border-top: 1px solid #d8cfca;
    background: #fffaf6;
  }

  .sqlharness-explorations__dot {
    width: 8px;
    height: 8px;
    padding: 0;
    border: 0;
    border-radius: 999px;
    background: #baaaa4;
    cursor: pointer;
  }

  .sqlharness-explorations__dot[aria-current='true'] {
    width: 26px;
    background: #6c4c3e;
  }

  @media (max-width: 620px) {
    .sqlharness-explorations__title span,
    .sqlharness-explorations__link { display: none; }
    .sqlharness-explorations__mode { padding: 0 6px; }
    .sqlharness-explorations__stage { padding-right: 44px; padding-left: 44px; }
  }
`;

const previewSlides = [
  {
    shortLabel: 'MODEL',
    heading: 'How the semantic model was developed',
    points: [
      'The graph structure was inspired by AMR, which keeps the underlying event instead of the sentence’s word order.',
      'Active and passive versions of the same sentence therefore produce the same map of connected ideas.',
      'SQLHarness applies that idea to data, calculations, rules, and requested answers that can be translated into SQL.',
    ],
  },
  {
    shortLabel: 'SQL FRAGMENTS',
    heading: 'How SQL fragments are selected',
    points: [
      'The intent graph becomes a parts list for the SQL query. Each labeled connection describes one job.',
      'SQLHarness searches a catalog of ready-made SQL pieces and keeps the piece that best fits the graph and database.',
      'The selected pieces are joined into one query; the catalog must cover the SQL patterns the system may need.',
    ],
  },
];

function FaithfulStylePreview({ variant, selected, onSelect, applying }) {
  const theme = variant.theme;
  const headerKey = theme.headerKey ?? 'signal';
  const [slideIndex, setSlideIndex] = useState(1);
  const slide = previewSlides[slideIndex];

  useEffect(() => setSlideIndex(1), [variant.name]);

  const variables = {
    '--style-body': theme.body,
    '--style-controls': theme.controls,
    '--style-button': theme.button,
    '--style-ink': theme.ink,
    '--style-accent': theme.accent,
    '--style-rule': theme.rule,
    '--controls-ink': theme.controlsInk,
    '--button-ink': theme.buttonInk,
    '--style-radius': `${theme.radius}px`,
    '--heading-font': theme.headingFont,
    '--body-font': theme.bodyFont,
    '--label-font': theme.labelFont,
    '--heading-weight': theme.headingWeight,
  };

  return (
    <article className="sqlharness-style-preview" data-style={theme.key} data-header={headerKey} style={variables} aria-label={`${variant.name} interactive carousel style`}>
      <button className="sqlharness-style-preview__select" type="button" data-selected={selected ? 'true' : 'false'} disabled={applying} onClick={onSelect}>
        {applying ? 'Applying…' : selected ? 'Using this style' : 'Use this style'}
      </button>
      <div className="sqlharness-style-preview__body" aria-live="polite">
        {headerKey === 'signal' ? <div className="sqlharness-style-preview__signal" /> : null}
        <h3>{slide.heading}</h3>
        {theme.showRule ? <div className="sqlharness-style-preview__rule" /> : null}
        <ul>
          {slide.points.map((point) => (
            <li key={point}>
              <span className="sqlharness-style-preview__bullet" aria-hidden="true">{theme.bullet}</span>
              <span>{point}</span>
            </li>
          ))}
        </ul>
      </div>
      <ControlBarPreview theme={theme} slideIndex={slideIndex} setSlideIndex={setSlideIndex} />
    </article>
  );
}

function ControlBarPreview({ theme, slideIndex, setSlideIndex }) {
  const current = slideIndex + 1;
  const total = previewSlides.length;
  const showPrevious = () => setSlideIndex((value) => Math.max(0, value - 1));
  const showNext = () => setSlideIndex((value) => Math.min(total - 1, value + 1));

  if (theme.controlsKey === 'chapters') {
    return (
      <div className="sqlharness-style-preview__controls" data-controls="chapters" aria-label="Preview slides">
        {previewSlides.map((slide, index) => (
          <button
            className={`sqlharness-style-preview__chapter${index === slideIndex ? ' sqlharness-style-preview__chapter--active' : ''}`}
            type="button"
            key={slide.shortLabel}
            aria-current={index === slideIndex ? 'page' : undefined}
            onClick={() => setSlideIndex(index)}
          >
            <span>0{index + 1}</span><strong>{slide.shortLabel}</strong>
          </button>
        ))}
      </div>
    );
  }

  if (theme.controlsKey === 'rail') {
    return (
      <div className="sqlharness-style-preview__controls" data-controls="rail">
        <div className="sqlharness-style-preview__rail-label"><strong>0{current}</strong><span>/ 0{total}</span></div>
        <div className="sqlharness-style-preview__rail" aria-label="Preview slides">
          {previewSlides.map((slide, index) => (
            <button type="button" key={slide.shortLabel} aria-label={`Show ${slide.shortLabel}`} aria-current={index === slideIndex ? 'true' : 'false'} onClick={() => setSlideIndex(index)} />
          ))}
        </div>
        <div className="sqlharness-style-preview__buttons"><button type="button" aria-label="Previous preview slide" disabled={slideIndex === 0} onClick={showPrevious}>←</button><button type="button" aria-label="Next preview slide" disabled={slideIndex === total - 1} onClick={showNext}>→</button></div>
      </div>
    );
  }

  if (theme.controlsKey === 'folio') {
    return (
      <div className="sqlharness-style-preview__controls" data-controls="folio">
        <button className="sqlharness-style-preview__folio-arrow" type="button" aria-label="Previous preview slide" disabled={slideIndex === 0} onClick={showPrevious}>←</button>
        <div className="sqlharness-style-preview__folio-number" aria-live="polite"><span>0{current}</span><i /><span>0{total}</span></div>
        <button className="sqlharness-style-preview__folio-arrow" type="button" aria-label="Next preview slide" disabled={slideIndex === total - 1} onClick={showNext}>→</button>
      </div>
    );
  }

  if (theme.controlsKey === 'split') {
    return (
      <div className="sqlharness-style-preview__controls" data-controls="split">
        <button className="sqlharness-style-preview__split-command" type="button" aria-label="Previous preview slide" disabled={slideIndex === 0} onClick={showPrevious}>←</button>
        <div className="sqlharness-style-preview__split-status" aria-live="polite"><strong>0{current}</strong><span>OF</span><strong>0{total}</strong></div>
        <button className="sqlharness-style-preview__split-command" type="button" aria-label="Next preview slide" disabled={slideIndex === total - 1} onClick={showNext}>→</button>
      </div>
    );
  }

  return (
    <div className="sqlharness-style-preview__controls" data-controls="utility">
      <span aria-live="polite">{current} / {total}</span>
      <div className="sqlharness-style-preview__buttons">
        <button type="button" aria-label="Previous preview slide" disabled={slideIndex === 0} onClick={showPrevious}>←</button>
        <button type="button" aria-label="Next preview slide" disabled={slideIndex === total - 1} onClick={showNext}>→</button>
      </div>
    </div>
  );
}

function ExplorationPanel({ active }) {
  const config = useParameter(PARAM_KEY);
  const controlVariants = config?.variants ?? [];
  const headerVariants = config?.headerVariants ?? [];
  const [focus, setFocus] = useState('header');
  const [index, setIndex] = useState(0);
  const [globals, updateGlobals] = useGlobals();
  const api = useStorybookApi();
  const [applying, setApplying] = useState(false);
  const variants = focus === 'header' ? headerVariants : controlVariants;

  useEffect(() => setIndex(0), [config, focus]);

  const show = (nextIndex) => {
    if (!variants.length) return;
    setIndex((nextIndex + variants.length) % variants.length);
  };

  useEffect(() => {
    if (!active || variants.length < 2) return undefined;
    const handleKeyDown = (event) => {
      if (event.key === 'ArrowLeft') setIndex((current) => (current - 1 + variants.length) % variants.length);
      if (event.key === 'ArrowRight') setIndex((current) => (current + 1) % variants.length);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [active, variants.length]);

  const variant = variants[index];
  const selectedControlStyle = globals.carouselControlStyle ?? 'chapters';
  const selectedHeaderStyle = globals.carouselHeaderStyle ?? 'signal';
  const selectedStyle = focus === 'header'
    ? selectedHeaderStyle === variant?.theme.headerKey
    : selectedControlStyle === variant?.theme.controlsKey;
  const previewVariant = variant ? {
    ...variant,
    theme: {
      ...variant.theme,
      controlsKey: focus === 'header' ? selectedControlStyle : variant.theme.controlsKey,
      headerKey: focus === 'controls' ? selectedHeaderStyle : variant.theme.headerKey,
    },
  } : null;

  const useStyle = async () => {
    setApplying(true);
    try {
      const selection = focus === 'header'
        ? { header: variant.theme.headerKey }
        : { controls: variant.theme.controlsKey };
      const response = await fetch('/__sqlharness/apply-carousel-style', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(selection),
      });
      if (!response.ok) throw new Error(await response.text());
      updateGlobals(focus === 'header'
        ? { carouselHeaderStyle: variant.theme.headerKey }
        : { carouselControlStyle: variant.theme.controlsKey });
      api.togglePanel(false);
    } finally {
      setApplying(false);
    }
  };

  return (
    <AddonPanel active={active} hasScrollbar={false}>
      <style>{styles}</style>
      {variant ? (
        <section className="sqlharness-explorations" aria-label="Carousel design explorations">
          <header className="sqlharness-explorations__header">
            <button className="sqlharness-explorations__button" type="button" onClick={() => show(index - 1)} aria-label="Previous design">←</button>
            <button className="sqlharness-explorations__button" type="button" onClick={() => show(index + 1)} aria-label="Next design">→</button>
            <div className="sqlharness-explorations__modes" aria-label="Exploration focus">
              <button className="sqlharness-explorations__mode" type="button" aria-pressed={focus === 'header'} onClick={() => setFocus('header')}>Top</button>
              <button className="sqlharness-explorations__mode" type="button" aria-pressed={focus === 'controls'} onClick={() => setFocus('controls')}>Bottom bar</button>
            </div>
            <div className="sqlharness-explorations__title">
              <strong>{index + 1} / {variants.length} · {variant.name}</strong>
              <span>{variant.lineage} · {variant.description}</span>
            </div>
            {variant.referenceUrl ? <a className="sqlharness-explorations__link" href={variant.referenceUrl} target="_blank" rel="noreferrer">Reference ↗</a> : null}
            <a className="sqlharness-explorations__link" href={config.figmaUrl} target="_blank" rel="noreferrer">Figma ↗</a>
          </header>
          <div className="sqlharness-explorations__stage" style={{ background: previewVariant.theme.canvas }}>
            <button className="sqlharness-explorations__arrow sqlharness-explorations__arrow--previous" type="button" onClick={() => show(index - 1)} aria-label="Previous design">←</button>
            <FaithfulStylePreview variant={previewVariant} selected={selectedStyle} onSelect={useStyle} applying={applying} />
            <button className="sqlharness-explorations__arrow sqlharness-explorations__arrow--next" type="button" onClick={() => show(index + 1)} aria-label="Next design">→</button>
          </div>
          <footer className="sqlharness-explorations__footer" aria-label="Choose a design">
            {variants.map((item, itemIndex) => (
              <button
                className="sqlharness-explorations__dot"
                type="button"
                key={item.name}
                aria-label={`Show ${item.name}`}
                aria-current={itemIndex === index ? 'true' : 'false'}
                onClick={() => show(itemIndex)}
              />
            ))}
          </footer>
        </section>
      ) : null}
    </AddonPanel>
  );
}

addons.register(ADDON_ID, () => {
  addons.add(PANEL_ID, {
    type: types.PANEL,
    title: 'Carousel explorations',
    paramKey: PARAM_KEY,
    render: ({ active }) => <ExplorationPanel active={active} />,
  });
});
