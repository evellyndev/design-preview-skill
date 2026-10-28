#!/usr/bin/env python3
"""Gerencia 3 previews HTML de uma skill Codex sem dependências de terceiros.

Executar da raiz do repositório, apontando --project-root para ela.
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

DESIGNS = ("design-01", "design-02", "design-03")
MANIFEST = ".design-preview.json"
MARKER = ".design-preview-managed"


class PreviewError(RuntimeError):
    pass


def paths(project_root: str) -> tuple[Path, Path]:
    root = Path(project_root).expanduser().resolve()
    if not root.is_dir():
        raise PreviewError(f"Raiz de projeto não encontrada: {root}")
    return root, root / "preview"


def assert_preview(preview: Path) -> None:
    if preview.is_symlink() or not preview.is_dir():
        raise PreviewError("preview/ precisa ser um diretório real, não um link simbólico")
    if not (preview / MANIFEST).is_file() or (preview / MANIFEST).is_symlink():
        raise PreviewError("preview/ não foi criado por esta skill (manifesto ausente)")


def read_manifest(preview: Path) -> dict:
    assert_preview(preview)
    try:
        manifest = json.loads((preview / MANIFEST).read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise PreviewError("Manifesto inválido") from exc
    if manifest.get("managed_by") != "design-preview":
        raise PreviewError("Manifesto não pertence à skill design-preview")
    if [v.get("id") for v in manifest.get("variants", [])] != list(DESIGNS):
        raise PreviewError("Manifesto não contém exatamente as três opções esperadas")
    return manifest


def write_manifest(preview: Path, manifest: dict) -> None:
    (preview / MANIFEST).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def validate_design(preview: Path, design: str) -> Path:
    if design not in DESIGNS:
        raise PreviewError("Design inválido; escolha 1, 2 ou 3")
    target = preview / design
    if target.is_symlink() or not target.is_dir():
        raise PreviewError(f"Pasta de design ausente ou não segura: {design}")
    if (target / MARKER).is_symlink() or not (target / MARKER).is_file():
        raise PreviewError(f"Pasta sem marca de gerenciamento: {design}")
    return target


def placeholder(design: str) -> str:
    number = design[-2:]
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Proposta {number}</title><style>
body{{margin:0;min-height:100vh;display:grid;place-items:center;font:16px system-ui,sans-serif;background:#f2f2f5;color:#252530}}
main{{max-width:32rem;padding:2rem}}small{{letter-spacing:.15em;text-transform:uppercase;color:#666}}
</style></head><body><main><small>Design Preview · {number}</small>
<h1>Proposta {number}</h1><p>O Codex substituirá esta tela pela proposta baseada no design_guideline.</p>
</main></body></html>
"""


def gallery(manifest: dict) -> str:
    cards = []
    for variant in manifest["variants"]:
        design = variant["id"]
        name = html.escape(str(variant.get("name") or design))
        desc = html.escape(str(variant.get("description") or ""))
        cards.append(f"""<article class="card">
  <div class="card-top"><div><p class="eyebrow">{html.escape(design.upper())}</p><h2>{name}</h2><p class="description">{desc}</p></div>
    <a href="./{design}/index.html" target="_blank" rel="noopener">Abrir em outra aba ↗</a></div>
  <iframe src="./{design}/index.html" title="Prévia {name}" loading="lazy"></iframe>
  <button type="button" data-select="{design}">Escolher esta opção</button>
</article>""")
    return """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Design Preview · Escolha uma proposta</title>
<style>
:root{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#20202a;background:#f5f5f8;font-synthesis:none}
*{box-sizing:border-box}body{margin:0}header{padding:clamp(24px,4vw,56px) clamp(16px,4vw,60px) 22px;max-width:1700px;margin:auto}
header p{color:#626275;max-width:70ch;line-height:1.55}h1{font-size:clamp(28px,3vw,46px);letter-spacing:-.04em;margin:0}h2{font-size:20px;letter-spacing:-.02em;margin:3px 0 8px}
.gallery{padding:12px clamp(16px,4vw,60px) 42px;max-width:1700px;margin:auto;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}
.card{background:white;border:1px solid #dddde5;border-radius:16px;overflow:hidden;display:flex;flex-direction:column;min-width:0;box-shadow:0 7px 24px #1010200c}
.card-top{padding:18px 18px 12px;min-height:160px;display:flex;justify-content:space-between;align-items:start;gap:12px;flex-wrap:wrap}
.eyebrow{font-size:11px;letter-spacing:.13em;color:#686879;font-weight:700;margin:0}.description{color:#6b6b78;margin:0;line-height:1.5;font-size:13px}
a{font-size:12px;color:#5546d8;text-decoration:none}a:hover{text-decoration:underline}
iframe{display:block;width:100%;height:min(63vh,650px);min-height:430px;border:0;border-block:1px solid #e4e4e8;background:white}
button{border:0;background:#292335;color:white;font:600 15px system-ui;padding:16px;cursor:pointer;margin:16px 18px 18px;border-radius:9px}
button:hover{background:#51416b}button:focus-visible,a:focus-visible{outline:3px solid #806bff;outline-offset:3px}
footer{padding:0 24px 28px;text-align:center;color:#686879;font-size:13px}
@media(max-width:1120px){.gallery{grid-template-columns:1fr}.card-top{min-height:unset}iframe{height:560px}}
</style></head><body>
<header><h1>Escolha um caminho visual</h1><p>Três propostas para a mesma interface, seguindo o design guideline. Navegue pelas telas e escolha apenas quando tiver decidido: as outras duas pastas serão excluídas.</p></header>
<main class="gallery">""" + "\n".join(cards) + """</main>
<footer>Para escolher pela galeria, abra esta página no servidor local da skill. Também é possível selecionar via Codex.</footer>
<script>
document.querySelectorAll('[data-select]').forEach(button => button.addEventListener('click', async () => {
  const design = button.dataset.select;
  if (!confirm(`Manter ${design} e apagar definitivamente as outras duas opções?`)) return;
  button.disabled = true;
  try {
    const response = await fetch('/api/select', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({design})});
    const data = await response.json();
    if (!response.ok) throw Error(data.error || 'Não foi possível selecionar.');
    location.href = `./${data.selected}/index.html`;
  } catch (error) { alert(`Escolha não aplicada: ${error.message}. Execute o servidor local da skill ou selecione pelo Codex.`); button.disabled = false; }
}));
</script></body></html>
"""


