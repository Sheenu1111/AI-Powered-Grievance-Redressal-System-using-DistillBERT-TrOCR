/* ─────────────────────────────────────────────────────────
   AI Grievance System — Main JS (Submit Page)
───────────────────────────────────────────────────────── */

const priorityBadgeClass = {
    'High'  : 'badge-high',
    'Medium': 'badge-medium',
    'Low'   : 'badge-low'
};

/* ── Input Method Tabs ──────────────────────────────────── */
document.querySelectorAll('.method-tab').forEach(tab => {
    tab.addEventListener('click', function () {
        document.querySelectorAll('.method-tab').forEach(t => t.classList.remove('active'));
        this.classList.add('active');

        const method = this.dataset.method;
        const textSec = document.getElementById('textInputSection');
        const fileSec = document.getElementById('fileInputSection');

        if (method === 'text') {
            textSec.style.display = 'block';
            fileSec.style.display = 'none';
            document.getElementById('complaint_text').value = '';
        } else {
            textSec.style.display = 'none';
            fileSec.style.display = 'block';
            const fi = document.getElementById('complaint_file');
            if (fi) fi.value = '';
            const fp = document.getElementById('filePreview');
            if (fp) { fp.innerHTML = ''; fp.classList.remove('show'); }
        }
    });
});

/* ── File Upload Preview ─────────────────────────────────── */
const fileInput = document.getElementById('complaint_file');
if (fileInput) {
    fileInput.addEventListener('change', function (e) {
        const file = e.target.files[0];
        const preview = document.getElementById('filePreview');
        if (!preview) return;

        if (file) {
            const reader = new FileReader();
            reader.onload = function (ev) {
                const isImage = file.type.startsWith('image/');
                preview.innerHTML = `
                    <div class="file-preview-name">
                        📄 <span>${file.name}</span>
                        <span style="font-size:12px;color:var(--gray-400);margin-left:auto;">${(file.size/1024).toFixed(1)} KB</span>
                    </div>
                    ${isImage ? `<img src="${ev.target.result}" alt="Preview">` : ''}
                `;
                preview.classList.add('show');
            };
            reader.readAsDataURL(file);
        } else {
            preview.innerHTML = '';
            preview.classList.remove('show');
        }
    });
}

/* ── Drag and Drop ───────────────────────────────────────── */
const dropZone = document.getElementById('dropZone');
if (dropZone) {
    ['dragenter', 'dragover'].forEach(ev =>
        dropZone.addEventListener(ev, e => { e.preventDefault(); dropZone.classList.add('drag-over'); })
    );
    ['dragleave', 'drop'].forEach(ev =>
        dropZone.addEventListener(ev, e => { e.preventDefault(); dropZone.classList.remove('drag-over'); })
    );
    dropZone.addEventListener('drop', e => {
        const file = e.dataTransfer.files[0];
        if (file && fileInput) {
            const dt = new DataTransfer();
            dt.items.add(file);
            fileInput.files = dt.files;
            fileInput.dispatchEvent(new Event('change'));
        }
    });
}

/* ── AI Loading Steps ────────────────────────────────────── */
function runLoadingSteps() {
    const steps = ['step1','step2','step3','step4','step5'];
    steps.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.className = 'ai-step';
    });

    let i = 0;
    const interval = setInterval(() => {
        if (i > 0) {
            const prev = document.getElementById(steps[i-1]);
            if (prev) prev.className = 'ai-step done';
        }
        if (i < steps.length) {
            const curr = document.getElementById(steps[i]);
            if (curr) curr.className = 'ai-step active';
        }
        i++;
        if (i > steps.length) clearInterval(interval);
    }, 600);

    return interval;
}

/* ── Form Submission ─────────────────────────────────────── */
const form = document.getElementById('complaintForm');
if (form) {
    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const formData  = new FormData();
        const textVal   = (document.getElementById('complaint_text')?.value || '').trim();
        const fileVal   = document.getElementById('complaint_file')?.files[0];

        if (!textVal && !fileVal) {
            showInlineError('Please provide a complaint text or upload an image.');
            return;
        }

        if (textVal) formData.append('complaint_text', textVal);
        if (fileVal) formData.append('complaint_file', fileVal);

        // Show loading
        const overlay   = document.getElementById('loadingOverlay');
        const resultCard = document.getElementById('resultCard');
        overlay.classList.add('active');
        if (resultCard) resultCard.classList.remove('show');

        const stepInterval = runLoadingSteps();

        try {
            const res  = await fetch('/submit_complaint', { method: 'POST', body: formData });
            const data = await res.json();

            clearInterval(stepInterval);
            overlay.classList.remove('active');

            if (data.success) {
                populateResult(data);
                if (resultCard) {
                    resultCard.classList.add('show');
                    resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            } else {
                showInlineError(data.error || 'An error occurred. Please try again.');
            }
        } catch (err) {
            clearInterval(stepInterval);
            overlay.classList.remove('active');
            showInlineError('Network error. Please check your connection and try again.');
            console.error(err);
        }
    });
}

/* ── Populate Result ─────────────────────────────────────── */
function populateResult(data) {
    const el = id => document.getElementById(id);

    if (el('ticketId'))       el('ticketId').textContent       = data.ticket_id;
    if (el('resultCategory')) el('resultCategory').textContent = data.category;
    if (el('resultDepartment')) el('resultDepartment').textContent = data.department;
    if (el('resultTimeline')) el('resultTimeline').textContent  = data.timeline;
    if (el('extractedText'))  el('extractedText').textContent   = data.complaint_text;

    if (el('resultSentiment')) {
        const s = data.sentiment;
        const icons = { 'Angry': '😡', 'Frustrated': '😤', 'Neutral': '😐', 'Satisfied': '😊' };
        el('resultSentiment').textContent = (icons[s] || '') + ' ' + s;
    }

    if (el('resultPriority')) {
        el('resultPriority').innerHTML = `<span class="badge ${priorityBadgeClass[data.priority] || 'badge-default'}">${data.priority}</span>`;
    }
}

/* ── Copy Ticket ID ──────────────────────────────────────── */
function copyTicketId() {
    const ticketId = document.getElementById('ticketId')?.textContent;
    if (!ticketId || ticketId === '—') return;

    navigator.clipboard.writeText(ticketId).catch(() => {
        // Fallback
        const tmp = document.createElement('input');
        tmp.value = ticketId;
        document.body.appendChild(tmp);
        tmp.select();
        document.execCommand('copy');
        document.body.removeChild(tmp);
    });

    const btn = document.getElementById('copyBtn');
    if (btn) {
        btn.textContent = '✓ Copied!';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.textContent = '📋 Copy ID';
            btn.classList.remove('copied');
        }, 2200);
    }
}

/* ── Inline Error ────────────────────────────────────────── */
function showInlineError(msg) {
    let errEl = document.getElementById('formError');
    if (!errEl) {
        errEl = document.createElement('div');
        errEl.id = 'formError';
        errEl.className = 'error-box show';
        errEl.innerHTML = `<span class="err-icon">⚠️</span><p></p>`;
        form.insertAdjacentElement('afterend', errEl);
    }
    errEl.querySelector('p').textContent = msg;
    errEl.classList.add('show');
    errEl.scrollIntoView({ behavior: 'smooth' });
    setTimeout(() => errEl.classList.remove('show'), 6000);
}
