const state = {
  admin: false,
  programs: false,
  fotos: [],
  programas: [],
};

const statusBanco = document.getElementById('statusBanco');
const statusProgramas = document.getElementById('statusProgramas');
const statusGestao = document.getElementById('statusGestao');
const btnLogout = document.getElementById('btnLogout');
const buscaGaleria = document.getElementById('buscaGaleria');
const buscaProgramas = document.getElementById('buscaProgramas');
const galeriaLista = document.getElementById('galeriaLista');
const programasLista = document.getElementById('programasLista');
const blocoBloqueado = document.getElementById('blocoBloqueado');
const blocoUpload = document.getElementById('blocoUpload');
const blocoCadastroPrograma = document.getElementById('blocoCadastroPrograma');
const mensagemGaleria = document.getElementById('mensagemGaleria');
const mensagemProgramas = document.getElementById('mensagemProgramas');
const templateFoto = document.getElementById('templateFoto');
const templatePrograma = document.getElementById('templatePrograma');

const modalSenhaProgramas = document.getElementById('modalSenhaProgramas');
const modalSenhaGestao = document.getElementById('modalSenhaGestao');
const modalSenhaIndividual = document.getElementById('modalSenhaIndividual');
const modalConteudoPrograma = document.getElementById('modalConteudoPrograma');

const formSenhaProgramas = document.getElementById('formSenhaProgramas');
const formSenhaGestao = document.getElementById('formSenhaGestao');
const formSenhaIndividual = document.getElementById('formSenhaIndividual');
const formGaleria = document.getElementById('formGaleria');
const formPrograma = document.getElementById('formPrograma');

const programaId = document.getElementById('programaId');
const programaTitulo = document.getElementById('programaTitulo');
const programaCategoria = document.getElementById('programaCategoria');
const programaDescricao = document.getElementById('programaDescricao');
const programaLink = document.getElementById('programaLink');
const programaSenha = document.getElementById('programaSenha');
const tituloProgramaForm = document.getElementById('tituloProgramaForm');
const btnSalvarPrograma = document.getElementById('btnSalvarPrograma');
const btnCancelarEdicaoPrograma = document.getElementById('btnCancelarEdicaoPrograma');
const programaSenhaId = document.getElementById('programaSenhaId');
const senhaIndividualPrograma = document.getElementById('senhaIndividualPrograma');
const conteudoProgramaTitulo = document.getElementById('conteudoProgramaTitulo');
const conteudoProgramaCompleto = document.getElementById('conteudoProgramaCompleto');

function toggleModal(modal, show) {
  modal.classList.toggle('hidden', !show);
}

function showNotice(el, text, isError = false) {
  el.textContent = text;
  el.classList.remove('hidden');
  el.style.background = isError ? 'rgba(255, 95, 122, 0.12)' : 'rgba(68, 217, 255, 0.10)';
  el.style.borderColor = isError ? 'rgba(255, 95, 122, 0.24)' : 'rgba(68, 217, 255, 0.18)';
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.add('hidden'), 3500);
}

function renderEmpty(container, text) {
  container.innerHTML = `<div class="empty-state">${text}</div>`;
}

function truncateText(text, max = 220) {
  if (!text) return '';
  return text.length > max ? `${text.slice(0, max)}...` : text;
}

function showProgramContent(title, content) {
  conteudoProgramaTitulo.textContent = title || 'Conteúdo do programa';
  conteudoProgramaCompleto.textContent = content || 'Sem conteúdo textual.';
  toggleModal(modalConteudoPrograma, true);
}

function updateUI() {
  statusProgramas.textContent = state.programs ? 'Liberados' : 'Bloqueados';
  statusGestao.textContent = state.admin ? 'Liberada' : 'Bloqueada';
  btnLogout.classList.toggle('hidden', !(state.programs || state.admin));
  blocoUpload.classList.toggle('hidden', !state.admin);
  blocoCadastroPrograma.classList.toggle('hidden', !state.admin);
  blocoBloqueado.classList.toggle('hidden', state.programs);
  programasLista.classList.toggle('hidden', !state.programs);
  buscaProgramas.classList.toggle('hidden', !state.programs);
}

