let botState = {
    step: 0,
    serviceId: null,
    duration: null,
    date: null,
    time: null,
    addToCalendar: false,
    isOpen: false,
    messagesHtml: '',
    inputAreaHtml: ''
};

function saveBotState() {
    const msgs = document.getElementById('chatbot-messages');
    const inputArea = document.getElementById('chatbot-input-area');
    if (msgs && inputArea) {
        botState.messagesHtml = msgs.innerHTML;
        botState.inputAreaHtml = inputArea.innerHTML;
        sessionStorage.setItem('leilaBotState', JSON.stringify(botState));
    }
}

function loadBotState() {
    const saved = sessionStorage.getItem('leilaBotState');
    if (saved) {
        try {
            botState = JSON.parse(saved);
        } catch (e) {
            console.error("Erro ao fazer parse do estado do bot", e);
        }
    }
}

function renderSavedState() {
    const msgs = document.getElementById('chatbot-messages');
    const inputArea = document.getElementById('chatbot-input-area');
    const container = document.getElementById('chatbot-container');
    const btn = document.getElementById('chatbot-toggle-btn');

    if (msgs) msgs.innerHTML = botState.messagesHtml || '';
    if (inputArea) inputArea.innerHTML = botState.inputAreaHtml || '';

    if (botState.isOpen) {
        container.style.display = 'flex';
        btn.style.display = 'none';
        scrollToBottom();
    } else {
        container.style.display = 'none';
        btn.style.display = 'flex';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.tipo !== 'CLIENT') {
            const wrapper = document.getElementById('chatbot-wrapper');
            if (wrapper) wrapper.remove();
            return;
        }
    } catch (e) { return; }

    const wrapper = document.getElementById('chatbot-wrapper');
    if (wrapper) wrapper.style.display = 'block';

    loadBotState();
    renderSavedState();
});

function toggleChatbot() {
    botState.isOpen = !botState.isOpen;
    renderSavedState();
    saveBotState();

    if (botState.isOpen && botState.step === 0) {
        initChatbot();
    }
}

function scrollToBottom() {
    const msgs = document.getElementById('chatbot-messages');
    if (msgs) msgs.scrollTop = msgs.scrollHeight;
}

function addBotMessage(text) {
    const msgs = document.getElementById('chatbot-messages');
    if (!msgs) return;
    const div = document.createElement('div');
    div.className = 'chat-msg-bot animate-fade-in';
    div.innerHTML = text;
    msgs.appendChild(div);
    scrollToBottom();
    saveBotState();
}

function addUserMessage(text) {
    const msgs = document.getElementById('chatbot-messages');
    if (!msgs) return;
    const div = document.createElement('div');
    div.className = 'chat-msg-user animate-fade-in';
    div.innerHTML = text;
    msgs.appendChild(div);
    scrollToBottom();
    saveBotState();
}

function renderOptions(optionsHTML) {
    const inputArea = document.getElementById('chatbot-input-area');
    if (!inputArea) return;
    inputArea.innerHTML = `<div class="d-flex flex-column gap-1">${optionsHTML}</div>`;
    saveBotState();
}

async function initChatbot() {
    document.getElementById('chatbot-messages').innerHTML = '';
    renderOptions('');
    addBotMessage("Olá! Sou a LeilaBot 🤖. Vou ajudar você a agendar um horário rapidamente.");
    botState.step = 1;
    saveBotState();
    await loadBotServices();
}

async function loadBotServices() {
    addBotMessage("Um momento, estou buscando os serviços disponíveis...");
    try {
        const data = await apiGet('/api/services');
        if (!data || !data.items || data.items.length === 0) {
            addBotMessage("Desculpe, não há serviços disponíveis no momento.");
            return;
        }
        addBotMessage("Qual serviço você gostaria de agendar?");
        let optionsHTML = data.items.map(s =>
            `<button class="btn chatbot-option-btn w-100" onclick="botSelectService(${s.id}, '${s.nome}', ${s.duracao_minutos})">
                ${s.nome} - R$ ${s.preco}
            </button>`
        ).join('');
        renderOptions(optionsHTML);
    } catch (e) {
        addBotMessage("Ops, houve um erro ao buscar os serviços.");
    }
}

function botSelectService(id, name, duration) {
    botState.serviceId = id;
    botState.duration = duration;
    saveBotState();
    addUserMessage(`Gostaria de agendar: ${name}`);
    renderOptions('');

    botState.step = 2;
    saveBotState();
    setTimeout(() => askBotDate(), 500);
}

