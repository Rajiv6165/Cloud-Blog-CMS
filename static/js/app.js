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
  window.toggleMobileMenu = function() {
    const menu = document.getElementById('mobile-menu');
    if (menu) menu.classList.toggle('open');
  }

  // ─── Back to top ─────────────────────────────────────────────────────
  const backToTop = document.getElementById('back-to-top');
  window.addEventListener('scroll', () => {
    if (backToTop) {
      backToTop.classList.toggle('visible', window.scrollY > 400);
    }
  }, { passive: true });

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
});
