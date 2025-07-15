// results.js

document.addEventListener('DOMContentLoaded', () => {
  const filterBox = document.getElementById('filter-detections');
  const cards = document.querySelectorAll('#cards .card');

  filterBox.addEventListener('change', () => {
    cards.forEach(card => {
      const has = card.getAttribute('data-has-detections') === 'True';
      card.style.display = filterBox.checked && !has ? 'none' : '';
    });
  });
});