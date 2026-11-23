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

  // ── Footer year ──
  document.querySelectorAll('[data-year]').forEach((el) => { el.textContent = new Date().getFullYear(); });
})();
