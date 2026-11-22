/**
 * main.js - JavaScript chinh cua he thong
 * SYS Viet Nam - 2026
 */

// ---- Sidebar toggle (mobile) ----
document.addEventListener('DOMContentLoaded', function () {
  const toggleBtn = document.getElementById('sidebarToggle');
  const sidebar   = document.getElementById('sidebar');
  const overlay   = document.getElementById('sidebarOverlay');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      overlay && overlay.classList.toggle('show');
    });
  }
  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar && sidebar.classList.remove('open');
      overlay.classList.remove('show');
    });
  }

  // ---- Auto close flash alerts ----
  document.querySelectorAll('.alert').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity .4s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    }, 4500);
    const closeBtn = el.querySelector('.alert-close');
    if (closeBtn) closeBtn.addEventListener('click', () => el.remove());
  });

  // ---- Modal helpers ----
  document.querySelectorAll('[data-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.modal;
      openModal(id);
    });
  });
  document.querySelectorAll('.modal-close, [data-modal-close]').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.modal-overlay').classList.remove('show');
    });
  });
  document.querySelectorAll('.modal-overlay').forEach(ov => {
    ov.addEventListener('click', e => {
      if (e.target === ov) ov.classList.remove('show');
    });
  });

  // ---- Active nav link ----
  const path = window.location.pathname.split('/')[1] || '';
  document.querySelectorAll('.nav-item a').forEach(link => {
    const href = link.getAttribute('href').replace('/', '').split('/')[0];
    if (href === path || (path === '' && href === '')) {
      link.classList.add('active');
    }
  });

  // ---- Number counter animation ----
  animateCounters();

  // ---- Confirm delete ----
  document.querySelectorAll('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', e => {
      if (!confirm(form.dataset.confirm || 'Bạn có chắc muốn xóa?')) {
        e.preventDefault();
      }
    });
  });

  // ---- Platform filter (dashboard) ----
  const platformRadios = document.querySelectorAll('input[name="platform_filter"]');
  if (platformRadios.length) {
    platformRadios.forEach(radio => {
      radio.addEventListener('change', () => {
        const platId = radio.value;
        fetch(`/api/stats/overview?platform=${platId}`)
          .then(r => r.json())
          .then(data => updateDashboardStats(data))
          .catch(console.error);
      });
    });
  }

  // ---- Tooltip simple ----
  document.querySelectorAll('[title]').forEach(el => {
    el.setAttribute('data-title', el.getAttribute('title'));
  });
});

// ---- Open / Close modal ----
function openModal(id) {
  const ov = document.getElementById(id);
  if (ov) ov.classList.add('show');
}
function closeModal(id) {
  const ov = document.getElementById(id);
  if (ov) ov.classList.remove('show');
}

// ---- Populate edit modal ----
function fillEditModal(modalId, data) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  Object.keys(data).forEach(key => {
    const el = modal.querySelector(`[name="${key}"]`);
    if (el) el.value = data[key];
  });
  openModal(modalId);
}

// ---- Counter animation ----
function animateCounters() {
  const els = document.querySelectorAll('.stat-card-value[data-value]');
  els.forEach(el => {
    const target = parseFloat(el.dataset.value) || 0;
    const isInt  = Number.isInteger(target);
    const duration = 1000;
    const step = 16;
    const steps = duration / step;
    let current = 0;
    const inc = target / steps;
    const timer = setInterval(() => {
      current += inc;
      if (current >= target) { current = target; clearInterval(timer); }
      el.textContent = isInt ? formatNumber(Math.floor(current)) : current.toFixed(2);
    }, step);
  });
}

// ---- Format number ----
function formatNumber(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000)    return (n / 1000).toFixed(1)    + 'K';
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

// ---- Update dashboard stats khi doi platform filter ----
function updateDashboardStats(data) {
  const setVal = (sel, val, fmt) => {
    const el = document.querySelector(sel);
    if (el) el.textContent = fmt ? fmt(val) : val;
  };
  setVal('#stat-videos', data.total_videos, formatNumber);
  setVal('#stat-views',  data.total_views,  formatNumber);
  setVal('#stat-interactions', data.total_interactions, formatNumber);
  setVal('#stat-orders', data.total_orders, formatNumber);
  setVal('#stat-engagement', data.engagement_rate, v => v.toFixed(2) + '%');
  setVal('#stat-op1k', data.orders_per_1000, v => v.toFixed(2));
}

// ---- Confirm xoa ----
function confirmDelete(formId, msg) {
  if (confirm(msg || 'Bạn có chắc muốn xóa mục này không?')) {
    document.getElementById(formId).submit();
  }
}

// ---- Format VND ----
function formatVND(n) {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(n);
}

// ---- Chart helpers ----
function makeLineChart(canvasId, labels, datasets, opts = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  return new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'top',
          labels: { font: { size: 12 }, boxWidth: 12, padding: 16 }
        },
        tooltip: {
          callbacks: {
            label: ctx => {
              const v = ctx.parsed.y;
              return ` ${ctx.dataset.label}: ${formatNumber(v)}`;
            }
          }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 11 }, maxTicksLimit: 10 } },
        y: {
          beginAtZero: true,
          grid: { color: '#F1F5F9' },
          ticks: { font: { size: 11 }, callback: v => formatNumber(v) },
          ...( opts.yRight ? {} : {} )
        },
        ...( opts.yRight ? {
          y1: {
            type: 'linear', position: 'right', beginAtZero: true,
            grid: { drawOnChartArea: false },
            ticks: { font: { size: 11 }, callback: v => formatNumber(v) }
          }
        } : {} )
      }
    }
  });
}

function makeBarChart(canvasId, labels, datasets) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  return new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { labels: { font: { size: 12 }, boxWidth: 12 } },
        tooltip: {
          callbacks: { label: ctx => ` ${ctx.dataset.label}: ${formatNumber(ctx.parsed.y)}` }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 11 } } },
        y: {
          beginAtZero: true, grid: { color: '#F1F5F9' },
          ticks: { font: { size: 11 }, callback: v => formatNumber(v) }
        }
      }
    }
  });
}

function makeDoughnutChart(canvasId, labels, data, colors) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  return new Chart(ctx, {
    type: 'doughnut',
    data: { labels, datasets: [{ data, backgroundColor: colors, borderWidth: 2, borderColor: '#fff' }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '70%',
      plugins: {
        legend: { position: 'bottom', labels: { font: { size: 12 }, boxWidth: 12, padding: 12 } }
      }
    }
  });
}
