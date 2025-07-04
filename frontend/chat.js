function getQueryParam(name) {
    const url = new URL(window.location.href);
    return url.searchParams.get(name);
}

document.addEventListener('DOMContentLoaded', () => {
    const patientId = getQueryParam('patient');
    const patient = patients.find(p => p.id === patientId);
    const chatHeader = document.getElementById('chat-patient-info');
    if (patient) {
        chatHeader.textContent = `${patient.name} (MRN: ${patient.mrn})`;
    } else {
        chatHeader.textContent = 'Patient not found.';
    }
    const chatHistory = document.getElementById('chat-history');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send-btn');
    const chatForm = document.getElementById('chat-form');

    function appendMsg(msg, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'chat-msg ' + sender;
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble';
        bubble.textContent = msg;
        msgDiv.appendChild(bubble);
        chatHistory.appendChild(msgDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function sendToBackend(message, callback) {
        // Simulate API call with canned response
        setTimeout(() => {
            callback("[MedGemma] This is a demo response. (In production, this would call the LLM API with patient context.)");
        }, 900);
    }

    function sendMessage() {
        const msg = chatInput.value.trim();
        if (!msg) return;
        appendMsg(msg, 'user');
        chatInput.value = '';
        sendBtn.disabled = true;
        sendToBackend(msg, (response) => {
            appendMsg(response, 'ai');
            sendBtn.disabled = false;
        });
    }

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') sendMessage();
    });
    chatForm.addEventListener('submit', sendMessage);
}); 