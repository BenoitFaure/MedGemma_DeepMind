function getQueryParam(name) {
    const url = new URL(window.location.href);
    return url.searchParams.get(name);
}

document.addEventListener('DOMContentLoaded', () => {
    const patientId = getQueryParam('patient');
    const patient = patients.find(p => p.id === patientId);
    const viewerTitle = document.getElementById('viewer-title');

    // Panel 1 controls
    const canvas1 = document.getElementById('scan-canvas-1');
    const ctx1 = canvas1.getContext('2d');
    const btnMRI1 = document.getElementById('btn-mri-1');
    const btnOverlay1 = document.getElementById('btn-overlay-1');
    const sliceSlider1 = document.getElementById('slice-slider-1');
    const sliceLabel1 = document.getElementById('slice-label-1');
    // Panel 2 controls
    const canvas2 = document.getElementById('scan-canvas-2');
    const ctx2 = canvas2.getContext('2d');
    const btnMRI2 = document.getElementById('btn-mri-2');
    const btnOverlay2 = document.getElementById('btn-overlay-2');
    const sliceSlider2 = document.getElementById('slice-slider-2');
    const sliceLabel2 = document.getElementById('slice-label-2');

    if (!patient) {
        viewerTitle.textContent = 'Patient not found.';
        return;
    }
    viewerTitle.textContent = `${patient.name} (MRN: ${patient.mrn})`;

    // Only for first patient: real images for both timepoints
    if (patient.id === 'p1') {
        // For demo, use same images for both timepoints, but code allows for different folders
        const scanFolders = [
            'assets/LUMIERE_001_0000_slices', // Baseline
            'assets/LUMIERE_001_0000_slices'  // Follow-up (replace with another folder if available)
        ];
        const maskFolders = [
            'assets/LUMIERE_001_slices',      // Baseline mask
            'assets/LUMIERE_001_slices'       // Follow-up mask (replace if available)
        ];
        const scanSlices = 48; // Update if needed
        // State for each panel
        let showOverlay = [false, false];
        // Set initial slice to the middle
        let initialSlice = Math.floor(scanSlices / 2);
        let currentSlice = [initialSlice, initialSlice];
        // Set slider range
        sliceSlider1.max = scanSlices;
        sliceSlider2.max = scanSlices;
        sliceSlider1.value = initialSlice;
        sliceSlider2.value = initialSlice;
        let imgW = 512, imgH = 512;

        function drawSlice(panelIdx) {
            const canvas = panelIdx === 0 ? canvas1 : canvas2;
            const ctx = panelIdx === 0 ? ctx1 : ctx2;
            const sliceIdx = currentSlice[panelIdx];
            const scanFolder = scanFolders[panelIdx];
            const maskFolder = maskFolders[panelIdx];
            const sliceNum = String(sliceIdx).padStart(3, '0');
            const scanSrc = `${scanFolder}/LUMIERE_001_0000_slice_${sliceNum}.jpg`;
            const maskSrc = `${maskFolder}/LUMIERE_001_slice_${sliceNum}.jpg`;
            // Load scan image
            const scanImg = new window.Image();
            scanImg.src = scanSrc;
            scanImg.onload = () => {
                imgW = scanImg.naturalWidth;
                imgH = scanImg.naturalHeight;
                // Set canvas size
                canvas.width = imgW;
                canvas.height = imgH;
                ctx.save();
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                // Rotate 90deg right: translate, rotate, then draw
                ctx.translate(canvas.width, 0);
                ctx.rotate(Math.PI / 2);
                ctx.drawImage(scanImg, 0, 0, imgW, imgH, 0, 0, canvas.height, canvas.width);
                ctx.restore();
                if (showOverlay[panelIdx]) {
                    // Load mask image and overlay in red only where mask is present
                    const maskImg = new window.Image();
                    maskImg.src = maskSrc;
                    maskImg.onload = () => {
                        // Draw mask to temp canvas
                        const temp = document.createElement('canvas');
                        temp.width = imgW;
                        temp.height = imgH;
                        const tctx = temp.getContext('2d');
                        tctx.drawImage(maskImg, 0, 0);
                        // Get mask pixel data
                        const maskData = tctx.getImageData(0, 0, imgW, imgH);
                        // Create red overlay only where mask is white
                        for (let i = 0; i < maskData.data.length; i += 4) {
                            // If mask pixel is white (or above threshold)
                            if (maskData.data[i] > 127) {
                                maskData.data[i] = 255;   // Red
                                maskData.data[i + 1] = 0; // Green
                                maskData.data[i + 2] = 0; // Blue
                                maskData.data[i + 3] = 90; // Alpha (0-255, ~0.35)
                            } else {
                                maskData.data[i + 3] = 0; // Fully transparent
                            }
                        }
                        tctx.putImageData(maskData, 0, 0);
                        ctx.save();
                        ctx.translate(canvas.width, 0);
                        ctx.rotate(Math.PI / 2);
                        ctx.drawImage(temp, 0, 0, imgW, imgH, 0, 0, canvas.height, canvas.width);
                        ctx.restore();
                    };
                }
            };
        }

        function updateSlice(panelIdx, sliceIdx) {
            currentSlice[panelIdx] = sliceIdx;
            drawSlice(panelIdx);
            if (panelIdx === 0) {
                sliceLabel1.textContent = `Slice ${sliceIdx} / ${scanSlices}`;
            } else {
                sliceLabel2.textContent = `Slice ${sliceIdx} / ${scanSlices}`;
            }
        }

        // Button logic for both panels
        btnMRI1.onclick = () => {
            btnMRI1.classList.add('active');
            btnOverlay1.classList.remove('active');
            showOverlay[0] = false;
            updateSlice(0, currentSlice[0]);
        };
        btnOverlay1.onclick = () => {
            btnOverlay1.classList.add('active');
            btnMRI1.classList.remove('active');
            showOverlay[0] = true;
            updateSlice(0, currentSlice[0]);
        };
        btnMRI2.onclick = () => {
            btnMRI2.classList.add('active');
            btnOverlay2.classList.remove('active');
            showOverlay[1] = false;
            updateSlice(1, currentSlice[1]);
        };
        btnOverlay2.onclick = () => {
            btnOverlay2.classList.add('active');
            btnMRI2.classList.remove('active');
            showOverlay[1] = true;
            updateSlice(1, currentSlice[1]);
        };
        // Slider
        sliceSlider1.oninput = e => {
            updateSlice(0, Number(e.target.value));
        };
        sliceSlider2.oninput = e => {
            updateSlice(1, Number(e.target.value));
        };
        // Mouse wheel
        canvas1.addEventListener('wheel', e => {
            e.preventDefault();
            let val = currentSlice[0];
            if (e.deltaY > 0 && val < scanSlices) val++;
            else if (e.deltaY < 0 && val > 1) val--;
            sliceSlider1.value = val;
            updateSlice(0, val);
        });
        canvas2.addEventListener('wheel', e => {
            e.preventDefault();
            let val = currentSlice[1];
            if (e.deltaY > 0 && val < scanSlices) val++;
            else if (e.deltaY < 0 && val > 1) val--;
            sliceSlider2.value = val;
            updateSlice(1, val);
        });
        // Keyboard shortcuts (left panel only)
        window.addEventListener('keydown', e => {
            if (e.key === 'ArrowLeft' || e.key === 'a') {
                if (currentSlice[0] > 1) {
                    sliceSlider1.value = currentSlice[0] - 1;
                    updateSlice(0, currentSlice[0] - 1);
                }
            } else if (e.key === 'ArrowRight' || e.key === 'd') {
                if (currentSlice[0] < scanSlices) {
                    sliceSlider1.value = currentSlice[0] + 1;
                    updateSlice(0, currentSlice[0] + 1);
                }
            }
        });
        // Initial
        updateSlice(0, initialSlice);
        updateSlice(1, initialSlice);
        return;
    }

    // Default: dummy placeholder for other patients
    viewerTitle.textContent = `${patient.name} (MRN: ${patient.mrn})`;
    [ctx1, ctx2].forEach(ctx => {
        ctx.fillStyle = '#222';
        ctx.fillRect(0, 0, 512, 512);
        ctx.font = '2rem Segoe UI, Arial';
        ctx.fillStyle = '#7ecbff';
        ctx.textAlign = 'center';
        ctx.fillText('No scan available', 256, 256);
    });
    sliceLabel1.textContent = '';
    sliceLabel2.textContent = '';
    sliceSlider1.style.display = 'none';
    sliceSlider2.style.display = 'none';
    btnMRI1.style.display = 'none';
    btnOverlay1.style.display = 'none';
    btnMRI2.style.display = 'none';
    btnOverlay2.style.display = 'none';
}); 