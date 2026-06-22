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
  function imgSrc(f, thumb) { return 'img.php?p=' + encodeURIComponent(PID) + '&f=' + encodeURIComponent(f) + (thumb ? '&t=1' : ''); }

  // ---- per-image rating actions (grid) ----
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
  function del(shot) {
    if (!confirm('Delete this image?')) return;
    post({ action: 'delete', file: shot.dataset.file }).then(function (res) { if (res.ok) shot.remove(); });
  }

  // ---- beat reorder ----
  function moveBeat(beatEl, to) {
    post({ action: 'move_beat', beat: beatEl.dataset.beat, to: to }).then(function (res) { if (res.ok) location.reload(); });
  }

  var gallery = document.getElementById('gallery');
  if (gallery) {
    gallery.addEventListener('click', function (e) {
      var rb = e.target.closest('.rb[data-act]');
      if (rb) {
        var shot = rb.closest('.shot'); if (!shot) return;
        var a = rb.dataset.act;
        if (a === 'good' || a === 'bad') rate(shot, a);
        else if (a === 'keep') keep(shot);
        else if (a === 'cover') post({ action: 'cover', file: shot.dataset.file });
        else if (a === 'delete') del(shot);
        return;
      }
      var mv = e.target.closest('.bmove');
      if (mv) {
        var beatEl = mv.closest('.beat'); var inp = beatEl.querySelector('.beat-pos');
        var pos = parseInt(inp && inp.value, 10) || 1;
        moveBeat(beatEl, mv.dataset.dir === 'up' ? pos - 1 : pos + 1);
        return;
      }
      if (e.target.closest('.bcompare')) {
        var b = e.target.closest('.beat'); lbOpen(beatFiles(b), 0, b.dataset.beat); return;
      }
      var im = e.target.closest('.shot-img');
      if (im) {
        var bb = e.target.closest('.beat'); var files = beatFiles(bb);
        var f = im.closest('.shot').dataset.file;
        lbOpen(files, Math.max(0, files.indexOf(f)), bb.dataset.beat);
      }
    });
    gallery.addEventListener('keydown', function (e) {
      if (!e.target.classList.contains('beat-pos')) return;
      if (e.key === 'Enter') { e.preventDefault(); var b = e.target.closest('.beat'); moveBeat(b, parseInt(e.target.value, 10) || 1); }
    });
  }
  function beatFiles(beatEl) { return [].map.call(beatEl.querySelectorAll('.shot'), function (s) { return s.dataset.file; }); }

  // ---- sequence: one beat each ----
  var oneeach = document.getElementById('oneeach');
  if (oneeach) oneeach.addEventListener('click', function () {
    if (!confirm('Put each image in its own beat (page) and mark all as keepers? Use this for a sequence (not variants); you can then delete any duplicates and Port.')) return;
    post({ action: 'one_beat_each' }).then(function (r) { if (r.ok) location.reload(); });
  });

  // ---- lightbox ----
  var LB = document.getElementById('lightbox');
  var lbImg = LB.querySelector('.lb-img'), lbCount = LB.querySelector('.lb-count'),
      lbBeatEl = LB.querySelector('.lb-beat'), lbKeepBtn = LB.querySelector('.lb-keep'),
      lbAn = LB.querySelector('.lb-analysis');
  var lbFiles = [], lbIdx = 0, lbBeat = '', lbDirty = false;
  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  function lbOpen(files, idx, beat) {
    if (!files || !files.length) return;
    lbFiles = files; lbIdx = idx || 0; lbBeat = beat || '';
    lbBeatEl.textContent = beat || '';
    LB.hidden = false; document.body.style.overflow = 'hidden';
    lbRender();
  }
  function lbRender() {
    var f = lbFiles[lbIdx];
    lbImg.src = imgSrc(f, false); // full-res for judging
    lbCount.textContent = (lbIdx + 1) + ' / ' + lbFiles.length;
    var shot = document.querySelector('.shot[data-file="' + f + '"]');
    lbKeepBtn.classList.toggle('on', !!(shot && shot.dataset.accepted === '1'));
    lbKeepBtn.textContent = (shot && shot.dataset.accepted === '1') ? '★ Winner ✓' : '★ Winner (Enter)';
    var an = (window.STUDIO_ANALYSIS || {})[f];
    if (an && (an.caption || (an.defects || []).length || an.tier || an.notes)) {
      var defs = (an.defects || []).map(function (x) { return '<span class="an-def">⚠ ' + esc(x) + '</span>'; }).join('');
      lbAn.innerHTML = (an.tier ? '<span class="an-tier">' + esc(an.tier) + '</span>' : '') +
        (an.caption ? '<span class="an-cap">' + esc(an.caption) + '</span>' : '') + defs +
        (an.notes ? '<div class="an-notes">' + esc(an.notes) + '</div>' : '');
      lbAn.hidden = false;
    } else { lbAn.hidden = true; lbAn.innerHTML = ''; }
  }
  function lbNav(d) { lbIdx = (lbIdx + d + lbFiles.length) % lbFiles.length; lbRender(); }
  function lbClose() { LB.hidden = true; document.body.style.overflow = ''; if (lbDirty) location.reload(); }
  function lbWinner() {
    var f = lbFiles[lbIdx];
    post({ action: 'winner', file: f }).then(function (res) {
      if (!res.ok) return;
      lbDirty = true;
      document.querySelectorAll('.beat[data-beat="' + lbBeat + '"] .shot').forEach(function (s) {
        var win = s.dataset.file === f;
        s.dataset.accepted = win ? '1' : '0';
        s.classList.toggle('kept', win);
        s.classList.remove('rate-good', 'rate-bad', 'rate-unrated');
        s.dataset.rating = win ? 'good' : (s.dataset.rating === 'good' ? 'unrated' : s.dataset.rating);
        s.classList.add('rate-' + s.dataset.rating);
      });
      lbRender();
    });
  }
  LB.querySelector('.lb-x').addEventListener('click', lbClose);
  LB.querySelector('.lb-prev').addEventListener('click', function () { lbNav(-1); });
  LB.querySelector('.lb-next').addEventListener('click', function () { lbNav(1); });
  lbKeepBtn.addEventListener('click', lbWinner);
  LB.addEventListener('click', function (e) { if (e.target === LB) lbClose(); });

  // ---- keyboard ----
  document.addEventListener('keydown', function (e) {
    if (!LB.hidden) {
      if (e.key === 'ArrowLeft') { lbNav(-1); e.preventDefault(); }
      else if (e.key === 'ArrowRight') { lbNav(1); e.preventDefault(); }
      else if (e.key === 'Enter') { lbWinner(); e.preventDefault(); }
      else if (e.key === 'Escape') { lbClose(); e.preventDefault(); }
      return;
    }
    if (/^(INPUT|TEXTAREA|SELECT)$/.test((document.activeElement || {}).tagName)) return;
    var shot = (document.activeElement && document.activeElement.closest && document.activeElement.closest('.shot')) || document.querySelector('.shot:hover');
    if (!shot) return;
    var k = e.key.toLowerCase();
    if (k === 'g') { rate(shot, 'good'); e.preventDefault(); }
    else if (k === 'b') { rate(shot, 'bad'); e.preventDefault(); }
    else if (k === 'a') { keep(shot); e.preventDefault(); }
  });

  // ---- upload (drag-drop + picker) ----
  var dz = document.getElementById('dropzone'), input = document.getElementById('fileinput'), bar = document.getElementById('uploadbar');
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
