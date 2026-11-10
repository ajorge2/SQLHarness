(function () {
  const definitions = {
    carousel: {
      id: 'carousel',
      labId: 'system-notes-carousel',
      title: 'SQLHarness — Carousel component lab',
      pageHash: 'system',
      publishHref: 'index.html#system',
      defaultMode: 'controls',
      preview: { width: 780, height: 600 },
      selection: { type: 'json', key: 'sqlharnessCarouselStyle' },
      modes: {
        header: {
          styleParam: 'header',
          slotKey: 'sqlharnessHeaderSlot',
          savedKey: 'sqlharnessSavedHeaderVariants',
          seenKey: 'sqlharnessSeenHeaderVariants',
          session: 'header-v1',
        },
        controls: {
          styleParam: 'controls',
          slotKey: 'sqlharnessControlsSlot',
          savedKey: 'sqlharnessSavedControlsVariants',
          seenKey: 'sqlharnessSeenControlsVariants',
          session: 'controls-v1',
        },
        shell: {
          styleParam: 'shell',
          slotKey: 'sqlharnessShellSlot',
          savedKey: 'sqlharnessSavedShellVariants',
          seenKey: 'sqlharnessSeenShellVariants',
          session: 'shell-v1',
        },
      },
    },
    'stage-table': {
      id: 'stage-table',
      labId: 'stage-table',
      title: 'SQLHarness — Stage table component lab',
      pageHash: 'system',
      publishHref: 'index.html#system',
      defaultMode: 'table',
      preview: { width: 780, height: 600 },
      selection: { type: 'scalar' },
      modes: {
        table: {
          styleParam: 'table-style',
          selectionKey: 'sqlharnessStageTableStyle',
          defaultStyle: 'workflow-canvas',
          slotKey: 'sqlharnessStageTableSlot',
          savedKey: 'sqlharnessSavedStageTableVariants',
          seenKey: 'sqlharnessSeenStageTableVariants',
          session: 'stage-table-v1',
        },
      },
    },
    'query-example': {
      id: 'query-example',
      labId: 'query-example',
      title: 'SQLHarness — Query example component lab',
      pageHash: 'overview',
      publishHref: 'index.html#overview',
      defaultMode: 'query',
      preview: { width: 780, height: 820 },
      selection: { type: 'scalar' },
      modes: {
        query: {
          styleParam: 'query-style',
          selectionKey: 'sqlharnessQueryExampleStyle',
          defaultStyle: 'hierarchy-stack',
          slotKey: 'sqlharnessQueryExampleSlot',
          savedKey: 'sqlharnessSavedQueryExampleVariants',
          seenKey: 'sqlharnessSeenQueryExampleVariants',
          session: 'query-example-v1',
        },
      },
    },
    'workflow-comparison': {
      id: 'workflow-comparison',
      labId: 'workflow-comparison',
      title: 'SQLHarness — Workflow comparison lab',
      pageHash: 'workflow',
      publishHref: 'index.html#workflow-comparison-title',
      defaultMode: 'workflow',
      preview: { width: 1440, height: 1600 },
      selection: { type: 'scalar' },
      modes: {
        workflow: {
          styleParam: 'workflow-style',
          selectionKey: 'sqlharnessWorkflowComparisonStyle',
          defaultStyle: 'technical-folio',
          slotKey: 'sqlharnessWorkflowComparisonSlot',
          savedKey: 'sqlharnessSavedWorkflowComparisonVariants',
          seenKey: 'sqlharnessSeenWorkflowComparisonVariants',
          session: 'workflow-comparison-v1',
        },
      },
    },
    masthead: {
      id:'masthead',
      labId:'masthead',
      title:'SQLHarness — Page masthead lab',
      targetSelector:'.page-masthead',
      pageHash:'overview',
      publishHref:'index.html#overview',
      defaultMode:'masthead',
      preview:{ width:1200, height:320 },
      selection:{ type:'scalar' },
      modes:{
        masthead:{
          styleParam:'masthead-style',
          selectionKey:'sqlharnessMastheadStyle',
          defaultStyle:'brutalist-title-block',
          slotKey:'sqlharnessMastheadSlot',
          savedKey:'sqlharnessSavedMastheadVariants',
          seenKey:'sqlharnessSeenMastheadVariants',
          session:'masthead-v1',
        },
      },
    },
    'overview-heading': {
      id:'overview-heading',
      labId:'overview-heading',
      title:'SQLHarness — Overview heading lab',
      targetSelector:'#overview > h2',
      pageHash:'overview',
      publishHref:'index.html#overview',
      defaultMode:'section-heading',
      preview:{ width:1200, height:300 },
      selection:{ type:'scalar' },
      modes:{
        'section-heading':{
          styleParam:'section-heading-style',
          selectionKey:'sqlharnessOverviewHeadingStyle',
          defaultStyle:'pattern-shadow',
          slotKey:'sqlharnessOverviewHeadingSlot',
          savedKey:'sqlharnessSavedOverviewHeadingVariants',
          seenKey:'sqlharnessSeenOverviewHeadingVariants',
          session:'overview-heading-v1',
        },
      },
    },
    'overview-composition': {
      id:'overview-composition',
      labId:'overview-composition',
      title:'SQLHarness — Overview composition lab',
      targetSelector:'#overview > .hero-columns',
      pageHash:'overview',
      publishHref:'index.html#overview',
      defaultMode:'overview-layout',
      preview:{ width:1200, height:900 },
      selection:{ type:'scalar' },
      modes:{
        'overview-layout':{
          styleParam:'overview-layout-style',
          selectionKey:'sqlharnessOverviewCompositionStyle',
          defaultStyle:'drawer-stack',
          slotKey:'sqlharnessOverviewCompositionSlot',
          savedKey:'sqlharnessSavedOverviewCompositionVariants',
          seenKey:'sqlharnessSeenOverviewCompositionVariants',
          session:'overview-composition-v1',
        },
      },
    },
  };

  function workflowFragmentDefinition({ id, title, selector, mode, preview, defaultStyle = 'baseline' }) {
    const prefix = id
      .split('-')
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join('');
    return {
      id,
      labId:id,
      title,
      targetSelector:selector,
      pageHash:'workflow-comparison-title',
      publishHref:'index.html#workflow-comparison-title',
      defaultMode:mode,
      preview,
      selection:{ type:'scalar' },
      modes:{
        [mode]:{
          styleParam:`${mode}-style`,
          selectionKey:`sqlharness${prefix}Style`,
          defaultStyle,
          slotKey:`sqlharness${prefix}Slot`,
          savedKey:`sqlharnessSaved${prefix}Variants`,
          seenKey:`sqlharnessSeen${prefix}Variants`,
          session:`${id}-v1`,
        },
      },
    };
  }

  Object.assign(definitions, {
    'request-sources': workflowFragmentDefinition({
      id:'request-sources',
      title:'SQLHarness — Request sources lab',
      selector:'#explanation-request',
      mode:'request',
      defaultStyle:'isometric-blocks',
      preview:{ width:900, height:420 },
    }),
    'intent-explanation': workflowFragmentDefinition({
      id:'intent-explanation',
      title:'SQLHarness — Intent explanation lab',
      selector:'#explanation-intent',
      mode:'panel',
      defaultStyle:'stacked-cards',
      preview:{ width:760, height:980 },
    }),
    'retrieval-explanation': workflowFragmentDefinition({
      id:'retrieval-explanation',
      title:'SQLHarness — Retrieval explanation lab',
      selector:'#explanation-retrieval',
      mode:'panel',
      defaultStyle:'stacked-cards',
      preview:{ width:760, height:980 },
    }),
    'assembly-explanation': workflowFragmentDefinition({
      id:'assembly-explanation',
      title:'SQLHarness — Assembly explanation lab',
      selector:'#explanation-assembly',
      mode:'panel',
      defaultStyle:'split-outline',
      preview:{ width:760, height:420 },
    }),
    'authority-card': workflowFragmentDefinition({
      id:'authority-card',
      title:'SQLHarness — Authority card lab',
      selector:'#explanation-authority .fragment-workflow-step--authority',
      mode:'panel',
      defaultStyle:'command-trace',
      preview:{ width:760, height:440 },
    }),
    'result-explanation': workflowFragmentDefinition({
      id:'result-explanation',
      title:'SQLHarness — Result explanation lab',
      selector:'#explanation-result',
      mode:'panel',
      preview:{ width:760, height:420 },
    }),
    'intent-edges': workflowFragmentDefinition({
      id:'intent-edges',
      title:'SQLHarness — Intent graph edges lab',
      selector:'#example-intent .example-intent-edges',
      mode:'edges',
      defaultStyle:'ink-and-accent',
      preview:{ width:760, height:720 },
    }),
    'retrieval-example': workflowFragmentDefinition({
      id:'retrieval-example',
      title:'SQLHarness — Candidate ranking lab',
      selector:'#example-retrieval',
      mode:'example',
      defaultStyle:'index-cards',
      preview:{ width:760, height:1040 },
    }),
  });

  function resolve(id) {
    return definitions[id] || definitions.carousel;
  }

  function readSelection(definition, runtimeDefaults) {
    const selected = { ...(runtimeDefaults || {}) };
    if (definition.selection.type === 'json') {
      try {
        const stored = JSON.parse(localStorage.getItem(definition.selection.key) || '{}');
        const obsolete = stored.controls === 'chapters' && stored.header === 'overline';
        if (!obsolete) Object.assign(selected, stored);
      } catch (_error) {}
      return selected;
    }
    Object.entries(definition.modes).forEach(([mode, config]) => {
      selected[mode] = localStorage.getItem(config.selectionKey) || config.defaultStyle;
    });
    return selected;
  }

  function writeSelection(definition, selected) {
    if (definition.selection.type === 'json') {
      localStorage.setItem(definition.selection.key, JSON.stringify(selected));
      return;
    }
    Object.entries(definition.modes).forEach(([mode, config]) => {
      localStorage.setItem(config.selectionKey, selected[mode]);
    });
  }

  function previewUrl(definition, choice, highlight) {
    const params = new URLSearchParams({ 'component-lab': definition.id });
    Object.entries(definition.modes).forEach(([mode, config]) => {
      if (choice[mode]) params.set(config.styleParam, choice[mode]);
    });
    if (highlight) params.set('highlight', highlight);
    return `index.html?${params.toString()}#${definition.pageHash}`;
  }

  window.SQLHarnessComponentLab = {
    definitions,
    previewUrl,
    readSelection,
    resolve,
    writeSelection,
  };
})();
