===========================================
HOW TO ADD YOUR GIF BACKGROUND
===========================================

1. Save your GIF file in this folder (static/images/)
2. Name it: login-bg.gif
   OR
   If you use a different name, update the CSS file:
   - Open: static/css/style.css
   - Find line with: background-image: url('/static/images/login-bg.gif');
   - Change 'login-bg.gif' to your GIF filename

3. Refresh your browser (Ctrl+F5 to clear cache)

===========================================
CURRENT SETTINGS:
===========================================
- GIF Width: 100vw (full viewport width)
- GIF Height: 100vh (full viewport height)
- Background Size: cover (scales to cover entire area)
- Background Position: center center

To adjust these settings, edit static/css/style.css
Look for the .bg-pattern section around line 862

