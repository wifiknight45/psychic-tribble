// Dynamically set API base URL for local dev and production
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://your-backend.onrender.com';

// Cache DOM nodes
const DOM = {
  authModal: document.getElementById('authModal'),
  modalTitle: document.getElementById('modalTitle'),
  authForm: document.getElementById('authForm'),
  authEmail: document.getElementById('authEmail'),
  authPassword: document.getElementById('authPassword'),
  authSpinner: document.getElementById('authSpinner'),
  authSubmitText: document.getElementById('authSubmitText'),
  toggleAuth: document.getElementById('toggleAuth'),
  closeModal: document.querySelector('#authModal .close-modal'),
  createEventSection: document.getElementById('create-event'),
  profileSection: document.getElementById('profile'),
  eventGrid: document.querySelector('.event-grid'),
  eventForm: document.getElementById('event-form'),
  calendarView: document.getElementById('calendar-view'),
  profileInfo: document.getElementById('profile-info'),
  logoutButton: document.getElementById('logout-button'),
  navCalendar: document.getElementById('nav-calendar'),
  navProfile: document.getElementById('nav-profile'),
  icsUrl: document.getElementById('ics-url'),
  statusContainer: document.getElementById('statusContainer'),
};

// Utility class
class Utils {
  static isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }
  static handleError(err) {
    console.error('Error:', err);
  }
  static formatDate(date) {
    return new Date(date).toLocaleString();
  }
  static showStatus(message, isSuccess = true) {
    DOM.statusContainer.innerHTML = `
      <div class="status-message ${isSuccess ? 'status-success' : 'status-error'} show">
        ${message}
      </div>
    `;
    setTimeout(() => {
      const msg = DOM.statusContainer.querySelector('.status-message');
      if (msg) msg.classList.remove('show');
    }, 5000);
  }
}

// Auth class
class Auth {
  static async login(email, password) {
    if (!Utils.isValidEmail(email)) throw new Error('Invalid email format');
    if (!password) throw new Error('Password is required');
    const res = await this._fetch('/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password }),
    });
    const { access_token, refresh_token } = await res.json();
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    return { access_token, refresh_token };
  }

  static async signup(email, password) {
    if (!Utils.isValidEmail(email)) throw new Error('Invalid email format');
    if (!password) throw new Error('Password is required');
    const res = await this._fetch('/register', {  // Assuming /register endpoint
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    Utils.showStatus('Signup successful! Logging in...', true);
    return this.login(email, password);  // Auto-login after signup
  }

  static async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) throw new Error('No refresh token available');
    const res = await this._fetch('/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    const { access_token } = await res.json();
    localStorage.setItem('access_token', access_token);
    return access_token;
  }

  static getToken() {
    return localStorage.getItem('access_token');
  }

  static logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  static async _fetch(path, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);  // 10s timeout
    try {
      const res = await fetch(`${API_BASE_URL}${path}`, { ...options, signal: controller.signal });
      clearTimeout(timeoutId);
      if (!res.ok) throw new Error(await res.text());
      return res;
    } catch (err) {
      clearTimeout(timeoutId);
      throw err;
    }
  }
}

