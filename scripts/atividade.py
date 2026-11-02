"""Atualiza a seção de atividade recente do README com dados públicos do GitHub."""

import html
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

USUARIO = "matheustonon1"
README = Path(__file__).resolve().parent.parent / "README.md"
MARCADORES = re.compile(r"(<!--INICIO:atividade-->).*?(<!--FIM:atividade-->)", re.DOTALL)
TOTAL_PRS = 5
TOTAL_REPOS = 4


def buscar(caminho, **parametros):
    url = f"https://api.github.com/{caminho}?{urllib.parse.urlencode(parametros)}"
    pedido = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        pedido.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(pedido, timeout=30) as resposta:
        return json.load(resposta)


def situacao(pr):
    if pr["pull_request"].get("merged_at"):
        return "🟣", "mesclado"
    if pr["state"] == "open":
        return "🟢", "aberto"
    return "🔴", "fechado"


def secao_prs():
    resultado = buscar(
        "search/issues",
        q=f"author:{USUARIO} type:pr is:public",
        sort="created",
        order="desc",
        per_page=TOTAL_PRS,
    )
    linhas = ["### Pull requests recentes", ""]
    for pr in resultado["items"]:
        repo = pr["repository_url"].removeprefix("https://api.github.com/repos/")
        titulo = html.escape(pr["title"])
        emoji, estado = situacao(pr)
        linhas.append(
            f'- {emoji} <a href="{pr["html_url"]}"><strong>{titulo}</strong></a><br>\n'
            f"  <sub><code>{repo}</code> • {pr['created_at'][:10]} • {estado}</sub>"
        )
    return linhas


def secao_repos():
    repos = buscar(f"users/{USUARIO}/repos", sort="pushed", per_page=30)
    visiveis = [r for r in repos if not r["fork"] and r["size"] > 0 and r["name"] != USUARIO]
    linhas = ["", "### Repositórios atualizados", ""]
    for repo in visiveis[:TOTAL_REPOS]:
        linha = f'- <a href="{repo["html_url"]}"><code>{repo["name"]}</code></a> • {repo["pushed_at"][:10]}'
        if repo["description"]:
            linha += f"<br>\n  <sub>{html.escape(repo['description'])}</sub>"
        linhas.append(linha)
    return linhas


def main():
    corpo = "\n".join(secao_prs() + secao_repos())
    atual = README.read_text(encoding="utf-8")
    novo, trocas = MARCADORES.subn(lambda m: f"{m[1]}\n{corpo}\n{m[2]}", atual)
    if trocas != 1:
        raise SystemExit("Marcadores de atividade não encontrados no README")
    README.write_text(novo, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
