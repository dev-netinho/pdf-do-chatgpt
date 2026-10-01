# Módulo de paçoca — protótipo CAD para validação

**Escopo:** um único módulo manual para paçoca rolha individualmente embalada. Não é um projeto pronto para imprimir nem um mecanismo comprovado. O retorno com filme flexível continua a exigir ensaio. Não inclui Halls, pé de moleque, eletrônica ou motor instalado.

## Arquivos e edição

- `montagem_completa.step`: montagem com componentes nomeados e três envelopes de teste. Os objetos `REF_*` são referências de produto e NÃO devem ser impressos.
- `vista_explodida.step`: peças afastadas para inspeção e montagem.
- `step/`: STEP individual por peça, estados do ciclo, cortes reais em Y=0 e um volume de referência para motor futuro.
- `stl/`: 16 componentes separados, já orientados para a impressão sugerida, posicionados sobre Z=0. Nenhum produto e nenhum motor em STL.
- `src/modelo.py` + `src/parametros.json`: fonte CAD **paramétrica em CadQuery**, em milímetros. O STEP contém sólidos B-rep editáveis, mas não preserva o histórico paramétrico. Para alterar dimensões de forma dependente, editar o JSON e regenerar a fonte.
- `verificacao/`: resultados dos testes de sólidos, malhas e interferência.
- `vistas/`: desenhos derivados dos mesmos sólidos, sem imagens generativas.

Regeração: Python com `cadquery==2.7.0`. Executar na pasta do pacote:

```bash
python src/modelo.py
python src/verificar.py
python src/complementos.py
```

As vistas usam adicionalmente Matplotlib/Pillow. `vistas.py` não é necessário para editar/exportar o CAD. Abrir o STEP em um CAD que importe montagem STEP, por exemplo FreeCAD. Não foi produzido um arquivo FCStd nativo ou Blender.

## Envelope provisório e orientação

Corpo cilíndrico nominal com seção 30 × 30 mm e comprimento axial 46 mm. Duas pontas cônicas representam a embalagem: 8 mm por lado, raio final nominal 6 mm; comprimento total 62 mm. A embalagem real pode divergir desse envelope.

A folga de teste é 1,5 mm **por lado** em X e em Z: corpo de colisão Ø33 × 46 mm. As pontas também recebem a margem. Não interpretar Ø33 como a medida final da paçoca. Comprimento do alojamento 68 mm, deixando 3 mm por extremidade. Medir amostras reais antes de reduzir folgas.

X é horizontal na vista frontal; Y é o eixo horizontal da roda e o comprimento da paçoca; Z é vertical. As paçocas são colocadas manualmente **deitadas**, com eixos paralelos a Y, em coluna vertical. A frente mostra a seção curta; o lado mostra o comprimento e as pontas. Não existe auto-orientação.

## Dimensões principais (mm)

| Parâmetro | Valor inicial |
|---|---:|
| Corpo nominal Largura × Profundidade × Comprimento | 30 × 30 × 46 |
| Pontas por lado | 8 |
| Folga lateral / vertical por lado | 1,5 / 1,5 |
| Folga axial por ponta | 3 |
| Roda: diâmetro × largura | 130 × 72 |
| Centro do berço: distância radial do eixo | 48,5 |
| Berço central: raio de corte | 18,5 |
| Alívio das pontas: raio de corte | 17,5 |
| Boca do berço central | 37 |
| Profundidade radial do berço | 35 |
| Canal interno do cartucho: X × Y | 38 × 70 |
| Cartucho com guias externas: X × Y × Z | 62 × 80 × 114 |
| Comporta: espessura da lâmina / curso nominal | 2,4 / 72 |
| Abertura central da comporta em U | 25 |
| Altura do eixo / base da lâmina | 130 / 196,2 |
| Folga radial roda–aro | 0,8 |
| Eixo D nominal / furo de apoio circular | Ø10 / Ø10,6 |
| Envelope geral em operação (com comporta aberta) | aprox. 259 × 218 × 309,2 |
| Espaço futuro para motor, somente referência | 80 × 55 × 80 |

O corpo Ø33 não pode passar pelo vão central de 25 mm da comporta. A roda contém um só berço: boca de 37 mm e profundidade de 35 mm não acomodam duas unidades Ø33 completas. Isso não elimina a entrada parcial da próxima embalagem, nem substitui ensaio.

## Solução mecânica

A comporta em U tem duas lâminas laterais que apoiam o corpo arredondado. Não se apoia exclusivamente nas pontas do filme. Em 180°, as lâminas fecham sob as laterais da unidade que está apoiada no topo sólido da roda: há cerca de 2,13 mm de folga nominal entre o envelope e a face superior dos garfos na linha de apoio. A parte central fica livre, evitando a interferência de uma placa cheia com a unidade apoiada sobre a roda.

