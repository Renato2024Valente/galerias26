import os
from datetime import datetime, timedelta
from io import BytesIO
from urllib.parse import quote_plus

from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session, send_file, g
from gridfs import GridFS
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.secret_key = os.getenv("SECRET_KEY", "troque-esta-chave-no-env")
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", str(16 * 1024 * 1024)))
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)
if os.getenv("VERCEL") or os.getenv("FLASK_ENV") == "production":
    app.config["SESSION_COOKIE_SECURE"] = True

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_FILES_PER_UPLOAD = int(os.getenv("MAX_FILES_PER_UPLOAD", "15"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")
PROGRAMS_PASSWORD = os.getenv("PROGRAMS_PASSWORD", "5678")
MONGO_DB_NAME = os.getenv("MONGO_DB", "arquivos2026")
PROGRAMS_COLLECTION = os.getenv("PROGRAMS_COLLECTION", "programas")
GALLERY_COLLECTION = os.getenv("GALLERY_COLLECTION", "fotos")


def get_mongo_uri() -> str:
    full_uri = os.getenv("MONGO_URI", "").strip()
    if full_uri:
        placeholders = ["SEU_USUARIO", "SUA_SENHA_CODIFICADA", "SEU_HOST", "seu_host"]
        if any(item in full_uri for item in placeholders):
            raise RuntimeError(
                "Seu ambiente ainda está com texto de exemplo. Troque pelos dados reais do MongoDB Atlas."
            )
        return full_uri

    user = os.getenv("MONGO_USER", "").strip()
    password = os.getenv("MONGO_PASSWORD", "").strip()
    host = os.getenv("MONGO_HOST", "").strip()
    db_name = os.getenv("MONGO_DB", "arquivos2026").strip()
    app_name = os.getenv("MONGO_APP_NAME", "arquivos2026").strip()

    if not all([user, password, host]):
        raise RuntimeError(
            "Defina MONGO_URI no ambiente da Vercel ou informe MONGO_USER, MONGO_PASSWORD e MONGO_HOST."
        )

    if host.lower() in {"seu_host", "mongodb.net", "cluster.mongodb.net"}:
        raise RuntimeError(
            "MONGO_HOST inválido. Use o host real do Atlas, por exemplo: arquivos2026.vryf3h8.mongodb.net"
        )

    password_encoded = quote_plus(password)
    return (
        f"mongodb+srv://{user}:{password_encoded}@{host}/{db_name}"
        f"?retryWrites=true&w=majority&appName={app_name}"
    )


def get_mongo_parts():
    if "mongo_parts" not in g:
        mongo_uri = get_mongo_uri()
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
        db = client[MONGO_DB_NAME]
        g.mongo_parts = {
            "client": client,
            "db": db,
            "programs": db[PROGRAMS_COLLECTION],
            "gallery_meta": db[GALLERY_COLLECTION],
            "fs": GridFS(db, collection="galeria_arquivos"),
        }
    return g.mongo_parts


@app.teardown_appcontext
def close_mongo(_exception=None):
    parts = g.pop("mongo_parts", None)
    if parts and parts.get("client"):
        parts["client"].close()


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({"erro": "Arquivo muito grande para envio."}), 413


@app.errorhandler(RuntimeError)
def handle_runtime_error(error):
    return jsonify({"erro": str(error)}), 500


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status():
    try:
        parts = get_mongo_parts()
        parts["client"].admin.command("ping")
        return jsonify({"ok": True, "mensagem": "MongoDB conectado com sucesso."})
    except Exception as e:
        return jsonify({"ok": False, "mensagem": str(e)}), 500


@app.route("/api/session")
def session_info():
    return jsonify({"admin_ok": is_admin(), "programs_ok": can_access_programs()})


def serializar_programa(doc: dict) -> dict:
    descricao = doc.get("descricao", "") or ""
    link = (doc.get("link", "") or "").strip()
    senha_individual = doc.get("senha_individual", "") or ""
    return {
        "id": str(doc.get("_id")),
        "titulo": doc.get("titulo", ""),
        "categoria": doc.get("categoria", ""),
        "descricao": descricao,
        "link": link,
        "tem_link": bool(link),
        "tem_conteudo": bool(descricao),
        "senha_individual": senha_individual,
        "protegido": bool(senha_individual),
        "updated_at": doc.get("updated_at", ""),
        "created_at": doc.get("created_at", ""),
    }



def serializar_foto(doc: dict) -> dict:
    return {
        "id": str(doc.get("_id")),
        "titulo": doc.get("titulo", ""),
        "descricao": doc.get("descricao", ""),
        "categoria": doc.get("categoria", ""),
        "autor": doc.get("autor", ""),
        "imagem_url": f"/foto/{str(doc.get('_id'))}",
        "created_at": doc.get("created_at", ""),
    }



def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS



def is_admin() -> bool:
    return bool(session.get("admin_ok"))



def can_access_programs() -> bool:
    return bool(session.get("admin_ok") or session.get("programs_ok"))



def require_admin():
    if not is_admin():
        return jsonify({"erro": "Acesso restrito à gestão."}), 403
    return None



def require_program_access():
    if not can_access_programs():
        return jsonify({"erro": "Informe a senha da área de programas."}), 403
    return None


@app.route("/api/auth/admin", methods=["POST"])
def login_admin():
    dados = request.get_json(silent=True) or {}
    senha = (dados.get("senha") or "").strip()

    if senha != ADMIN_PASSWORD:
        return jsonify({"erro": "Senha da gestão incorreta."}), 401

    session.clear()
    session.permanent = True
    session["admin_ok"] = True
    session["programs_ok"] = True
    session.modified = True
    return jsonify({"mensagem": "Gestão liberada com sucesso."})


@app.route("/api/auth/programs", methods=["POST"])
def login_programs():
    dados = request.get_json(silent=True) or {}
    senha = (dados.get("senha") or "").strip()

    if senha != PROGRAMS_PASSWORD:
        return jsonify({"erro": "Senha da área de programas incorreta."}), 401

    session.permanent = True
    session["programs_ok"] = True
    session.modified = True
    return jsonify({"mensagem": "Área de programas liberada com sucesso."})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    session.modified = True
    return jsonify({"mensagem": "Sessão encerrada."})


@app.route("/api/galeria", methods=["GET"])
def listar_galeria():
    q = request.args.get("q", "").strip()
    filtro = {}
    if q:
        filtro = {
            "$or": [
                {"titulo": {"$regex": q, "$options": "i"}},
                {"descricao": {"$regex": q, "$options": "i"}},
                {"categoria": {"$regex": q, "$options": "i"}},
                {"autor": {"$regex": q, "$options": "i"}},
            ]
        }

    docs = get_mongo_parts()["gallery_meta"].find(filtro).sort("created_at", -1)
    return jsonify([serializar_foto(doc) for doc in docs])


@app.route("/api/galeria", methods=["POST"])
def enviar_galeria():
    auth_error = require_admin()
    if auth_error:
        return auth_error

    arquivos = request.files.getlist("imagens")
    if not arquivos:
        return jsonify({"erro": "Selecione pelo menos uma imagem."}), 400

    if len(arquivos) > MAX_FILES_PER_UPLOAD:
        return jsonify({"erro": f"Envie no máximo {MAX_FILES_PER_UPLOAD} imagens por vez."}), 400

    titulo_base = (request.form.get("titulo") or "").strip()
    descricao = request.form.get("descricao") or ""
    categoria = (request.form.get("categoria") or "").strip()
    autor = (request.form.get("autor") or "").strip()

    salvos = []
    agora = datetime.utcnow().isoformat()
    parts = get_mongo_parts()
    fs = parts["fs"]
    gallery_meta = parts["gallery_meta"]

    for idx, arquivo in enumerate(arquivos, start=1):
        if not arquivo or not arquivo.filename:
            continue
        if not allowed_file(arquivo.filename):
            return jsonify({"erro": f"Arquivo não permitido: {arquivo.filename}"}), 400

        filename = secure_filename(arquivo.filename)
        conteudo = arquivo.read()
        grid_id = fs.put(
            conteudo,
            filename=filename,
            content_type=arquivo.mimetype or "application/octet-stream",
        )

        titulo = titulo_base or filename.rsplit('.', 1)[0]
        if len(arquivos) > 1 and titulo_base:
            titulo = f"{titulo_base} {idx}"

        doc = {
            "titulo": titulo,
            "descricao": descricao,
            "categoria": categoria,
            "autor": autor,
            "filename": filename,
            "content_type": arquivo.mimetype or "application/octet-stream",
            "gridfs_id": grid_id,
            "created_at": agora,
        }
        resultado = gallery_meta.insert_one(doc)
        doc["_id"] = resultado.inserted_id
        salvos.append(serializar_foto(doc))

    return jsonify({"mensagem": "Imagens enviadas com sucesso.", "itens": salvos}), 201


@app.route("/foto/<foto_id>")
def obter_foto(foto_id):
    try:
        doc = get_mongo_parts()["gallery_meta"].find_one({"_id": ObjectId(foto_id)})
    except Exception:
        return jsonify({"erro": "ID de foto inválido."}), 400

    if not doc:
        return jsonify({"erro": "Foto não encontrada."}), 404

    arquivo = get_mongo_parts()["fs"].get(doc["gridfs_id"])
    return send_file(
        BytesIO(arquivo.read()),
        mimetype=doc.get("content_type", "application/octet-stream"),
        download_name=doc.get("filename", "imagem"),
    )


@app.route("/api/galeria/<foto_id>", methods=["DELETE"])
def excluir_foto(foto_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error

    parts = get_mongo_parts()
    try:
        doc = parts["gallery_meta"].find_one({"_id": ObjectId(foto_id)})
    except Exception:
        return jsonify({"erro": "ID de foto inválido."}), 400

    if not doc:
        return jsonify({"erro": "Foto não encontrada."}), 404

    try:
        parts["fs"].delete(doc["gridfs_id"])
    except Exception:
        pass

    parts["gallery_meta"].delete_one({"_id": doc["_id"]})
    return jsonify({"mensagem": "Foto excluída com sucesso."})


@app.route("/api/programas", methods=["GET"])
def listar_programas():
    auth_error = require_program_access()
    if auth_error:
        return auth_error

    q = request.args.get("q", "").strip()
    filtro = {}
    if q:
        filtro = {
            "$or": [
                {"titulo": {"$regex": q, "$options": "i"}},
                {"descricao": {"$regex": q, "$options": "i"}},
                {"categoria": {"$regex": q, "$options": "i"}},
                {"link": {"$regex": q, "$options": "i"}},
            ]
        }

    docs = get_mongo_parts()["programs"].find(filtro).sort("created_at", -1)
    return jsonify([serializar_programa(doc) for doc in docs])


@app.route("/api/programas", methods=["POST"])
def criar_programa():
    auth_error = require_admin()
    if auth_error:
        return auth_error

    dados = request.get_json(silent=True) or {}
    titulo = (dados.get("titulo") or "").strip()
    categoria = (dados.get("categoria") or "").strip()
    descricao = dados.get("descricao") or ""
    link = (dados.get("link") or "").strip()
    senha_individual = (dados.get("senha_individual") or "").strip()

    if not titulo:
        return jsonify({"erro": "O título do programa é obrigatório."}), 400
    if not link and not descricao:
        return jsonify({"erro": "Informe um link ou cole um conteúdo do programa."}), 400

    agora = datetime.utcnow().isoformat()
    doc = {
        "titulo": titulo,
        "categoria": categoria,
        "descricao": descricao,
        "link": link,
        "senha_individual": senha_individual,
        "created_at": agora,
        "updated_at": agora,
    }
    resultado = get_mongo_parts()["programs"].insert_one(doc)
    doc["_id"] = resultado.inserted_id
    return jsonify(serializar_programa(doc)), 201


@app.route("/api/programas/<programa_id>", methods=["PUT"])
def editar_programa(programa_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error

    dados = request.get_json(silent=True) or {}
    titulo = (dados.get("titulo") or "").strip()
    categoria = (dados.get("categoria") or "").strip()
    descricao = dados.get("descricao") or ""
    link = (dados.get("link") or "").strip()
    senha_individual = (dados.get("senha_individual") or "").strip()

    if not titulo:
        return jsonify({"erro": "O título do programa é obrigatório."}), 400
    if not link and not descricao:
        return jsonify({"erro": "Informe um link ou cole um conteúdo do programa."}), 400

    try:
        resultado = get_mongo_parts()["programs"].update_one(
            {"_id": ObjectId(programa_id)},
            {
                "$set": {
                    "titulo": titulo,
                    "categoria": categoria,
                    "descricao": descricao,
                    "link": link,
                    "senha_individual": senha_individual,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            },
        )
    except Exception:
        return jsonify({"erro": "ID de programa inválido."}), 400

    if resultado.matched_count == 0:
        return jsonify({"erro": "Programa não encontrado."}), 404

    doc = get_mongo_parts()["programs"].find_one({"_id": ObjectId(programa_id)})
    return jsonify(serializar_programa(doc))


@app.route("/api/programas/<programa_id>", methods=["DELETE"])
def excluir_programa(programa_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error

    try:
        resultado = get_mongo_parts()["programs"].delete_one({"_id": ObjectId(programa_id)})
    except Exception:
        return jsonify({"erro": "ID de programa inválido."}), 400

    if resultado.deleted_count == 0:
        return jsonify({"erro": "Programa não encontrado."}), 404

    return jsonify({"mensagem": "Programa excluído com sucesso."})


@app.route("/api/programas/<programa_id>/abrir", methods=["POST"])
def validar_senha_programa(programa_id):
    auth_error = require_program_access()
    if auth_error:
        return auth_error

    try:
        doc = get_mongo_parts()["programs"].find_one({"_id": ObjectId(programa_id)})
    except Exception:
        return jsonify({"erro": "ID de programa inválido."}), 400

    if not doc:
        return jsonify({"erro": "Programa não encontrado."}), 404

    senha_cadastrada = (doc.get("senha_individual") or "").strip()
    if senha_cadastrada:
        dados = request.get_json(silent=True) or {}
        senha = (dados.get("senha") or "").strip()
        if senha != senha_cadastrada:
            return jsonify({"erro": "Senha individual do programa incorreta."}), 401

    link = (doc.get("link") or "").strip()
    descricao = doc.get("descricao") or ""

    if link:
        return jsonify({"ok": True, "tipo": "link", "link": link})
    if descricao:
        return jsonify({
            "ok": True,
            "tipo": "texto",
            "titulo": doc.get("titulo", "Programa"),
            "conteudo": descricao,
        })

    return jsonify({"erro": "Esse programa não possui link nem conteúdo para exibir."}), 400


@app.route("/api/seed", methods=["POST"])
def seed_programas():
    auth_error = require_admin()
    if auth_error:
        return auth_error

    parts = get_mongo_parts()
    if parts["programs"].count_documents({}) > 0:
        return jsonify({"mensagem": "A coleção de programas já possui registros."})

    agora = datetime.utcnow().isoformat()
    exemplos = [
        {
            "titulo": "Sistema de Ocorrências",
            "categoria": "Gestão escolar",
            "descricao": "Link para o sistema principal de ocorrências.",
            "link": "https://exemplo.com/ocorrencias",
            "senha_individual": "",
            "created_at": agora,
            "updated_at": agora,
        },
        {
            "titulo": "Modelo de texto preservado",
            "categoria": "TXT / Código",
            "descricao": "linha 1\nlinha 2\n    bloco com recuo\nvalor = 10",
            "link": "",
            "senha_individual": "",
            "created_at": agora,
            "updated_at": agora,
        },
    ]
    parts["programs"].insert_many(exemplos)
    return jsonify({"mensagem": "Programas de exemplo criados."})


if __name__ == "__main__":
    porta = int(os.getenv("PORT", 5000))
    try:
        parts = get_mongo_parts()
        parts["client"].admin.command("ping")
        print("MongoDB conectado com sucesso.")
    except PyMongoError as e:
        print(f"Aviso: não foi possível validar a conexão com o MongoDB agora: {e}")
    except Exception as e:
        print(f"Aviso: configuração do ambiente: {e}")
    app.run(host="0.0.0.0", port=porta, debug=True)
