// Shared site behavior: sticky-nav scroll hint, mobile menu, FAQ toggles,
// publication filter, smooth anchor scroll (handled in CSS), and the
// per-theme accent palette.

(function () {
  // --- External links and PDFs open in a new tab ---
  document.querySelectorAll('a[href]').forEach(a => {
    const external = a.hostname && a.hostname !== location.hostname;
    const pdf = a.pathname && a.pathname.endsWith('.pdf');
    if (external || pdf) {
      a.target = '_blank';
      a.rel = 'noopener';
    }
  });

  // --- Sticky nav scroll state ---
  const nav = document.querySelector('.site-nav');
  if (nav) {
    const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // --- Mobile menu toggle ---
  const toggle = document.querySelector('.menu-toggle');
  const menu = document.querySelector('.mobile-menu');
  if (toggle && menu) {
    toggle.addEventListener('click', () => {
      const open = menu.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });
    // Close the drawer when a nav link is tapped, so the transition to the
    // next page doesn't show a half-open menu mid-navigation.
    menu.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        menu.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // --- FAQ accordion ---
  document.querySelectorAll('.faq-item button').forEach(btn => {
    btn.setAttribute('aria-expanded', 'false');
    btn.addEventListener('click', () => {
      const open = btn.parentElement.classList.toggle('open');
      btn.setAttribute('aria-expanded', String(open));
    });
  });

  // --- Publications filter ---
  // Entries carry a comma-separated `data-tags` list; "All" shows everything,
  // any other button shows entries whose tag list includes the selected tag.
  const filterButtons = document.querySelectorAll('.pubs-filter button');
  if (filterButtons.length) {
    // Correct the counter from the actual entry count on load, so the HTML
    // literal can't drift when papers are added. Only write when it really
    // differs — the span is an aria-live region, and rewriting it with the
    // same text would announce itself to screen readers for no reason.
    const initCounter = document.querySelector('.pubs-filter .count');
    const total = document.querySelectorAll('.pub-entry').length;
    const initText = `${total} ${total === 1 ? 'paper' : 'papers'}`;
    if (initCounter && initCounter.textContent.trim() !== initText) initCounter.textContent = initText;
    filterButtons.forEach(btn => {
      btn.setAttribute('aria-pressed', String(btn.classList.contains('active')));
      btn.addEventListener('click', () => {
        const tag = btn.dataset.tag;
        filterButtons.forEach(b => {
          b.classList.toggle('active', b === btn);
          b.setAttribute('aria-pressed', String(b === btn));
        });
        document.querySelectorAll('.pub-entry').forEach(entry => {
          const tags = (entry.dataset.tags || '').split(',').map(s => s.trim()).filter(Boolean);
          entry.dataset.visible = (tag === 'all' || tags.includes(tag)) ? '1' : '0';
        });
        let count = 0;
        document.querySelectorAll('.pubs-year').forEach(yr => {
          const visibles = yr.querySelectorAll('.pub-entry[data-visible="1"]').length;
          yr.style.display = visibles ? '' : 'none';
          count += visibles;
        });
        const counter = document.querySelector('.pubs-filter .count');
        if (counter) counter.textContent = `${count} ${count === 1 ? 'paper' : 'papers'}`;
      });
    });
  }
})();
