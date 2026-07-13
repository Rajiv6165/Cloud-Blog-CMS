// ─── Dark mode ───────────────────────────────────────────────────────
const html = document.documentElement;
const moonIcon = document.getElementById('icon-moon');
const sunIcon  = document.getElementById('icon-sun');

function applyTheme(dark) {
  if (dark) {
    html.classList.add('dark');
    if (moonIcon) moonIcon.style.display = 'none';
    if (sunIcon)  sunIcon.style.display  = 'block';
  } else {
    html.classList.remove('dark');
    if (moonIcon) moonIcon.style.display = 'block';
    if (sunIcon)  sunIcon.style.display  = 'none';
  }
}

// Eye toggle and setup for High Contrast
(function() {
  const isHighContrast = localStorage.getItem('high-contrast') === 'true';
  if (isHighContrast) {
    html.classList.add('high-contrast');
  }
})();

function toggleTheme() {
  const isDark = html.classList.contains('dark');
  localStorage.setItem('theme', isDark ? 'light' : 'dark');
  applyTheme(!isDark);
}

// Apply saved preference immediately (prevents flash)
(function() {
  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  applyTheme(saved ? saved === 'dark' : prefersDark);
})();

// Helper to get CSRF Token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// HTML Escaper
function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Simple stacked diff generator
function generateDiffHtml(original, improved) {
  let html = '<div class="space-y-3">';
  html += '<div><span class="text-[9px] font-bold text-red-500 uppercase tracking-wider block mb-1">Original Content</span>';
  html += '<div class="bg-red-950/20 text-red-300/80 p-2.5 rounded border border-red-900/30 line-through text-[11px] font-mono leading-relaxed select-none">' + escapeHtml(original) + '</div></div>';
  html += '<div><span class="text-[9px] font-bold text-green-500 uppercase tracking-wider block mb-1">AI Improved Content</span>';
  html += '<div class="bg-green-950/20 text-green-300 p-2.5 rounded border border-green-900/30 text-[11px] font-mono leading-relaxed">' + escapeHtml(improved) + '</div></div>';
  html += '</div>';
  return html;
}

