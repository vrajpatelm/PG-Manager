// Main JS
document.addEventListener('DOMContentLoaded', () => {
  console.log('Main JS loaded');

  const els = {
    loginDesktop: document.getElementById('btn-login-desktop'),
    signupDesktop: document.getElementById('btn-signup-desktop'),
    loginMobile: document.getElementById('btn-login-mobile'),
    signupMobile: document.getElementById('btn-signup-mobile'),
    mobileToggle: document.getElementById('btn-mobile-toggle'),
    mobileMenu: document.getElementById('mobile-menu'),
    iconOpen: document.getElementById('icon-open'),
    iconClose: document.getElementById('icon-close'),
  };

  function setActive(isLoginActive) {
    const desktopPair = [els.loginDesktop, els.signupDesktop];
    const mobilePair = [els.loginMobile, els.signupMobile];

    applyPair(desktopPair[0], desktopPair[1], isLoginActive);
    applyPair(mobilePair[0], mobilePair[1], isLoginActive);
  }

  function applyPair(loginEl, signupEl, isLoginActive) {
    if (loginEl) applyState(loginEl, isLoginActive);
    if (signupEl) applyState(signupEl, !isLoginActive);
  }

  // active = blue button; inactive = white button with gray border (both rounded-md)
  function applyState(el, active) {
    const activeClasses = [
      'bg-blue-600',
      'text-white',
      'border',
      'border-transparent',
      'hover:bg-blue-700',
      'focus:bg-blue-700',
      'rounded-md',
    ];
    const inactiveClasses = [
      'bg-white',
      'text-black',
      'border',
      'border-gray-200',
      'hover:bg-gray-50',
      'focus:bg-gray-50',
      'rounded-md',
    ];

    // Remove previous state classes
    el.classList.remove(
      'bg-blue-600','text-white','border','border-transparent','hover:bg-blue-700','focus:bg-blue-700',
      'bg-white','text-black','border-gray-200','hover:bg-gray-50','focus:bg-gray-50','rounded-full','rounded-md'
    );

    if (active) {
      el.classList.add(...activeClasses);
    } else {
      el.classList.add(...inactiveClasses);
    }
  }

  // Wire events
  if (els.loginDesktop) {
    els.loginDesktop.addEventListener('click', (e) => { setActive(true); });
  }
  if (els.signupDesktop) {
    els.signupDesktop.addEventListener('click', (e) => { setActive(false); });
  }
  if (els.loginMobile) {
    els.loginMobile.addEventListener('click', (e) => { setActive(true); });
  }
  if (els.signupMobile) {
    els.signupMobile.addEventListener('click', (e) => { setActive(false); });
  }

  // Mobile hamburger toggle
  if (els.mobileToggle && els.mobileMenu && els.iconOpen && els.iconClose) {
    els.mobileToggle.addEventListener('click', () => {
      const isHidden = els.mobileMenu.classList.contains('hidden');
      els.mobileMenu.classList.toggle('hidden');
      // swap icons
      els.iconOpen.classList.toggle('hidden', !isHidden === false);
      els.iconOpen.classList.toggle('block', !els.iconOpen.classList.contains('hidden'));
      els.iconClose.classList.toggle('hidden', isHidden === false);
      els.iconClose.classList.toggle('block', !els.iconClose.classList.contains('hidden'));
      // aria-expanded for accessibility
      els.mobileToggle.setAttribute('aria-expanded', String(isHidden));
    });
  }
});

