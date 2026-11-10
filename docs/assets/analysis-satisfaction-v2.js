/* The carousel pairs each example with its explanation. */
(() => {
  const workflow = document.querySelector('.workflow-stage-list');
  if (!workflow) return;
  if (document.documentElement.classList.contains('workflow-lab-preview')) {
    document.body.append(workflow);
    window.requestAnimationFrame(() => window.scrollTo(0, 0));
  }
  const rows = [...workflow.querySelectorAll('.workflow-stage-row')];
  const headings = workflow.querySelector('.workflow-column-headings');
  const viewport = document.createElement('div');
  const track = document.createElement('div');
  const controls = document.createElement('nav');
  const previous = document.createElement('button');
  const next = document.createElement('button');
  const position = document.createElement('span');
  const dots = document.createElement('div');
  workflow.classList.add('workflow-stage-carousel');
  viewport.className = 'workflow-carousel-viewport';
  track.className = 'workflow-carousel-track';
  controls.className = 'workflow-carousel-controls';
  controls.setAttribute('aria-label', 'Workflow stage navigation');
  previous.type = 'button';
  previous.className = 'workflow-carousel-arrow workflow-carousel-arrow--previous';
  previous.setAttribute('aria-label', 'Show previous workflow stage');
  previous.textContent = '↑';
  next.type = 'button';
  next.className = 'workflow-carousel-arrow workflow-carousel-arrow--next';
  next.setAttribute('aria-label', 'Show next workflow stage');
  next.textContent = '↓';
  position.className = 'workflow-carousel-position';
  position.setAttribute('aria-live', 'polite');
  dots.className = 'workflow-carousel-dots';
  dots.setAttribute('aria-label', 'Choose a workflow stage');
  rows.forEach((row) => track.append(row));
  viewport.append(track);
  headings.after(viewport);
  controls.append(previous, position, dots, next);
  workflow.append(controls);

  window.localStorage.removeItem('sqlharnessWorkflowStageIndex');
  let stageIndex = 0;
  const stageDots = rows.map((row, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'workflow-carousel-dot';
    button.setAttribute('aria-label', `Show ${row.querySelector('.workflow-stage-title').textContent.trim()}`);
    button.addEventListener('click', () => showStage(index));
    dots.append(button);
    return button;
  });

  function measureStage() {
    const active = rows[stageIndex];
    if (!active) return;
    const tallestStage = Math.max(...rows.map((row) => row.scrollHeight));
    const activeStageHeight = active.scrollHeight;
    const workflowChromeHeight = Math.max(0, workflow.offsetHeight - viewport.offsetHeight);
    const reservedWorkflowHeight = workflowChromeHeight + tallestStage;
    const stickyTrack = workflow.closest('.scroll-sticky-track--workflow');
    if (stickyTrack) {
      stickyTrack.dataset.stickyReservedHeight = String(reservedWorkflowHeight);
      stickyTrack.style.setProperty('--sticky-stage-content-height', `${reservedWorkflowHeight}px`);
    }
    viewport.style.height = `${activeStageHeight}px`;
    track.style.transform = `translateY(-${active.offsetTop}px)`;
  }

  function animateStage(active, direction) {
    if (!active || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const distance = direction < 0 ? -1 : 1;
    const style = workflow.dataset.workflowStyle || 'baseline';
    const motions = {
      baseline: {
        frames: [{ opacity:.55, transform:`translateY(${12 * distance}px)` }, { opacity:1, transform:'translateY(0)' }],
        options: { duration:260, easing:'ease-out' },
      },
      'paired-rail': {
        frames: [{ opacity:.35, transform:`translateY(${28 * distance}px)` }, { opacity:1, transform:'translateY(0)' }],
        options: { duration:420, easing:'cubic-bezier(.22,.61,.36,1)' },
      },
      'completion-path': {
        frames: [{ opacity:.35, transform:`translateY(${18 * distance}px) scale(.985)` }, { opacity:1, transform:'translateY(0) scale(1)' }],
        options: { duration:520, easing:'cubic-bezier(.16,1,.3,1)' },
      },
      'process-cards': {
        frames: [{ opacity:0, transform:`translateY(${24 * distance}px) rotate(${.35 * distance}deg)` }, { opacity:1, transform:'translateY(0) rotate(0)' }],
        options: { duration:380, easing:'cubic-bezier(.2,.8,.2,1)' },
      },
      'numbered-spine': {
        frames: [{ opacity:.45, clipPath:direction < 0 ? 'inset(0 0 100% 0)' : 'inset(100% 0 0 0)' }, { opacity:1, clipPath:'inset(0 0 0 0)' }],
        options: { duration:300, easing:'cubic-bezier(.4,0,.2,1)' },
      },
      'process-pillars': {
        frames: [{ opacity:.45, transform:'scaleX(.965)' }, { opacity:1, transform:'scaleX(1)' }],
        options: { duration:460, easing:'cubic-bezier(.33,1,.68,1)' },
      },
      'split-comparison': {
        frames: [{ opacity:.6, clipPath:direction < 0 ? 'inset(0 0 0 48%)' : 'inset(0 48% 0 0)' }, { opacity:1, clipPath:'inset(0 0 0 0)' }],
        options: { duration:420, easing:'cubic-bezier(.65,0,.35,1)' },
      },
      'revision-log': {
        frames: [{ opacity:.25, transform:`translateY(${10 * distance}px)` }, { opacity:1, transform:'translateY(0)' }],
        options: { duration:280, easing:'steps(4,end)' },
      },
      'blueprint-grid': {
        frames: [{ opacity:.25, transform:'scale(.97)', filter:'blur(2px)' }, { opacity:1, transform:'scale(1)', filter:'blur(0)' }],
        options: { duration:440, easing:'cubic-bezier(.22,.61,.36,1)' },
      },
      'alternating-ledger': {
        frames: [{ opacity:.35, transform:`translateX(${22 * distance}px)` }, { opacity:1, transform:'translateX(0)' }],
        options: { duration:360, easing:'cubic-bezier(.34,1.56,.64,1)' },
      },
      'technical-folio': {
        frames: [{ opacity:0 }, { opacity:1 }],
        options: { duration:500, easing:'linear' },
      },
    };
    const motion = motions[style] || motions.baseline;
    active.getAnimations().forEach((animation) => animation.cancel());
    active.animate(motion.frames, { ...motion.options, fill:'both' });
  }

  function showStage(nextIndex, { animate = true } = {}) {
    const previousIndex = stageIndex;
    stageIndex = (nextIndex + rows.length) % rows.length;
    const direction = stageIndex < previousIndex ? -1 : 1;
    rows.forEach((row, index) => {
      const active = index === stageIndex;
      row.classList.toggle('is-carousel-active', active);
      row.setAttribute('aria-hidden', String(!active));
      row.inert = !active;
    });
    stageDots.forEach((dot, index) => dot.setAttribute('aria-current', String(index === stageIndex)));
    position.textContent = `${stageIndex + 1} / ${rows.length}`;
    previous.disabled = stageIndex === 0;
    next.disabled = stageIndex === rows.length - 1;
    window.requestAnimationFrame(() => {
      measureStage();
      if (animate) animateStage(rows[stageIndex], direction);
    });
  }

  previous.addEventListener('click', () => showStage(stageIndex - 1));
  next.addEventListener('click', () => showStage(stageIndex + 1));
  window.addEventListener('resize', measureStage, { passive: true });
  if (typeof ResizeObserver !== 'undefined') {
    const stageSizeObserver = new ResizeObserver(measureStage);
    rows.forEach((row) => stageSizeObserver.observe(row));
  }
  showStage(stageIndex, { animate:false });

  const intent = workflow.querySelector('[data-stage="intent"]');
  const connector = intent?.querySelector('.intent-output-connector');
  const finalStep = intent?.querySelector('[data-intent-output-source]');
  const graph = intent?.querySelector('.example-intent-graph');
  const output = intent?.querySelector('.workflow-stage-example');
  const explanation = intent?.querySelector('.workflow-stage-explanation');
  if (!connector || !finalStep || !graph || !output || !explanation) return;
  const line = connector.querySelector('.intent-output-line');
  const head = connector.querySelector('.intent-output-head');
  const verb = connector.querySelector('.intent-output-verb');

  function drawHandoff() {
    const bounds = connector.getBoundingClientRect();
    if (!bounds.width || !bounds.height) return;
    connector.setAttribute('viewBox', `0 0 ${bounds.width} ${bounds.height}`);
    if (window.matchMedia('(max-width: 760px)').matches) {
      const x = bounds.width / 2;
      const y = bounds.height - 7;
      line.setAttribute('d', `M ${x} 2 L ${x} ${y}`);
      head.setAttribute('d', `M ${x - 5} ${y - 5} L ${x} ${y} L ${x + 5} ${y - 5}`);
      verb.textContent = '';
      return;
    }
    const card = finalStep.getBoundingClientRect();
    const inputPanel = explanation.getBoundingClientRect();
    const panel = output.getBoundingClientRect();
    const graphBox = graph.getBoundingClientRect();
    const panelInset = parseFloat(getComputedStyle(workflow).getPropertyValue('--workflow-panel-inset')) || 0;
    const from = { x: inputPanel.right - bounds.left + panelInset + 8, y: card.top + card.height / 2 - bounds.top };
    const to = {
      x: panel.left - bounds.left - panelInset - 8,
      y: Math.max(graphBox.top + 14 - bounds.top, Math.min(from.y, graphBox.bottom - 14 - bounds.top)),
    };
    const middleX = (from.x + to.x) / 2;
    line.setAttribute('d', `M ${from.x} ${from.y} L ${middleX} ${from.y} L ${middleX} ${to.y} L ${to.x} ${to.y}`);
    head.setAttribute('d', `M ${to.x - 5} ${to.y - 5} L ${to.x} ${to.y} L ${to.x - 5} ${to.y + 5}`);
    verb.textContent = 'produces';
    verb.setAttribute('x', middleX);
    verb.setAttribute('y', from.y - 9);
  }
  let frame = 0;
  function scheduleHandoff() {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(drawHandoff);
  }
  if (typeof ResizeObserver !== 'undefined') {
    const observer = new ResizeObserver(scheduleHandoff);
    [intent, finalStep, output].forEach((element) => observer.observe(element));
  }
  window.addEventListener('resize', scheduleHandoff, { passive: true });
  drawHandoff();
})();