O rasgo longitudinal da comporta e um pino M2 no cartucho limitam o curso e mantêm a lâmina presa ao cartucho. Para desmontar a comporta, esvaziar o cartucho e retirar esse pino. As guias do dock recebem duas abas do cartucho, apoiadas em batentes inferiores. O pino lateral retém o cartucho na altura de operação. **Não há intertravamento entre esse pino e a comporta:** a retirada exige cumprir a ordem indicada abaixo.

O berço da roda tem fundo arredondado, duas profundidades axiais e paredes nas extremidades. As pontas recebem alívio próprio; não se trata de uma caixa retangular grande. Guias do cartucho e o berço restringem desalinhamento. A embalagem cilíndrica ainda pode girar dentro das folgas; verificar experimentalmente.

O aro fixo contém a unidade transportada ao longo do arco lateral. A superfície sólida da própria roda sustenta a coluna entre cargas. O aro **não** é uma comporta horizontal oculta atravessando a entrada. Sua abertura superior é maior para acomodar o cartucho/dock; quem limita a alimentação são o canal interno de 38 mm e o único berço de 37 mm.

O eixo D passa por dois apoios reais: tampa frontal de 4 mm e placa traseira do dock de 6 mm, com furos Ø10,6. Colares limitam deslocamento axial e a manivela tem encaixe D. Um pino da manivela percorre o rasgo semicircular do batente, com extremos nominais em 0°/180°. A folga do rasgo deixa aproximadamente ±0,54° de jogo nos extremos, a confirmar com a impressão.

## Lista de peças

| Código | Peça | Quantidade | Montagem / função |
|---|---|---:|---|
| 01 | Cartucho | 1 | Aberto em cima, duas abas de encaixe e guias para comporta |
| 02 | Comporta em U | 1 | Desliza ao longo de +Y para abrir; garfos retêm corpo |
| 03 | Dock | 1 | Base, apoio traseiro, trilhos e apoio dos batentes |
| 04 | Roda | 1 | Uma cavidade com berço e alívio das pontas |
| 05 | Aro fixo | 1 | Dois arcos unidos por travessa traseira; retenção lateral |
| 06 | Eixo D | 1 | Conecta roda e manivela |
| 07 | Manivela | 1 | Braço, pino do batente e haste do punho |
| 08 | Calha | 1 | Rampa com laterais e quatro pés aparafusados |
| 09 | Bandeja | 1 | Entrada rebaixada; apoiada sobre a bancada |
| 10 | Tampa de inspeção | 1 | Removível por quatro parafusos; também apoio frontal |
| 11 / 12 | Colares frontal / traseiro | 1 de cada | Ajustar junto aos apoios, sem apertar o giro |
| 13 | Punho | 1 | Gira na haste; reter por arruela e parafuso M3 |
| 14 | Placa de batentes | 1 | Rasgo semicircular para pino da manivela |
| 15 | Pino lateral do cartucho | 1 | Retém cartucho no dock; peça provisória sem trava contra retirada acidental |
| 16 | Retenção M2 da comporta | 1 | Representação simplificada: preferir parafuso/pino M2 metálico |

Ferragens não detalhadas com roscas: oito M3 para aro/tampa (quatro frente, quatro traseira); dois M3 para placa de batentes; quatro M3 com porcas nos alojamentos hexagonais da base para fixar a calha; três M3 de pressão para colares/manivela; um M3 com arruela externa Ø16 mm para reter o punho; um M2 para reter a comporta. Confirmar comprimentos e executar roscas/inserções após teste do material. Não imprimir ferragens pequenas como substituto de ferragem estrutural; o STL 16 é somente referência/fallback dimensional.

## Montagem

1. Limpar suportes e rebarbas dos rasgos. Confirmar Ø10,6 nos apoios, o encaixe D, o rasgo da comporta e o alojamento do berço com gabaritos reais.
2. Aparafusar o aro ao apoio traseiro do dock pelos quatro furos alinhados. Manter a travessa atrás da roda e a saída aberta embaixo.
3. Posicionar a roda entre os arcos, passar o eixo D e montar a tampa frontal pelos quatro furos. A tampa deve sair axialmente para inspeção após retirar manivela/colares.
4. Ajustar os dois colares junto aos apoios; apertar parafusos de pressão. A roda deve girar livremente, com pequena folga axial, sem tocar no aro.
5. Aparafusar a placa de batentes ao suporte frontal. Introduzir o pino da manivela no rasgo e fixar seu encaixe D. Montar o punho e reter com M3/arruela; não apertar o punho contra a haste.
6. Aparafusar os quatro pés da calha à base. Os alojamentos da rampa deixam as cabeças rebaixadas; as porcas entram pelos recessos hexagonais sob a base. Confirmar comprimentos com a peça física.
7. Colocar a bandeja na saída; entrada baixa alinhada com a rampa. A bandeja não é aparafusada ao dock nesta revisão.
8. Introduzir a comporta no rasgo inferior do cartucho e montar o M2 através do rasgo longo. Checar batentes de abertura/fechamento e retenção antes de carregar.
9. Com a comporta fechada, carregar pelo topo três unidades deitadas. Baixar o cartucho nos trilhos até o batente e inserir o pino lateral. Começar a operação em 0°.

