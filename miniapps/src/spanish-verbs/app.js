'use strict';

var TENSES = ['presente', 'indefinido', 'futuro'];

var state = { correct: 0, wrong: 0, streak: 0 };
var current = null;
var currentVerb = null;

function $(id) { return document.getElementById(id); }
function log(msg) { $('log').textContent += msg + '\n'; }
function hasBridge() { return typeof window.miniapp !== 'undefined'; }
function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
function norm(s) { return s.trim().toLowerCase(); }

function saveProgress() {
  if (!hasBridge()) return;
  window.miniapp.storage.set('progress', JSON.stringify(state)).catch(function (e) { log('storage.set: ' + e.code); });
}
function restoreProgress() {
  if (!hasBridge()) return Promise.resolve();
  return window.miniapp.storage.get('progress').then(function (v) {
    if (v) { try { state = JSON.parse(v); } catch (e) {} updateScore(); }
  }).catch(function () {});
}
function updateScore() { $('score').textContent = state.correct + ' ✓ · ' + state.wrong + ' ✗'; }
function grantMilestones() {
  if (!hasBridge() || !window.miniapp.game) return;
  [10, 25, 50, 100].forEach(function (m) {
    if (state.correct >= m) {
      window.miniapp.game.grantReward({ resource: 'xp', amount: m / 2, key: 'correct-' + m })
        .then(function () { log('reward ' + m + ' xp'); })
        .catch(function (e) { log('reward ' + m + ': ' + e.code); });
    }
  });
}
function answered(ok, el, rightForm) {
  if (ok) { state.correct++; state.streak++; grantMilestones(); }
  else { state.wrong++; state.streak = 0; }
  updateScore(); saveProgress();
  return ok ? '¡Correcto! streak: ' + state.streak : '✗ ' + rightForm;
}

// ---- mode switching ----
function show(mode) {
  ['list', 'verb', 'train', 'quiz'].forEach(function (m) {
    $(m).className = m === mode ? '' : 'hidden';
  });
  document.querySelectorAll('nav .mode').forEach(function (b) {
    b.className = 'mode' + (b.dataset.mode === mode ? ' active' : '');
  });
  if (mode === 'list') renderList();
  if (mode === 'train') nextTrain();
  if (mode === 'quiz') nextQuiz();
}
document.querySelectorAll('nav .mode').forEach(function (b) {
  b.onclick = function () { show(b.dataset.mode); };
});

// ---- verb list ----
function renderList() {
  var el = $('list');
  el.innerHTML = '';
  VERBS.forEach(function (v) {
    var b = document.createElement('button');
    b.className = 'verb';
    b.innerHTML = '<b>' + v[0] + '</b><small>' + v[1] + ' · ' + (v[3] === 'r' ? 'regular' : 'irregular') + '</small>';
    b.onclick = function () { currentVerb = v; renderVerb(v); show('verb'); };
    el.appendChild(b);
  });
}

// ---- verb detail ----
function renderVerb(v) {
  $('verb-head').innerHTML = '<h2>' + v[0] + ' <small style="color:#9aa4b2">' + v[1] + '</small></h2>';
  var html = '<tr><th></th><th>presente</th><th>indefinido</th><th>futuro</th></tr>';
  PRONOUNS.forEach(function (p, i) {
    html += '<tr><td>' + p + '</td>' + TENSES.map(function (t) { return '<td>' + v[2][t][i] + '</td>'; }).join('') + '</tr>';
  });
  $('conj').innerHTML = html;
}
$('verb-back').onclick = function () { show('list'); };
$('train-verb').onclick = function () { show('train'); };

// ---- training (type the form) ----
var trainQ = null;
function nextTrain() {
  var v = currentVerb || pick(VERBS);
  var tense = pick(TENSES);
  var person = Math.floor(Math.random() * 6);
  trainQ = { verb: v, tense: tense, person: person, form: v[2][tense][person] };
  $('train-prompt').innerHTML = '<b>' + v[0] + '</b> (' + v[1] + ') — ' + tense + '<br><span style="font-size:1.3em">' + PRONOUNS[person] + ' (' + PRONOUN_EN[person] + ') ___</span>';
  var input = $('train-input');
  input.value = ''; input.className = ''; input.disabled = false; input.focus();
  $('train-feedback').textContent = '';
  $('train-check').className = '';
  $('train-next').className = 'hidden';
}
function checkTrain() {
  var input = $('train-input');
  var ok = norm(input.value) === norm(trainQ.form);
  input.className = ok ? 'correct' : 'wrong';
  input.disabled = true;
  $('train-feedback').textContent = answered(ok, input, trainQ.form);
  $('train-check').className = 'hidden';
  $('train-next').className = '';
}
$('train-check').onclick = checkTrain;
$('train-input').addEventListener('keydown', function (e) { if (e.key === 'Enter') checkTrain(); });
$('train-next').onclick = nextTrain;

// ---- quiz (4 options) ----
function nextQuiz() {
  var v = pick(VERBS);
  var tense = pick(TENSES);
  var person = Math.floor(Math.random() * 6);
  var rightForm = v[2][tense][person];
  var options = [rightForm];
  while (options.length < 4) {
    var other = pick(VERBS)[2][tense][person];
    if (options.indexOf(other) === -1) options.push(other);
  }
  options.sort(function () { return Math.random() - 0.5; });
  current = { right: rightForm };
  $('prompt').innerHTML = '<b>' + v[0] + '</b> (' + v[1] + ') — ' + tense + '<br><span style="font-size:1.4em">' + PRONOUNS[person] + ' (' + PRONOUN_EN[person] + ') ___</span>';
  var opts = $('options');
  opts.innerHTML = '';
  options.forEach(function (opt) {
    var b = document.createElement('button');
    b.textContent = opt;
    b.onclick = function () { quizAnswer(b, opt); };
    opts.appendChild(b);
  });
  $('feedback').textContent = '';
  $('next').className = 'hidden';
}
function quizAnswer(btn, opt) {
  var buttons = $('options').children;
  for (var i = 0; i < buttons.length; i++) buttons[i].disabled = true;
  var ok = opt === current.right;
  btn.className = ok ? 'correct' : 'wrong';
  $('feedback').textContent = answered(ok, btn, current.right);
  $('next').className = '';
}
$('next').onclick = nextQuiz;

// ---- bridge test buttons ----
$('btn-info').onclick = function () {
  if (!hasBridge()) { log('no bridge'); return; }
  window.miniapp.system.getInfo().then(function (i) { log('host: ' + JSON.stringify(i)); });
};
$('btn-neg1').onclick = function () {
  if (!hasBridge()) { log('no bridge'); return; }
  window.miniapp.network.request({ url: 'https://example.com' }).catch(function (e) { log('neg1 → ' + e.code); });
};
$('btn-neg2').onclick = function () {
  if (!hasBridge()) { log('no bridge'); return; }
  window.miniapp.device.vibrate(100).catch(function (e) { log('neg2 → ' + e.code); });
};

restoreProgress().then(function () { show('list'); });
