// Dynamically set API base URL for local dev and production
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://your-backend.onrender.com';

// Cache all frequently-used DOM nodes
const DOM = {
  loginSection: document.getElementById('login'),
  createEventSection: document.getElementById('create-event'),
  profileSection: document.getElementById('profile'),
  eventGrid: document.querySelector('.event-grid'),
  loginForm: document.getElementById('login-form'),
  eventForm: document.getElementById('event-form'),
  calendarView: document.getElementById('calendar-view'),
  profileInfo: document.getElementById('profile-info'),
  logoutButton: document.getElementById('logout-button'),
  navCreateEvent: document.getElementById('nav-create-event'),
  navProfile: document.getElementById('nav-profile'),
  icsUrl: document.getElementById('ics-url'), // For calendar feed URL
};

// Utility functions
const Utils = {
  isValidEmail: email => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email),
  handleError: err => console.error('Error:', err),
  formatDate: date => new Date(date).toLocaleString(),
};

// Authentication methods
const Auth = {
  async login(email, password) {
    if (!Utils.isValidEmail(email)) throw new Error('Invalid email format');
    if (!password) throw new Error('Password is required');

    const res = await fetch(`${API_BASE_URL}/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password }),
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail?.message || `Login failed: ${res.statusText}`);
    }
    const { access_token, refresh_token } = await res.json();
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    return { access_token, refresh_token };
  },

  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) throw new Error('No refresh token available');

    const res = await fetch(`${API_BASE_URL}/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) throw new Error('Failed to refresh token');
    const { access_token } = await res.json();
    localStorage.setItem('access_token', access_token);
    return access_token;
  },

  getToken() {
    return localStorage.getItem('access_token');
  },

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};

// Wrap all backend calls to automatically add Authorization header
const API = {
  async request(path, options = {}) {
    const token = Auth.getToken();
    const headers = { ...(options.headers || {}) };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    });

    if (res.status === 401) {
      try {
        await Auth.refreshToken();
        return this.request(path, options); // Retry with new token
      } catch (err) {
        Auth.logout();
        throw new Error('Session expired. Please log in again.');
      }
    }

    if (!res.ok) throw new Error((await res.json()).detail?.message || res.statusText);
    return res.json();
  },

  fetchEvents: () => API.request('/events'),
  fetchEvent: id => API.request(`/events/${id}`),
  createEvent: data => API.request('/events', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }),
  deleteEvent: id => API.request(`/events/${id}`, { method: 'DELETE' }),
  fetchProfile: () => API.request('/users/me'),
};

