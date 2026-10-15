(() => {
  const section = document.querySelector('.challenge-testcase-editor');
  if (!section) return;

  const list = section.querySelector('[data-test-case-list]');
  const template = section.querySelector('[data-test-case-template]');
  const addButton = section.querySelector('[data-add-test-case]');
  const prefix = section.dataset.formsetPrefix;
  const totalForms = section.querySelector(`[name="${prefix}-TOTAL_FORMS"]`);

  addButton.addEventListener('click', () => {
    const index = Number(totalForms.value);
    const row = document.createElement('div');
    row.innerHTML = template.innerHTML.replaceAll('__prefix__', index);
    list.append(row.firstElementChild);
    totalForms.value = index + 1;
  });

  list.addEventListener('change', (event) => {
    if (event.target.matches('input[type="checkbox"][name$="-DELETE"]') && event.target.checked) {
      event.target.closest('[data-test-case-row]').hidden = true;
    }
  });
})();