(function () {
  function ready(data){
    try { window.JURIS_DATA = data || {}; }
    catch(e){ console.error('JURIS_DATA assign failed', e); }
    window.dispatchEvent(new Event('juris:ready'));
  }

  fetch('{{ url_for("static", filename="data/jurisdictions.json") }}', {cache: 'no-store'})
    .then(r => r.json())
    .then(ready)
    .catch(err => { console.warn('Could not load jurisdictions.json', err); ready({ countries:{} }); });
})();
