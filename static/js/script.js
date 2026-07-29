document.addEventListener('DOMContentLoaded', function () {
  const sidebar = document.getElementById('mobileSidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const openBtn = document.getElementById('sidebarOpenBtn');
  const closeBtn = document.getElementById('sidebarCloseBtn');

  function openSidebar() {
    // Compensate for the scrollbar disappearing so page content doesn't
    // visibly jump sideways when overflow gets locked (a common source of
    // perceived "lag"/jank when opening a mobile nav).
    const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
    sidebar.classList.add('active');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    if (scrollbarWidth > 0) document.body.style.paddingRight = scrollbarWidth + 'px';
  }
  function closeSidebar() {
    sidebar.classList.remove('active');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
  }

  if (openBtn) openBtn.addEventListener('click', openSidebar);
  if (closeBtn) closeBtn.addEventListener('click', closeSidebar);
  if (overlay) overlay.addEventListener('click', closeSidebar);

  // Auto-dismiss flash messages after 5 seconds
  const messages = document.querySelectorAll('.messages li');
  messages.forEach(function (msg) {
    setTimeout(function () {
      msg.style.transition = 'opacity 0.5s ease';
      msg.style.opacity = '0';
      setTimeout(function () { msg.remove(); }, 500);
    }, 5000);
  });

  // ---------------- Hero carousel (Amazon-style auto-rotating banner) ----------------
  const carousel = document.getElementById('heroCarousel');
  if (carousel) {
    const slides = carousel.querySelectorAll('.hero-slide');
    const dots = carousel.querySelectorAll('.hero-dot');
    const prevBtn = document.getElementById('heroPrev');
    const nextBtn = document.getElementById('heroNext');
    let current = 0;
    let autoplayTimer = null;
    const AUTOPLAY_MS = 4500;

    function goToSlide(index) {
      slides[current].classList.remove('active');
      dots[current].classList.remove('active');
      current = (index + slides.length) % slides.length;
      slides[current].classList.add('active');
      dots[current].classList.add('active');
    }

    function nextSlide() { goToSlide(current + 1); }
    function prevSlide() { goToSlide(current - 1); }

    function startAutoplay() {
      stopAutoplay();
      autoplayTimer = setInterval(nextSlide, AUTOPLAY_MS);
    }
    function stopAutoplay() {
      if (autoplayTimer) clearInterval(autoplayTimer);
    }

    if (nextBtn) nextBtn.addEventListener('click', function () { nextSlide(); startAutoplay(); });
    if (prevBtn) prevBtn.addEventListener('click', function () { prevSlide(); startAutoplay(); });
    dots.forEach(function (dot) {
      dot.addEventListener('click', function () {
        goToSlide(parseInt(dot.dataset.index, 10));
        startAutoplay();
      });
    });

    // Pause on hover/touch so shoppers can read a slide, resume after
    carousel.addEventListener('mouseenter', stopAutoplay);
    carousel.addEventListener('mouseleave', startAutoplay);

    if (slides.length > 1) startAutoplay();
  }

  // ---------------- Product share button ----------------
  function getCookie(name) {
    const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? decodeURIComponent(match.pop()) : '';
  }

  function trackShare(productId) {
    // Best-effort: awards loyalty points server-side for sharing. Only
    // called when we know the visitor is logged in (the endpoint requires
    // it) and never blocks the actual share action if it fails/is slow.
    if (!productId || !window.CORAZON || !window.CORAZON.isAuthenticated) return;
    fetch('/loyalty/track-share/' + productId + '/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') },
      keepalive: true,
    }).catch(function () {
      // Silently ignore — sharing itself already happened via the browser
      // share sheet / platform link, points are a bonus, not the point.
    });
  }

  const shareBtn = document.getElementById('shareToggleBtn');
  const shareMenu = document.getElementById('shareMenu');
  if (shareBtn && shareMenu) {
    const productId = shareBtn.dataset.productId;

    shareBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      const url = shareBtn.dataset.shareUrl;
      const title = shareBtn.dataset.shareTitle;

      // On phones/tablets that support it, use the native share sheet
      // (Messages, WhatsApp, Instagram, etc. all show up automatically).
      if (navigator.share) {
        navigator.share({ title: title, url: url }).then(function () {
          trackShare(productId);
        }).catch(function () {
          // User cancelled the native share sheet — no points, no action needed.
        });
        return;
      }

      // Desktop fallback: toggle our own dropdown of platform links.
      const isOpen = shareMenu.classList.contains('open');
      shareMenu.classList.toggle('open', !isOpen);
      shareBtn.setAttribute('aria-expanded', String(!isOpen));
    });

    document.addEventListener('click', function (e) {
      if (shareMenu.classList.contains('open') && !shareMenu.contains(e.target) && e.target !== shareBtn) {
        shareMenu.classList.remove('open');
        shareBtn.setAttribute('aria-expanded', 'false');
      }
    });

    // Any real platform link (X, Facebook, WhatsApp, LinkedIn, Email) counts
    // as a completed share the moment it's clicked.
    shareMenu.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        trackShare(productId);
      });
    });

    const copyBtn = shareMenu.querySelector('.share-copy-btn');
    if (copyBtn) {
      copyBtn.addEventListener('click', function () {
        const url = copyBtn.dataset.copyUrl;
        const originalText = copyBtn.textContent;
        navigator.clipboard.writeText(url).then(function () {
          copyBtn.textContent = 'Link copied!';
          copyBtn.classList.add('copied');
          trackShare(productId);
          setTimeout(function () {
            copyBtn.textContent = originalText;
            copyBtn.classList.remove('copied');
          }, 2000);
        });
      });
    }
  }

  // ---------------- Deal of the Day countdown ----------------
  const countdownEl = document.getElementById('dealCountdown');
  if (countdownEl) {
    const endsAt = new Date(countdownEl.dataset.endsAt).getTime();
    const hoursEl = document.getElementById('cdHours');
    const minutesEl = document.getElementById('cdMinutes');
    const secondsEl = document.getElementById('cdSeconds');

    function pad(n) { return String(n).padStart(2, '0'); }

    function tick() {
      const diff = endsAt - Date.now();
      if (diff <= 0) {
        countdownEl.innerHTML = '<span class="cd-ended">Deal ended</span>';
        clearInterval(timer);
        return;
      }
      const totalSeconds = Math.floor(diff / 1000);
      const hours = Math.floor(totalSeconds / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = totalSeconds % 60;
      if (hoursEl) hoursEl.textContent = pad(hours);
      if (minutesEl) minutesEl.textContent = pad(minutes);
      if (secondsEl) secondsEl.textContent = pad(seconds);
    }

    tick();
    const timer = setInterval(tick, 1000);
  }
});

