
Here are a few random examples on how newslinkrss can be used to generate
feeds from several types of sites. They were working (or mostly working!)
in the moment this file was created but sites can change every time and
break the feeds.




# Sources in English


## News

#### [Associated Press / AP](https://apnews.com/)

    newslinkrss -t 5 -p 'https://apnews.com/article/.+' --follow --with-body --body-csss 'main' -C '.Page-actions, div.Page-below, template, div.Carousel-slides' -C '.Advertisement, div.Enhancement' -X '//a[not(@href) and not(node())]' --author-from-csss 'div.Page-authors span' -Q '^utm_' --title-regex '([^|]+)\s*|' https://apnews.com/

#### [Reuters](https://www.reuters.com/)

    newslinkrss  --follow  -p 'https://www.reuters.com/.+/.+\d{4}-\d{2}-\d{2}.+'  --max-page-length 512  --with-body  --body-xpath '//article'  --body-remove-csss 'div[class*="article-header__toolbar__"], div[class*="article-body__toolbar__"]'  --body-remove-csss 'div[class*="article__read-next__"], div.read-next-panel'  --require-dates  --title-regex '(.+)\s+\|'  https://www.reuters.com/

#### [The Washington Post / WaPo](https://www.washingtonpost.com/)

    newslinkrss -n 60 -p '^https://www.washingtonpost.com/.+/\d+/\d+/\d+/.+' --follow --author-from-xpath '//a[@rel="author"]/text()' --with-body --body-csss 'main header h1, main header h2, main header .print-byline, main .article-body' --title-regex '(.*\S)\s*-[^-]*'  -C '.hide-for-print' https://www.washingtonpost.com/

#### [The Economist](https://www.economist.com/)

    newslinkrss --follow -t 4 -p 'https://www.economist.com/.+/\d{4}/\d{2}/\d{2}/.+' --max-page-length 512 --with-body --body-csss 'article section' --title-regex '(.+)\s*|' --date-from-xpath '//time[@datetime]/@datetime' -C style --require-dates https://www.economist.com/

#### [KyivPost](https://www.kyivpost.com/)

    newslinkrss -p 'https://www.kyivpost.com/post/\d+' -fB --body-csss '.post-lead, div#post-content' --title-from-csss 'h1.post-title' --date-from-csss 'div.post-info' --csss-date-regex '.*([A-Z][a-z]+.*\s\d+,\s+\d+.+[ap]m)'  --author-from-csss 'div.post-info a[href*="/authors/"], a.post-author-name' https://www.kyivpost.com/

#### [ABC News](https://abcnews.go.com/)

    newslinkrss  -p 'https://abcnews.go.com/.+/.+(-|id=)\d+' --follow --date-from-xpath '//meta[@property="lastPublishedDate"]/@content' --with-body --body-csss 'div.FITT_Article_main__body' --require-dates --title-regex '(.+)\s*-\s*ABC News' https://abcnews.go.com/

#### [Intelligencer – New York Magazine](https://nymag.com/intelligencer/)

    newslinkrss --follow -p '.*//nymag.com/intelligencer/(article|\d+/\d+)/.+\.html' --with-body --body-csss 'article' -C 'aside.newsletter-flex-text' -C 'section.package-list' -C 'div.comments-link' -C 'div.tags' -C 'style' https://nymag.com/intelligencer/


## J. R. R. Tolkien

#### [DeviantArt Tolkien search](https://www.deviantart.com/search?q=tolkien)

    newslinkrss  -p 'https://www.deviantart.com/.+/art/.+-\d+' --follow --date-from-xpath '(//main//time[@datetime])[1]/@datetime' --with-body --body-xpath '//main/div' -X '//a[@data-hook="deviation_link"]/../../..' -X '//section[@data-hook="action_bar"]' https://www.deviantart.com/search?q=tolkien

