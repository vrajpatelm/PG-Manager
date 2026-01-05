// Typing Animation
const phrases = ["Made Simple", "Made Easy", "Automated", "Efficient"];
let phraseIndex = 0;
let charIndex = 0;
let isDeleting = false;
const typingSpeed = 100;
const deletingSpeed = 50;
const pauseTime = 2000;

function type() {
  const currentPhrase = phrases[phraseIndex];
  const typingElement = document.getElementById('typing-text');

  if (isDeleting) {
    typingElement.textContent = currentPhrase.substring(0, charIndex - 1);
    charIndex--;
  } else {
    typingElement.textContent = currentPhrase.substring(0, charIndex + 1);
    charIndex++;
  }

  let delay = isDeleting ? deletingSpeed : typingSpeed;

  if (!isDeleting && charIndex === currentPhrase.length) {
    delay = pauseTime;
    isDeleting = true;
  } else if (isDeleting && charIndex === 0) {
    isDeleting = false;
    phraseIndex = (phraseIndex + 1) % phrases.length;
    delay = 500;
  }

  setTimeout(type, delay);
}

// Custom Cursor
const cursor = document.querySelector('.cursor');
const cursorDot = document.querySelector('.cursor-dot');

document.addEventListener('mousemove', (e) => {
  cursor.style.left = e.clientX + 'px';
  cursor.style.top = e.clientY + 'px';
  
  cursorDot.style.left = e.clientX + 'px';
  cursorDot.style.top = e.clientY + 'px';
});

document.addEventListener('mousedown', () => {
  cursor.classList.add('click');
});

document.addEventListener('mouseup', () => {
  cursor.classList.remove('click');
});

//Floating Particles
function createParticle(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  const particle = document.createElement('div');
  particle.classList.add('particle');
  
  // Random horizontal position
  particle.style.left = Math.random() * 100 + '%';
  
  // Start particles at RANDOM heights
  particle.style.top = (Math.random() * 120 + 10) + '%'; // Start between 10% and 130%
  
  const duration = Math.random() * 6 + 8; // 8-14 seconds
  const delay = Math.random() * 5; // 0-5 second delay
  
  particle.style.animationDuration = duration + 's';
  particle.style.animationDelay = delay + 's';
  
  // Random size variation
  const size = Math.random() * 4 + 6; // 6-10px
  particle.style.width = size + 'px';
  particle.style.height = size + 'px';
  
  container.appendChild(particle);

  // Remove after animation completes
  setTimeout(() => {
    particle.remove();
  }, (duration + delay) * 1000);
}

// All particle containers
const particleContainers = [
  'particles-container',
  'particles-container-features',
  'particles-container-about',
  'particles-container-cta'
];

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
  
  // Start typing animation
  setTimeout(type, 500);
  
  // For each section, create particles continuously
  particleContainers.forEach(containerId => {
    // Create initial particles with staggered timing
    for (let i = 0; i < 15; i++) {
      setTimeout(() => createParticle(containerId), i * 400);
    }
    
    // Then create new particles continuously at random intervals
    setInterval(() => {
      createParticle(containerId);
    }, 800); // Create a new particle every 800ms
  });
  

});