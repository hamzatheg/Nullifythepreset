/* Nullify the Preset — shared behaviour (every page loads this). */
(function () {
  // ── First-touch source (ad or link that brought the visitor), kept for this tab only ──
  try {
    if (!sessionStorage.getItem('ntp_src')) {
      const q = new URLSearchParams(location.search);
      const ref = document.referrer && !document.referrer.includes(location.hostname) ? document.referrer : '';
      sessionStorage.setItem('ntp_src', JSON.stringify({
        source: q.get('utm_source') || '', medium: q.get('utm_medium') || '',
        campaign: q.get('utm_campaign') || '', content: q.get('utm_content') || '',
        referrer: ref, landing: location.pathname,
      }));
    }
  } catch (e) { /* storage unavailable: applications still send, just without a source */ }

  // ── Questions: on phones each answer opens and closes ──
  const phone = matchMedia('(max-width: 719px)');
  const toggles = [...document.querySelectorAll('.qa-toggle')];
  function syncToggles() {
    toggles.forEach((b) => {
      if (phone.matches) b.setAttribute('aria-expanded', b.closest('.qa-row').classList.contains('open') ? 'true' : 'false');
      else b.removeAttribute('aria-expanded');
    });
  }
  toggles.forEach((b) => b.addEventListener('click', () => {
    if (!phone.matches) return;
    b.closest('.qa-row').classList.toggle('open');
    syncToggles();
  }));
  if (phone.addEventListener) phone.addEventListener('change', syncToggles);
  syncToggles();

  // ── Phones: a slim apply bar, shown only while no other apply button or the footer is on screen ──
  const bar = document.getElementById('mobileCta');
  if (bar && 'IntersectionObserver' in window) {
    const onScreen = new Set();
    const update = () => bar.classList.toggle('show', window.scrollY > window.innerHeight * 0.6 && onScreen.size === 0);
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => (e.isIntersecting ? onScreen.add(e.target) : onScreen.delete(e.target)));
      update();
    });
    document.querySelectorAll('main .btn, .site-footer').forEach((el) => io.observe(el));
    addEventListener('scroll', update, { passive: true });
  }

  // ── Footer year ──
  document.querySelectorAll('[data-year]').forEach((el) => { el.textContent = new Date().getFullYear(); });
})();