async function checkStatusBanco() {
  try {
    const resp = await fetch('/api/status');
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.mensagem || 'Falha ao conectar.');
    statusBanco.textContent = 'Conectado';
  } catch (error) {
    statusBanco.textContent = 'Erro';
    showNotice(mensagemGaleria, `Banco: ${error.message}`, true);
  }
}

async function loadSession() {
  const resp = await fetch('/api/session');
  const data = await resp.json();
  state.admin = !!data.admin_ok;
  state.programs = !!data.programs_ok;
  updateUI();
}

function createFotoCard(item) {
  const node = templateFoto.content.cloneNode(true);
  node.querySelector('.photo-card__image').src = item.imagem_url;
  node.querySelector('.photo-card__title').textContent = item.titulo || 'Sem título';
  node.querySelector('.photo-card__meta').textContent = [item.categoria, item.autor].filter(Boolean).join(' • ') || 'Galeria';
  node.querySelector('.photo-card__desc').textContent = item.descricao || 'Sem descrição.';

  const actionWrap = node.querySelector('.photo-card__actions');
  if (state.admin) {
    actionWrap.classList.remove('hidden');
    node.querySelector('.btnExcluirFoto').addEventListener('click', () => deleteFoto(item.id));
  }
  return node;
}

function renderFotos(list) {
  galeriaLista.innerHTML = '';
  if (!list.length) {
    renderEmpty(galeriaLista, 'Nenhuma foto encontrada na galeria.');
    return;
  }
  list.forEach(item => galeriaLista.appendChild(createFotoCard(item)));
}

async function loadFotos(term = '') {
  try {
    const url = term ? `/api/galeria?q=${encodeURIComponent(term)}` : '/api/galeria';
    const resp = await fetch(url);
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.erro || 'Erro ao carregar galeria.');
    state.fotos = data;
    renderFotos(state.fotos);
  } catch (error) {
    showNotice(mensagemGaleria, error.message, true);
  }
}

function createProgramaCard(item) {
  const node = templatePrograma.content.cloneNode(true);
  node.querySelector('.program-card__title').textContent = item.titulo || 'Sem título';
  node.querySelector('.program-card__category').textContent = item.categoria || 'Programa';
  node.querySelector('.program-card__desc').textContent = truncateText(item.descricao || 'Sem conteúdo textual.');

  if (item.protegido) {
    node.querySelector('.program-card__lock').classList.remove('hidden');
  }

  const btnAbrirPrograma = node.querySelector('.btnAbrirPrograma');
  const btnVerTextoPrograma = node.querySelector('.btnVerTextoPrograma');

  if (item.tem_link) {
    btnAbrirPrograma.addEventListener('click', () => openPrograma(item));
  } else {
    btnAbrirPrograma.classList.add('hidden');
  }

  if (item.tem_conteudo) {
    btnVerTextoPrograma.classList.remove('hidden');
    btnVerTextoPrograma.addEventListener('click', () => showProgramContent(item.titulo, item.descricao));
  }

  const adminWrap = node.querySelector('.program-card__admin');
  if (state.admin) {
    adminWrap.classList.remove('hidden');
    node.querySelector('.btnEditarPrograma').addEventListener('click', () => fillProgramaForm(item));
    node.querySelector('.btnExcluirPrograma').addEventListener('click', () => deletePrograma(item.id));
  }

  return node;
}

function renderProgramas(list) {
  programasLista.innerHTML = '';
  if (!state.programs) return;
  if (!list.length) {
    renderEmpty(programasLista, 'Nenhum programa cadastrado.');
    return;
  }
  list.forEach(item => programasLista.appendChild(createProgramaCard(item)));
}

async function loadProgramas(term = '') {
  if (!state.programs) {
    programasLista.innerHTML = '';
    return;
  }

  try {
    const url = term ? `/api/programas?q=${encodeURIComponent(term)}` : '/api/programas';
    const resp = await fetch(url);
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.erro || 'Erro ao carregar programas.');
    state.programas = data;
    renderProgramas(state.programas);
  } catch (error) {
    showNotice(mensagemProgramas, error.message, true);
  }
}

