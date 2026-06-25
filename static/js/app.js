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

  // ─── EasyMDE rich text editor ────────────────────────────────────────
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
        'guide'
      ],
      placeholder: 'Write your story…',
      status: ['lines', 'words'],
    });
  }

  // ─── Dismiss flash messages ───────────────────────────────────────────
  document.querySelectorAll('[data-dismiss]').forEach(btn => {
    btn.addEventListener('click', () => {
      const msg = btn.closest('[data-message]');
      if (msg) msg.remove();
    });
  });
});
