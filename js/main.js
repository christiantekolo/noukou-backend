/**
 * NOUKOU — Fonctions communes à toutes les pages
 */

// Navbar mobile toggle
function initNavbar() {
  const toggle = document.getElementById('nav-toggle');
  const menu = document.getElementById('nav-menu');
  
  if (toggle && menu) {
    toggle.addEventListener('click', () => {
      menu.classList.toggle('nav-open');
      toggle.classList.toggle('nav-active');
    });
    
    // Close menu on link click (mobile)
    menu.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        menu.classList.remove('nav-open');
        toggle.classList.remove('nav-active');
      });
    });
  }
  
  // Update auth button based on login state
  updateAuthUI();
}

function updateAuthUI() {
  const user = getCurrentUser();
  const authBtn = document.getElementById('auth-btn');
  if (!authBtn) return;
  
  if (user) {
    authBtn.textContent = user.prenom || 'Compte';
    authBtn.href = 'dashboard.html';
  } else {
    authBtn.textContent = 'Connexion';
    authBtn.href = 'login.html';
  }
}

// Smooth scroll
function smoothScrollTo(targetId) {
  const el = document.getElementById(targetId);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// Scroll-triggered animations
function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-in');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
  
  document.querySelectorAll('.animate-on-scroll').forEach(el => {
    observer.observe(el);
  });
}

// Navbar scroll effect
function initNavbarScroll() {
  const navbar = document.querySelector('.navbar');
  if (!navbar) return;
  
  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      navbar.classList.add('navbar-scrolled');
    } else {
      navbar.classList.remove('navbar-scrolled');
    }
  });
}

// Format numbers
function formatNumber(num, decimals = 2) {
  return parseFloat(num).toFixed(decimals);
}

// Format date
function formatDate(dateStr) {
  const d = new Date(dateStr);
  return d.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  });
}

function formatDateShort(dateStr) {
  const d = new Date(dateStr);
  return d.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
}

// Time ago
function timeAgo(dateStr) {
  const now = new Date();
  const d = new Date(dateStr);
  const diff = Math.floor((now - d) / 1000);
  
  if (diff < 60) return "À l'instant";
  if (diff < 3600) return `Il y a ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `Il y a ${Math.floor(diff / 3600)} h`;
  if (diff < 604800) return `Il y a ${Math.floor(diff / 86400)} jour(s)`;
  return formatDateShort(dateStr);
}

// Score color
function getScoreColor(score) {
  if (score >= 80) return '#84ECAE';
  if (score >= 60) return '#FFB74D';
  return '#FF7043';
}

function getScoreLabel(score) {
  if (score >= 80) return 'Excellent';
  if (score >= 60) return 'Bon';
  return 'Modéré';
}

// Init everything on page load
document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initNavbarScroll();
  initScrollAnimations();
});
