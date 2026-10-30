'use strict';

// verb -> [infinitive, english, {presente, indefinido, futuro}] each [yo, tu, el, nosotros, vosotros, ellos]
var VERBS = [
  ['hablar', 'to speak', { presente: ['hablo','hablas','habla','hablamos','habláis','hablan'], indefinido: ['hablé','hablaste','habló','hablamos','hablasteis','hablaron'], futuro: ['hablaré','hablarás','hablará','hablaremos','hablaréis','hablarán'] }],
  ['comer', 'to eat', { presente: ['como','comes','come','comemos','coméis','comen'], indefinido: ['comí','comiste','comió','comimos','comisteis','comieron'], futuro: ['comeré','comerás','comerá','comeremos','comeréis','comerán'] }],
  ['vivir', 'to live', { presente: ['vivo','vives','vive','vivimos','vivís','viven'], indefinido: ['viví','viviste','vivió','vivimos','vivisteis','vivieron'], futuro: ['viviré','vivirás','vivirá','viviremos','viviréis','vivirán'] }],
  ['ser', 'to be', { presente: ['soy','eres','es','somos','sois','son'], indefinido: ['fui','fuiste','fue','fuimos','fuisteis','fueron'], futuro: ['seré','serás','será','seremos','seréis','serán'] }],
  ['estar', 'to be', { presente: ['estoy','estás','está','estamos','estáis','están'], indefinido: ['estuve','estuviste','estuvo','estuvimos','estuvisteis','estuvieron'], futuro: ['estaré','estarás','estará','estaremos','estaréis','estarán'] }],
  ['ir', 'to go', { presente: ['voy','vas','va','vamos','vais','van'], indefinido: ['fui','fuiste','fue','fuimos','fuisteis','fueron'], futuro: ['iré','irás','irá','iremos','iréis','irán'] }],
  ['tener', 'to have', { presente: ['tengo','tienes','tiene','tenemos','tenéis','tienen'], indefinido: ['tuve','tuviste','tuvo','tuvimos','tuvisteis','tuvieron'], futuro: ['tendré','tendrás','tendrá','tendremos','tendréis','tendrán'] }],
  ['hacer', 'to do', { presente: ['hago','haces','hace','hacemos','hacéis','hacen'], indefinido: ['hice','hiciste','hizo','hicimos','hicisteis','hicieron'], futuro: ['haré','harás','hará','haremos','haréis','harán'] }],
  ['poder', 'can', { presente: ['puedo','puedes','puede','podemos','podéis','pueden'], indefinido: ['pude','pudiste','pudo','pudimos','pudisteis','pudieron'], futuro: ['podré','podrás','podrá','podremos','podréis','podrán'] }],
  ['decir', 'to say', { presente: ['digo','dices','dice','decimos','decís','dicen'], indefinido: ['dije','dijiste','dijo','dijimos','dijisteis','dijeron'], futuro: ['diré','dirás','dirá','diremos','diréis','dirán'] }],
  ['querer', 'to want', { presente: ['quiero','quieres','quiere','queremos','queréis','quieren'], indefinido: ['quise','quisiste','quiso','quisimos','quisisteis','quisieron'], futuro: ['querré','querrás','querrá','querremos','querréis','querrán'] }],
  ['saber', 'to know', { presente: ['sé','sabes','sabe','sabemos','sabéis','saben'], indefinido: ['supe','supiste','supo','supimos','supisteis','supieron'], futuro: ['sabré','sabrás','sabrá','sabremos','sabréis','sabrán'] }],
  ['poner', 'to put', { presente: ['pongo','pones','pone','ponemos','ponéis','ponen'], indefinido: ['puse','pusiste','puso','pusimos','pusisteis','pusieron'], futuro: ['pondré','pondrás','pondrá','pondremos','pondréis','pondrán'] }],
  ['salir', 'to leave', { presente: ['salgo','sales','sale','salimos','salís','salen'], indefinido: ['salí','saliste','salió','salimos','salisteis','salieron'], futuro: ['saldré','saldrás','saldrá','saldremos','saldréis','saldrán'] }],
  ['venir', 'to come', { presente: ['vengo','vienes','viene','venimos','venís','vienen'], indefinido: ['vine','viniste','vino','vinimos','vinisteis','vinieron'], futuro: ['vendré','vendrás','vendrá','vendremos','vendréis','vendrán'] }],
  ['ver', 'to see', { presente: ['veo','ves','ve','vemos','veis','ven'], indefinido: ['vi','viste','vio','vimos','visteis','vieron'], futuro: ['veré','verás','verá','veremos','veréis','verán'] }],
  ['dar', 'to give', { presente: ['doy','das','da','damos','dais','dan'], indefinido: ['di','diste','dio','dimos','disteis','dieron'], futuro: ['daré','darás','dará','daremos','daréis','darán'] }],
  ['pensar', 'to think', { presente: ['pienso','piensas','piensa','pensamos','pensáis','piensan'], indefinido: ['pensé','pensaste','pensó','pensamos','pensasteis','pensaron'], futuro: ['pensaré','pensarás','pensará','pensaremos','pensaréis','pensarán'] }],
  ['dormir', 'to sleep', { presente: ['duermo','duermes','duerme','dormimos','dormís','duermen'], indefinido: ['dormí','dormiste','durmió','dormimos','dormisteis','durmieron'], futuro: ['dormiré','dormirás','dormirá','dormiremos','dormiréis','dormirán'] }],
  ['pedir', 'to ask for', { presente: ['pido','pides','pide','pedimos','pedís','piden'], indefinido: ['pedí','pediste','pidió','pedimos','pedisteis','pidieron'], futuro: ['pediré','pedirás','pedirá','pediremos','pediréis','pedirán'] }]
];
var PRONOUNS = ['yo', 'tú', 'él/ella', 'nosotros', 'vosotros', 'ellos/ellas'];
var TENSES = ['presente', 'indefinido', 'futuro'];

