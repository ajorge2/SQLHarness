(() => {
  const html = document.documentElement;
  if (
    html.classList.contains('component-lab') ||
    html.classList.contains('workflow-fragment-preview') ||
    html.classList.contains('workflow-lab-preview')
  ) return;

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const stickyStagesEnabled = window.matchMedia('(min-width: 1361px)');

  const createStickyTrack = (nodes, name) => {
    const stageNodes = (Array.isArray(nodes) ? nodes : [nodes]).filter(Boolean);
    const firstNode = stageNodes[0];
    if (!firstNode?.parentNode) return null;

    const track = document.createElement('div');
    const content = document.createElement('div');
    track.className = `scroll-sticky-track scroll-sticky-track--${name}`;
    content.className = 'scroll-sticky-content';
    firstNode.parentNode.insertBefore(track, firstNode);
    track.appendChild(content);
    stageNodes.forEach((node) => content.appendChild(node));
    return { track, content };
  };

  const overviewNode = document.querySelector('#overview > .hero-columns');
  const systemNode = document.querySelector('#system > .system-columns');
  const systemPrimary = systemNode?.querySelector(':scope > .system-primary');
  const systemDetails = systemNode?.querySelector(':scope > .system-details-page');
  const workflowReveal = document.querySelector('#workflow');
  const closingNode = document.querySelector('.closing-columns');

  const overviewStage = createStickyTrack(overviewNode, 'overview');
  const systemStage = createStickyTrack([systemPrimary, systemDetails], 'system');
  const workflowStage = createStickyTrack(workflowReveal, 'workflow');
  const closingStage = createStickyTrack(closingNode, 'closing');

  const pairs = [
    {
      node: overviewNode,
      stage: overviewStage,
      headers: [document.querySelector('#overview > h2')],
      start: 0.9,
      finish: 0.28,
    },
    {
      node: systemNode,
      stage: systemStage,
      headers: [document.querySelector('#system > h2')],
      start: 0.94,
      finish: 0.14,
    },
    {
      node: closingNode,
      stage: closingStage,
      start: 0.94,
      finish: 0.14,
    },
  ].filter(({ node }) => node);
  const workflowHeading = document.querySelector('.workflow-comparison-heading');

  if (!pairs.length && !workflowReveal) return;

  html.classList.add('page-convergence-enabled', 'sticky-scroll-stages-enabled');

  let framePending = false;

  const clamp = (value, min, max) => Math.min(Math.max(value, min), max);
  const smoothstep = (value) => value * value * (3 - 2 * value);

  const viewportProgress = (node, start, finish, viewportHeight) => {
    const startLine = viewportHeight * start;
    const finishLine = viewportHeight * finish;
    const rect = node.getBoundingClientRect();
    return clamp((startLine - rect.top) / (startLine - finishLine), 0, 1);
  };

  const update = () => {
    framePending = false;
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight;

    pairs.forEach(({ node, stage, headers = [], start, finish }) => {
      if (stage) {
        const reservedHeight = Number.parseFloat(stage.track.dataset.stickyReservedHeight) || 0;
        const stageHeight = Math.max(stage.content.offsetHeight, reservedHeight);
        stage.track.style.setProperty('--sticky-stage-content-height', `${stageHeight}px`);
      }
      const rawProgress = reducedMotion.matches
        ? 1
        : viewportProgress(stage?.track || node, start, finish, viewportHeight);
      const progress = smoothstep(rawProgress).toFixed(4);
      node.style.setProperty('--page-convergence', progress);
      headers.filter(Boolean).forEach((header) => {
        header.style.setProperty('--page-convergence', progress);
      });
    });

    if (workflowReveal) {
      if (workflowStage) {
        const reservedHeight = Number.parseFloat(workflowStage.track.dataset.stickyReservedHeight) || 0;
        const stageHeight = Math.max(workflowStage.content.offsetHeight, reservedHeight);
        workflowStage.track.style.setProperty('--sticky-stage-content-height', `${stageHeight}px`);
      }
      const rawProgress = reducedMotion.matches
        ? 1
        : viewportProgress(workflowStage?.track || workflowReveal, 0.94, 0.28, viewportHeight);
      const progress = smoothstep(rawProgress).toFixed(4);
      workflowReveal.style.setProperty('--workflow-reveal', progress);
      workflowHeading?.style.setProperty('--workflow-reveal', progress);
    }
  };

  const requestUpdate = () => {
    if (framePending) return;
    framePending = true;
    window.requestAnimationFrame(update);
  };

  window.addEventListener('scroll', requestUpdate, { passive: true });
  window.addEventListener('resize', requestUpdate, { passive: true });
  reducedMotion.addEventListener?.('change', requestUpdate);
  stickyStagesEnabled.addEventListener?.('change', requestUpdate);
  update();
})();