// API class with auth
class API {
  static async request(path, options = {}) {
    let token = Auth.getToken();
    const headers = { ...(options.headers || {}) };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
      const res = await Auth._fetch(path, { ...options, headers });
      return await res.json();
    } catch (err) {
      if (err.message.includes('401')) {
        try {
          token = await Auth.refreshToken();
          headers['Authorization'] = `Bearer ${token}`;
          return await (await Auth._fetch(path, { ...options, headers })).json();
        } catch {
          Auth.logout();
          throw new Error('Session expired. Please log in again.');
        }
      }
      throw err;
    }
  }

  static fetchEvents() { return this.request('/events'); }
  static fetchEvent(id) { return this.request(`/events/${id}`); }
  static createEvent(data) {
    return this.request('/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  }
  static deleteEvent(id) { return this.request(`/events/${id}`, { method: 'DELETE' }); }
  static fetchProfile() { return this.request('/users/me'); }
}

// UI class
class UI {
  static showAuthModal(show = true) {
    DOM.authModal.classList.toggle('active', show);
  }

  static toggleSections(show = true) {
    DOM.createEventSection.style.display = show ? 'block' : 'none';
    DOM.profileSection.style.display = show ? 'block' : 'none';
    DOM.navCalendar.style.display = show ? 'inline' : 'none';
    DOM.navProfile.style.display = show ? 'inline' : 'none';
  }

  static showLoading(container, show = true) {
    container.classList.toggle('loading', show);
  }

  static renderEvents(events) {
    if (!events?.length) {
      DOM.eventGrid.innerHTML = '<p>No events found.</p>';
      return;
    }
    DOM.eventGrid.innerHTML = events.map(e => `
      <div class="event-card" role="article" data-id="${e.id}">
        <h3>${e.title || 'Untitled Event'}</h3>
        <p>${e.description || 'No description'}</p>
        <p>Start: ${Utils.formatDate(e.start_time)}</p>
        <p>End: ${Utils.formatDate(e.end_time)}</p>
        <button class="view-details" aria-label="View details for ${e.title || 'event'}">View Details</button>
        <button class="delete-event" aria-label="Delete ${e.title || 'event'}">Delete</button>
      </div>
    `).join('');
  }

  static openDetailsModal(contentHtml) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay active';
    modal.innerHTML = `
      <div class="modal">
        <span class="close-modal" role="button" tabindex="0" aria-label="Close modal">&times;</span>
        <div class="modal-content">${contentHtml}</div>
      </div>
    `;
    document.body.appendChild(modal);
    const closeBtn = modal.querySelector('.close-modal');
    closeBtn.focus();
    const removeModal = () => modal.remove();
    closeBtn.addEventListener('click', removeModal);
    closeBtn.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') removeModal(); });
    modal.addEventListener('click', e => { if (e.target === modal) removeModal(); });
  }

  static updateIcsUrl() {
    const token = Auth.getToken();
    if (token) {
      DOM.icsUrl.href = `${API_BASE_URL}/calendar/feed.ics`;
      DOM.icsUrl.textContent = 'Subscribe to calendar feed';
    } else {
      DOM.icsUrl.href = '#';
      DOM.icsUrl.textContent = 'Log in to get your calendar feed URL.';
    }
  }
}

// App class
class App {
  static calendar = null;
  static isSignup = false;

  static async loadEvents() {
    if (!Auth.getToken()) return;
    UI.showLoading(DOM.eventGrid);
    UI.showLoading(DOM.calendarView);
    try {
      const events = await API.fetchEvents();
      UI.renderEvents(events);
      this.updateCalendar(events);
      Utils.showStatus('Events loaded successfully', true);
    } catch (err) {
      Utils.handleError(err);
      Utils.showStatus(`Error loading events: ${err.message}`, false);
    } finally {
      UI.showLoading(DOM.eventGrid, false);
      UI.showLoading(DOM.calendarView, false);
    }
  }

  static updateCalendar(events = []) {
    if (!this.calendar) {
      this.calendar = new FullCalendar.Calendar(DOM.calendarView, {
        initialView: 'dayGridMonth',
        events: [],  // Start empty
        eventClick: info => this.showEventDetails(info.event.id),
        headerToolbar: {
          left: 'prev,next today',
          center: 'title',
          right: 'dayGridMonth,timeGridWeek,timeGridDay',
        },
      });
      this.calendar.render();
    }
    this.calendar.removeAllEvents();
    this.calendar.addEventSource(events.map(e => ({
      id: e.id,
      title: e.title,
      start: e.start_time,
      end: e.end_time,
      extendedProps: { description: e.description },
    })));
  }

  static async showEventDetails(id) {
    try {
      const e = await API.fetchEvent(id);
      UI.openDetailsModal(`
        <h2>${e.title || 'Untitled Event'}</h2>
        <p>${e.description || 'No description'}</p>
        <p>Start: ${Utils.formatDate(e.start_time)}</p>
        <p>End: ${Utils.formatDate(e.end_time)}</p>
      `);
    } catch (err) {
      Utils.handleError(err);
      Utils.showStatus(`Failed to load event details: ${err.message}`, false);
    }
  }

  static async deleteEvent(id) {
    if (!confirm('Are you sure you want to delete this event?')) return;
    try {
      await API.deleteEvent(id);
      await this.loadEvents();
      Utils.showStatus('Event deleted successfully!', true);
    } catch (err) {
      Utils.handleError(err);
      Utils.showStatus(`Failed to delete event: ${err.message}`, false);
    }
  }

  static async createEvent(data) {
    await API.createEvent({
      title: data.title,
      description: data.description,
      start_time: new Date(data.start_time).toISOString(),
      end_time: new Date(data.end_time).toISOString(),
    });
    await this.loadEvents();
    Utils.showStatus('Event created successfully!', true);
  }

