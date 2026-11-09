/* Pairing carries the explanation; direct interaction adds optional focus. */
(() => {
  const workflow = document.querySelector('.workflow-stage-list');
  if (!workflow) return;
  const rows = [...workflow.querySelectorAll('.workflow-stage-row')];
  const clear = document.querySelector('.clear-workflow-selection');
  const status = document.querySelector('#comparison-status');
  let focused = '';

  function update() {
    if (focused) workflow.dataset.focusedStage = focused;
    else delete workflow.dataset.focusedStage;
    rows.forEach((row) => {
      const active = row.dataset.stage === focused;
      row.classList.toggle('is-focused', active);
      row.querySelector('.stage-focus-toggle').setAttribute('aria-pressed', String(active));
    });
    clear.hidden = !focused;
  }
  function toggle(row) {
    focused = focused === row.dataset.stage ? '' : row.dataset.stage;
    status.textContent = focused
      ? `${row.querySelector('.workflow-stage-title').textContent.trim()} explanation focused.`
      : 'Focus cleared.';
    update();
  }
  rows.forEach((row) => {
    const source = row.querySelector('[data-workflow-hover]');
    const example = row.querySelector('.workflow-stage-example');
    const button = row.querySelector('.stage-focus-toggle');
    button.addEventListener('click', () => toggle(row));
    button.addEventListener('focus', () => row.classList.add('is-previewed'));
    button.addEventListener('blur', () => row.classList.remove('is-previewed'));
    example.addEventListener('pointerenter', () => row.classList.add('is-previewed'));
    example.addEventListener('pointerleave', () => row.classList.remove('is-previewed'));
    source.addEventListener('click', (event) => {
      if (event.target.closest('code, pre, a, button, input, summary, .example-data-context')) return;
      if (!window.getSelection()?.isCollapsed) return;
      toggle(row);
    });
  });
  function reset() {
    if (!focused) return;
    focused = '';
    status.textContent = 'Focus cleared.';
    update();
  }
  clear.addEventListener('click', () => {
    const active = rows.find((row) => row.dataset.stage === focused);
    reset();
    active?.querySelector('.stage-focus-toggle').focus({ preventScroll: true });
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && focused) {
      event.preventDefault();
      reset();
    }
  });
  update();

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
    const from = { x: inputPanel.left - bounds.left - panelInset - 8, y: card.top + card.height / 2 - bounds.top };
    const to = {
      x: panel.right - bounds.left + panelInset + 8,
      y: Math.max(graphBox.top + 14 - bounds.top, Math.min(from.y, graphBox.bottom - 14 - bounds.top)),
    };
    const middleX = (from.x + to.x) / 2;
    line.setAttribute('d', `M ${from.x} ${from.y} L ${middleX} ${from.y} L ${middleX} ${to.y} L ${to.x} ${to.y}`);
    head.setAttribute('d', `M ${to.x + 5} ${to.y - 5} L ${to.x} ${to.y} L ${to.x + 5} ${to.y + 5}`);
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
