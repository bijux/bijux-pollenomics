// Mount supplied display choices; the host owns selection, URL state and map rendering.
function mountScientificPicker(container, catalog, owners) {
  let query = '', actionError = '';
  function render(caret = null) {
    const current = owners.read();
    container.innerHTML = renderScientificPicker(catalog, current.state, query)
      + (current.error ? `<p role="status">${escapeHtml(current.error)}</p><button type="button" class="inline-button" data-scientific-reset-pins>Reset comparison pins</button>` : '')
      + (actionError ? `<p role="status">${escapeHtml(actionError)}</p>` : '');
    if (caret !== null) {
      const input = container.querySelector('[data-scientific-query]');
      if (input) {
        input.focus();
        input.setSelectionRange(caret.start, caret.end);
      }
    }
  }
  container.addEventListener('input', event => {
    if (!event.target.matches('[data-scientific-query]')) return;
    query = event.target.value;
    render({start: event.target.selectionStart, end: event.target.selectionEnd});
  });
  container.addEventListener('click', event => {
    const reset = event.target.closest('[data-scientific-reset-pins]');
    if (reset && container.contains(reset)) {
      actionError = '';
      owners.reset();
      return;
    }
    const button = event.target.closest('[data-scientific-action]');
    if (!button || !container.contains(button) || button.disabled) return;
    const current = owners.read();
    if (current.error) return;
    const result = scientificPickerAction(catalog, current.state, {
      type: button.dataset.scientificAction, id: button.dataset.scientificId,
    });
    actionError = result.error || '';
    if (result.error) render();
    else owners.change(result.state);
  });
  return Object.freeze({render, clearSearch() { query = ''; actionError = ''; }});
}