// ─── DOM Content Loaded Handlers ─────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Sync the theme icons after DOM load
  const isDark = html.classList.contains('dark');
  applyTheme(isDark);

  // ─── Mobile menu ─────────────────────────────────────────────────────
  const menuBtn = document.getElementById('mobile-menu-btn');
  const mobileMenu = document.getElementById('mobile-menu');
  let firstFocusable = null;
  let lastFocusable = null;

  function focusTrapListener(e) {
    if (e.key === 'Tab') {
      const activeEl = document.activeElement;
      if (e.shiftKey) {
        if (activeEl === firstFocusable) {
          lastFocusable.focus();
          e.preventDefault();
        }
      } else {
        if (activeEl === lastFocusable) {
          firstFocusable.focus();
          e.preventDefault();
        }
      }
    } else if (e.key === 'Escape') {
      window.toggleMobileMenu();
    }
  }

  window.toggleMobileMenu = function() {
    const menu = document.getElementById('mobile-menu');
    if (!menu) return;
    const isOpen = menu.classList.toggle('open');
    const btn = document.getElementById('mobile-menu-btn');
    if (btn) {
      btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    }

    if (isOpen) {
      const focusables = menu.querySelectorAll('a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), [tabindex="0"]');
      if (focusables.length > 0) {
        firstFocusable = focusables[0];
        lastFocusable = focusables[focusables.length - 1];
        firstFocusable.focus();
        menu.addEventListener('keydown', focusTrapListener);
      }
    } else {
      menu.removeEventListener('keydown', focusTrapListener);
      const btn = document.getElementById('mobile-menu-btn');
      if (btn) {
        btn.focus();
      }
    }
  }

  // ─── Back to top ─────────────────────────────────────────────────────
  const backToTop = document.getElementById('back-to-top');
  if (backToTop) {
    window.addEventListener('scroll', () => {
      backToTop.classList.toggle('visible', window.scrollY > 400);
    }, { passive: true });

    backToTop.addEventListener('click', () => {
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      window.scrollTo({
        top: 0,
        behavior: prefersReducedMotion ? 'auto' : 'smooth'
      });
    });
  }

  // ─── Reading progress bar ─────────────────────────────────────────────
  const progressBar = document.getElementById('reading-progress');
  if (progressBar) {
    window.addEventListener('scroll', () => {
      const doc   = document.documentElement;
      const total = doc.scrollHeight - doc.clientHeight;
      const pct   = total > 0 ? (window.scrollY / total) * 100 : 0;
      progressBar.style.width = Math.min(pct, 100) + '%';
    }, { passive: true });
  }

  // ─── Auto table of contents ──────────────────────────────────────────
  const tocContainer = document.getElementById('toc-links');
  if (tocContainer) {
    const headings = document.querySelectorAll('.prose-content h2, .prose-content h3');
    headings.forEach((h, i) => {
      if (!h.id) h.id = 'heading-' + i;
      const a = document.createElement('a');
      a.href = '#' + h.id;
      a.textContent = h.textContent;
      a.className = 'transition-colors duration-200 border-l-2 border-transparent';
      a.style.paddingLeft = h.tagName === 'H3' ? '20px' : '10px';
      a.style.fontSize    = h.tagName === 'H3' ? '13px' : '14px';
      tocContainer.appendChild(a);
    });

    // Highlight active heading on scroll
    const tocLinks = tocContainer.querySelectorAll('a');
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          tocLinks.forEach(link => {
            const isActive = link.getAttribute('href') === `#${entry.target.id}`;
            link.classList.toggle('active', isActive);
            if (isActive) {
              link.style.color = 'var(--accent)';
              link.style.borderLeftColor = 'var(--accent)';
            } else {
              link.style.color = '';
              link.style.borderLeftColor = '';
            }
          });
        }
      });
    }, { rootMargin: '-20% 0px -60% 0px' });
    headings.forEach(h => observer.observe(h));
  }

  // ─── Slug auto-generation from title ─────────────────────────────────
  const titleInput = document.getElementById('id_title');
  const slugInput  = document.getElementById('id_slug');
  if (titleInput && slugInput && !slugInput.value) {
    titleInput.addEventListener('input', () => {
      slugInput.value = titleInput.value
        .toLowerCase()
        .trim()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_-]+/g, '-')
        .replace(/^-+|-+$/g, '');
    });
  }

  // ─── Live character counter for summary ──────────────────────────────
  const summaryInput   = document.getElementById('id_summary');
  const summaryCounter = document.getElementById('summary-counter');
  if (summaryInput && summaryCounter) {
    const maxLen = 300;
    function updateCounter() {
      const remaining = maxLen - summaryInput.value.length;
      summaryCounter.textContent = remaining + ' characters remaining';
      summaryCounter.style.color = remaining < 30 ? '#ef4444' : 'var(--text-muted)';
    }
    summaryInput.addEventListener('input', updateCounter);
    updateCounter();
  }

  // ─── EasyMDE rich text editor & AI Assistant Integration ─────────────
  let currentEditor = null;
  const contentTextarea = document.getElementById('id_content');
  if (contentTextarea && typeof EasyMDE !== 'undefined') {
    const easyMDE = new EasyMDE({
      element: contentTextarea,
      spellChecker: false,
      autosave: { enabled: true, delay: 3000, uniqueId: 'blog-post-content' },
      toolbar: [
        'bold', 'italic', 'heading', '|',
        'quote', 'unordered-list', 'ordered-list', '|',
        'link', 'image', 'code', '|',
        'preview', 'side-by-side', 'fullscreen', '|',
        {
          name: "ai-assistant",
          action: function(editor) {
            window.toggleAIPanel(editor);
          },
          className: "fa fa-magic !text-purple-500 dark:!text-purple-400",
          title: "AI Assistant",
        },
        '|',
        'guide'
      ],
      placeholder: 'Write your story…',
      status: ['lines', 'words'],
    });
    currentEditor = easyMDE;
    window.easyMDE = easyMDE;
  }

  // Dismiss flash messages
  document.querySelectorAll('[data-dismiss]').forEach(btn => {
    btn.addEventListener('click', () => {
      const msg = btn.closest('[data-message]');
      if (msg) msg.remove();
    });
  });

  // ─── AI Assistant Panel Logic ───────────────────────────────────────
  const aiPanel = document.getElementById('ai-assistant-panel');
  const closePanelBtn = document.getElementById('close-ai-panel');
  const selectionStatus = document.getElementById('ai-selection-status');
  const tokenEstimate = document.getElementById('ai-token-estimate');

  const btnImprove = document.getElementById('ai-btn-improve');
  const btnGrammar = document.getElementById('ai-btn-grammar');
  const btnContinue = document.getElementById('ai-btn-continue');
  const btnTone = document.getElementById('ai-btn-tone');
  const toneSelect = document.getElementById('ai-tone-select');

  const loadingContainer = document.getElementById('ai-loading-container');
  const errorContainer = document.getElementById('ai-error-container');
  const resultSection = document.getElementById('ai-result-section');
  const previewContent = document.getElementById('ai-preview-content');
  const diffContent = document.getElementById('ai-diff-content');

  const tabResult = document.getElementById('tab-result');
  const tabDiff = document.getElementById('tab-diff');

  const btnApply = document.getElementById('ai-btn-apply');
  const btnDiscard = document.getElementById('ai-btn-discard');

  let activeAction = "";
  let textOriginal = "";
  let textResult = "";
  let isSelectionUsed = false;

  window.toggleAIPanel = function(editor = currentEditor) {
    if (!aiPanel) return;
    currentEditor = editor;
    
    // Toggle class
    const isOpen = aiPanel.classList.contains('open');
    if (isOpen) {
      aiPanel.classList.remove('open');
      aiPanel.classList.add('translate-x-full');
    } else {
      aiPanel.classList.add('open');
      aiPanel.classList.remove('translate-x-full');
      checkEditorSelection();
    }
  }

  if (closePanelBtn) {
    closePanelBtn.addEventListener('click', () => {
      window.toggleAIPanel();
    });
  }

  function checkEditorSelection() {
    if (!currentEditor || !selectionStatus) return;
    const selectedText = currentEditor.codemirror.getSelection();
    if (selectedText && selectedText.trim().length > 0) {
      selectionStatus.innerHTML = `<span class="text-purple-400 font-semibold">Active Selection:</span> "${escapeHtml(selectedText.substring(0, 40))}${selectedText.length > 40 ? '...' : ''}" will be sent to Claude.`;
      isSelectionUsed = true;
    } else {
      selectionStatus.innerHTML = `<span class="text-zinc-300 font-semibold">Full Context:</span> No text highlighted. Actions will run on full content.`;
      isSelectionUsed = false;
    }
  }

  // Update selection message whenever editor changes cursor or focus
  if (currentEditor) {
    currentEditor.codemirror.on('cursorActivity', () => {
      if (aiPanel && aiPanel.classList.contains('open')) {
        checkEditorSelection();
      }
    });
  }

  // Tab selections
  if (tabResult && tabDiff) {
    tabResult.addEventListener('click', () => {
      tabResult.classList.add('border-purple-500', 'text-white');
      tabResult.classList.remove('border-transparent');
      tabDiff.classList.remove('border-purple-500', 'text-white');
      tabDiff.classList.add('border-transparent');
      previewContent.classList.remove('hidden');
      diffContent.classList.add('hidden');
    });

    tabDiff.addEventListener('click', () => {
      tabDiff.classList.add('border-purple-500', 'text-white');
      tabDiff.classList.remove('border-transparent');
      tabResult.classList.remove('border-purple-500', 'text-white');
      tabResult.classList.add('border-transparent');
      diffContent.classList.remove('hidden');
      previewContent.classList.add('hidden');
    });
  }

  async function callAIAssist(action, payload) {
    // UI state loading
    errorContainer.classList.add('hidden');
    resultSection.classList.add('hidden');
    loadingContainer.classList.remove('hidden');
    tokenEstimate.textContent = "Est: -- tokens";

    try {
      const response = await fetch('/ai/assist/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      loadingContainer.classList.add('hidden');

      if (!response.ok || data.error) {
        errorContainer.textContent = data.error || "An unknown server error occurred.";
        errorContainer.classList.remove('hidden');
        return;
      }

      activeAction = action;
      textResult = data.result;
      textOriginal = payload.text;

      // Update token estimates
      if (data.input_tokens_est && data.output_tokens_est) {
        const total = data.input_tokens_est + data.output_tokens_est;
        tokenEstimate.textContent = `Est: ${total} tokens (${data.input_tokens_est} in / ${data.output_tokens_est} out)`;
      }

      if (action === 'grammar') {
        // Applies directly to editor as per specs
        if (isSelectionUsed) {
          currentEditor.codemirror.replaceSelection(textResult);
        } else {
          currentEditor.codemirror.setValue(textResult);
        }
        selectionStatus.innerHTML = `<span class="text-green-400 font-semibold">Success!</span> Grammar & spelling corrections applied directly.`;
      } else {
        // Show result section and update content panels
        previewContent.textContent = textResult;
        diffContent.innerHTML = generateDiffHtml(textOriginal, textResult);
        resultSection.classList.remove('hidden');

        // Automatically click the right tab for improved writing vs others
        if (action === 'improve') {
          tabDiff.click();
        } else {
          tabResult.click();
        }
      }
    } catch (err) {
      loadingContainer.classList.add('hidden');
      errorContainer.textContent = "Connection failed. Please verify your network and Django server.";
      errorContainer.classList.remove('hidden');
    }
  }

  function getActiveText(fallbackToFull = true) {
    if (!currentEditor) return "";
    const selection = currentEditor.codemirror.getSelection();
    if (selection && selection.trim().length > 0) {
      isSelectionUsed = true;
      return selection;
    }
    if (fallbackToFull) {
      isSelectionUsed = false;
      return currentEditor.codemirror.getValue();
    }
    return "";
  }

  // Action buttons events
  if (btnImprove) {
    btnImprove.addEventListener('click', () => {
      const text = getActiveText(true);
      if (!text.trim()) {
        alert("Please write something in the editor first.");
        return;
      }
      callAIAssist('improve', { action: 'improve', text: text });
    });
  }

  if (btnGrammar) {
    btnGrammar.addEventListener('click', () => {
      // Fix grammar is specified to run on full content
      const text = currentEditor ? currentEditor.codemirror.getValue() : "";
      if (!text.trim()) {
        alert("Please write something in the editor first.");
        return;
      }
      isSelectionUsed = false;
      callAIAssist('grammar', { action: 'grammar', text: text });
    });
  }

  if (btnContinue) {
    btnContinue.addEventListener('click', () => {
      // Sends last 500 characters of content
      if (!currentEditor) return;
      const fullText = currentEditor.codemirror.getValue();
      if (!fullText.trim()) {
        alert("Please write some content first so the AI can continue from it.");
        return;
      }
      const last500 = fullText.slice(-500);
      isSelectionUsed = false; // Always append to the end
      callAIAssist('continue', { action: 'continue', text: last500 });
    });
  }

  if (btnTone) {
    btnTone.addEventListener('click', () => {
      const text = getActiveText(true);
      const tone = toneSelect ? toneSelect.value : 'Professional';
      if (!text.trim()) {
        alert("Please write something in the editor first.");
        return;
      }
      callAIAssist('tone', { action: 'tone', text: text, tone: tone });
    });
  }

  // Apply changes
  if (btnApply) {
    btnApply.addEventListener('click', () => {
      if (!currentEditor) return;

      if (activeAction === 'continue') {
        // Appends to editor content
        const doc = currentEditor.codemirror.getDoc();
        const currentVal = doc.getValue();
        const separator = currentVal.endsWith('\n') ? '\n' : '\n\n';
        doc.setValue(currentVal + separator + textResult);
      } else {
        // Replaces text
        if (isSelectionUsed) {
          currentEditor.codemirror.replaceSelection(textResult);
        } else {
          currentEditor.codemirror.setValue(textResult);
        }
      }

      // Hide results
      resultSection.classList.add('hidden');
      selectionStatus.innerHTML = `<span class="text-green-400 font-semibold">Applied!</span> AI edits merged successfully.`;
    });
  }

  if (btnDiscard) {
    btnDiscard.addEventListener('click', () => {
      resultSection.classList.add('hidden');
      selectionStatus.innerHTML = `<span class="text-zinc-400 font-semibold">Discarded.</span> Original text retained.`;
    });
  }

  // ─── Auto Summarize Logic ──────────────────────────────────────────
  const btnAutoSummarize = document.getElementById('btn-auto-summarize');
  const summaryTextarea = document.getElementById('id_summary');

  if (btnAutoSummarize && summaryTextarea) {
    btnAutoSummarize.addEventListener('click', async () => {
      if (!window.easyMDE) {
        alert("Editor is not initialized.");
        return;
      }
      const content = window.easyMDE.value();
      if (!content.trim()) {
        alert("Please write some content in the editor first before generating a summary.");
        return;
      }

      // Start loading state
      const originalBtnText = btnAutoSummarize.innerHTML;
      btnAutoSummarize.innerHTML = `<span class="inline-flex items-center gap-1"><span class="w-3.5 h-3.5 border-2 border-purple-500/20 border-t-purple-500 rounded-full animate-spin"></span> Generating...</span>`;
      btnAutoSummarize.disabled = true;

      const originalPlaceholder = summaryTextarea.placeholder;
      const originalValue = summaryTextarea.value;
      summaryTextarea.value = "";
      summaryTextarea.placeholder = "Generating summary with AI...";
      summaryTextarea.disabled = true;

      try {
        const response = await fetch('/ai/summarize/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
          },
          body: JSON.stringify({ content: content })
        });

        const data = await response.json();

        if (!response.ok || data.error) {
          alert(data.error || "Failed to generate summary.");
          summaryTextarea.value = originalValue;
        } else {
          summaryTextarea.value = data.summary;
          // Trigger char counter change
          summaryTextarea.dispatchEvent(new Event('input'));
          btnAutoSummarize.innerHTML = "✨ Regenerate";
        }
      } catch (err) {
        alert("Connection error. Could not connect to summary API.");
        summaryTextarea.value = originalValue;
      } finally {
        btnAutoSummarize.disabled = false;
        if (btnAutoSummarize.innerHTML.includes("Generating...")) {
          btnAutoSummarize.innerHTML = "✨ Auto-generate";
        }
        summaryTextarea.placeholder = originalPlaceholder;
        summaryTextarea.disabled = false;
      }
    });
  }

  // ─── Smart Tag Suggestions Logic ────────────────────────────────────
  const btnSuggestTags = document.getElementById('btn-suggest-tags');
  const tagsSelect = document.getElementById('id_tags');
  const suggestedTagsContainer = document.getElementById('suggested-tags-container');

  if (btnSuggestTags && tagsSelect && suggestedTagsContainer) {
    btnSuggestTags.addEventListener('click', async () => {
      const title = document.getElementById('id_title') ? document.getElementById('id_title').value : "";
      const summary = summaryTextarea ? summaryTextarea.value : "";
      const content = window.easyMDE ? window.easyMDE.value() : "";

      if (!title.trim() && !content.trim()) {
        alert("Please write a Title or Content first so the AI can suggest tags.");
        return;
      }

      // Start loading
      const originalBtnText = btnSuggestTags.innerHTML;
      btnSuggestTags.innerHTML = `<span class="inline-flex items-center gap-1"><span class="w-3.5 h-3.5 border-2 border-purple-500/20 border-t-purple-500 rounded-full animate-spin"></span> Suggesting...</span>`;
      btnSuggestTags.disabled = true;

      try {
        const response = await fetch('/ai/suggest-tags/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
          },
          body: JSON.stringify({ title, content, summary })
        });

        const data = await response.json();

        if (!response.ok || data.error) {
          alert(data.error || "Failed to suggest tags.");
          return;
        }

        renderSuggestedTags(data.tags);
      } catch (err) {
        alert("Connection error. Could not reach the tag suggestion API.");
      } finally {
        btnSuggestTags.disabled = false;
        btnSuggestTags.innerHTML = originalBtnText;
      }
    });

    function renderSuggestedTags(tags) {
      suggestedTagsContainer.innerHTML = "";

      if (!tags || tags.length === 0) {
        suggestedTagsContainer.innerHTML = `<span class="text-xs text-zinc-500">No tag suggestions found.</span>`;
        return;
      }

      tags.forEach(tagName => {
        const lowerName = tagName.toLowerCase().trim();
        const options = Array.from(tagsSelect.options);
        const existingOption = options.find(opt => opt.text.toLowerCase().trim() === lowerName);

        const pill = document.createElement('button');
        pill.type = "button";
        pill.setAttribute('data-tag-name', lowerName);

        if (existingOption) {
          const isSelected = existingOption.selected;
          pill.className = getPillClass(true, isSelected);
          pill.innerHTML = `<span>#${escapeHtml(lowerName)}</span>`;
          pill.addEventListener('click', () => toggleExistingTag(existingOption, pill));
        } else {
          // New tag
          pill.className = getPillClass(false, false);
          pill.innerHTML = `<span>#${escapeHtml(lowerName)}</span> <span class="text-[9px] uppercase tracking-wider bg-zinc-700/60 text-zinc-300 px-1 py-0.5 rounded ml-1 font-bold">(new)</span>`;
          pill.addEventListener('click', () => createAndSelectNewTag(lowerName, pill));
        }

        suggestedTagsContainer.appendChild(pill);
      });
    }

    function getPillClass(exists, selected) {
      const base = "text-[11px] font-mono font-semibold px-2.5 py-1 rounded-full border transition-all select-none flex items-center gap-1 ";
      if (!exists) {
        // Greyed out new tag
        return base + "bg-zinc-800/40 border-zinc-700/40 border-dashed text-zinc-400 hover:text-zinc-200 hover:border-zinc-500 cursor-pointer";
      }
      if (selected) {
        // Highlighted active tag
        return base + "bg-purple-600 text-white border-purple-500 cursor-pointer shadow-sm";
      }
      // Unselected active tag
      return base + "bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border-zinc-250 dark:border-zinc-700 hover:bg-zinc-200 dark:hover:bg-zinc-700 cursor-pointer";
    }

    function toggleExistingTag(option, pill) {
      option.selected = !option.selected;
      tagsSelect.dispatchEvent(new Event('change'));
      pill.className = getPillClass(true, option.selected);
    }

    async function createAndSelectNewTag(tagName, pill) {
      // Show loading inside pill
      const originalHtml = pill.innerHTML;
      pill.innerHTML = `<span class="w-2.5 h-2.5 border border-purple-500/20 border-t-purple-500 rounded-full animate-spin"></span> <span>Saving...</span>`;
      pill.disabled = true;

      try {
        const response = await fetch('/ai/create-tag/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
          },
          body: JSON.stringify({ name: tagName })
        });

        const data = await response.json();

        if (!response.ok || data.error) {
          alert(data.error || "Failed to create new tag.");
          pill.innerHTML = originalHtml;
          pill.disabled = false;
          return;
        }

        // Add option to select list
        const newOpt = document.createElement('option');
        newOpt.value = data.id;
        newOpt.text = data.name;
        newOpt.selected = true;
        tagsSelect.add(newOpt);
        tagsSelect.dispatchEvent(new Event('change'));

        // Upgrade pill styling
        pill.innerHTML = `<span>#${escapeHtml(data.name)}</span>`;
        pill.className = getPillClass(true, true);
        pill.disabled = false;

        // Hook up standard toggle listener going forward
        pill.replaceWith(pill.cloneNode(true)); // remove old listener
        const freshPill = suggestedTagsContainer.querySelector(`[data-tag-name="${tagName}"]`);
        if (freshPill) {
          freshPill.addEventListener('click', () => toggleExistingTag(newOpt, freshPill));
        }
      } catch (err) {
        alert("Failed to create tag due to connectivity issues.");
        pill.innerHTML = originalHtml;
        pill.disabled = false;
      }
    }
  }

  // ─── AI Related Posts dynamic fetching logic ───────────────────────
  const relatedSection = document.getElementById('related-stories-section');
  if (relatedSection) {
    const slug = relatedSection.getAttribute('data-slug');
    const skeleton = document.getElementById('related-stories-skeleton');
    const container = document.getElementById('related-stories-container');

    if (slug) {
      fetch(`/ai/related/${slug}/`)
        .then(res => res.json())
        .then(data => {
          if (data && data.posts && data.related && data.related.length > 0) {
            container.innerHTML = "";
            data.related.forEach(relatedSlug => {
              const post = data.posts[relatedSlug];
              if (post) {
                const card = document.createElement('a');
                card.href = post.url;
                card.className = "block p-4 bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)] border border-[var(--border)] hover:border-[var(--border-hover)] rounded-xl transition-all duration-200";
                card.innerHTML = `
                  <h4 class="text-xs font-semibold text-[var(--text-primary)] leading-snug mb-1 text-ellipsis overflow-hidden line-clamp-2">
                    ${escapeHtml(post.title)}
                  </h4>
                  <div class="flex items-center gap-2 mt-2 text-[10px] text-[var(--text-muted)]">
                    <span>${post.reading_time}m read</span>
                    <span>•</span>
                    <span>${post.view_count} views</span>
                  </div>
                `;
                container.appendChild(card);
                const prefetchLink = document.createElement('link');
                prefetchLink.rel = 'prefetch';
                prefetchLink.href = post.url;
                document.head.appendChild(prefetchLink);
              }
            });
            if (skeleton) skeleton.classList.add('hidden');
            container.classList.remove('hidden');
          } else {
            relatedSection.classList.add('hidden'); // hide if no related stories found
          }
        })
        .catch(() => {
          relatedSection.classList.add('hidden'); // fail silently
        });
    }
  }

  // ─── Lazy Loading Images ─────────────────────────────────────────────
  const lazyImages = document.querySelectorAll('.lazy-img');
  const imgObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        if (img.dataset.src) {
          img.src = img.dataset.src;
        }
        img.classList.add('loaded');
        imgObserver.unobserve(img);
      }
    });
  });
  lazyImages.forEach(img => imgObserver.observe(img));
});