async function deleteFoto(id) {
  if (!confirm('Deseja excluir esta foto?')) return;
  try {
    const resp = await fetch(`/api/galeria/${id}`, { method: 'DELETE' });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.erro || 'Erro ao excluir foto.');
    showNotice(mensagemGaleria, data.mensagem);
    await loadFotos(buscaGaleria.value.trim());
  } catch (error) {
    showNotice(mensagemGaleria, error.message, true);
  }
}

async function deletePrograma(id) {
  if (!confirm('Deseja excluir este programa?')) return;
  try {
    const resp = await fetch(`/api/programas/${id}`, { method: 'DELETE' });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.erro || 'Erro ao excluir programa.');
    showNotice(mensagemProgramas, data.mensagem);
    resetProgramaForm();
    await loadProgramas(buscaProgramas.value.trim());
  } catch (error) {
    showNotice(mensagemProgramas, error.message, true);
  }
}

async function authPrograms(password) {
  const resp = await fetch('/api/auth/programs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ senha: password }),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.erro || 'Senha inválida.');
  state.programs = true;
  updateUI();
  await loadProgramas();
  showNotice(mensagemProgramas, data.mensagem);
}

async function authAdmin(password) {
  const resp = await fetch('/api/auth/admin', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ senha: password }),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.erro || 'Senha inválida.');
  state.admin = true;
  state.programs = true;
  updateUI();
  await Promise.all([loadFotos(buscaGaleria.value.trim()), loadProgramas(buscaProgramas.value.trim())]);
  showNotice(mensagemProgramas, data.mensagem);
}

async function openPrograma(item) {
  if (item.protegido) {
    programaSenhaId.value = item.id;
    senhaIndividualPrograma.value = '';
    toggleModal(modalSenhaIndividual, true);
    return;
  }

  const resp = await fetch(`/api/programas/${item.id}/abrir`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ senha: '' }),
  });
  const data = await resp.json();
  if (!resp.ok) {
    showNotice(mensagemProgramas, data.erro || 'Erro ao abrir programa.', true);
    return;
  }

  if (data.tipo === 'texto') {
    showProgramContent(data.titulo, data.conteudo);
    return;
  }

  if (data.link) {
    window.open(data.link, '_blank', 'noopener');
  }
}

function fillProgramaForm(item) {
  programaId.value = item.id;
  programaTitulo.value = item.titulo || '';
  programaCategoria.value = item.categoria || '';
  programaDescricao.value = item.descricao || '';
  programaLink.value = item.link || '';
  programaSenha.value = item.senha_individual || '';
  tituloProgramaForm.textContent = 'Editar programa';
  btnSalvarPrograma.textContent = 'Atualizar programa';
  btnCancelarEdicaoPrograma.classList.remove('hidden');
  window.scrollTo({ top: document.body.scrollHeight / 3, behavior: 'smooth' });
}

function resetProgramaForm() {
  formPrograma.reset();
  programaId.value = '';
  tituloProgramaForm.textContent = 'Cadastrar programa';
  btnSalvarPrograma.textContent = 'Salvar programa';
  btnCancelarEdicaoPrograma.classList.add('hidden');
}

formSenhaProgramas.addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    await authPrograms(document.getElementById('senhaProgramas').value.trim());
    formSenhaProgramas.reset();
    toggleModal(modalSenhaProgramas, false);
  } catch (error) {
    showNotice(mensagemProgramas, error.message, true);
  }
});

formSenhaGestao.addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    await authAdmin(document.getElementById('senhaGestao').value.trim());
    formSenhaGestao.reset();
    toggleModal(modalSenhaGestao, false);
  } catch (error) {
    showNotice(mensagemProgramas, error.message, true);
  }
});

