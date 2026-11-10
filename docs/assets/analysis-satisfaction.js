/* Independent, read-only comparison controls for the reader preview. */
(() => {
  const comparison = document.querySelector('.system-columns');
  if (!comparison) return;

  const stages = {
    request: 'request',
    intent: 'intent graph',
    retrieval: 'fragment retrieval',
    assembly: 'query assembly',
    authority: 'authority boundary',
    result: 'result',
  };
  const controls = [...comparison.querySelectorAll('[data-workflow-hover]')];
  const targets = [...comparison.querySelectorAll('[data-workflow-match]')];
  const clear = document.querySelector('.clear-workflow-selection');
  const status = document.querySelector('#comparison-status');
  const buttons = new Map();
  let previewStage = '';

  const refresh = () => {
    const active = comparison.dataset.workflowActive || '';
    buttons.forEach((button, stage) => {
      button.setAttribute('aria-pressed', String(active === stage));
      button.textContent = active === stage ? 'Clear comparison' : 'Compare';
      button.setAttribute('aria-label', active === stage
        ? `Clear ${stages[stage]} comparison`
        : `Compare ${stages[stage]} with the algorithm`);
    });
    targets.forEach((target) => {
      target.classList.toggle('workflow-match--preview', !active && target.dataset.workflowMatch === previewStage);
    });
    clear.hidden = !active;
  };

  const select = (stage) => {
    const next = comparison.dataset.workflowActive === stage ? '' : stage;
    if (next) comparison.dataset.workflowActive = next;
    else delete comparison.dataset.workflowActive;
    status.textContent = next ? `${stages[next]} comparison selected.` : 'Comparison cleared. All stages remain visible.';
    refresh();
  };

  const clearSelection = () => {
    const active = comparison.dataset.workflowActive;
    if (!active) return;
    delete comparison.dataset.workflowActive;
    previewStage = '';
    status.textContent = 'Comparison cleared. All stages remain visible.';
    refresh();
    return active;
  };

  targets.forEach((target, index) => {
    target.id = `algorithm-${target.dataset.workflowMatch}-${index}`;
    target.tabIndex = -1;
  });

  controls.forEach((control) => {
    const stage = control.dataset.workflowHover;
    const label = stages[stage];
    const matches = targets.filter((target) => target.dataset.workflowMatch === stage);
    control.id = `example-${stage}`;
    control.removeAttribute('role');
    control.removeAttribute('tabindex');
    control.tabIndex = -1;
    control.style.scrollMarginTop = '48px';

    const actions = document.createElement('div');
    actions.className = 'stage-actions';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'stage-compare';
    button.textContent = 'Compare';
    button.setAttribute('aria-label', `Compare ${label} with the algorithm`);
    button.setAttribute('aria-pressed', 'false');
    button.setAttribute('aria-controls', matches.map((target) => target.id).join(' '));
    button.addEventListener('click', () => select(stage));
    const preview = (value) => {
      previewStage = value;
      refresh();
    };
    button.addEventListener('pointerenter', () => preview(stage));
    button.addEventListener('pointerleave', () => preview(''));
    button.addEventListener('focus', () => preview(stage));
    button.addEventListener('blur', () => preview(''));
    actions.append(button);
    buttons.set(stage, button);

    const link = document.createElement('a');
    link.className = 'counterpart-link';
    link.href = `#${matches[0].id}`;
    link.textContent = 'See algorithm ↓';
    link.setAttribute('aria-label', `See the algorithm for ${label}`);
    actions.append(link);
    control.before(actions);

    control.addEventListener('click', (event) => {
      // Selecting or copying SQL must never activate a comparison.
      if (event.target.closest('code, pre, a, button, input, summary')) return;
      if (!window.getSelection()?.isCollapsed) return;
      select(stage);
    });

    const backActions = document.createElement('div');
    backActions.className = 'stage-actions';
    const back = document.createElement('a');
    back.className = 'counterpart-link';
    back.href = `#${control.id}`;
    back.textContent = 'Back to example ↑';
    back.setAttribute('aria-label', `Back to the ${label} example`);
    backActions.append(back);
    matches[0].before(backActions);
  });

  clear.addEventListener('click', () => {
    const previous = clearSelection();
    buttons.get(previous)?.focus({ preventScroll: true });
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && comparison.dataset.workflowActive) {
      event.preventDefault();
      clearSelection();
    }
  });
  comparison.addEventListener('click', (event) => {
    const link = event.target.closest('.counterpart-link');
    if (!link) return;
    document.getElementById(link.hash.slice(1))?.focus({ preventScroll: true });
  });
  refresh();
})();
