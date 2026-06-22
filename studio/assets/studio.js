(function () {
  var root = document.getElementById('proj');
  if (!root) return;
  var PID = root.dataset.id, CSRF = root.dataset.csrf;

  function post(data) {
    var fd = new FormData();
    fd.append('p', PID); fd.append('csrf', CSRF);
    Object.keys(data).forEach(function (k) { fd.append(k, data[k]); });
    return fetch('api.php', { method: 'POST', body: fd, credentials: 'same-origin' }).then(function (r) { return r.json(); });
  }

  // ---- per-image actions ----
  function rate(shot, act) {
    var nv = shot.dataset.rating === act ? 'unrated' : act;
    post({ action: 'rate', file: shot.dataset.file, rating: nv }).then(function (res) {
      if (!res.ok) return;
      shot.dataset.rating = res.rating;
      shot.classList.remove('rate-good', 'rate-bad', 'rate-unrated');
      shot.classList.add('rate-' + res.rating);
    });
  }
  function keep(shot) {
    var nv = shot.dataset.accepted === '1' ? 0 : 1;
    post({ action: 'keep', file: shot.dataset.file, accepted: nv }).then(function (res) {
      if (!res.ok) return;
      shot.dataset.accepted = res.accepted ? '1' : '0';
      shot.classList.toggle('kept', !!res.accepted);
    });
  }
  function cover(shot) { post({ action: 'cover', file: shot.dataset.file }); }
  function del(shot) {
    if (!confirm('Delete this image?')) return;
    post({ action: 'delete', file: shot.dataset.file }).then(function (res) { if (res.ok) shot.remove(); });
  }

  var gallery = document.getElementById('gallery');
  if (gallery) gallery.addEventListener('click', function (e) {
    var btn = e.target.closest('.rb[data-act]'); if (!btn) return;
    var shot = btn.closest('.shot'); if (!shot) return;
    var a = btn.dataset.act;
    if (a === 'good' || a === 'bad') rate(shot, a);
    else if (a === 'keep') keep(shot);
    else if (a === 'cover') cover(shot);
    else if (a === 'delete') del(shot);
  });

  // keyboard: act on the focused (or hovered) shot
  document.addEventListener('keydown', function (e) {
    if (/^(INPUT|TEXTAREA|SELECT)$/.test((document.activeElement || {}).tagName)) return;
    var shot = (document.activeElement && document.activeElement.closest && document.activeElement.closest('.shot')) || document.querySelector('.shot:hover');
    if (!shot) return;
    var k = e.key.toLowerCase();
    if (k === 'g') { rate(shot, 'good'); e.preventDefault(); }
    else if (k === 'b') { rate(shot, 'bad'); e.preventDefault(); }
    else if (k === 'a') { keep(shot); e.preventDefault(); }
  });

  // ---- upload (drag-drop + picker) ----
  var dz = document.getElementById('dropzone'),
      input = document.getElementById('fileinput'),
      bar = document.getElementById('uploadbar');
  if (!dz) return;
  document.getElementById('pickbtn').addEventListener('click', function () { input.click(); });
  input.addEventListener('change', function () { if (input.files.length) upload(input.files); input.value = ''; });
  ['dragenter', 'dragover'].forEach(function (ev) { dz.addEventListener(ev, function (e) { e.preventDefault(); dz.classList.add('drag'); }); });
  ['dragleave', 'drop'].forEach(function (ev) { dz.addEventListener(ev, function (e) { e.preventDefault(); if (ev === 'drop' || e.target === dz) dz.classList.remove('drag'); }); });
  dz.addEventListener('drop', function (e) {
    e.preventDefault();
    var files = [].filter.call(e.dataTransfer.files, function (f) { return f.type.indexOf('image') === 0; });
    if (files.length) upload(files);
  });

  function upload(files) {
    var fd = new FormData();
    fd.append('action', 'upload'); fd.append('p', PID); fd.append('csrf', CSRF);
    [].forEach.call(files, function (f) { fd.append('files[]', f); });
    bar.hidden = false; bar.firstElementChild.style.width = '8%';
    var xhr = new XMLHttpRequest();
    xhr.open('POST', 'api.php');
    xhr.upload.onprogress = function (e) { if (e.lengthComputable) bar.firstElementChild.style.width = Math.round(e.loaded / e.total * 90) + '%'; };
    xhr.onload = function () {
      bar.firstElementChild.style.width = '100%';
      try { var res = JSON.parse(xhr.responseText); if (res.ok) { location.reload(); return; } alert('Upload failed: ' + (res.error || '?')); }
      catch (e) { alert('Upload error — still signed in?'); }
      bar.hidden = true; bar.firstElementChild.style.width = '0';
    };
    xhr.onerror = function () { bar.hidden = true; alert('Network error during upload.'); };
    xhr.send(fd);
  }
})();