formSenhaIndividual.addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const resp = await fetch(`/api/programas/${programaSenhaId.value}/abrir`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ senha: senhaIndividualPrograma.value.trim() }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.erro || 'Senha inválida.');
    toggleModal(modalSenhaIndividual, false);
    formSenhaIndividual.reset();

    if (data.tipo === 'texto') {
      showProgramContent(data.titulo, data.conteudo);
      return;
    }

    if (data.link) {
      window.open(data.link, '_blank', 'noopener');
    }
  } catch (error) {
    showNotice(mensagemProgramas, error.message, true);
  }
});

formGaleria.addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const files = document.getElementById('fotoArquivos').files;
    if (!files.length) throw new Error('Selecione pelo menos uma imagem.');

    const formData = new FormData();
    formData.append('titulo', document.getElementById('fotoTitulo').value.trim());
    formData.append('categoria', document.getElementById('fotoCategoria').value.trim());
    formData.append('descricao', document.getElementById('fotoDescricao').value);
    formData.append('autor', document.getElementById('fotoAutor').value.trim());
    [...files].forEach(file => formData.append('imagens', file));

    const resp = await fetch('/api/galeria', { method: 'POST', body: formData });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.erro || 'Erro ao enviar imagens.');

    formGaleria.reset();
    showNotice(mensagemGaleria, data.mensagem || 'Imagens enviadas com sucesso.');
    await loadFotos(buscaGaleria.value.trim());
  } catch (error) {
    showNotice(mensagemGaleria, error.message, true);
  }
});

formPrograma.addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const payload = {
      titulo: programaTitulo.value.trim(),
      categoria: programaCategoria.value.trim(),
      descricao: programaDescricao.value,
      link: programaLink.value.trim(),
      senha_individual: programaSenha.value.trim(),
    };

    const id = programaId.value.trim();
    const endpoint = id ? `/api/programas/${id}` : '/api/programas';
    const method = id ? 'PUT' : 'POST';

    const resp = await fetch(endpoint, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.erro || 'Erro ao salvar programa.');

    showNotice(mensagemProgramas, id ? 'Programa atualizado com sucesso.' : 'Programa salvo com sucesso.');
    resetProgramaForm();
    await loadProgramas(buscaProgramas.value.trim());
  } catch (error) {
    showNotice(mensagemProgramas, error.message, true);
  }
});

document.getElementById('btnCriarExemplos').addEventListener('click', async () => {
  try {
    const resp = await fetch('/api/seed', { method: 'POST' });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.erro || 'Erro ao criar exemplos.');
    showNotice(mensagemProgramas, data.mensagem);
    await loadProgramas();
  } catch (error) {
    showNotice(mensagemProgramas, error.message, true);
  }
});

btnCancelarEdicaoPrograma.addEventListener('click', resetProgramaForm);
btnLogout.addEventListener('click', async () => {
  await fetch('/api/logout', { method: 'POST' });
  state.admin = false;
  state.programs = false;
  updateUI();
  resetProgramaForm();
  await loadProgramas();
  showNotice(mensagemProgramas, 'Sessão encerrada.');
});

buscaGaleria.addEventListener('input', () => loadFotos(buscaGaleria.value.trim()));
buscaProgramas.addEventListener('input', () => loadProgramas(buscaProgramas.value.trim()));

document.getElementById('btnAbrirProgramas').addEventListener('click', () => toggleModal(modalSenhaProgramas, true));
document.getElementById('btnAbrirProgramas2').addEventListener('click', () => toggleModal(modalSenhaProgramas, true));
document.getElementById('btnAbrirGestao').addEventListener('click', () => toggleModal(modalSenhaGestao, true));

document.querySelectorAll('[data-close]').forEach(btn => {
  btn.addEventListener('click', () => toggleModal(document.querySelector(btn.dataset.close), false));
});

window.addEventListener('click', (event) => {
  [modalSenhaProgramas, modalSenhaGestao, modalSenhaIndividual, modalConteudoPrograma].forEach(modal => {
    if (event.target === modal) toggleModal(modal, false);
  });
});

document.addEventListener('DOMContentLoaded', async () => {
  await checkStatusBanco();
  await loadSession();
  await loadFotos();
  if (state.programs) {
    await loadProgramas();
  }
  updateUI();
});