var state = { correct: 0, wrong: 0, streak: 0 };
var current = null;

function log(msg) { document.getElementById('log').textContent += msg + '\n'; }
function hasBridge() { return typeof window.miniapp !== 'undefined'; }

function saveProgress() {
  if (!hasBridge()) return;
  window.miniapp.storage.set('progress', JSON.stringify(state)).catch(function (e) { log('storage.set: ' + e.code); });
}

function restoreProgress() {
  if (!hasBridge()) return Promise.resolve();
  return window.miniapp.storage.get('progress').then(function (v) {
    if (v) { try { state = JSON.parse(v); } catch (e) {} updateScore(); }
  });
}

function updateScore() {
  document.getElementById('score').textContent = state.correct + ' ✓ · ' + state.wrong + ' ✗';
}

function grantMilestones() {
  if (!hasBridge() || !window.miniapp.game) return;
  [10, 25, 50, 100].forEach(function (m) {
    if (state.correct >= m) {
      window.miniapp.game.grantReward({ resource: 'xp', amount: m / 2, key: 'correct-' + m })
        .then(function () { log('reward ' + m + ' xp granted'); })
        .catch(function (e) { log('reward ' + m + ': ' + e.code); });
    }
  });
}

function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

function newQuestion() {
  var verb = pick(VERBS);
  var tense = pick(TENSES);
  var person = Math.floor(Math.random() * 6);
  var answer = verb[2][tense][person];
  var options = [answer];
  while (options.length < 4) {
    var other = pick(VERBS)[2][tense][person];
    if (options.indexOf(other) === -1) options.push(other);
  }
  options.sort(function () { return Math.random() - 0.5; });
  current = { verb: verb, tense: tense, person: person, answer: answer };

  document.getElementById('prompt').innerHTML =
    '<b>' + verb[0] + '</b> (' + verb[1] + ') — ' + tense + '<br><span style="font-size:1.4em">' + PRONOUNS[person] + ' ___</span>';
  var opts = document.getElementById('options');
  opts.innerHTML = '';
  options.forEach(function (opt) {
    var b = document.createElement('button');
    b.textContent = opt;
    b.onclick = function () { answer(b, opt); };
    opts.appendChild(b);
  });
  document.getElementById('feedback').textContent = '';
  document.getElementById('next').className = 'hidden';
}

function answer(btn, opt) {
  var buttons = document.getElementById('options').children;
  for (var i = 0; i < buttons.length; i++) buttons[i].disabled = true;
  if (opt === current.answer) {
    btn.className = 'correct';
    state.correct++; state.streak++;
    document.getElementById('feedback').textContent = '¡Correcto! streak: ' + state.streak;
    grantMilestones();
  } else {
    btn.className = 'wrong';
    state.wrong++; state.streak = 0;
    document.getElementById('feedback').textContent = '✗ ' + current.answer;
  }
  updateScore();
  saveProgress();
  document.getElementById('next').className = '';
}

document.getElementById('next').onclick = newQuestion;
document.getElementById('btn-info').onclick = function () {
  if (!hasBridge()) { log('no bridge'); return; }
  window.miniapp.system.getInfo().then(function (i) { log('host: ' + JSON.stringify(i)); });
};
document.getElementById('btn-neg1').onclick = function () {
  if (!hasBridge()) { log('no bridge'); return; }
  window.miniapp.network.request({ url: 'https://example.com' })
    .catch(function (e) { log('neg1 → ' + e.code); });
};
document.getElementById('btn-neg2').onclick = function () {
  if (!hasBridge()) { log('no bridge'); return; }
  window.miniapp.device.vibrate(100).catch(function (e) { log('neg2 → ' + e.code); });
};

restoreProgress().then(newQuestion);