  static async loadProfile() {
    try {
      const u = await API.fetchProfile();
      DOM.profileInfo.textContent = `Welcome, ${u.email}`;
    } catch (err) {
      Utils.handleError(err);
      DOM.profileInfo.textContent = 'Error loading profile';
      Utils.showStatus('Error loading profile', false);
    }
  }

  static initNav() {
    document.querySelectorAll('nav a').forEach(a => {
      a.addEventListener('click', e => {
        e.preventDefault();
        const target = document.getElementById(a.getAttribute('href').slice(1));
        if (target) target.scrollIntoView({ behavior: 'smooth' });
      });
    });
  }

  static bindEvents() {
    // Auth form submit
    DOM.authForm.addEventListener('submit', async e => {
      e.preventDefault();
      const email = DOM.authEmail.value.trim();
      const password = DOM.authPassword.value.trim();
      DOM.authSpinner.style.display = 'inline-block';
      DOM.authSubmitText.textContent = this.isSignup ? 'Signing up...' : 'Logging in...';
      try {
        if (this.isSignup) {
          await Auth.signup(email, password);
        } else {
          await Auth.login(email, password);
        }
        UI.showAuthModal(false);
        UI.toggleSections(true);
        await this.loadEvents();
        await this.loadProfile();
        UI.updateIcsUrl();
      } catch (err) {
        Utils.showStatus(`Auth failed: ${err.message}`, false);
      } finally {
        DOM.authSpinner.style.display = 'none';
        DOM.authSubmitText.textContent = this.isSignup ? 'Sign up' : 'Login';
      }
    });

    // Toggle login/signup
    DOM.toggleAuth.addEventListener('click', e => {
      e.preventDefault();
      this.isSignup = !this.isSignup;
      DOM.modalTitle.textContent = this.isSignup ? 'Sign Up' : 'Login';
      DOM.authSubmitText.textContent = this.isSignup ? 'Sign up' : 'Login';
      DOM.toggleAuth.textContent = this.isSignup ? 'Login instead' : 'Sign up instead';
    });

    // Close auth modal
    DOM.closeModal.addEventListener('click', () => UI.showAuthModal(false));
    DOM.closeModal.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') UI.showAuthModal(false);
    });
    DOM.authModal.addEventListener('click', e => {
      if (e.target === DOM.authModal) UI.showAuthModal(false);
    });

    // Create event
    DOM.eventForm.addEventListener('submit', async e => {
      e.preventDefault();
      const title = DOM.eventForm['event-title'].value.trim();
      const description = DOM.eventForm['event-desc'].value.trim();
      const start_time = DOM.eventForm['event-start'].value;
      const end_time = DOM.eventForm['event-end'].value;
      if (!title || !start_time || !end_time || new Date(end_time) <= new Date(start_time)) {
        Utils.showStatus('Invalid event details', false);
        return;
      }
      try {
        await this.createEvent({ title, description, start_time, end_time });
        DOM.eventForm.reset();
      } catch (err) {
        Utils.showStatus(`Failed to create event: ${err.message}`, false);
      }
    });

    // Event grid delegation
    DOM.eventGrid.addEventListener('click', e => {
      const card = e.target.closest('.event-card');
      if (!card) return;
      const id = card.dataset.id;
      if (e.target.matches('.view-details')) {
        this.showEventDetails(id);
      } else if (e.target.matches('.delete-event')) {
        this.deleteEvent(id);
      }
    });

    // Logout
    DOM.logoutButton.addEventListener('click', () => {
      Auth.logout();
      UI.toggleSections(false);
      UI.showAuthModal(true);
      DOM.eventGrid.innerHTML = '<p>Please log in to view events.</p>';
      if (this.calendar) this.calendar.removeAllEvents();
      DOM.profileInfo.textContent = 'Log in to view your profile.';
      UI.updateIcsUrl();
      Utils.showStatus('Logged out successfully', true);
    });
  }

  static async init() {
    this.bindEvents();
    this.initNav();
    UI.updateIcsUrl();
    const token = Auth.getToken();
    if (token) {
      UI.toggleSections(true);
      await this.loadEvents();
      await this.loadProfile();
    } else {
      UI.showAuthModal(true);
      DOM.eventGrid.innerHTML = '<p>Please log in to view events.</p>';
    }
  }
}

// Bootstrap
document.addEventListener('DOMContentLoaded', () => App.init());