#### [DeviantArt Tolkien cosplay](https://www.deviantart.com/search?q=tolkiencosplay+or+silmarillioncosplay+or+lotrcosplay)

    newslinkrss  -p 'https://www.deviantart.com/.+/art/.+-\d+' --follow --date-from-xpath '(//main//time[@datetime])[1]/@datetime' --with-body --body-xpath '//main/div' -X '//a[@data-hook="deviation_link"]/../../..' -X '//section[@data-hook="action_bar"]' https://www.deviantart.com/search?q=tolkiencosplay+or+silmarillioncosplay+or+lotrcosplay


## Science

#### [Nature](https://www.nature.com/)

    newslinkrss -p 'https://www.nature.com/articles/.+' --follow  --with-body --body-csss 'main' --date-from-xpath '//time[@datetime]/@datetime' --title-regex '(.+)\s*\|\s*Nature' -C '.u-hide-print' -C '.hide-print' -C 'style' https://www.nature.com/

#### [Reuters / Science](https://www.reuters.com/science/)

    newslinkrss  --follow  -p 'https://www.reuters.com/.+/.+\d{4}-\d{2}-\d{2}.+'  --max-page-length 512  --with-body  --body-xpath '//article'  --body-remove-csss 'div[class*="article-header__toolbar__"], div[class*="article-body__toolbar__"]'  --body-remove-csss 'div[class*="article__read-next__"], div.read-next-panel'  --require-dates  --title-regex '(.+)\s+\|'  https://www.reuters.com/science/


## Computing

#### [USENIX - ;login:](https://www.usenix.org/publications/loginonline)

    newslinkrss -p 'https://www.usenix.org/publications/loginonline/[^/]+' -i '.*/loginonline/writing$' -t 5 --follow --with-body --body-csss '#main-wrapper' --title-regex '^([^|]*[^|\s])' https://www.usenix.org/publications/loginonline

#### [USENIX - Proceedings](https://www.usenix.org/publications/proceedings)

    newslinkrss -p 'https://www.usenix.org/conference/[^/]+/presentation/.+' -t 5 --follow --with-body --body-csss 'article' --title-regex '^([^|]*[^|\s])' https://www.usenix.org/publications/proceedings



# Sources in Portuguese / Fontes em Português


## Jornais e revistas

#### [Folha de S.Paulo](https://www.folha.uol.com.br/)

    newslinkrss --follow -p 'https://www.*\.folha\.uol\.com.br/.+/\d+/\d+/.+\.shtml' --with-body --body-csss 'header.c-content-head h1, header.c-content-head h2, div.c-signature, div.c-news__body' -C 'div.rs_skip'  --title-regex '(.+) - \d+/\d+/\d+ -\s+.+\s+- Folha' --author-from-csss '.c-signature__author a, .c-signature__author, cite.c-blog-top__author-name, .c-author__name a, .c-top-columnist__name a' --encoding 'utf-8' --max-page-length 512 --body-rename-attr img data-src src https://www.folha.uol.com.br/

#### [Folha de S.Paulo - Hélio Schwartsman](https://www1.folha.uol.com.br/colunas/helioschwartsman/)

    newslinkrss --follow -p 'https://www1.folha.uol.com.br/colunas/helioschwartsman/\d+/\d+/.+\.shtml' --with-body --body-csss 'header.c-content-head h1, header.c-content-head h2, div.c-signature, div.c-news__body' -C 'div.rs_skip'  --title-regex '(.+) - \d+/\d+/\d+ -\s+.+\s+- Folha' --author-from-csss '.c-signature__author a, cite.c-blog-top__author-name, .c-author__name a, .c-top-columnist__name a' --encoding 'utf-8' --require-dates https://www1.folha.uol.com.br/colunas/helioschwartsman/

#### [Folha de S.Paulo - Reinaldo José Lopes](https://www1.folha.uol.com.br/autores/reinaldo-jose-lopes.shtml)

    newslinkrss --follow -p 'https://www1.folha.uol.com.br/.+/\d+/\d+/.+\.shtml' --with-body --body-csss 'header.c-content-head h1, header.c-content-head h2, div.c-signature, div.c-news__body' -C 'div.rs_skip'  --title-regex '(.+) - \d+/\d+/\d+ -\s+.+\s+- Folha' --author-from-csss '.c-signature__author a, cite.c-blog-top__author-name, .c-author__name a, .c-top-columnist__name a' --encoding 'utf-8' --max-page-length 512 --require-dates https://www1.folha.uol.com.br/autores/reinaldo-jose-lopes.shtml

