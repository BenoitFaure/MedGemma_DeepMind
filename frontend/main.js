document.addEventListener('DOMContentLoaded', () => {
  const tableBody = document.getElementById('patient-list');

  patients.forEach((patient, idx) => {
    // Main row
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${patient.name}</td>
      <td>${patient.mrn}</td>
      <td>${patient.birthdate}</td>
      <td>${patient.scans[0]?.date || '-'}</td>
      <td><button class="action-btn" data-idx="${idx}">Expand</button></td>
    `;
    tableBody.appendChild(row);

    // Expandable row (hidden by default)
    const expandRow = document.createElement('tr');
    expandRow.className = 'expand-row';
    expandRow.style.display = 'none';
    expandRow.innerHTML = `<td colspan="5">
      <div><b>Scans:</b></div>
      <ul style="margin: 8px 0 16px 0;">
        ${patient.scans.map(scan => `<li>${scan.date} (${scan.file})</li>`).join('')}
      </ul>
      <div style="margin-bottom: 10px;">
        <button class="action-btn viewer-btn">Basic Viewer</button>
        <button class="action-btn ariae-btn" disabled>ARIA-E Analysis</button>
        <button class="action-btn report-btn" ${patient.scans[0]?.reportAvailable ? '' : 'disabled'}>Download Report</button>
        <button class="action-btn chat-btn">Chat with MedGemma</button>
      </div>
    </td>`;
    tableBody.appendChild(expandRow);

    // Expand/collapse logic
    row.querySelector('button').addEventListener('click', () => {
      expandRow.style.display = expandRow.style.display === 'none' ? '' : 'none';
      row.classList.toggle('selected');
    });

    // Action buttons logic
    const viewerBtn = expandRow.querySelector('.viewer-btn');
    viewerBtn.addEventListener('click', () => {
      // Pass patient id to viewer.html
      window.location.href = `viewer.html?patient=${encodeURIComponent(patient.id)}`;
    });
    const reportBtn = expandRow.querySelector('.report-btn');
    const ariaeBtn = expandRow.querySelector('.ariae-btn');
    ariaeBtn.disabled = false;
    ariaeBtn.addEventListener('click', async () => {
      ariaeBtn.disabled = true;
      reportBtn.disabled = true;
      // Show loading spinner
      let spinner = document.createElement('span');
      spinner.className = 'loading-spinner';
      spinner.style.marginLeft = '12px';
      spinner.innerHTML = 'Running ARIA-E Analysis...';
      ariaeBtn.parentNode.appendChild(spinner);
      try {
        // Timepoint 1
        await fetch('http://localhost:5001/run_ariae', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            input_path: 'assets/LUMIERE_001_0000.nii.gz',
            output_path: 'assets/LUMIERE_001.nii.gz'
          })
        }).then(r => r.json()).then(res => {
          if (res.status !== 'success') throw new Error(res.message || 'Error in ARIA-E 1');
        });
        // Timepoint 2
        await fetch('http://localhost:5001/run_ariae', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            input_path: 'assets/LUMIERE_002_0000.nii.gz',
            output_path: 'assets/LUMIERE_002.nii.gz'
          })
        }).then(r => r.json()).then(res => {
          if (res.status !== 'success') throw new Error(res.message || 'Error in ARIA-E 2');
        });
        // Success
        spinner.innerHTML = 'Analysis complete!';
        setTimeout(() => spinner.remove(), 1200);
        reportBtn.disabled = false;
      } catch (err) {
        spinner.innerHTML = 'Error: ' + err.message;
        ariaeBtn.disabled = false;
        setTimeout(() => spinner.remove(), 3000);
      }
    });
    reportBtn.addEventListener('click', () => {
      if (!reportBtn.disabled) {
        // Simulate fetching PDF
        window.open(`/api/report?patient=${encodeURIComponent(patient.id)}`, '_blank');
      }
    });
    const chatBtn = expandRow.querySelector('.chat-btn');
    chatBtn.addEventListener('click', () => {
      window.location.href = `chat.html?patient=${encodeURIComponent(patient.id)}`;
    });
  });
}); 