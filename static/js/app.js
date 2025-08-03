
// Replace with your FastAPI backend URL
const API_BASE_URL = 'https://your-backend.onrender.com';

// Authentication
async function login(username, password) {
  const response = await fetch(`${API_BASE_URL}/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username, password })
  });
  if (!response.ok) throw new Error('Login failed');
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
  return data.access_token;
}

// Fetch events with token
async function fetchEvents() {
  const token = localStorage.getItem('token');
  if (!token) {
    console.error('No token found, please login');
    document.querySelector('.event-grid').innerHTML = '<p>Please log in to view events.</p>';
    return [];
  }
  try {
    const response = await fetch(`${API_BASE_URL}/events`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Failed to fetch events');
    return await response.json();
  } catch (error) {
    console.error('Error fetching events:', error);
    return [];
  }
}

// Display events in grid
async function displayEvents() {
  const eventGrid = document.querySelector('.event-grid');
  if (!eventGrid) return;

  const events = await fetchEvents();
  eventGrid.innerHTML = '';

  events.forEach(event => {
    const card = document.createElement('div');
    card.className = 'event-card';
    card.innerHTML = `
      <h3>${event.title || 'Untitled Event'}</h3>
      <p>${event.description || 'No description'}</p>
      <p>Start: ${new Date(event.start_time).toLocaleString()}</p>
      <button onclick="showEventDetails(${event.id})">View Details</button>
    `;
    eventGrid.appendChild(card);
  });
}

// Show event details in modal
async function showEventDetails(eventId) {
  const token = localStorage.getItem('token');
  try {
    const response = await fetch(`${API_BASE_URL}/events/${eventId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Failed to fetch event details');
    const event = await response.json();

    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-content">
        <span class="close-modal" onclick="this.parentElement.parentElement.remove()">&times;</span>
        <h2>${event.title || 'Untitled Event'}</h2>
        <p>${event.description || 'No description'}</p>
        <p>Start: ${new Date(event.start_time).toLocaleString()}</p>
        <p>End: ${new Date(event.end_time).toLocaleString()}</p>
      </div>
    `;
    document.body.appendChild(modal);
    modal.style.display = 'flex';
  } catch (error) {
    console.error('Error fetching event details:', error);
  }
}

// Create event
async function createEvent(eventData) {
  const token = localStorage.getItem('token');
  try {
    const response = await fetch(`${API_BASE_URL}/events`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(eventData)
    });
    if (!response.ok) throw new Error('Failed to create event');
    await displayEvents();
  } catch (error) {
    console.error('Error creating event:', error);
    alert('Failed to create event: ' + error.message);
  }
}

// Fetch and display user profile
async function fetchProfile() {
  const token = localStorage.getItem('token');
  try {
    const response = await fetch(`${API_BASE_URL}/users/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Failed to fetch profile');
    const user = await response.json();
    document.getElementById('profile-info').textContent = `Welcome, ${user.email}`;
  } catch (error) {
    console.error('Error fetching profile:', error);
  }
}

// Smooth scrolling for navigation
document.querySelectorAll('nav a').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    e.preventDefault();
    const targetId = this.getAttribute('href').substring(1);
    const target = document.getElementById(targetId);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  });
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  const token = localStorage.getItem('token');
  const loginSection = document.getElementById('login');
  const createEventSection = document.getElementById('create-event');
  const profileSection = document.getElementById('profile');

  if (token) {
    loginSection.style.display = 'none';
    createEventSection.style.display = 'block';
    profileSection.style.display = 'block';
    displayEvents();
    fetchProfile();
    const calendarEl = document.getElementById('calendar-view');
    const calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      events: async () => await fetchEvents(),
      eventClick: (info) => showEventDetails(info.event.id)
    });
    calendar.render();
  } else {
    loginSection.style.display = 'block';
    createEventSection.style.display = 'none';
    profileSection.style.display = 'none';
  }

  document.getElementById('login-form').onsubmit = async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    try {
      await login(username, password);
      loginSection.style.display = 'none';
      createEventSection.style.display = 'block';
      profileSection.style.display = 'block';
      displayEvents();
      fetchProfile();
      const calendarEl = document.getElementById('calendar-view');
      const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: async () => await fetchEvents(),
        eventClick: (info) => showEventDetails(info.event.id)
      });
      calendar.render();
    } catch (error) {
      alert('Login failed: ' + error.message);
    }
  };

  document.getElementById('event-form').onsubmit = async (e) => {
    e.preventDefault();
    const eventData = {
      title: document.getElementById('event-title').value,
      description: document.getElementById('event-desc').value,
      start_time: document.getElementById('event-start').value,
      end_time: document.getElementById('event-end').value
    };
    await createEvent(eventData);
    document.getElementById('event-form').reset();
  };

  // Close modal on outside click
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
      e.target.remove();
    }
  });
});
