'use strict';

var VERBS = [
  ['hablar', 'to speak', { presente: ['hablo','hablas','habla','hablamos','habláis','hablan'], indefinido: ['hablé','hablaste','habló','hablamos','hablasteis','hablaron'], futuro: ['hablaré','hablarás','hablará','hablaremos','hablaréis','hablarán'] }, 'r'],
  ['comer', 'to eat', { presente: ['como','comes','come','comemos','coméis','comen'], indefinido: ['comí','comiste','comió','comimos','comisteis','comieron'], futuro: ['comeré','comerás','comerá','comeremos','comeréis','comerán'] }, 'r'],
  ['vivir', 'to live', { presente: ['vivo','vives','vive','vivimos','vivís','viven'], indefinido: ['viví','viviste','vivió','vivimos','vivisteis','vivieron'], futuro: ['viviré','vivirás','vivirá','viviremos','viviréis','vivirán'] }, 'r'],
  ['ser', 'to be', { presente: ['soy','eres','es','somos','sois','son'], indefinido: ['fui','fuiste','fue','fuimos','fuisteis','fueron'], futuro: ['seré','serás','será','seremos','seréis','serán'] }, 'i'],
  ['estar', 'to be', { presente: ['estoy','estás','está','estamos','estáis','están'], indefinido: ['estuve','estuviste','estuvo','estuvimos','estuvisteis','estuvieron'], futuro: ['estaré','estarás','estará','estaremos','estaréis','estarán'] }, 'i'],
  ['ir', 'to go', { presente: ['voy','vas','va','vamos','vais','van'], indefinido: ['fui','fuiste','fue','fuimos','fuisteis','fueron'], futuro: ['iré','irás','irá','iremos','iréis','irán'] }, 'i'],
  ['tener', 'to have', { presente: ['tengo','tienes','tiene','tenemos','tenéis','tienen'], indefinido: ['tuve','tuviste','tuvo','tuvimos','tuvisteis','tuvieron'], futuro: ['tendré','tendrás','tendrá','tendremos','tendréis','tendrán'] }, 'i'],
  ['hacer', 'to do', { presente: ['hago','haces','hace','hacemos','hacéis','hacen'], indefinido: ['hice','hiciste','hizo','hicimos','hicisteis','hicieron'], futuro: ['haré','harás','hará','haremos','haréis','harán'] }, 'i'],
  ['poder', 'can', { presente: ['puedo','puedes','puede','podemos','podéis','pueden'], indefinido: ['pude','pudiste','pudo','pudimos','pudisteis','pudieron'], futuro: ['podré','podrás','podrá','podremos','podréis','podrán'] }, 'i'],
  ['decir', 'to say', { presente: ['digo','dices','dice','decimos','decís','dicen'], indefinido: ['dije','dijiste','dijo','dijimos','dijisteis','dijeron'], futuro: ['diré','dirás','dirá','diremos','diréis','dirán'] }, 'i'],
  ['querer', 'to want', { presente: ['quiero','quieres','quiere','queremos','queréis','quieren'], indefinido: ['quise','quisiste','quiso','quisimos','quisisteis','quisieron'], futuro: ['querré','querrás','querrá','querremos','querréis','querrán'] }, 'i'],
  ['saber', 'to know', { presente: ['sé','sabes','sabe','sabemos','sabéis','saben'], indefinido: ['supe','supiste','supo','supimos','supisteis','supieron'], futuro: ['sabré','sabrás','sabrá','sabremos','sabréis','sabrán'] }, 'i'],
  ['poner', 'to put', { presente: ['pongo','pones','pone','ponemos','ponéis','ponen'], indefinido: ['puse','pusiste','puso','pusimos','pusisteis','pusieron'], futuro: ['pondré','pondrás','pondrá','pondremos','pondréis','pondrán'] }, 'i'],
  ['salir', 'to leave', { presente: ['salgo','sales','sale','salimos','salís','salen'], indefinido: ['salí','saliste','salió','salimos','salisteis','salieron'], futuro: ['saldré','saldrás','saldrá','saldremos','saldréis','saldrán'] }, 'i'],
  ['venir', 'to come', { presente: ['vengo','vienes','viene','venimos','venís','vienen'], indefinido: ['vine','viniste','vino','vinimos','vinisteis','vinieron'], futuro: ['vendré','vendrás','vendrá','vendremos','vendréis','vendrán'] }, 'i'],
  ['ver', 'to see', { presente: ['veo','ves','ve','vemos','veis','ven'], indefinido: ['vi','viste','vio','vimos','visteis','vieron'], futuro: ['veré','verás','verá','veremos','veréis','verán'] }, 'i'],
  ['dar', 'to give', { presente: ['doy','das','da','damos','dais','dan'], indefinido: ['di','diste','dio','dimos','disteis','dieron'], futuro: ['daré','darás','dará','daremos','daréis','darán'] }, 'i'],
  ['pensar', 'to think', { presente: ['pienso','piensas','piensa','pensamos','pensáis','piensan'], indefinido: ['pensé','pensaste','pensó','pensamos','pensasteis','pensaron'], futuro: ['pensaré','pensarás','pensará','pensaremos','pensaréis','pensarán'] }, 'i'],
  ['dormir', 'to sleep', { presente: ['duermo','duermes','duerme','dormimos','dormís','duermen'], indefinido: ['dormí','dormiste','durmió','dormimos','dormisteis','durmieron'], futuro: ['dormiré','dormirás','dormirá','dormiremos','dormiréis','dormirán'] }, 'i'],
  ['pedir', 'to ask for', { presente: ['pido','pides','pide','pedimos','pedís','piden'], indefinido: ['pedí','pediste','pidió','pedimos','pedisteis','pidieron'], futuro: ['pediré','pedirás','pedirá','pediremos','pediréis','pedirán'] }, 'i']
];
var PRONOUNS = ['yo', 'tú', 'él/ella', 'nosotros', 'vosotros', 'ellos/ellas'];
var PRONOUN_EN = ['I', 'you', 'he/she', 'we', 'you all', 'they'];