#### [Folha de S.Paulo - Lygia Maria](https://www1.folha.uol.com.br/colunas/lygia-maria/)

    newslinkrss --follow -p 'https://www1.folha.uol.com.br/.+/lygia-maria/\d+/\d+/.+\.shtml' --with-body --body-csss 'header.c-content-head h1, header.c-content-head h2, div.c-signature, div.c-news__body' -C 'div.rs_skip'  --title-regex '(.+) - \d+/\d+/\d+ -\s+.+\s+- Folha' --author-from-csss '.c-signature__author a, cite.c-blog-top__author-name, .c-author__name a, .c-top-columnist__name a' --encoding 'utf-8' --max-page-length 512 --require-dates https://www1.folha.uol.com.br/colunas/lygia-maria/

#### [Jornal do Médio Vale](https://www.jornaldomediovale.com.br/)

    newslinkrss --follow --with-body  -p 'https://(www.)?jornaldomediovale.com.br/\S+\.\d+' --date-from-csss 'ul.post-meta-info > li:last-of-type' --csss-date-regex '\s*(\S.*\S).*' --csss-date-fmt '%d/%m/%Y %H:%M' --body-csss 'div.entry-content' --title-regex '.*/\s*([^/]+)$'  https://www.jornaldomediovale.com.br/

#### [Diário da Jaraguá](https://www.diariodajaragua.com.br/jaragua-do-sul/)

    newslinkrss -f -B -p 'https://www.diariodajaragua.com.br/.+/[0-9]+/' --body-xpath '//article' --max-page-length 1024 https://www.diariodajaragua.com.br/jaragua-do-sul/ -X '//a[contains(@href, "https://chat.whatsapp.com")]/..' -C '.squareBanner' -X '//header' -X '//section'

#### [O Globo - Últimas notícias](https://oglobo.globo.com/ultimas-noticias/)

    newslinkrss -p 'https://oglobo.globo.com/.+noticia/\d+/\d+/\d+/.+.ghtml' -fB --body-csss 'section.content--header div.content-head, section.content--header div.content__signature, article' --date-from-xpath '//time[@itemprop="datePublished" and @datetime]/@datetime' --author-from-csss 'address[itemprop="author"] a span[itemprop="name"]' -C 'section.mc-column.box-wrapper, section.passador-materia'  https://oglobo.globo.com/ultimas-noticias/ https://oglobo.globo.com/ultimas-noticias/index/feed/pagina-4 https://oglobo.globo.com/ultimas-noticias/index/feed/pagina-5 https://oglobo.globo.com/ultimas-noticias/index/feed/pagina-6

#### [O Globo - Elio Gaspari](https://oglobo.globo.com/opiniao/elio-gaspari/)

    newslinkrss -p 'https://oglobo.globo.com/opiniao/elio-gaspari/.+/\d+/\d+/.+\.ghtml' -fB --body-csss 'section.content--header div.content-head, section.content--header div.content__signature, article' --date-from-xpath '//time[@itemprop="datePublished" and @datetime]/@datetime' --author-from-csss 'address.header-coluna__title' -C 'section.mc-column.box-wrapper, section.passador-materia' https://oglobo.globo.com/opiniao/elio-gaspari/


## Portais

#### [UOL - Últimas notícias](https://noticias.uol.com.br/)

    newslinkrss --follow -t 4  -p 'https://noticias.uol.com.br/.+/\d+/\d+/.+' --date-from-xpath '//p[@ia-date-publish]/@ia-date-publish | //article//time[@datetime]/@datetime' --with-body --body-csss 'article div.author, article div.text, main article' --title-regex '(.+)\s+- UOL Notícias' -X '//div[@ia-related-content]' -C 'div.ads-wrapper, .solar-ads, .jupiter-ads, .solar-comment, .jupiter-see-too, .solar-social-media, .jupiter-share' -C 'aside, div.related-content, .related-content-front, div.related-content-piano, .chartbeat-related-content, .related-content-hyperlink, .blogs-and-columns-recommendation' -C 'div.loading-box, div.clearfix, .new-post-notice, .new-post-notice-columnist' -C 'svg' -C 'style' -C 'img.img-author' -C 'div.magazine-cover' -C '.disclaimer-exclusive-content'  --body-rename-attr img data-src src https://noticias.uol.com.br/

