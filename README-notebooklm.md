https://share.gemini.google/OrZmK0yFNhWG


Crie uma aula de no máximo 3 minutos abordando desenvolvimento de sistemas distribuídos e associando isso ao projeto segcar que encaminhei

Aqui está um roteiro estruturado de microaula de 3 minutos, cronometrado e direto ao ponto, conectando a teoria de Sistemas Distribuídos à implementação real do SegCar.   
analise_sistemas_segcar.pdf
+ 1

Roteiro de Aula: Engenharia de Sistemas Distribuídos na Prática com o SegCar
Duração estimada: 3 minutos (~390 a 430 palavras faladas em ritmo dinâmico)

Minuto 0:00 – 0:45 | Bloco 1: O Que é um Sistema Distribuído e a Borda IoT
"Um sistema distribuído é uma coleção de componentes computacionais autônomos, fisicamente separados, que se comunicam via rede e aparecem para o usuário final como um sistema único e coerente.

Na prática, isso não começa na nuvem, mas na borda (Edge Computing). No projeto SegCar, o nó computacional primário está dentro do veículo: um microcontrolador que realiza a ingestão e decodificação local de sentenças NMEA do sensor GPS NEO-6M. O microcontrolador filtra o ruído de satélite e calcula parâmetros cinemáticos antes de transmitir os dados pela rede móvel celular via HTTP POST. Isso economiza largura de banda e reduz a latência da telemetria, aplicando o conceito clássico de computação na borda."   
analise_sistemas_segcar.pdf
+ 4

Minuto 0:45 – 1:40 | Bloco 2: Comunicação Interprocessos, Web e Segurança Distribuída
"Quando os dados saem do veículo, entramos na camada de Comunicação entre Processos (IPC) e nos Sistemas Baseados na Web.   
analise_sistemas_segcar.pdf

Em vez de tecnologias legadas de chamada remota como RPC binário ou CORBA, o SegCar adota o padrão da indústria moderna: Web Services RESTful e stateless sobre HTTP/JSON.
Aqui, dois princípios distribuídos são fundamentais:   
analise_sistemas_segcar.pdf
+ 3

Segurança de borda a borda: A API valida a identidade da máquina transmissora com cabeçalhos criptográficos X-API-Key antes de processar as coordenadas.   
analise_sistemas_segcar.pdf
+ 1

Reatividade e Eventos: O backend avalia as coordenadas em tempo real com fórmulas geodésicas (Haversine) disparando eventos automáticos, como alertas de quebra de cerca virtual (geofence breach) e detecção de paradas."   
analise_sistemas_segcar.pdf
+ 1

Minuto 1:40 – 2:30 | Bloco 3: Tolerância a Falhas e Persistência Híbrida
"A premissa número um de qualquer sistema distribuído é: a rede e os nós vão falhar. O SegCar implementa resiliência em duas frentes:   
analise_sistemas_segcar.pdf
+ 2

No canal de rede: Trata a perda momentânea de sinal de satélite em túneis e oscilações do sinal celular 4G.   
analise_sistemas_segcar.pdf
+ 1

Na persistência (Tolerância a Falhas): Se a instância central do MySQL ficar indisponível, a API entra em contingência imediata, gravando os pacotes num arquivo sequencial append-only (gps_logs.jsonl). Assim que o serviço se restabelece, a rotina de sincronização drena esse log para a base relacional sem perda de telemetria."   
analise_sistemas_segcar.pdf
+ 2

Minuto 2:30 – 3:00 | Bloco 4: Conclusão e Próximos Passos de Arquitetura
"Para fechar: o SegCar prova como modelos cliente-servidor, computação em borda e contingência híbrida constroem um sistema distribuído funcional para mobilidade urbana.   
analise_sistemas_segcar.pdf
+ 1

Para escalar a plataforma para milhares de veículos simultâneos, a evolução natural envolve substituir o pooling direto por um broker de mensageria assíncrona (como RabbitMQ ou Kafka) e empacotar os serviços em contêineres Docker orquestrados por Kubernetes. Essa é a rota da teoria à engenharia de software no mundo real."   
analise_sistemas_segcar.pdf
+ 4
