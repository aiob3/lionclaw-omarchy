'use strict';
const repository = 'https://github.com/aiob3/lionclaw-omarchy';
const storageKey = 'lionclaw-omarchy-reviewed-v1';
let steps = [];
let reviewed = new Set();
try { const saved = JSON.parse(localStorage.getItem(storageKey) || '[]'); if (Array.isArray(saved)) reviewed = new Set(saved.filter(x => typeof x === 'string')); } catch (_) { /* Storage is optional. */ }
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const copyIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M15 5V3H3v13h2"/></svg>';
function codePanel(code) { return `<div class="code-panel"><div class="code-heading">TERMINAL<button class="copy" type="button" aria-label="Copiar comando">${copyIcon}<span>Copiar</span></button></div><pre><code>${esc(code)}</code></pre></div>`; }
function sectionHTML(section) { return `<section class="section"><h2>${esc(section.heading)}</h2><p>${esc(section.text)}</p>${section.code ? codePanel(section.code) : ''}${section.caption ? `<p class="caption">${esc(section.caption)}</p>` : ''}${section.expected ? `<div class="expected"><strong>Como validar</strong>${esc(section.expected)}</div>` : ''}${section.note ? `<p class="note">${esc(section.note)}</p>` : ''}</section>`; }
function notify(message) { const toast = document.querySelector('#toast'); toast.textContent = message; toast.classList.add('visible'); setTimeout(() => toast.classList.remove('visible'), 2400); }
function saveProgress() { try { localStorage.setItem(storageKey, JSON.stringify([...reviewed])); } catch (_) { notify('Marcações disponíveis apenas nesta sessão.'); } updateProgress(); }
function updateProgress() {
  const count = steps.filter(s => reviewed.has(s.id)).length;
  document.querySelector('#progress').value = count;
  document.querySelector('#progress-label').textContent = `${count} de ${steps.length} etapas revisadas`;
  document.querySelectorAll('#steps-nav a').forEach(a => a.classList.toggle('reviewed', reviewed.has(a.dataset.id)));
}
function closeMenu() { document.body.classList.remove('nav-open'); document.querySelector('#menu-toggle').setAttribute('aria-expanded','false'); }
function render() {
  const id = location.hash.slice(1) || 'overview';
  const index = Math.max(0, steps.findIndex(s => s.id === id));
  const step = steps[index];
  const overview = step.id === 'overview';
  document.title = `${step.title} — LionClaw no Omarchy`;
  document.querySelectorAll('#steps-nav a').forEach(a => { if (a.dataset.id === step.id) a.setAttribute('aria-current','step'); else a.removeAttribute('aria-current'); });
  const header = `<div class="breadcrumb">GUIA / ${String(step.number).padStart(2,'0')}</div><h1>${overview ? 'LionClaw no Omarchy.<span>Da preparação à primeira janela.</span>' : esc(step.title)}</h1><p class="intro">${overview ? 'Um percurso verificável para instalar a revisão validada, entender cada dependência e confirmar o resultado.' : esc(step.summary)}</p>`;
  const metadata = overview ? '<div class="versions"><span>LionClaw 3.9.0</span><span>Node 24.11.1</span><span>Electron 33.4.11</span></div><div class="actions"><button class="button" id="installer-cta">Usar o instalador</button><a class="button secondary" href="'+ repository +'" target="_blank" rel="noopener">Ver repositório</a></div><hr class="intro-separator">' : '<hr class="intro-separator">';
  const content = overview ? sectionHTML({...step.sections[0], expected: undefined}) + '<p class="scope">Validação local: instalação, módulos nativos e abertura. Login e provedores ainda não validados.</p><details class="details" id="installer-details"><summary>Baixar o instalador e conhecer os limites da validação</summary>' + step.sections.slice(1).map(sectionHTML).join('') + '</details>' : step.sections.map(sectionHTML).join('');
  const next = steps[index + 1];
  const prev = steps[index - 1];
  document.querySelector('#content').innerHTML = header + metadata + content + `<div class="footer-nav"><label class="review"><input type="checkbox" id="reviewed" ${reviewed.has(step.id) ? 'checked' : ''}>Marcar como revisada</label><div class="next-links">${prev ? `<a class="previous" href="#${prev.id}">Anterior</a>` : ''}${next ? `<a class="button" href="#${next.id}">Próxima: ${esc(next.title)} <span aria-hidden="true">&nbsp;→</span></a>` : `<a class="button" href="#overview">Voltar ao início</a>`}</div></div><div class="page-tools"><span>Guia comunitário · revisão validada em 19/09/2026</span><button class="text-button" id="print">Imprimir guia completo</button><a href="${repository}/blob/main/HOMOLOGACAO.md" target="_blank" rel="noopener">Evidências e limites ↗</a></div>`;
  document.querySelector('#reviewed').addEventListener('change', e => { if (e.target.checked) reviewed.add(step.id); else reviewed.delete(step.id); saveProgress(); });
  document.querySelector('#print').addEventListener('click', () => window.print());
  document.querySelector('#installer-cta')?.addEventListener('click', () => { const details = document.querySelector('#installer-details'); details.open = true; details.scrollIntoView({block:'start',behavior:'instant'}); details.querySelector('summary').focus(); });
  closeMenu(); updateProgress();
}
document.addEventListener('click', async event => {
  const button = event.target.closest('.copy'); if (!button) return;
  const code = button.closest('.code-panel').querySelector('code').textContent;
  try { await navigator.clipboard.writeText(code); button.querySelector('span').textContent = 'Copiado'; notify('Comando copiado. Revise antes de executar.'); setTimeout(() => { if (button.isConnected) button.querySelector('span').textContent = 'Copiar'; }, 2000); }
  catch (_) { notify('Não foi possível copiar. Selecione o comando no bloco.'); }
});
document.querySelector('#menu-toggle').addEventListener('click', event => { const open = document.body.classList.toggle('nav-open'); event.currentTarget.setAttribute('aria-expanded',String(open)); });
document.querySelector('.skip').addEventListener('click', event => { event.preventDefault(); document.querySelector('#content').focus(); });
document.addEventListener('keydown', event => { if (event.key === 'Escape' && document.body.classList.contains('nav-open')) { closeMenu(); document.querySelector('#menu-toggle').focus(); } });
document.querySelector('#reset-progress').addEventListener('click', () => { reviewed.clear(); saveProgress(); const box = document.querySelector('#reviewed'); if (box) box.checked = false; notify('Marcações locais removidas.'); });
window.addEventListener('hashchange', () => { if (!steps.length) return; render(); window.scrollTo(0,0); document.querySelector('#content').focus({preventScroll:true}); });
fetch('steps.json').then(response => { if (!response.ok) throw new Error('Roteiro indisponível'); return response.json(); }).then(data => {
  steps = data;
  document.querySelector('#steps-nav').innerHTML = steps.map(s => `<a href="#${s.id}" data-id="${s.id}"><span>${String(s.number).padStart(2,'0')}</span><span>${esc(s.title)}</span></a>`).join('');
  document.querySelector('#print-content').innerHTML = steps.map(s => `<article class="print-step"><h1>${String(s.number).padStart(2,'0')} · ${esc(s.title)}</h1><p>${esc(s.summary)}</p>${s.sections.map(sectionHTML).join('')}</article>`).join('');
  render();
}).catch(() => { document.querySelector('#content').innerHTML = '<h1>Não foi possível carregar o roteiro.</h1><p>Recarregue a página ou leia o <a href="'+repository+'">guia no GitHub</a>. Para uso local, sirva a pasta docs com python3 -m http.server.</p>'; });