#### [G1 Santa Catarina](https://g1.globo.com/sc/santa-catarina/index/feed/pagina-1.ghtml)

    newslinkrss --follow -p 'https://g1.globo.com/.+santa-catarina/.*\d+/\d+/\d+/.+\.ghtml' -i '.+/especial-publicitario/.+' --with-body --body-xpath '//article' -N amp-img img --date-from-xpath '//time[@datetime]/@datetime' --title-regex '([^|]+)' $(seq -f "https://g1.globo.com/sc/santa-catarina/index/feed/pagina-%.0f.ghtml"  1 5)

#### [G1 Paraná](https://g1.globo.com/pr/parana/)

    newslinkrss --follow -p 'https://g1.globo.com/.+parana/.*\d+/\d+/\d+/.+\.ghtml' -i '.+/especial-publicitario/.+' --with-body --body-xpath '//article' -N amp-img img --date-from-xpath '//time[@datetime]/@datetime' --title-regex '([^|]+)'  'https://g1.globo.com/pr/parana/'  $(seq -f "https://g1.globo.com/pr/parana/index/feed/pagina-%.0f.ghtml"  1 5)

#### [NSC Total](https://www.nsctotal.com.br/)

    newslinkrss -t 4 -p 'https://www.nsctotal.com.br/(noticias|colunistas/.+)/.+' -i '.+//www.nsctotal.com.br/noticias/noticias-whatsapp-nsc-total' --follow --with-body --body-csss '#post-content' --title-from-csss h1.title --author-from-csss 'div.author a' -C 'a[href*=whatsapp]' --categories-from-csss 'div.tags a.tag' -C '.ad-single' https://www.nsctotal.com.br/ https://www.nsctotal.com.br/ultimas-noticias https://www.nsctotal.com.br/ultimas-noticias?paged=2

#### [Crusoé](https://crusoe.com.br/)

    newslinkrss -f -B -p 'https://crusoe.com.br/(edicoes/\d+|secao|diario)/.+'  --body-csss 'article.post' -C 'style, svg' -C 'div.share, .container_share, div.tags' -C '#action-mark, #show-audio-player' -C '#wallcontent, #move-banner-box1' -C '.comment-section'  --date-from-csss 'span.data' --csss-date-regex '(\d+\.\d+.\d+ \d+:\d+)' --csss-date-fmt  '%d.%m.%y %H:%M' --title-regex '(.+\S)\s*-\s*Crusoé\s*$' --author-from-csss 'span.autor-info span' --no-cookies https://crusoe.com.br/

#### [Migalhas](https://www.migalhas.com.br/)

    newslinkrss -n 30 -t 2 --follow --with-body --max-page-length 256 -p '^https://www.migalhas.com.br/(\w+/)+[0-9]+/.+' --body-xpath "//article" --require-dates -X '//app-compartilhamento-topo'  --title-regex '(.+)\s+-\s+Migalhas' https://www.migalhas.com.br/


## Universidades

#### [UDESC Joinville](https://www.udesc.br/cct/noticias)

    newslinkrss -n 100 -t 20 -T 'UDESC Joinville' -a '.*(\d{2}/\d{2}/\d{4}-\d{2}h\d{2}).*' --text-date-fmt '%d/%m/%Y-%Hh%M' -p '.+/cct/noticia/.+' https://www.udesc.br/cct/noticias


## Entidades governamentais

