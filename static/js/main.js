// LoveSpace — Main JS
async function api(url, method, body) {
  method = method || 'GET';
  const opts = { method, headers: {} };
  if (body && !(body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  } else if (body) { opts.body = body; }
  const res = await fetch(url, opts);
  return res.json();
}
function toast(msg, type) {
  const t = document.createElement('div');
  const bg = type==='error'
    ? 'linear-gradient(135deg,#ff8fa3,#d63660)'
    : 'linear-gradient(135deg,#f472a8,#c9566e)';
  t.style.cssText=`position:fixed;bottom:24px;right:24px;z-index:9999;background:${bg};color:white;padding:12px 22px;border-radius:30px;font-weight:700;font-size:15px;box-shadow:0 4px 24px rgba(196,86,110,0.35);pointer-events:none;font-family:Nunito,sans-serif`;
  t.textContent=msg; document.body.appendChild(t);
  setTimeout(()=>t.remove(),3200);
}
function openModal(id){document.getElementById(id).classList.add('open');}
function closeModal(id){document.getElementById(id).classList.remove('open');}
function formatMoney(n){
  return new Intl.NumberFormat('ru-RU',{style:'currency',currency:'RUB',maximumFractionDigits:0}).format(n);
}
const MOODS = {
  happy:{emoji:'😊',label:'Радость'},love:{emoji:'🥰',label:'Влюблённость'},
  calm:{emoji:'😌',label:'Спокойствие'},neutral:{emoji:'😐',label:'Нейтрально'},
  tired:{emoji:'😴',label:'Усталость'},sad:{emoji:'😢',label:'Грусть'},
  anxious:{emoji:'😟',label:'Тревога'},angry:{emoji:'😡',label:'Злость'},
  excited:{emoji:'🤩',label:'Восторг'},romantic:{emoji:'💕',label:'Романтика'},
};
window.LOVESPACE = {api,toast,openModal,closeModal,formatMoney,MOODS};