// UI-rendering helpers
const UI = {
  showSection(section, show = true) {
    [DOM.loginSection, DOM.createEventSection, DOM.profileSection].forEach(
      sec => (sec.style.display = sec === section ? (show ? 'block' : 'none') : 'none')
    );
    [DOM.navCreateEvent, DOM.navProfile].forEach(
      nav => (nav.style.display = show && section !== DOM.loginSection ? 'block' : 'none')
    );
  },

  showMessage(containerSelector, html, isError = false) {
    const container = document.querySelector(containerSelector);
    container.innerHTML = `<p aria-live="polite" class="${isError ? 'error' : ''}">${html}</p>`;
  },

  showLoading(containerSelector) {
    this.showMessage(containerSelector, 'Loading...');
  },

  renderEvents(events) {
    if (!events.length) {
      this.showMessage('.event-grid', 'No events found.');
      return;
    }

    DOM.eventGrid.innerHTML = events
      .map(
        e => `
      <div class="event-card" role="article" data-id="${e.id}">
        <h3>${e.title || 'Untitled Event'}</h3>
        <p>${e.description || 'No description'}</p>
        <p>Start: ${Utils.formatDate(e.start_time)}</p>
        <p>End: ${Utils.formatDate(e.end_time)}</p>
        <button class="view-details" aria-label="View details for ${e.title || 'event'}">
          View Details
        </button>
        <button class="delete-event" aria-label="Delete ${e.title || 'event'}">
          Delete
        </button>
      </div>
    `
      )
      .join('');
  },

  openModal(contentHtml) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-content">
        ${contentHtml}
        <span class="close-modal" role="button" tabindex="0">&times;</span>
      </div>
    `;
    document.body.appendChild(modal);
    modal.style.display = 'flex';

    const closeBtn = modal.querySelector('.close-modal');
    closeBtn.focus();
    const removeModal = () => modal.remove();

    closeBtn.addEventListener('click', removeModal);
    closeBtn.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') removeModal();
    });
    modal.addEventListener('click', e => {
      if (e.target === modal) removeModal();
    });
  },

  updateIcsUrl() {
    if (DOM.icsUrl) {
      DOM.icsUrl.textContent = Auth.getToken()
        ? `${API_BASE_URL}/calendar/feed.ics`
        : 'Log in to get your calendar feed URL.';
    }
  },
};

// Core application logic
const App = {
  async loadEvents() {
    if (!Auth.getToken()) {
      UI.showMessage('.event-grid', 'Please log in to view events.');
      UI.showMessage('#calendar-view', 'Please log in to view calendar.', false);
      return;
    }
    UI.showLoading('.event-grid');
    UI.showLoading('#calendar-view');
    try {
      const events = await API.fetchEvents();
      UI.renderEvents(events);
      this.initCalendar(events);
    } catch (err) {
      Utils.handleError(err);
      UI.showMessage('.event-grid', 'Error loading events. Please try again.', true);
      UI.showMessage('#calendar-view', 'Error loading calendar.', true);
    }
  },

  async showEventDetails(id) {
    try {
      const e = await API.fetchEvent(id);
      UI.openModal(`
        <h2>${e.title || 'Untitled Event'}</h2>
        <p>${e.description || 'No description'}</p>
        <p>Start: ${Utils.formatDate(e.start_time)}</p>
        <p>End: ${Utils.formatDate(e.end_time)}</p>
      `);
    } catch (err) {
      Utils.handleError(err);
      alert(`Failed to load event details: ${err.message}`);
    }
  },

  async deleteEvent(id) {
    if (!confirm('Are you sure you want to delete this event?')) return;
    try {
      await API.deleteEvent(id);
      await this.loadEvents();
      alert('Event deleted successfully!');
    } catch (err) {
      Utils.handleError(err);
      alert(`Failed to delete event: ${err.message}`);
    }
  },

  async createEvent(data) {
    await API.createEvent({
      title: data.title,
      description: data.description,
      start_time: new Date(data.start_time).toISOString(),
      end_time: new Date(data.end_time).toISOString(),
    });
    await this.loadEvents();
  },

  async loadProfile() {
    try {
      const u = await API.fetchProfile();
      DOM.profileInfo.textContent = `Welcome, ${u.email}`;
    } catch (err) {
      Utils.handleError(err);
      DOM.profileInfo.textContent = 'Error loading profile';
    }
  },

  initCalendar(events = []) {
    if (!DOM.calendarView) return;
    DOM.calendarView.innerHTML = ''; // Clear previous calendar
    const calendar = new FullCalendar.Calendar(DOM.calendarView, {
      initialView: 'dayGridMonth',
      events: events.map(e => ({
        id: e.id,
        title: e.title,
        start: e.start_time,
        end: e.end_time,
        extendedProps: { description: e.description },
      })),
      eventClick: info => this.showEventDetails(info.event.id),
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,timeGridDay',
      },
    });
    calendar.render();
  },

  initNav() {
    document.querySelectorAll('nav a').forEach(a => {
      a.addEventListener('click', e => {
        e.preventDefault();
        document
          .getElementById(a.getAttribute('href').slice(1))
          .scrollIntoView({ behavior: 'smooth' });
      });
    });
  },

  bindEvents() {
    // LOGIN
    DOM.loginForm.addEventListener('submit', async e => {
      e.preventDefault();
      const email = e.target.username.value;
      const password = e.target.password.value;
      try {
        await Auth.login(email, password);
        UI.showSection(DOM.createEventSection);
        UI.showSection(DOM.profileSection);
        await this.loadEvents();
        await this.loadProfile();
        UI.updateIcsUrl();
      } catch (err) {
        alert(`Login failed: ${err.message}`);
      }
    });

    // CREATE EVENT
    DOM.eventForm.addEventListener('submit', async e => {
      e.preventDefault();
      const title = e.target['event-title'].value.trim();
      const description = e.target['event-desc'].value.trim();
      const start_time = e.target['event-start'].value;
      const end_time = e.target['event-end'].value;

      if (!title) return alert('Event title is required');
      if (!start_time || !end_time) return alert('Start and end times are required');
      if (new Date(end_time) <= new Date(start_time))
        return alert('End time must be after start time');

      try {
        await this.createEvent({ title, description, start_time, end_time });
        alert('Event created successfully!');
        e.target.reset();
      } catch (err) {
        alert(`Failed to create event: ${err.message}`);
      }
    });

    // DELEGATE: View Details and Delete buttons
    DOM.eventGrid.addEventListener('click', e => {
      if (e.target.matches('.view-details')) {
        const id = e.target.closest('.event-card').dataset.id;
        this.showEventDetails(id);
      } else if (e.target.matches('.delete-event')) {
        const id = e.target.closest('.event-card').dataset.id;
        this.deleteEvent(id);
      }
    });

    // LOGOUT
    DOM.logoutButton.addEventListener('click', () => {
      Auth.logout();
      UI.showSection(DOM.loginSection);
      UI.showMessage('.event-grid', 'Please log in to view events.');
      DOM.calendarView.innerHTML = '';
      DOM.profileInfo.textContent = 'Log in to view your profile.';
      UI.updateIcsUrl();
    });
  },

  async init() {
    this.bindEvents();
    this.initNav();
    UI.updateIcsUrl();

    const token = Auth.getToken();
    if (token) {
      UI.showSection(DOM.createEventSection);
      UI.showSection(DOM.profileSection);
      await this.loadEvents();
      await this.loadProfile();
    } else {
      UI.showSection(DOM.loginSection);
      UI.showMessage('.event-grid', 'Please log in to view events.');
    }
  },
};

// Bootstrap after DOM is ready
document.addEventListener('DOMContentLoaded', () => App.init());
