// verify.js - Visual Verification Ceremony

document.addEventListener('DOMContentLoaded', function () {
    const forms = document.querySelectorAll('form');
    const overlay = document.getElementById('scanning-overlay');
    const statusText = document.getElementById('scan-status');
    const detailsText = document.getElementById('scan-details');

    if (!overlay || !forms.length) return;

    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            // Check if this is a file upload form (has input[type="file"])
            // or a hash input form. Both should trigger animation.

            // Prevent default submission initially
            e.preventDefault();

            // Show overlay
            overlay.classList.remove('hidden');
            overlay.classList.add('flex');

            // Animation Sequence
            const sequence = [
                { text: "Extracting PDF Metadata...", delay: 800 },
                { text: "Calculating SHA-256 Hash...", delay: 1600 },
                { text: "Querying Blockchain Ledger...", delay: 2400 },
                { text: "Verifying Cryptographic Signature...", delay: 3200 },
                { text: "Finalizing Verification...", delay: 4000 }
            ];

            let currentTime = 0;

            sequence.forEach(step => {
                setTimeout(() => {
                    statusText.textContent = step.text;
                    // Add random hex code lines for effect
                    const hex = Math.random().toString(16).substring(2, 10).toUpperCase();
                    const p = document.createElement('p');
                    p.className = 'code-line';
                    p.textContent = `> PROCESS: ${hex}`;
                    detailsText.appendChild(p);
                    detailsText.scrollTop = detailsText.scrollHeight;
                }, step.delay);
            });

            // Submit form after animation finishes
            setTimeout(() => {
                form.submit();
            }, 4500);
        });
    });
});
