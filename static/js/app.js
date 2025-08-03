// Authentication
async function login(username, password) {
  const response = await fetch('/token', {
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
    return [];
  }
  try {
    const response = await fetch('/events', {
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
    const response = await fetch(`/events/${eventId}`, {
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
  // Example login (replace with actual form handling)
  login('user@example.com', 'password').then(() => {
    displayEvents();
  }).catch(error => {
    console.error('Initialization error:', error);
    document.querySelector('.event-grid').innerHTML = '<p>Please log in to view events.</p>';
  });

  // Close modal on outside click
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
      e.target.remove();
    }
  });
});
