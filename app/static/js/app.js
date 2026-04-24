function getToken() {
    return localStorage.getItem('access_token');
}

function getUser() {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
}

function isAuthenticated() {
    return !!getToken();
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    document.cookie = 'access_token=; path=/; max-age=0';
    window.location.href = '/login';
}

function requireAuth(requiredType) {
    if (!isAuthenticated()) {
        window.location.href = '/login';
        return;
    }
    const user = getUser();
    if (requiredType && user && user.tipo !== requiredType) {
        window.location.href = user.tipo === 'ADMIN' ? '/admin/dashboard' : '/client/dashboard';
    }
}


async function apiRequest(method, url, body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const token = getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    const options = { method, headers };
    if (body && method !== 'GET') {
        options.body = JSON.stringify(body);
    }

    const res = await fetch(url, options);
    const data = await res.json();

    if (!res.ok) {
        if (res.status === 401) {
            logout();
            return;
        }
        throw new Error(data.detail || `Erro ${res.status}`);
    }

    return data;
}

function apiGet(url) { return apiRequest('GET', url); }
function apiPost(url, body) { return apiRequest('POST', url, body); }
function apiPut(url, body) { return apiRequest('PUT', url, body); }
function apiDelete(url) { return apiRequest('DELETE', url); }


function formatDate(isoString) {
    const d = new Date(isoString);
    return d.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

function formatTime(isoString) {
    const d = new Date(isoString);
    return d.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function statusBadge(status) {
    const map = {
        PENDING: { class: 'bg-warning-subtle text-warning', icon: 'hourglass-split', label: 'Pendente' },
        APPROVED: { class: 'bg-success-subtle text-success', icon: 'check-circle', label: 'Aprovado' },
        REJECTED: { class: 'bg-danger-subtle text-danger', icon: 'x-circle', label: 'Rejeitado' },
        CANCELLED: { class: 'bg-secondary-subtle text-secondary', icon: 'dash-circle', label: 'Cancelado' },
        COMPLETED: { class: 'bg-info-subtle text-info', icon: 'check-all', label: 'Concluído' },
    };
    const s = map[status] || { class: 'bg-secondary', icon: 'question', label: status };
    return `<span class="badge ${s.class}"><i class="bi bi-${s.icon} me-1"></i>${s.label}</span>`;
}


async function showConfirmModal(title, message, onConfirm, btnClass = 'btn-primary', btnText = 'Confirmar') {
    const modalId = 'confirmModal';
    const modalHtml = `
        <div class="modal fade" id="${modalId}" tabindex="-1">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content card-glass border-white border-opacity-10 shadow-lg">
                    <div class="modal-header border-bottom border-white border-opacity-10">
                        <h5 class="modal-title fw-bold gradient-text">${title}</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body py-4">
                        <p class="mb-0 text-white opacity-75 fs-5">${message}</p>
                    </div>
                    <div class="modal-footer border-top border-white border-opacity-10">
                        <button type="button" class="btn btn-outline-light" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn ${btnClass}" id="confirmModalBtn">${btnText}</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    let existingModal = document.getElementById(modalId);
    if (existingModal) existingModal.remove();

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modalElem = document.getElementById(modalId);
    const modal = new bootstrap.Modal(modalElem);

    document.getElementById('confirmModalBtn').onclick = () => {
        onConfirm();
        modal.hide();
    };

    modal.show();
}

function showAlertModal(title, message, btnText = 'Entendi') {
    const modalId = 'alertModal';
    const modalHtml = `
        <div class="modal fade" id="${modalId}" tabindex="-1">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content card-glass border-white border-opacity-10 shadow-lg">
                    <div class="modal-header border-bottom border-white border-opacity-10">
                        <h5 class="modal-title fw-bold gradient-text">${title}</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body py-4 text-center">
                        <div class="mb-3">
                            <i class="bi bi-info-circle text-info fs-1"></i>
                        </div>
                        <p class="mb-0 text-white opacity-90 fs-5">${message}</p>
                    </div>
                    <div class="modal-footer border-top border-white border-opacity-10">
                        <button type="button" class="btn btn-primary-gradient w-100" data-bs-dismiss="modal">${btnText}</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    let existingModal = document.getElementById(modalId);
    if (existingModal) existingModal.remove();

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modalElem = document.getElementById(modalId);
    const modal = new bootstrap.Modal(modalElem);
    modal.show();
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const icons = {
        success: 'check-circle-fill',
        danger: 'exclamation-triangle-fill',
        warning: 'exclamation-circle-fill',
        info: 'info-circle-fill',
    };

    const id = `toast_${Date.now()}`;
    const html = `
        <div id="${id}" class="toast toast-custom border-${type} show" role="alert"
             style="border-left: 3px solid var(--bs-${type})">
            <div class="toast-body d-flex align-items-center">
                <i class="bi bi-${icons[type] || icons.info} text-${type} me-2 fs-5"></i>
                <span class="flex-grow-1">${message}</span>
                <button type="button" class="btn-close btn-close-white ms-2" onclick="this.closest('.toast').remove()"></button>
            </div>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', html);

    setTimeout(() => {
        const el = document.getElementById(id);
        if (el) {
            el.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            el.style.opacity = '0';
            el.style.transform = 'translateX(100%)';
            setTimeout(() => el.remove(), 300);
        }
    }, 4000);
}


function buildNavbar() {
    const menu = document.getElementById('navMenu');
    if (!menu) return;

    const user = getUser();

    if (!user) {
        menu.innerHTML = `
            <li class="nav-item"><a class="nav-link nav-link-custom" href="/login"><i class="bi bi-box-arrow-in-right me-1"></i>Login</a></li>
            <li class="nav-item"><a class="nav-link nav-link-custom" href="/register"><i class="bi bi-person-plus me-1"></i>Cadastro</a></li>
        `;
        return;
    }

    const path = window.location.pathname;

    if (user.tipo === 'ADMIN') {
        menu.innerHTML = `
            <li class="nav-item"><a class="nav-link nav-link-custom ${path === '/admin/dashboard' ? 'active' : ''}" href="/admin/dashboard"><i class="bi bi-speedometer2 me-1"></i>Dashboard</a></li>
            <li class="nav-item"><a class="nav-link nav-link-custom ${path === '/admin/calendar' ? 'active' : ''}" href="/admin/calendar"><i class="bi bi-calendar-week me-1"></i>Calendário</a></li>
            <li class="nav-item"><a class="nav-link nav-link-custom ${path === '/admin/appointments' ? 'active' : ''}" href="/admin/appointments"><i class="bi bi-card-list me-1"></i>Agendamentos</a></li>
            <li class="nav-item"><a class="nav-link nav-link-custom ${path === '/admin/clients' ? 'active' : ''}" href="/admin/clients"><i class="bi bi-people me-1"></i>Clientes</a></li>
            <li class="nav-item"><a class="nav-link nav-link-custom ${path === '/admin/services' ? 'active' : ''}" href="/admin/services"><i class="bi bi-list-stars me-1"></i>Serviços</a></li>
            ${user.email === 'renangs2222@gmail.com' ? `
                <li class="nav-item"><a class="nav-link nav-link-custom ${path === '/admin/settings' ? 'active' : ''}" href="/admin/settings"><i class="bi bi-gear me-1"></i>Config</a></li>
            ` : ''}
            <li class="nav-item"><a class="nav-link nav-link-custom" href="/swagger" target="_blank"><i class="bi bi-code-slash me-1"></i>Swagger</a></li>
            <li class="nav-item ms-lg-2">
                <a class="nav-link nav-link-custom text-danger" href="#" onclick="logout()">
                    <i class="bi bi-box-arrow-right me-1"></i>Sair
                </a>
            </li>
        `;
    } else {
        menu.innerHTML = `
            <li class="nav-item"><a class="nav-link nav-link-custom ${path === '/client/dashboard' ? 'active' : ''}" href="/client/dashboard"><i class="bi bi-house me-1"></i>Painel</a></li>
            <li class="nav-item"><a class="nav-link nav-link-custom ${path === '/client/new-appointment' ? 'active' : ''}" href="/client/new-appointment"><i class="bi bi-plus-circle me-1"></i>Agendar</a></li>
            <li class="nav-item"><a class="nav-link nav-link-custom ${path === '/client/my-appointments' ? 'active' : ''}" href="/client/my-appointments"><i class="bi bi-calendar3 me-1"></i>Meus Agendamentos</a></li>
            <li class="nav-item ms-lg-2">
                <a class="nav-link nav-link-custom text-danger" href="#" onclick="logout()">
                    <i class="bi bi-box-arrow-right me-1"></i>Sair
                </a>
            </li>
        `;
    }
}


window.addEventListener('scroll', () => {
    const navbar = document.getElementById('mainNavbar');
    if (navbar) {
        if (window.scrollY > 20) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }
});

async function syncUserData() {
    if (!isAuthenticated()) return;

    try {
        const serverUser = await apiGet('/api/auth/me');
        const localUser = getUser();

        if (!localUser || serverUser.tipo !== localUser.tipo || serverUser.email !== localUser.email) {
            console.log("Cargo do usuário mudou! Atualizando localmente...", serverUser.tipo);
            localStorage.setItem('user', JSON.stringify(serverUser));
            buildNavbar();

            const path = window.location.pathname;
            if (serverUser.tipo === 'ADMIN' && path.startsWith('/client/')) {
                window.location.href = '/admin/dashboard';
            } else if (serverUser.tipo === 'CLIENT' && path.startsWith('/admin/')) {
                window.location.href = '/client/dashboard';
            }
        }
    } catch (err) {
        console.error("Erro ao sincronizar usuário:", err);
    }
}


document.addEventListener('DOMContentLoaded', async () => {
    buildNavbar();

    await syncUserData();
});
