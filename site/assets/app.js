// Comportamento do site da documentação: tema claro/escuro, menu no celular, item ativo do menu e diagramas.
(function () {
  var raiz = document.documentElement;

  // Tema: escolha salva no navegador; sem escolha, segue o sistema operacional.
  function temaInicial() {
    try {
      var salvo = localStorage.getItem("prioriza-tema");
      if (salvo) return salvo;
    } catch (e) { /* navegação privada: segue o sistema */ }
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "escuro" : "claro";
  }
  function aplicarTema(tema) {
    raiz.setAttribute("data-tema", tema);
    var botao = document.getElementById("alternar-tema");
    if (botao) {
      botao.textContent = tema === "escuro" ? "☀" : "☾";
      botao.setAttribute("aria-label", tema === "escuro" ? "Usar modo claro" : "Usar modo escuro");
    }
  }
  aplicarTema(temaInicial());

  document.addEventListener("DOMContentLoaded", function () {
    aplicarTema(raiz.getAttribute("data-tema"));

    var botaoTema = document.getElementById("alternar-tema");
    if (botaoTema) {
      botaoTema.addEventListener("click", function () {
        var novo = raiz.getAttribute("data-tema") === "escuro" ? "claro" : "escuro";
        try { localStorage.setItem("prioriza-tema", novo); } catch (e) { /* sem armazenamento */ }
        aplicarTema(novo);
        desenharDiagramas();
      });
    }

    // Menu lateral no celular.
    var botaoMenu = document.getElementById("abrir-menu");
    if (botaoMenu) {
      botaoMenu.addEventListener("click", function () { document.body.classList.toggle("menu-aberto"); });
      document.querySelectorAll(".menu-lateral a").forEach(function (link) {
        link.addEventListener("click", function () { document.body.classList.remove("menu-aberto"); });
      });
    }

    // Destaca no menu a seção que está na tela.
    var links = Array.prototype.slice.call(document.querySelectorAll(".menu-lateral a[href^='#']"));
    var secoes = links.map(function (l) { return document.getElementById(l.getAttribute("href").slice(1)); }).filter(Boolean);
    if ("IntersectionObserver" in window && secoes.length) {
      var observador = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (entrada) {
          if (!entrada.isIntersecting) return;
          links.forEach(function (l) { l.classList.toggle("ativo", l.getAttribute("href") === "#" + entrada.target.id); });
        });
      }, { rootMargin: "-80px 0px -70% 0px" });
      secoes.forEach(function (s) { observador.observe(s); });
    }

    desenharDiagramas();
  });

  // Diagramas Mermaid: o texto original fica guardado para redesenhar ao trocar o tema.
  function desenharDiagramas() {
    if (!window.mermaid) return;
    var blocos = document.querySelectorAll(".mermaid");
    blocos.forEach(function (bloco) {
      if (!bloco.dataset.fonte) bloco.dataset.fonte = bloco.textContent;
      bloco.removeAttribute("data-processed");
      bloco.innerHTML = bloco.dataset.fonte;
    });
    window.mermaid.initialize({ startOnLoad: false, theme: raiz.getAttribute("data-tema") === "escuro" ? "dark" : "neutral", securityLevel: "strict" });
    window.mermaid.run({ nodes: blocos });
  }
})();
