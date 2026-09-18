/* Nullify the Preset — shared behaviour (every page loads this). */
(function () {
  // ── Smooth scroll (graceful: native scroll if Lenis is missing) ──
  let lenis = null;
  try {
    if (typeof Lenis !== 'undefined' && !window.__noLenis) {
      lenis = new Lenis({
        duration: 1.2,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        direction: 'vertical',
        smooth: true,
        smoothTouch: false,
      });
      const raf = (t) => { lenis.raf(t); requestAnimationFrame(raf); };
      requestAnimationFrame(raf);
    }
  } catch (e) { lenis = null; }
  window.__lenis = lenis;

  // ── Topbar + progress ──
  const topbar = document.getElementById('topbar');
  const progress = document.getElementById('progress');
  function onScroll() {
    const y = window.scrollY;
    if (topbar) topbar.classList.toggle('scrolled', y > 24);
    if (progress) {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      progress.style.width = (Math.max(0, Math.min(1, y / Math.max(h, 1))) * 100) + '%';
    }
  }
  if (lenis) lenis.on('scroll', onScroll);
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ── Custom cursor (desktop only; CSS hides it elsewhere) ──
  const dot = document.getElementById('cursorDot');
  const ring = document.getElementById('cursorRing');
  if (dot && ring && matchMedia('(hover: hover)').matches) {
    let mx = -100, my = -100, rx = mx, ry = my;
    addEventListener('mousemove', (e) => {
      mx = e.clientX; my = e.clientY;
      dot.style.transform = `translate(${mx}px, ${my}px) translate(-50%, -50%)`;
    }, { passive: true });
    (function loop() {
      rx += (mx - rx) * 0.18; ry += (my - ry) * 0.18;
      ring.style.transform = `translate(${rx}px, ${ry}px) translate(-50%, -50%)`;
      requestAnimationFrame(loop);
    })();
    document.addEventListener('mouseover', (e) => {
      if (e.target.closest('a, button, input, textarea, label, [data-magnetic]')) ring.classList.add('hover');
    });
    document.addEventListener('mouseout', (e) => {
      if (e.target.closest('a, button, input, textarea, label, [data-magnetic]')) ring.classList.remove('hover');
    });
  }

  // ── Reveal on scroll ──
  const reveals = document.querySelectorAll('.reveal');
  if (reveals.length) {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add('in'); obs.unobserve(en.target); } });
    }, { threshold: 0.1, rootMargin: '0px 0px -6% 0px' });
    reveals.forEach((el) => obs.observe(el));
  }

  // ── Pointer spotlight on panels / CTAs / features ──
  document.addEventListener('mousemove', (e) => {
    const el = e.target.closest('.panel, .cta, .feature, .field-wrap');
    if (!el) return;
    const r = el.getBoundingClientRect();
    el.style.setProperty('--mx', ((e.clientX - r.left) / r.width * 100) + '%');
    el.style.setProperty('--my', ((e.clientY - r.top) / r.height * 100) + '%');
  }, { passive: true });

  // ── Magnetic CTAs ──
  if (matchMedia('(hover: hover)').matches) {
    document.querySelectorAll('[data-magnetic]').forEach((el) => {
      el.addEventListener('mousemove', (e) => {
        const r = el.getBoundingClientRect();
        const dx = (e.clientX - (r.left + r.width / 2)) * 0.12;
        const dy = (e.clientY - (r.top + r.height / 2)) * 0.18;
        el.style.transform = `translate(${dx}px, ${dy - 2}px)`;
      });
      el.addEventListener('mouseleave', () => { el.style.transform = ''; });
    });
  }

  // ── Footer year ──
  document.querySelectorAll('[data-year]').forEach((el) => { el.textContent = new Date().getFullYear(); });
})();
