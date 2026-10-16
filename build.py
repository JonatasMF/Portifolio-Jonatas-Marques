"""
Gera o site estático a partir do content.py.

Como usar:
    1. Edite textos, links e projetos no content.py.
    2. Rode:  python build.py
    3. Publique a pasta "site/" (Vercel, Netlify, GitHub Pages...).

Fotos, currículo e planilhas ficam em assets/ (img/ e docs/) e são copiados para site/.
"""
import html
import re
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import content

RAIZ = Path(__file__).resolve().parent
ASSETS = RAIZ / "assets"
SAIDA = RAIZ / "site"

# Só esses endereços podem abrir dentro da janela do painel.
HOSTS_PERMITIDOS_NA_JANELA = {"app.powerbi.com", "app.fabric.microsoft.com"}


def e(valor):
    return html.escape(str(valor), quote=True)


def limpar_url(valor):
    """Aceita o link puro ou o código <iframe ...> inteiro copiado do Power BI."""
    valor = (valor or "").strip()
    achado = re.search(r"""src=["']([^"']+)["']""", valor)
    if achado:
        valor = achado.group(1)
    valor = valor.replace("&amp;", "&")
    return valor if valor.lower().startswith(("https://", "http://")) else ""


def preparar_projeto(projeto):
    p = dict(projeto)
    p["url"] = limpar_url(p.get("url"))
    host = urlparse(p["url"]).hostname if p["url"] else None
    p["incorporado"] = (
        bool(p.get("incorporar")) and p["url"].startswith("https://") and host in HOSTS_PERMITIDOS_NA_JANELA
    )
    return p


# ---------------------------------------------------------------------------
# Estrutura comum às duas páginas
# ---------------------------------------------------------------------------
FAVICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
    "%3Crect width='32' height='32' rx='7' fill='%230b6a62'/%3E"
    "%3Ctext x='16' y='22' font-family='Arial' font-size='15' font-weight='700' "
    "text-anchor='middle' fill='white'%3EJF%3C/text%3E%3C/svg%3E"
)