## Operação e retirada

0. Fora do dock: garfos fechados sustentam o corpo; três unidades alinhadas; topo aberto para reposição.
1. Encaixar e inserir pino lateral mantendo a comporta fechada.
2. Com a roda em 0°, puxar o manípulo da comporta até o batente aberto. A coluna desce; unidade 1 ocupa o berço; unidade 2 fica sobre ela.
3. Girar manualmente até 180°. O topo sólido passa a apoiar a unidade 2; aro contém a unidade 1 durante o transporte; janela inferior libera a unidade 1 para a calha.
4. Retornar vazio até 0°. A próxima unidade pode começar a descer antes do batente. Não forçar se houver resistência: esse contato com a borda é um risco ainda não validado.
5. Em 0°, a unidade 2 desce no berço e a unidade 3 desce para o apoio acima; a fonte inclui uma posição intermediária de queda.
6. Repetir o giro até 180° para entregar a unidade 2. Não tocar no estoque entre as vendas.

**Para retirar com estoque:** parar em 180° com a cavidade vazia; empurrar a comporta até o batente fechado; conferir retenção; retirar o pino lateral; levantar o cartucho verticalmente. Nos primeiros ~2,13 mm a coluna permanece apoiada na roda; depois a comporta assume o peso. Não retirar com a comporta aberta. A posição de remoção em 0° com uma unidade alojada não é autorizada por esta solução.

## Impressão: orientação e limites

Os STLs já estão nas orientações abaixo; o STEP mantém coordenadas de montagem. Não reposicionar o STL usando coordenadas do STEP sem considerar essa rotação.

- Cartucho: em pé, topo aberto para cima; suporte localizado nos rasgos da comporta e nas abas.
- Comporta: plana; remover qualquer rebarba no vão/rasgo longo; não arredondar ao acaso os apoios de retenção.
- Roda: face axial sobre a mesa, eixo vertical; suporte localizado nos degraus de alívio das pontas, conforme o fatiamento.
- Aro: face axial sobre a mesa; travessa traseira para cima. Apoios localizados sob travessa/conectores.
- Eixo: vertical; confirmar ajuste D e rigidez. Considerar eixo metálico com face D após validar encaixe.
- Manivela: face axial na mesa; pino do batente e haste do punho para cima, com suporte localizado.
- Tampa/colares/punho/batentes: face axial sobre a mesa.
- Dock, calha, bandeja: base na mesa; dock exige suporte na ponte de saída e nas ligações superiores. Dock: 174 × 115 × 228 mm; verificar volume útil da impressora.
- Pino lateral: cabeça sobre a mesa; confirmar retenção. Pino M2: usar ferragem real, não considerar o STL uma peça estrutural aprovada.

Não foram fixados material, espessura de camada, preenchimento ou resistência admissível: dependem da impressora/material. Folgas paramétricas são de projeto, não compensações finais de FDM. Testar primeiro eixo/apoio e comporta/cartucho com pequenas amostras.

## Verificação realizada e condições pendentes

OpenCascade confirmou 16 sólidos válidos, um por componente. Os 16 STLs passaram em: arestas abertas = 0; arestas/vertices não manifold = 0; orientação inconsistente = 0; triângulos degenerados = 0; uma componente conexa; volume assinado positivo. STL não codifica unidade: importar explicitamente em **mm**. STEP exportado em mm.

Interseções B-rep foram verificadas em sete poses. Limite de relatório: 0,05 mm³; máximos encontrados zero nas poses e nas varreduras: comporta em 180° (16 posições), transporte 0–180° (passo 10°), descida alinhada em 0° (18 posições), retirada com comporta fechada (16 alturas) e queda vertical da saída (20 posições). São amostras geométricas, não prova de movimento contínuo ou dinâmica.

**Ainda não validado:** retorno com recarga antecipada; pinçamento de filme entre borda/guia; rolamento dentro da folga; comportamento das pontas reais; resistência da comporta/pinos; atrito nos apoios impressos; retenção do pino lateral sem intertravamento; trajetória real sobre a calha. Bordas da boca têm raio de 0,6 mm, que reduz uma aresta viva, mas não garante ausência de engate. O berço é côncavo: a queda parcial pode criar um ponto de cunhamento mesmo sem colisão nas poses estáticas. Os objetos REF mostram ocupação/espaço livre, não contatos dinâmicos calculados. Pela folga do berço, o corpo nominal Ø30 pode assentar 3,5 mm abaixo do centro geométrico; o envelope Ø33, 2 mm. No início do giro, isso pode exigir elevar a coluna até cerca de 5 mm (nominal) ou 2 mm (envelope). Esse contato também precisa de ensaio e não está validado pela varredura com estoque já apoiado no topo sólido.

Ensaio inicial: medir pelo menos três embalagens reais; operar lentamente com uma unidade, depois com três; registrar duas entregas consecutivas e o retorno; interromper se houver resistência. Somente considerar a geometria aprovada depois desse ensaio. Não avançar aos outros produtos nesta revisão.
