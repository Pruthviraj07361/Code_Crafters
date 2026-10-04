const frontendScriptUrl = document.currentScript.src;

document.addEventListener("DOMContentLoaded", function() {
  const stylesheet = document.querySelector('link[rel="stylesheet"][href="style.css"]') || document.createElement('link');
  stylesheet.rel = 'stylesheet';
  stylesheet.href = new URL('style.css', frontendScriptUrl).href;
  if (!stylesheet.isConnected) document.head.append(stylesheet);

  VANTA.WAVES({
    el: "#vanta-canvas",
    mouseControls: true,
    touchControls: true,
    gyroControls: false,
    minHeight: 200.00,
    minWidth: 200.00,
    scale: 1.00,
    scaleMobile: 1.00,
    color: 0x1e293b, /* Slate gray */
    backgroundColor: 0x0f172a, /* Deep navy */
    waveHeight: 15.00, /* Flattened for a calm look */
    waveSpeed: 0.5 /* Slowed down */
  });
});

document.addEventListener('click', function(event) {
  const link = event.target.closest('a[data-path="login"], a[data-path="dashboard"]');
  if (!link) return;

  event.preventDefault();
  if (link.dataset.path === 'login') {
    sessionStorage.removeItem('authToken');
    sessionStorage.removeItem('authUser');
    window.location.assign('/preview/');
    return;
  }

  window.location.assign('/preview/student/');
});