def pagina(titulo, descricao, ativa, corpo):
    pessoa = content.PESSOA

    def aba(arquivo, pequeno, texto, chave):
        atual = ' aria-current="page"' if ativa == chave else ""
        return f'<a class="tab" href="{arquivo}"{atual}><small>{pequeno}</small>{texto}</a>'

    return f"""<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>{e(titulo)}</title>
  <meta name="description" content="{e(descricao)}">
  <link rel="icon" href="{FAVICON}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <a class="skip" href="#conteudo">Pular para o conteúdo</a>

  <header class="bar">
    <div class="wrap bar-in">
      <div class="brand">Jônatas Farias <span>portfólio de dados</span></div>
      <nav class="tabs" aria-label="Páginas do portfólio">
        {aba("index.html", "Página 1 de 2", "Perfil e projetos", "perfil")}
        {aba("contato.html", "Página 2 de 2", "Contato e currículo", "contato")}
      </nav>
    </div>
  </header>

  <main class="wrap" id="conteudo">
{corpo}
  </main>

  <footer>
    <div class="wrap">© {date.today().year} {e(pessoa["nome"])}</div>
  </footer>

  <script src="js/site.js" defer></script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Página 1: perfil e projetos
# ---------------------------------------------------------------------------
def cartao_projeto(p):
    partes = [f'        <article class="card{" pending" if p.get("pendente") else ""}" data-ferramenta="{e(p["ferramenta"])}">']
    partes.append('          <div class="top">')
    partes.append(f'            <span class="stack">{e(p["stack"])}</span>')
    if p.get("pendente"):
        partes.append('            <span class="badge">Em breve</span>')
    partes.append("          </div>")
    partes.append(f'          <h3>{e(p["titulo"])}</h3>')
    partes.append(f'          <p>{e(p["texto"])}</p>')
    if p.get("visuais"):
        itens = "".join(f"<li>{e(v)}</li>" for v in p["visuais"])
        partes.append(f'          <ul class="visuais" aria-label="O que o projeto mostra">{itens}</ul>')

    acoes = []
    tem_download = bool(p.get("download") and p.get("slug"))
    if p["incorporado"]:
        acoes.append(
            f'<button type="button" class="btn primary" data-painel-url="{e(p["url"])}" '
            f'data-painel-titulo="{e(p["titulo"])}">Ver painel aqui</button>'
        )
        acoes.append(f'<a class="btn" href="{e(p["url"])}" target="_blank" rel="noopener">Abrir em nova aba</a>')
    elif p["url"]:
        acoes.append(f'<a class="btn" href="{e(p["url"])}" target="_blank" rel="noopener">Abrir projeto</a>')
    elif not p.get("download"):
        acoes.append('<span class="btn" aria-disabled="true">Link em breve</span>')
    if tem_download:
        nome = Path(p["download"]).name
        rotulo = p.get("download_rotulo") or "Baixar arquivo"
        acoes.append(f'<a class="btn primary" href="{e(p["download"])}" download="{e(nome)}">{e(rotulo)}</a>')
    partes.append('          <div class="acoes">' + "".join(acoes) + "</div>")

    if p.get("meta"):
        partes.append(f'          <p class="meta">{e(p["meta"])}</p>')
    partes.append("        </article>")
    return "\n".join(partes)


def corpo_perfil():
    pessoa = content.PESSOA
    projetos = [preparar_projeto(p) for p in content.PROJETOS]

    sobre = "\n".join(f'        <p class="lead">{e(par)}</p>' for par in pessoa["sobre"])
    ficha = "\n".join(f"      <div><dt>{e(r)}</dt><dd>{e(v)}</dd></div>" for r, v in content.FICHA)

    chips = []
    for chave, nome in content.FILTROS:
        atual = ' aria-current="true"' if chave == "todos" else ""
        chips.append(f'      <a class="chip" href="#projetos" data-filtro="{e(chave)}"{atual}>{e(nome)}</a>')
    cartoes = "\n".join(cartao_projeto(p) for p in projetos)

    trajetoria = []
    for t in content.TRAJETORIA:
        atual = ' <span class="tag-now">Atual</span>' if t.get("atual") else ""
        itens = "".join(f"<li>{e(i)}</li>" for i in t["itens"])
        trajetoria.append(
            f"""      <li>
        <span class="when">{e(t["quando"])}</span>
        <div>
          <h3>{e(t["titulo"])}{atual}</h3>
          <p class="org">{e(t["org"])}</p>
          <ul class="itens">{itens}</ul>
        </div>
      </li>"""
        )

    ferramentas = "\n".join(
        f'      <div class="tool"><h3>{e(n)}</h3><p>{e(t)}</p></div>' for n, t in content.FERRAMENTAS
    )
    competencias = "".join(f"<li>{e(c)}</li>" for c in content.COMPETENCIAS)
    form = content.FORMACAO
    cursos = "\n".join(
        f'      <li><span>{e(c)}</span><span class="escola">{e(s)}</span></li>' for c, s in content.CURSOS
    )

    return f"""    <div class="panel">

      <section class="hero" aria-label="Apresentação">
        <img class="foto" src="{e(pessoa["foto"])}" alt="{e(pessoa["foto_alt"])}" width="720" height="720">
        <div>
          <p class="eyebrow">{e(pessoa["titulo"])}</p>
          <h1>{e(pessoa["nome"])}</h1>
          <p class="role">{e(pessoa["frase"])}</p>
{sobre}
        </div>
      </section>

      <dl class="ficha">
{ficha}
      </dl>

      <section aria-labelledby="h-projetos" id="projetos">
        <div class="sec-head">
          <p class="eyebrow">Power BI · Python · Excel</p>
          <h2 id="h-projetos">Projetos</h2>
          <p>Escolha uma ferramenta para filtrar os projetos.</p>
        </div>

        <nav class="filters" aria-label="Filtrar projetos por ferramenta">
{chr(10).join(chips)}
        </nav>

        <div class="projects">
{cartoes}
        </div>
        <p class="hint">Os painéis de Power BI abrem aqui mesmo, em uma janela. Os apps do Streamlit abrem no site de origem, em uma nova aba.</p>

        <dialog class="painel" id="painel" aria-labelledby="painel-titulo">
          <div class="painel-topo">
            <h2 id="painel-titulo">Painel</h2>
            <form method="dialog"><button class="copy" autofocus>Fechar</button></form>
          </div>
          <iframe id="painel-quadro" title="Painel de Power BI" src="about:blank" allowfullscreen referrerpolicy="no-referrer"></iframe>
          <div class="painel-rodape">
            <span class="so-celular">No celular, o painel fica melhor em uma nova aba.</span>
            <a id="painel-link" href="#" target="_blank" rel="noopener">Abrir em nova aba</a>
          </div>
        </dialog>
      </section>

      <section aria-labelledby="h-trajetoria">
        <div class="sec-head">
          <p class="eyebrow">Do mais recente ao mais antigo</p>
          <h2 id="h-trajetoria">Trajetória</h2>
        </div>
        <ul class="timeline">
{chr(10).join(trajetoria)}
        </ul>
      </section>

      <section aria-labelledby="h-ferramentas">
        <div class="sec-head">
          <p class="eyebrow">O que uso no dia a dia</p>
          <h2 id="h-ferramentas">Ferramentas</h2>
        </div>
        <div class="tools">
{ferramentas}
        </div>
        <ul class="visuais competencias" aria-label="Competências">{competencias}</ul>
      </section>

      <section aria-labelledby="h-formacao">
        <div class="sec-head">
          <p class="eyebrow">Graduação e cursos</p>
          <h2 id="h-formacao">Formação</h2>
        </div>
        <ul class="timeline">
          <li>
            <span class="when">{e(form["quando"])}</span>
            <div><h3>{e(form["titulo"])}</h3><p class="org">{e(form["org"])}</p></div>
          </li>
        </ul>
        <ul class="cursos">
{cursos}
        </ul>
      </section>

    </div>"""


# ---------------------------------------------------------------------------
# Página 2: contato e currículo
# ---------------------------------------------------------------------------
def corpo_contato():
    pessoa = content.PESSOA
    linhas = []
    for c in content.CONTATOS:
        if not c["valor"]:
            continue
        if c.get("link"):
            externo = ' target="_blank" rel="noopener"' if c["link"][:4] == "http" else ""
            valor = f'<a class="v" href="{e(c["link"])}"{externo}>{e(c["valor"])}</a>'
        else:
            valor = f'<span class="v">{e(c["valor"])}</span>'
        if c.get("copiar"):
            botao = f'<button type="button" class="copy" data-copiar="{e(c["valor"])}">Copiar</button>'
        else:
            botao = "<span></span>"
        linhas.append(f'          <li>\n            <span class="k">{e(c["rotulo"])}</span>\n            {valor}\n            {botao}\n          </li>')

    return f"""    <div class="panel">
      <div class="sec-head" style="margin-bottom:0">
        <p class="eyebrow">Vamos conversar</p>
        <h1 class="h2-like">Contato e currículo</h1>
      </div>

      <div class="two">
        <div>
          <h2 class="eyebrow" style="margin-bottom:12px">Onde me encontrar</h2>
          <ul class="contact-list">
{chr(10).join(linhas)}
          </ul>
        </div>

        <div class="cv">
          <div class="file">
            <div class="doc-icon" aria-hidden="true">PDF</div>
            <div>
              <h2>Currículo</h2>
              <p class="mono meta-cv">{e(pessoa["curriculo_info"])}</p>
            </div>
          </div>
          <p>Formação, experiência, habilidades e cursos, pronto para imprimir ou anexar.</p>
          <div class="actions">
            <a class="btn primary" href="{e(pessoa["curriculo_arquivo"])}" download="{e(pessoa["curriculo_download"])}">Baixar currículo (PDF)</a>
            <a class="btn" href="{e(pessoa["curriculo_arquivo"])}" target="_blank" rel="noopener">Ver no navegador</a>
          </div>
        </div>
      </div>
    </div>"""


def main():
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    shutil.copytree(ASSETS, SAIDA)

    pessoa = content.PESSOA
    (SAIDA / "index.html").write_text(
        pagina(
            "Portfólio Jônatas Farias",
            f'Portfólio de {pessoa["nome"]}: {pessoa["titulo"]}, projetos de Power BI e Python, contato e currículo.',
            "perfil",
            corpo_perfil(),
        ),
        encoding="utf-8",
    )
    (SAIDA / "contato.html").write_text(
        pagina(
            "Contato e currículo · Jônatas Farias",
            f'Contato e currículo em PDF de {pessoa["nome"]}.',
            "contato",
            corpo_contato(),
        ),
        encoding="utf-8",
    )
    print("Site gerado em:", SAIDA)


if __name__ == "__main__":
    main()
