document.addEventListener("DOMContentLoaded", function() {
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