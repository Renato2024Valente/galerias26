# Portal de Galeria + Programas com Senha

Projeto completo em **Flask + MongoDB Atlas** com:

- galeria de fotos
- upload de múltiplas imagens
- armazenamento das imagens no MongoDB usando **GridFS**
- área de programas protegida por senha
- área de gestão com senha separada
- cadastro, edição e exclusão de programas
- exclusão de fotos pela gestão
- visual moderno responsivo

## 1) Instalação

```bash
pip install -r requirements.txt
```

## 2) Configure o `.env`

Copie `.env.exemplo` para `.env`.

Preencha com sua URI real do MongoDB Atlas.

**Atenção:** se sua senha tiver `#`, use `%23` na URI.

Exemplo:

```env
MONGO_URI=mongodb+srv://renatovalente:SENHA_CODIFICADA@arquivos2026.vryf3h8.mongodb.net/arquivos2026?retryWrites=true&w=majority&appName=arquivos2026
MONGO_DB=arquivos2026
SECRET_KEY=troque-esta-chave
ADMIN_PASSWORD=1234
PROGRAMS_PASSWORD=5678
PORT=5000
```

## 3) Rodar

```bash
python app.py
```

Abra:

```text
http://127.0.0.1:5000
```

## Senhas

- `ADMIN_PASSWORD` libera a gestão completa
- `PROGRAMS_PASSWORD` libera apenas a área de programas

## Observação

As fotos ficam salvas no MongoDB usando GridFS, então não dependem de pasta local.


## Deploy na Vercel

Defina estas variáveis no painel da Vercel e depois faça um novo deploy:

- MONGO_URI
- MONGO_DB
- SECRET_KEY
- ADMIN_PASSWORD
- PROGRAMS_PASSWORD

Observação: alterações em variáveis de ambiente na Vercel só entram em um novo deploy.
