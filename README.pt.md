# Mecanismo de Anticítera: uma reconstrução 3D funcional e verificada

[English](README.md) · [Français](README.fr.md) · [Español](README.es.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · **Português** · [Ελληνικά](README.el.md) · [中文](README.zh.md) · [日本語](README.ja.md)

![O mecanismo reconstruído, vista frontal a três quartos](docs/images/front34.jpg)

O Mecanismo de Anticítera é uma calculadora astronómica de bronze, acionada à mão por uma manivela, construída na Grécia no século II ou I a.C. e recuperada de um naufrágio em 1901. É a mais antiga máquina complexa de engrenagens que se conhece. Este repositório contém uma reconstrução 3D completa do mecanismo em **Blender 5.2**:

- todas as **69 engrenagens** têm o seu número real de dentes;
- os dentes têm perfil evolvente conjugado, de modo que cada par engrena e funciona realmente;
- cada trem de engrenagens foi **verificado em frações exatas** em relação ao ciclo astronómico que representa;
- as peças foram **verificadas quanto a colisões** em toda a amplitude de movimento.

Todo o conjunto foi produzido numa só passagem pelo Claude Opus 5.5 a partir de um único prompt mestre autossuficiente ([`PROMPT_OPUS.md`](PROMPT_OPUS.md)) e depois verificado de forma independente.

## Destaques

- **69 engrenagens**, classificadas segundo o grau de certeza:
  - 30 **conservadas**, fisicamente presentes nos fragmentos (tomografias de raios X);
  - 7 **reconstruídas**, a partir de indícios sólidos;
  - 32 **hipotéticas**, segundo o modelo de Freeth et al. 2021.

  Cada categoria tem a sua própria coleção no Blender, para que cada grupo possa ser ocultado ou mostrado.
- **Matemática exata.** 1 volta da roda principal b1 corresponde a 1 ano. O mecanismo tem exatamente **um grau de liberdade** (a manivela), e os 22 valores-alvo coincidem exatamente como frações (exemplos abaixo).

  | Saída | Velocidade exata (voltas/ano) | Ciclo |
  |---|---|---|
  | Lua (média) | 254/19 | 254 meses siderais em 19 anos |
  | Mostrador de Méton | −5/19 | 5 voltas = 19 anos = 235 meses lunares |
  | Mostrador do Saros | −940/4237 | 4 voltas = 223 meses lunares |
  | Nodos lunares (Ponteiro do Dragão) | −5/93 | 18.6 anos, em sentido inverso |
  | Vénus | 289/462 em relação a b1 | 289 períodos sinódicos em 462 anos |
- **Funciona mecanicamente.**
  - As distâncias entre eixos são exatas a 10⁻⁶ mm, e todas as razões de contacto são ≥ 1.2.
  - Há **0 interpenetrações** em milhares de amostras 3D (BVH): cada engrenamento ao longo de um passo de dente, cada ciclo de pino e ranhura, e 168 pares de peças em 240 posições da manivela.
- **A Lua acelera e desacelera com engrenagens redondas**, e não ovais. Um sistema de pino e ranhura montado no prato giratório e3 reproduz a anomalia lunar de Hiparco (±6.58°).
- **Os planetas recuam no momento certo.** Marte, Júpiter e Saturno entram em movimento retrógrado na oposição (180° ± 0.03°), e Mercúrio e Vénus permanecem dentro das suas elongações máximas.
- **Uma única manivela aciona tudo.** Todo o movimento provém de `AM_Controller["crank"]`, em anos, através de drivers de expressão simples, de modo que a animação funciona sem ativar scripts Python.
- **Visualização legível.** Cada um dos sete "planetas" da Antiguidade tem a sua cor e uma etiqueta que o acompanha (Sol, Lua, Mercúrio, Vénus, Marte, Júpiter, Saturno), além de uma legenda.
- **Iluminação de museu.** A cena tem um fundo em ciclorama escuro e softboxes de luz quente, e é renderizada com a transformação de cor AgX. Esta configuração foi escolhida entre três propostas renderizadas lado a lado.
- **Vista explodida.** Mova `AM_Controller["explode"]` de 0 para 1 e cada peça desliza ao longo do eixo de empilhamento.
- **Impressão 3D.** Um STL por peça e um 3MF completo, em três perfis: resina ×1, resina ×1.5 e FDM ×2.

| Mostrador frontal | Mostradores traseiros |
|---|---|
| ![Mostrador frontal com os planetas coloridos e identificados](docs/images/front.jpg) | ![Espirais de Méton e do Saros](docs/images/back.jpg) |

| Vista explodida | O interior, aberto |
|---|---|
| ![Imagem fixa da vista explodida](docs/images/exploded.jpg) | ![Imagem do vídeo em vista explodida](docs/images/exploded_video_frame.jpg) |

## Vídeos

- [`antikythera.mp4`](build/out/renders/antikythera.mp4): 20 s. A manivela avança 4 anos; os planetas, a Lua e os mostradores traseiros estão todos em movimento.
- [`antikythera_eclate.mp4`](build/out/renders/antikythera_eclate.mp4): 15 s em vista explodida. O mecanismo abre, camada a camada, enquanto as engrenagens continuam a girar, e depois volta a fechar.

Os planetas que às vezes andam **para trás** nos vídeos não são um erro. Trata-se do **movimento retrógrado** visto da Terra, e é precisamente isso que o mecanismo foi construído para mostrar. O Ponteiro do Dragão (os nodos lunares) gira sempre para trás.

## Início rápido

1. Instale o **Blender 5.2** ou uma versão posterior.
2. Abra [`build/out/am.blend`](build/out/am.blend) e pressione **Espaço** para reproduzir a animação.
3. Selecione `AM_Controller` e altere as suas propriedades personalizadas:
   - `crank`: anos; 1 corresponde a uma volta de b1;
   - `explode`: de 0 a 1;
   - `patina`: 0 é bronze novo, 1 é pátina de museu.
4. Use o Outliner para ocultar coleções:
   - `AM_CASE` e `AM_DIALS` para ver as engrenagens;
   - `AM_HYPOTHETICAL` para manter apenas o que está atestado;
   - `AM_LABELS` para retirar as etiquetas;
   - `AM_STAGE` para retirar o cenário de iluminação.
5. Clique em qualquer peça para ler as suas propriedades personalizadas: `status`, `role`, `teeth`, `module` e `sources`.

### Voltar a executar a verificação

Use o Python incluído no Blender. Os caminhos abaixo são para macOS; adapte-os para outros sistemas.

```sh
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
BL=/Applications/Blender.app/Contents/MacOS/Blender

$PY tools/validate_spec.py          # exact linear solve (1 DOF, 22 targets), centre distances, collision screening
$PY tools/check_kinematics.py       # pin-and-slot laws, followers, elongations, retrogrades, solar apogee
cd build && $PY -m unittest discover -s tests && $PY -m am.verify --stage all && cd ..
$BL -b build/out/am.blend --python-exit-code 1 -P tools/crosscheck_blend.py   # Blender rotations vs an independent solver
```

[`build/README.md`](build/README.md) lista cada etapa de construção, verificação, exportação e renderização, com um comando por etapa.

### Reconstruir tudo a partir do prompt mestre

Numa pasta **vazia**, com o [Claude Code](https://claude.com/claude-code):

```sh
claude -p --model 'claude-opus-5-5[1m]' --effort xhigh --permission-mode acceptEdits \
  --allowedTools Bash Read Write Edit Glob Grep < PROMPT_OPUS.md
```

- [`prompts/PROMPT_OPUS_v1_validated.md`](prompts/PROMPT_OPUS_v1_validated.md) é a versão exata que produziu esta construção numa só passagem (89 min).
- [`PROMPT_OPUS.md`](PROMPT_OPUS.md) é a v1.2. Acrescenta as cores e as etiquetas dos planetas, a encenação de museu, o deslizador da vista explodida e o vídeo em vista explodida. Todos estes elementos foram acrescentados posteriormente a esta construção com os scripts de `tools/`, e a v1.2 ainda não foi executada de novo a partir do zero.

## Como foi feito

1. **Pesquisa.** Agentes em paralelo leram as fontes primárias: Freeth et al. 2006, 2008 e 2021 (com a Supplementary Information), Price 1974, Budiselic et al. 2020, Woan & Bayley 2024, Anastasiou et al. 2014, entre outras. Os resultados foram conciliados num único conjunto de dados e depois verificados por um agente cético.
2. **Especificação.** [`spec/antikythera.json`](spec/antikythera.json) é a única fonte de verdade. Indica o número de dentes, o módulo, a posição do eixo, o intervalo em z e o furo de cada engrenagem, bem como cada eixo físico, pino fixo, cubo, pino, mostrador e material. É gerado por `tools/make_spec.py`, que corrige 22 impossibilidades geométricas nos dados publicados (por exemplo, b2 não pode engrenar simultaneamente com c1 e com l1 às distâncias publicadas). Cada distância entre eixos é resolvida de forma exata.
3. **Verificações independentes.** `tools/validate_spec.py` e `tools/check_kinematics.py` não têm nenhum código em comum com o gerador, e testes de mutação confirmam que identificam os erros introduzidos de propósito.
4. **Dentes de coroa por envolvente.** `tools/crown_envelope.py` calcula os dentes de coroa de a1 e q1 como a região que os dentes conjugados nunca varrem. Em seguida, `tools/test_crowns_blender.py` confirma o resultado com BVH no Blender.
5. **Revisões adversariais.** Duas séries de revisores independentes cobriram os dados, a API do Blender (testada em execução real), a executabilidade e a geometria, e encontraram 5 falhas bloqueantes e cerca de 60 outros problemas. Todos foram corrigidos.
6. **Construção numa só passagem** por uma sessão nova do Opus 5.5, apenas a partir do prompt: 131 turnos, cerca de 5000 linhas de código e todos os critérios de aceitação cumpridos.
7. **Verificação independente** do resultado: testes, verificações exatas, a verificação BVH completa e uma comparação cruzada de cada corpo de `am.blend` com o solver independente (7·10⁻⁷ rad).

## Estrutura do repositório

```
PROMPT_OPUS.md            master prompt (v1.2), self-contained; embeds the full JSON spec + SHA-256
prompts/                  the prompt version validated by the one-pass build (v1)
spec/antikythera.json     single source of truth (gears, axes, shafts, trains, dials, staging, video)
research/                 raw multi-agent research results with source URLs
tools/                    spec generator, validators, crown envelopes, annotation/staging/explode/render scripts
build/                    the project generated by the one-pass build (am/, blender_scripts/, tests/, README)
build/out/                am.blend, verification report (report.md/html), checks, print files, renders, videos
docs/                     dossier (HTML) and images
```

## Limitações assumidas

- Os trens planetários, os nodos lunares e o Sol verdadeiro seguem o modelo **hipotético** de Freeth et al. 2021. Uma animação que funciona não prova como o original foi construído.
- Algumas grandezas não estão publicadas. Para essas, a especificação usa valores predefinidos documentados, listados em `spec/antikythera.json` → `unresolved_defaults`:
  - os ângulos dos eixos na placa traseira;
  - os raios dos anéis do cosmos;
  - as fases iniciais (a época não está calibrada).
- Os dentes são evolventes conjugados (cremalheira de 30°, que corresponde ao dente antigo em triângulo equilátero), e não os triângulos limados à mão do original.
- As cores dos planetas servem apenas para facilitar a leitura; não são históricas.

## Fontes principais

- T. Freeth et al., "A Model of the Cosmos in the ancient Greek Antikythera Mechanism", *Scientific Reports* 11, 5821 (2021), com a sua Supplementary Information.
- T. Freeth et al., "Decoding the ancient Greek astronomical calculator known as the Antikythera Mechanism", *Nature* 444, 587 (2006).
- T. Freeth, A. Jones, J. Steele, Y. Bitsakis, "Calendars with Olympiad display and eclipse prediction on the Antikythera Mechanism", *Nature* 454, 614 (2008).
- T. Freeth & A. Jones, "The Cosmos in the Antikythera Mechanism", ISAW Papers 4 (2012).
- D. de Solla Price, *Gears from the Greeks* (1974).
- C. Budiselic et al. (2020); G. Woan & J. Bayley (2024): número de furos do anel do calendário.
- M. Anastasiou et al. (2014): as espirais dos mostradores traseiros.

A lista completa, com os URLs, está em `spec/antikythera.json` → `sources`.

## Licença

- **Código**: MIT ([`LICENSE`](LICENSE)).
- **Renderizações, vídeos, modelo 3D, peças para impressão e textos**: CC BY 4.0 ([`LICENSE-MEDIA.md`](LICENSE-MEDIA.md)).
- **Dados científicos**: por favor, cite os trabalhos acima.

---

Construído com o [Claude Code](https://claude.com/claude-code) (Claude Opus 5 / 5.5) para taciclei.
