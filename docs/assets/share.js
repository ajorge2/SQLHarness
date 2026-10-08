const content = document.querySelector("#brief-content");
const count = document.querySelector("#brief-count");
const copyButton = document.querySelector("#copy-brief");
const copyStatus = document.querySelector("#copy-status");
let rawBrief = "";

function inlineMarkdown(value) {
  const fragment = document.createDocumentFragment();
  const pieces = value.split(/(\*\*[^*]+\*\*)/g);
  pieces.forEach((piece) => {
    if (piece.startsWith("**") && piece.endsWith("**")) {
      const strong = document.createElement("strong");
      strong.textContent = piece.slice(2, -2);
      fragment.append(strong);
    } else {
      fragment.append(document.createTextNode(piece));
    }
  });
  return fragment;
}

function renderMarkdown(markdown) {
  const lines = markdown.split("\n");
  const output = document.createDocumentFragment();
  let list = null;
  let listType = null;

  function closeList() {
    if (list) output.append(list);
    list = null;
    listType = null;
  }

  lines.forEach((line) => {
    const ordered = line.match(/^\d+\.\s+(.*)$/);
    const unordered = line.match(/^-\s+(.*)$/);
    if (ordered || unordered) {
      const nextType = ordered ? "ol" : "ul";
      if (!list || listType !== nextType) {
        closeList();
        list = document.createElement(nextType);
        listType = nextType;
      }
      const item = document.createElement("li");
      item.append(inlineMarkdown((ordered || unordered)[1]));
      list.append(item);
      return;
    }

    closeList();
    if (!line.trim()) return;
    const heading = line.match(/^(#{1,2})\s+(.*)$/);
    const node = document.createElement(heading ? `h${heading[1].length}` : "p");
    node.append(inlineMarkdown(heading ? heading[2] : line));
    output.append(node);
  });
  closeList();
  content.replaceChildren(output);
}

async function copyBrief() {
  if (!rawBrief) return;
  try {
    await navigator.clipboard.writeText(rawBrief);
    copyStatus.textContent = "Copied — ready to paste into Gemini";
    copyButton.textContent = "Copied";
    window.setTimeout(() => {
      copyButton.textContent = "Copy complete brief";
      copyStatus.textContent = "";
    }, 3500);
  } catch (error) {
    copyStatus.textContent = "Copy failed — use Download Markdown";
  }
}

async function loadBrief() {
  try {
    const response = await fetch("share-brief.md");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    rawBrief = await response.text();
    renderMarkdown(rawBrief);
    count.textContent = `${rawBrief.trim().split(/\s+/).length.toLocaleString()} words`;
  } catch (error) {
    const message = document.createElement("p");
    message.className = "brief-error";
    message.textContent = "The brief could not be loaded. Serve the docs directory through a local web server.";
    content.replaceChildren(message);
    count.textContent = "Unavailable";
  }
}

copyButton.addEventListener("click", copyBrief);
loadBrief();
