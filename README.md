# Biomimesis × Codeblocks

**Buinho FabLab · Messejana, Alentejo · [buinho.pt](https://buinho.pt)**

Ferramenta educativa open-source que analisa fotografias de padrões naturais e gera orientações pedagógicas para reproduzir esses padrões em Tinkercad Codeblocks, seguindo a metodologia biomimética.

## Como funciona

1. O professor/aluno carrega uma foto de um padrão natural (concha, folha, favo de mel, etc.)
2. A app analisa o padrão com visão computacional (Claude API)
3. Devolve uma sequência pedagógica de 5 momentos biomimético:
   - **Observar** — identificar o padrão e as suas características
   - **Abstrair** — extrair as variáveis matemáticas
   - **Emular** — traduzir para blocos Codeblocks
   - **Prototipar** — passos concretos no Tinkercad
   - **Transferir** — outros contextos onde este padrão aparece

## Deploy local

```bash
git clone https://github.com/Buinho-Creative-Hub/biomimesis-codeblocks
cd biomimesis-codeblocks
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python app.py
```

## Deploy Render

1. Fork este repositório
2. Criar Web Service no [Render](https://render.com)
3. Adicionar variável de ambiente: `ANTHROPIC_API_KEY`
4. Deploy automático a cada push

## Licença

CC-BY-SA 4.0 · Buinho Associação / Zingarelho Lda

---

# Biomimesis × Codeblocks (EN)

Open-source educational tool that analyses photographs of natural patterns and generates pedagogical guidance to reproduce those patterns in Tinkercad Codeblocks, following the biomimetic methodology.

Developed by [Buinho FabLab](https://buinho.pt), a rural FabLab and Artist-in-Residence programme in Messejana, Alentejo, Portugal.

Licensed CC-BY-SA 4.0 — free to adapt and share with attribution.