#### [Prefeitura de Jaraguá do Sul](https://www.jaraguadosul.sc.gov.br/noticias.php)

    newslinkrss -p 'https://www.jaraguadosul.sc.gov.br/news/.+' --http-timeout 10 --follow --with-body --body-csss 'div#area_impressao' --date-from-csss 'small.text-muted > b' --csss-date-fmt '%d/%m/%Y' https://www.jaraguadosul.sc.gov.br/noticias.php

#### [Câmara de Vereadores de Jaraguá do Sul](https://www.jaraguadosul.sc.leg.br/)

    newslinkrss -p 'https://www.jaraguadosul.sc.leg.br/(destaques|geral)/.+' -fB --body-csss '.elementor-widget-theme-post-content' --title-regex '(.*\S)\s*-[^-]+$' https://www.jaraguadosul.sc.leg.br/  https://www.jaraguadosul.sc.leg.br/publicacoes/destaques/ https://www.jaraguadosul.sc.leg.br/geral/

#### [ACN - Agência Catarinense de Notícias](https://estado.sc.gov.br/noticias/)

    newslinkrss -t 5 -p '^https://estado.sc.gov.br/noticias/[^/]+/?$' --follow --with-body --body-csss article.post -C '.addtoany_content' -i 'https://estado.sc.gov.br/noticias/todos-os-videos-da-tvsecom/?' -i 'https://estado.sc.gov.br/noticias/todos-os-audios-da-radio/?' -i 'https://estado.sc.gov.br/noticias/todas-as-noticias/?' -i 'https://estado.sc.gov.br/noticias/lista-de-assessores?/?' -i 'https://estado.sc.gov.br/noticias/transparencia/?' -i 'https://estado.sc.gov.br/noticias/todos-os-videos-da-tvsecom/?'   https://estado.sc.gov.br/noticias/ https://estado.sc.gov.br/noticias/todas-as-noticias/  https://estado.sc.gov.br/noticias/todas-as-noticias/page/2/ https://estado.sc.gov.br/noticias/todas-as-noticias/page/3/

#### [Gov.br — Secretaria de Comunicação Social](https://www.gov.br/secom/pt-br/fatos/brasil-contra-fake/noticias?b_size=60)

    newslinkrss -p '^https://www.gov.br/secom/pt-br/fatos/brasil-contra-fake/noticias/.+' --follow --with-body  --body-xpath '//article' --date-from-csss 'span.documentPublished span.value, span.documentModified span.value' --csss-date-fmt '%d/%m/%Y %Hh%M' -C 'div.social-links' --title-regex '(.+) — '  https://www.gov.br/secom/pt-br/fatos/brasil-contra-fake/noticias?b_size=60

#### [Anatel](https://www.gov.br/anatel/pt-br/assuntos/noticias?b_size=40)

    newslinkrss -p '^https://www.gov.br/anatel/pt-br/assuntos/noticias/.+' --follow --with-body  --body-xpath '//article' --date-from-csss 'span.documentPublished span.value, span.documentModified span.value' --csss-date-fmt '%d/%m/%Y %Hh%M' -C 'div.social-links' --title-regex '(.+) — '  https://www.gov.br/anatel/pt-br/assuntos/noticias?b_size=40

#### [Autoridade Nacional de Proteção de Dados - ANPD](https://www.gov.br/anpd/pt-br/assuntos/noticias)

    newslinkrss -p '^https://www.gov.br/anpd/pt-br/assuntos/noticias/.+' --follow --with-body  --body-xpath '//article' --date-from-csss 'span.documentPublished span.value' --csss-date-fmt '%d/%m/%Y %Hh%M' -C 'div.social-links'  --title-regex '(.+) — '  https://www.gov.br/anpd/pt-br/assuntos/noticias

#### [Instituto Butantan](https://butantan.gov.br/noticias/)

    newslinkrss -t 4 --follow -p '^https://butantan.gov.br/noticias/.+' --max-page-length 2048 --with-body --body-xpath '//h2/..' --date-from-csss 'small' --csss-date-regex '\s*Publicado em:\s*(\d+/\d+/\d+)\s*' --csss-date-fmt '%d/%m/%Y' -C 'style'  https://butantan.gov.br/noticias/

