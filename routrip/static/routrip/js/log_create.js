document.getElementById('add-card').addEventListener('click', () => {
  const totalInput = document.querySelector('[name$="-TOTAL_FORMS"]');
  const index = Number(totalInput.value);

  const html = document.getElementById('card-template').innerHTML
    .replaceAll('__prefix__', index);
  document.getElementById('card-list').insertAdjacentHTML('beforeend', html);

  totalInput.value = index + 1;
});