// app.js

const API_BASE_URL = 'https://your-backend.onrender.com';

// Cache all frequently-used DOM nodes
const DOM = {
  loginSection:      document.getElementById('login'),
  createEventSection:document.getElementById('create-event'),
  profileSection:    document.getElementById('profile'),
  eventGrid:         document.querySelector('.event-grid'),
  loginForm:         document.getElementById('login-form'),
  eventForm:         document.getElementById('event-form'),
  calendarView:      document.getElementById('calendar-view'),
  profileInfo:       document.getElementById('profile-info'),
};

// Utility functions
const Utils = {
  isValidEmail: email => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email),
  handleError: err => console.error(err),
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

    if (!res.ok) throw new Error(`Login failed: ${res.statusText}`);
    const { access_token } = await res.json();
    localStorage.setItem('token', access_token);
    return access_token;
  },

  getToken() {
    return localStorage.getItem('token');
  }
};

// Wrap all backend calls to automatically add Authorization header
const API = {
  async request(path, options = {}) {
    const token = Auth.getToken();
    const headers = { ...(options.headers || {}) };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers
    });

    if (!res.ok) throw new Error(res.statusText);
    return res.json();
  },

  fetchEvents: ()      => API.request('/events'),
  fetchEvent: id       => API.request(`/events/${id}`),
  createEvent: data    => API.request('/events', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(data)
  }),
  fetchProfile: ()     => API.request('/users/me'),
};

// UI-rendering helpers
const UI = {
  showSection(section) {
    [DOM.loginSection, DOM.createEventSection, DOM.profileSection]
      .forEach(sec => sec.style.display = sec === section ? 'block' : 'none');
  },

  showMessage(containerSelector, html) {
    document.querySelector(containerSelector).innerHTML = html;
  },

  showLoading() {
    DOM.eventGrid.innerHTML = '<p aria-live="polite">Loading events...</p>';
  },

  renderEvents(events) {
    if (!events.length) {
      DOM.eventGrid.innerHTML = '<p aria-live="polite">No events found.</p>';
      return;
    }

    DOM.eventGrid.innerHTML = events.map(e => `
      <div class="event-card" role="article" data-id="${e.id}">
        <h3>${e.title || 'Untitled Event'}</h3>
        <p>${e.description || 'No description'}</p>
        <p>Start: ${new Date(e.start_time).toLocaleString()}</p>
        <button class="view-details"
                aria-label="View details for ${e.title || 'event'}">
          View Details
        </button>
      </div>
    `).join('');
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

    closeBtn.addEventListener('click',  removeModal);
    closeBtn.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') removeModal();
    });
    modal.addEventListener('click', e => {
      if (e.target === modal) removeModal();
    });
  }
};

// Core application logic
const App = {
  // Load & render the event list
  async loadEvents() {
    if (!Auth.getToken()) {
      UI.showMessage('.event-grid', '<p aria-live="polite">Please log in to view events.</p>');
      return;
    }
    UI.showLoading();
    try {
      const events = await API.fetchEvents();
      UI.renderEvents(events);
    } catch (err) {
      Utils.handleError(err);
      UI.showMessage('.event-grid', '<p aria-live="polite">Error loading events. Please try again.</p>');
    }
  },

  // Open detail modal for a single event
  async showEventDetails(id) {
    try {
      const e = await API.fetchEvent(id);
      UI.openModal(`
        <h2>${e.title || 'Untitled Event'}</h2>
        <p>${e.description || 'No description'}</p>
        <p>Start: ${new Date(e.start_time).toLocaleString()}</p>
        <p>End:   ${new Date(e.end_time).toLocaleString()}</p>
      `);
    } catch (err) {
      Utils.handleError(err);
      alert(`Failed to load event details: ${err.message}`);
    }
  },

  // POST a new event then refresh the list
  async createEvent(data) {
    await API.createEvent(data);
    await this.loadEvents();
  },

  // Fetch & display user profile
  async loadProfile() {
    try {
      const u = await API.fetchProfile();
      DOM.profileInfo.textContent = `Welcome, ${u.email}`;
    } catch (err) {
      Utils.handleError(err);
      DOM.profileInfo.textContent = 'Error loading profile';
    }
  },

  // Initialize FullCalendar
  initCalendar() {
    if (!DOM.calendarView) return;
    const calendar = new FullCalendar.Calendar(DOM.calendarView, {
      initialView: 'dayGridMonth',
      events: () => this.loadEvents(),
      eventClick: info => this.showEventDetails(info.event.id),
      headerToolbar: {
        left:   'prev,next today',
        center: 'title',
        right:  'dayGridMonth,timeGridWeek,timeGridDay'
      }
    });
    calendar.render();
  },

  // Smooth-scroll nav links
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

  // Wire up form submissions & grid clicks
  bindEvents() {
    // LOGIN
    DOM.loginForm.addEventListener('submit', async e => {
      e.preventDefault();
      const email    = e.target.username.value;
      const password = e.target.password.value;
      try {
        await Auth.login(email, password);
        UI.showSection(DOM.createEventSection);
        UI.showSection(DOM.profileSection);
        await this.loadEvents();
        await this.loadProfile();
        this.initCalendar();
      } catch (err) {
        alert(`Login failed: ${err.message}`);
      }
    });

    // CREATE EVENT
    DOM.eventForm.addEventListener('submit', async e => {
      e.preventDefault();
      const title = e.target['event-title'].value.trim();
      const desc  = e.target['event-desc'].value.trim();
      const start = e.target['event-start'].value;
      const end   = e.target['event-end'].value;

      if (!title) return alert('Event title is required');
      if (!start || !end) return alert('Start and end times are required');
      if (new Date(end) <= new Date(start))
        return alert('End time must be after start time');

      try {
        await this.createEvent({ title, description: desc, start_time: start, end_time: end });
        alert('Event created successfully!');
        e.target.reset();
      } catch (err) {
        alert(err.message);
      }
    });

    // DELEGATE: View Details buttons inside .event-grid
    DOM.eventGrid.addEventListener('click', e => {
      if (e.target.matches('.view-details')) {
        const id = e.target.closest('.event-card').dataset.id;
        this.showEventDetails(id);
      }
    });
  },

  // App startup
  async init() {
    this.bindEvents();
    this.initNav();

    const token = Auth.getToken();
    if (token) {
      UI.showSection(DOM.createEventSection);
      UI.showSection(DOM.profileSection);
      await this.loadEvents();
      await this.loadProfile();
      this.initCalendar();
    } else {
      UI.showSection(DOM.loginSection);
      UI.showMessage('.event-grid', '<p aria-live="polite">Please log in to view events.</p>');
    }
  }
};

// Bootstrap after DOM is ready
document.addEventListener('DOMContentLoaded', () => App.init());