function askBotDate() {
    addBotMessage("Ótimo! Para qual dia você gostaria de agendar?");
    const today = new Date().toISOString().split('T')[0];
    let optionsHTML = `
        <div class="input-group">
            <input type="date" id="botDateInput" class="form-control bg-dark text-white border-secondary" min="${today}">
            <button class="btn btn-primary" onclick="botSelectDate()">Avançar</button>
        </div>
    `;
    renderOptions(optionsHTML);
}

window.botSelectDate = function () {
    const dateVal = document.getElementById('botDateInput').value;
    if (!dateVal) return;

    const selected = new Date(dateVal + 'T00:00:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (selected < today) {
        alert('Escolha uma data igual ou superior a hoje.');
        return;
    }

    const dateStr = selected.toLocaleDateString('pt-BR');
    botState.date = dateVal;
    saveBotState();

    addUserMessage(`Para o dia ${dateStr}`);
    renderOptions('');

    botState.step = 3;
    saveBotState();
    setTimeout(() => loadBotSlots(), 500);
}

async function loadBotSlots() {
    addBotMessage("Buscando horários livres... 🕒");
    try {
        const data = await apiGet(`/api/appointments/available-slots?date=${botState.date}&duration=${botState.duration}`);
        if (!data || data.length === 0) {
            addBotMessage("Poxa, não temos horários disponíveis nesse dia. Vamos tentar outra data?");
            askBotDate();
            return;
        }

        const available = data.filter(s => s.disponivel);
        if (available.length === 0) {
            addBotMessage("Todos os horários estão ocupados nesse dia. Vamos tentar outra data?");
            askBotDate();
            return;
        }

        addBotMessage("Aqui estão os horários que encontrei. Qual você prefere?");

        let optionsHTML = `<div style="max-height: 150px; overflow-y: auto;" class="d-flex flex-wrap gap-2 justify-content-center">`;
        optionsHTML += available.map(s => {
            const timeStr = new Date(s.data_hora).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
            return `<button class="btn btn-sm chatbot-option-btn w-auto" onclick="botSelectTime('${s.data_hora}', '${timeStr}')">${timeStr}</button>`;
        }).join('');
        optionsHTML += `</div>`;
        renderOptions(optionsHTML);

    } catch (e) {
        addBotMessage("Erro ao buscar horários. Vamos recomeçar?");
        botState.step = 0;
        saveBotState();
        initChatbot();
    }
}

window.botSelectTime = function (isoString, timeStr) {
    botState.time = isoString;
    saveBotState();

    addUserMessage(`Quero às ${timeStr}`);
    renderOptions('');

    botState.step = 4;
    saveBotState();
    setTimeout(() => askBotCalendar(), 500);
}

function askBotCalendar() {
    addBotMessage("Quase lá! Deseja que eu adicione este agendamento no seu Google Calendar para você não esquecer?");
    let optionsHTML = `
        <div class="d-flex gap-2 w-100">
            <button class="btn chatbot-option-btn flex-fill" onclick="botFinish(true)">Sim, por favor</button>
            <button class="btn chatbot-option-btn flex-fill" onclick="botFinish(false)">Não precisa</button>
        </div>
    `;
    renderOptions(optionsHTML);
}

window.botFinish = async function (syncCalendar) {
    botState.addToCalendar = syncCalendar;
    saveBotState();

    addUserMessage(syncCalendar ? "Sim, por favor." : "Não precisa.");
    renderOptions('');

    addBotMessage("Perfeito! Registrando seu agendamento... ⏳");

    try {
        const payload = {
            data_hora: botState.time,
            service_ids: [botState.serviceId],
            add_to_google_calendar: botState.addToCalendar
        };

        await apiPost('/api/appointments', payload);
        addBotMessage("🎉 Tudo certo! Seu agendamento foi solicitado com sucesso.");
        addBotMessage("Você pode conferir o status na sua lista de agendamentos. Nos vemos em breve!");

        if (typeof loadClientDashboard === 'function') {
            loadClientDashboard();
        } else if (typeof loadMyAppointments === 'function') {
            loadMyAppointments();
        }

        setTimeout(() => {
            renderOptions(`<button class="btn chatbot-option-btn w-100 text-center" onclick="resetChatbot()">Fazer outro agendamento</button>`);
        }, 2000);

    } catch (err) {
        addBotMessage(`Ops, deu erro: ${err.message}`);
        renderOptions(`<button class="btn chatbot-option-btn w-100 text-center" onclick="initChatbot()">Tentar Novamente</button>`);
    }
}

window.resetChatbot = function () {
    sessionStorage.removeItem('leilaBotState');
    botState = { step: 0, serviceId: null, duration: null, date: null, time: null, addToCalendar: false, isOpen: true, messagesHtml: '', inputAreaHtml: '' };
    initChatbot();
}