def winner_page(selected: str) -> str:
    label = html.escape(selected)
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="0;url=./{label}/index.html"><title>Design escolhido</title></head>
<body><p>Proposta escolhida: <a href="./{label}/index.html">{label}</a>.</p></body></html>"""


def init(preview: Path) -> None:
    if preview.exists() or preview.is_symlink():
        raise PreviewError("preview/ já existe. Nenhum arquivo foi alterado: inspecione antes de refazer")
    preview.mkdir()
    manifest = {
        "managed_by": "design-preview",
        "status": "awaiting_selection",
        "selected": None,
        "variants": [
            {"id": item, "name": f"Proposta {idx}", "description": "Aguardando criação do design pelo Codex"}
            for idx, item in enumerate(DESIGNS, 1)
        ],
    }
    write_manifest(preview, manifest)
    for design in DESIGNS:
        directory = preview / design
        directory.mkdir()
        (directory / MARKER).write_text("Gerenciado pela skill design-preview.\n", encoding="utf-8")
        (directory / "index.html").write_text(placeholder(design), encoding="utf-8")
    (preview / "index.html").write_text(gallery(manifest), encoding="utf-8")
    print(f"Criado: {preview} (3 propostas pendentes)")


def render_index(preview: Path) -> None:
    manifest = read_manifest(preview)
    if manifest["status"] == "selected":
        content = winner_page(manifest["selected"])
    elif manifest["status"] == "awaiting_selection":
        for design in DESIGNS:
            validate_design(preview, design)
        content = gallery(manifest)
    else:
        raise PreviewError("Estado inválido no manifesto")
    (preview / "index.html").write_text(content, encoding="utf-8")
    print(f"Galeria atualizada: {preview / 'index.html'}")


def select(preview: Path, design: str) -> str:
    manifest = read_manifest(preview)
    if manifest["status"] == "selected":
        if manifest.get("selected") == design:
            print(f"Design {design} já havia sido selecionado")
            return design
        raise PreviewError("Já existe um design escolhido. Nenhuma pasta foi apagada")
    if manifest["status"] != "awaiting_selection":
        raise PreviewError("Estado inválido; nenhuma pasta foi apagada")
    # Verificar TODAS as pastas antes de iniciar qualquer exclusão.
    for item in DESIGNS:
        validate_design(preview, item)
    for item in DESIGNS:
        if item != design:
            shutil.rmtree(preview / item)
    manifest["status"] = "selected"
    manifest["selected"] = design
    write_manifest(preview, manifest)
    (preview / "index.html").write_text(winner_page(design), encoding="utf-8")
    print(f"Escolhido: {design}. Os outros dois diretórios foram removidos de {preview}")
    return design


def serve(preview: Path, port: int) -> None:
    read_manifest(preview)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(preview), **kwargs)

        def do_POST(self):
            if urlparse(self.path).path != "/api/select":
                self.send_error(404)
                return
            origin = self.headers.get("Origin")
            allowed = {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}
            if origin and origin not in allowed:
                self.send_json(403, {"error": "Origem não autorizada"})
                return
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                self.send_json(415, {"error": "Envie application/json"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length < 1024:
                    raise ValueError("Corpo inválido")
                data = json.loads(self.rfile.read(length))
                design = data["design"]
                if not isinstance(design, str) or design not in DESIGNS:
                    raise ValueError("Escolha inválida")
                selected = select(preview, design)
                self.send_json(200, {"selected": selected})
            except (ValueError, KeyError, json.JSONDecodeError) as exc:
                self.send_json(400, {"error": str(exc)})
            except PreviewError as exc:
                self.send_json(409, {"error": str(exc)})

        def send_json(self, status: int, value: dict):
            data = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"Galeria disponível em http://127.0.0.1:{port}/ (Ctrl+C para parar)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Galeria local com 3 designs, 1 escolha e exclusão controlada")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "index", "select", "serve"):
        p = sub.add_parser(command)
        p.add_argument("--project-root", default=".", help="Raiz do projeto onde fica preview/")
        if command == "select":
            p.add_argument("--design", required=True, choices=("1", "2", "3"))
        if command == "serve":
            p.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    _, preview = paths(args.project_root)
    try:
        if args.command == "init":
            init(preview)
        elif args.command == "index":
            render_index(preview)
        elif args.command == "select":
            select(preview, f"design-0{args.design}")
        elif args.command == "serve":
            serve(preview, args.port)
    except PreviewError as exc:
        parser.exit(1, f"Erro: {exc}\n")


if __name__ == "__main__":
    main()