#### [Poder Judiciário de Santa Catarina](https://www.tjsc.jus.br/web/imprensa/noticias)

    newslinkrss -p 'https://www.tjsc.jus.br/web/imprensa/-/' --follow --with-body --body-csss '.journal-content-article' --date-from-csss '.tjsc-asset-publisher-list-asset-entry-date-time' --csss-date-fmt '%d %B %Y | %Hh%Mmin' -Q 'redirect' --title-regex '(.+) +- Imprensa' --locale 'pt_BR.UTF-8' https://www.tjsc.jus.br/web/imprensa/noticias

#### [MPF - Ministério Público Federal](https://www.mpf.mp.br/sala-de-imprensa/noticias)

    newslinkrss -t 4 --follow -p 'https://www.mpf.mp.br/.+/noticias-.+/.+' -B --body-csss 'div#content' https://www.mpf.mp.br/sala-de-imprensa/noticias

#### [MPF/SC - Santa Catarina](https://www.mpf.mp.br/sc/sala-de-imprensa)

    newslinkrss -t 4 --follow -p 'https://www.mpf.mp.br/.+/noticias-.+/.+' -B --body-csss 'div#content' https://www.mpf.mp.br/sc/sala-de-imprensa


## Cultura em geral

#### [Agenda de eventos da SCAR](https://scar.art.br/evento/)

    newslinkrss -p 'https://scar.art.br/eventos/.+' --follow --with-body --body-xpath '//main' https://scar.art.br/evento/

#### [Academia Brasileira de Letras](https://www.academia.org.br/noticias/)

    newslinkrss  --follow -p 'https://www.academia.org.br/noticias/.*'  --with-body --body-xpath '(//*[@id="main-content"])/..' --title-regex '^([^|]+)\s+|'  https://www.academia.org.br/noticias/

#### [Novas Palavras | Academia Brasileira de Letras](https://www.academia.org.br/nossa-lingua/sobre-novas-palavras)

    newslinkrss  --follow -p 'https://www.academia.org.br/nossa-lingua/nova-palavra/.+' --with-body --body-xpath '(//*[@id="main-content"])/..'  https://www.academia.org.br/nossa-lingua/sobre-novas-palavras

#### [Cultura - Estadão](https://www.estadao.com.br/cultura/)

    newslinkrss -p '^https://www.estadao.com.br/cultura/.+/.+' -t 4 --follow --with-body --body-csss ".authors-info authors-names, #content .content" -C ".ads-placeholder-label, #social-media-lower, .share-container" --date-from-csss 'time' --csss-date-regex '(\d+/\d+/\d+)' --csss-date-fmt '%d/%m/%Y' --title-regex '(.+) - Estadão' --author-from-csss 'div.authors-info .authors-names' --csss-author-regex 'Por\s+(.+)' https://www.estadao.com.br/cultura/

#### [Omelete](https://www.omelete.com.br/noticias)

    newslinkrss  -n 30 -f -B -p '^https://www.omelete.com.br/.+/.+' --max-page-length 256 --require-dates --body-csss 'div.article__body' https://www.omelete.com.br/noticias


## Outros

#### [AEROIN](https://aeroin.net/)

    newslinkrss -p 'https://aeroin.net/[^/]+(-[^/]+){3,}/?$' -fB --body-csss 'article .td-post-content' -Q 'amp' -C 'i-amphtml-sizer, style' -C .td-post-sharing --author-from-xpath '//meta[@name="author"]/@content' https://aeroin.net/

#### [Idec - Instituto Brasileiro de Defesa do Consumidor](https://idec.org.br/noticias)

    newslinkrss  -p '^https://idec.org.br/.+/.+' --follow --with-body --body-csss '#main-content header, div.datapublicacao, div.field-name-field-linha-fina, div#content div.field-name-body div.field-item' --date-from-csss 'div.field-name-changed-date div.field-item, div.field-name-post-date div.field-item' --csss-date-fmt '%d/%m/%Y' --require-dates --title-regex '^([^|]+)\s*|' https://idec.org.br/noticias https://idec.org.br/artigos

