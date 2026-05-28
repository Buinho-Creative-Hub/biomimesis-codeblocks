import os
import json
import base64
import anthropic
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """És especialista em biomimética e educação maker para crianças do 1º ciclo.
Analisa a imagem de um padrão natural e gera orientações pedagógicas para reproduzir no Tinkercad Codeblocks.

Responde APENAS com JSON válido, sem markdown nem texto extra. Formato obrigatório:
{
  "padrao": "nome curto do padrão",
  "momento1": {
    "texto": "Descrição simples do padrão para crianças, 2-3 frases.",
    "caracteristicas": ["característica 1", "característica 2", "característica 3"]
  },
  "momento2": {
    "texto": "Explica as variáveis matemáticas em linguagem simples.",
    "variaveis": [
      {"nome": "Ângulo de rotação", "valor_tipico": "137", "unidade": "graus", "explicacao": "porquê este valor existe na natureza"},
      {"nome": "Factor de crescimento", "valor_tipico": "1.15", "unidade": "x", "explicacao": "como o padrão cresce a cada repetição"},
      {"nome": "Número de elementos", "valor_tipico": "60", "unidade": "unidades", "explicacao": "quantas vezes o padrão se repete"}
    ]
  },
  "momento3": {
    "texto": "Instrução pedagógica para construir no Tinkercad.",
    "blocos": [
      {"type": "set", "keyword": "Set", "variable": "Ângulo", "value": "137"},
      {"type": "set", "keyword": "Set", "variable": "Raio Base", "value": "4"},
      {"type": "set", "keyword": "Set", "variable": "Elementos", "value": "60"},
      {"type": "repeat", "keyword": "Repeat", "variable": "Elementos", "value": null},
      {"type": "fn", "keyword": "Calcular Raio", "variable": "Raio Base × i", "value": null},
      {"type": "move", "keyword": "Move", "variable": "x y z", "value": null}
    ]
  },
  "momento4": {
    "passos": ["passo 1", "passo 2", "passo 3", "passo 4"]
  },
  "momento5": {
    "outros_exemplos": ["exemplo na natureza 1", "exemplo na natureza 2"],
    "aplicacoes_humanas": ["aplicação humana 1", "aplicação humana 2"],
    "pergunta_reflexao": "Pergunta aberta para o aluno pensar."
  }
}"""

HTML = """<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Buinho · Biomimesis × Codeblocks</title>
<link href="https://fonts.googleapis.com/css2?family=Asap:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Asap',sans-serif;background:#FAF0E1;min-height:100vh}
.header{padding:18px 24px 12px;display:flex;align-items:flex-start;justify-content:space-between;border-bottom:2px solid #2038A6;background:#FAF0E1}
.brand{font-weight:700;font-size:22px;color:#2038A6;letter-spacing:-0.5px}
.brand-sub{font-size:12px;color:#FA6415;font-weight:500;margin-top:2px}
.main{display:grid;grid-template-columns:1fr 1fr;min-height:calc(100vh - 74px)}
@media(max-width:640px){.main{grid-template-columns:1fr}}
.panel-l{padding:20px 20px 20px 24px;border-right:1.5px solid #2038A640;display:flex;flex-direction:column;gap:16px}
.panel-r{padding:20px 36px 20px 20px;display:flex;flex-direction:column;gap:12px;position:relative}
.label{font-size:10px;font-weight:700;letter-spacing:1.5px;color:#2038A6;text-transform:uppercase;margin-bottom:4px}
.upload-btn{background:#FAF0E1;border:2px dashed #2038A680;border-radius:8px;padding:18px 16px;text-align:center;cursor:pointer;width:100%;font-family:'Asap',sans-serif;transition:.2s}
.upload-btn:hover{border-color:#2038A6;background:#F0E4CC}
.upload-btn svg{display:block;margin:0 auto 8px}
.upload-btn .ut{font-size:13px;color:#2038A6;font-weight:600}
.upload-btn .uh{font-size:11px;color:#2038A680;margin-top:3px}
#prevImg{display:none;width:100%;max-height:160px;object-fit:cover;border-radius:6px;border:1.5px solid #2038A640}
select{width:100%;font-family:'Asap',sans-serif;font-size:13px;padding:8px 10px;border:1.5px solid #2038A640;border-radius:6px;background:#FAF0E1;color:#2038A6;font-weight:600}
.btn-go{background:#2038A6;color:#FAF0E1;border:none;border-radius:6px;padding:12px 16px;font-family:'Asap',sans-serif;font-size:14px;font-weight:700;cursor:pointer;width:100%;display:flex;align-items:center;justify-content:center;gap:8px;transition:.15s}
.btn-go:hover{background:#162d85}
.btn-go:disabled{background:#2038A640;cursor:not-allowed}
.mnav{display:none;flex-wrap:wrap;gap:4px;margin-bottom:4px}
.pill{background:#FAF0E1;border:1.5px solid #2038A640;border-radius:20px;padding:4px 10px;font-size:10px;font-weight:700;color:#2038A680;cursor:pointer;transition:.15s}
.pill.active{background:#2038A6;color:#FAF0E1;border-color:#2038A6}
.rarea{flex:1;overflow-y:auto;max-height:calc(100vh - 200px)}
.mcard{border:1.5px solid #2038A640;border-radius:8px;padding:14px 16px;display:none}
.mcard.on{display:block}
.mh{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.mn{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0}
.m1 .mn{background:#2038A6;color:#FAF0E1}
.m2 .mn{background:#FA6415;color:#FAF0E1}
.m3 .mn{background:#F23A2F;color:#FAF0E1}
.m4 .mn{background:#FCB515;color:#2038A6}
.m5 .mn{background:#2038A6;color:#FAF0E1}
.mt{font-size:13px;font-weight:700;color:#2038A6}
.mb{font-size:13px;color:#2038A6cc;line-height:1.6}
.vtag{display:inline-block;background:#2038A620;color:#2038A6;border-radius:4px;padding:1px 7px;font-size:11px;font-weight:700;margin:1px 2px;font-family:monospace}
.cbv{background:#2038A610;border-radius:6px;padding:10px 12px;margin-top:8px;border-left:3px solid #2038A6}
.cbl{font-size:11px;color:#2038A6;line-height:1.9;display:flex;align-items:center;gap:5px;flex-wrap:wrap}
.cbb{display:inline-block;border-radius:3px;padding:1px 7px;font-size:10px;font-weight:700}
.cs{background:#5C9BE6;color:#fff}.cv{background:#5C9BE6bb;color:#fff}.cval{background:#fff;color:#2038A6;border:1px solid #2038A640}.cr{background:#FA6415;color:#fff}.cf{background:#4CAF50;color:#fff}.cm{background:#9C6FD6;color:#fff}
.lds{display:inline-flex;gap:4px;align-items:center}
.lds span{width:6px;height:6px;border-radius:50%;background:#FAF0E1;animation:db 1.2s infinite}
.lds span:nth-child(2){animation-delay:.2s}.lds span:nth-child(3){animation-delay:.4s}
@keyframes db{0%,80%,100%{transform:scale(.7);opacity:.5}40%{transform:scale(1);opacity:1}}
.empty{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:40px 20px;text-align:center}
.empty p{font-size:13px;color:#2038A680;font-weight:500;max-width:200px;line-height:1.5}
.edu{position:absolute;right:8px;top:0;bottom:0;width:18px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;padding-bottom:20px;gap:3px;pointer-events:none}
.edu span{font-size:10px;font-weight:500;color:#FA6415;line-height:1}
.err{background:#F23A2F15;border:1.5px solid #F23A2F40;border-radius:6px;padding:10px 12px;font-size:12px;color:#F23A2F;font-weight:500;display:none}
.chip{background:#2038A615;color:#2038A6;font-size:11px;font-weight:600;padding:3px 9px;border-radius:12px;display:inline-block;margin:2px}
.chip-o{background:#FA641515;color:#FA6415;font-size:11px;font-weight:600;padding:3px 9px;border-radius:12px;display:inline-block;margin:2px}
.vcard{margin-bottom:8px;padding:8px 10px;background:#2038A608;border-radius:6px;border-left:3px solid #FA6415}
</style>
</head>
<body>
<div class="header">
  <div>
    <div class="brand">Buinho</div>
    <div class="brand-sub">biomimesis × codeblocks</div>
  </div>
  <svg width="36" height="22" viewBox="0 0 36 22" aria-hidden="true">
    <rect x="0" y="10" width="14" height="12" fill="#FCB515" rx="1" transform="rotate(3 7 16)"/>
    <rect x="11" y="6" width="12" height="10" fill="#FA6415" rx="1" transform="rotate(-2 17 11)"/>
    <rect x="22" y="2" width="13" height="9" fill="#2038A6" rx="1" transform="rotate(4 28 6)"/>
  </svg>
</div>

<div class="main">
  <div class="panel-l">
    <div>
      <div class="label">padrão natural</div>
      <button class="upload-btn" id="btnUp" onclick="document.getElementById('fi').click()">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <rect x="3" y="7" width="26" height="18" rx="3" fill="#2038A615" stroke="#2038A6" stroke-width="1.5"/>
          <circle cx="12" cy="14" r="3" fill="#2038A630"/>
          <path d="M3 21 l7-7 6 6 4-4 8 5" stroke="#2038A6" stroke-width="1.5" fill="none" stroke-linecap="round"/>
        </svg>
        <div class="ut">clica aqui para carregar foto</div>
        <div class="uh">folha · concha · favo · espiral · casca</div>
      </button>
      <input type="file" id="fi" accept="image/*" style="display:none">
      <img id="prevImg" alt="Padrão carregado">
    </div>
    <div>
      <div class="label">nível do aluno</div>
      <select id="lvl">
        <option value="basic">iniciante — 1º e 2º ano</option>
        <option value="intermediate" selected>intermédio — 3º e 4º ano</option>
        <option value="advanced">avançado — com experiência Codeblocks</option>
      </select>
    </div>
    <div id="errMsg" class="err"></div>
    <button class="btn-go" id="btnGo" disabled>
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/><path d="M5 8l2 2 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
      analisar padrão
    </button>
  </div>

  <div class="panel-r">
    <div class="edu" aria-hidden="true">
      <span>o</span><span>v</span><span>i</span><span>t</span><span>a</span><span>c</span><span>u</span><span>d</span><span>e</span>
    </div>
    <div class="mnav" id="mnav">
      <span class="pill active" data-m="1">1 · observar</span>
      <span class="pill" data-m="2">2 · abstrair</span>
      <span class="pill" data-m="3">3 · emular</span>
      <span class="pill" data-m="4">4 · prototipar</span>
      <span class="pill" data-m="5">5 · transferir</span>
    </div>
    <div class="rarea" id="rarea">
      <div class="empty" id="empt">
        <svg width="52" height="56" viewBox="0 0 52 56" aria-hidden="true">
          <rect x="10" y="34" width="32" height="20" fill="#FCB515" rx="2" transform="rotate(2 26 44)"/>
          <rect x="12" y="18" width="28" height="18" fill="#FA6415" rx="2" transform="rotate(-2 26 27)"/>
          <circle cx="26" cy="9" r="9" fill="#2038A6"/>
        </svg>
        <p>clica em "carregar foto" e escolhe uma imagem de um padrão da natureza</p>
      </div>
      <div class="mcard m1" id="c1"><div class="mh"><div class="mn">1</div><div class="mt">observar</div></div><div class="mb" id="b1"></div></div>
      <div class="mcard m2" id="c2"><div class="mh"><div class="mn">2</div><div class="mt">abstrair as variáveis</div></div><div class="mb" id="b2"></div></div>
      <div class="mcard m3" id="c3"><div class="mh"><div class="mn">3</div><div class="mt">emular em Codeblocks</div></div><div class="mb" id="b3"></div></div>
      <div class="mcard m4" id="c4"><div class="mh"><div class="mn">4</div><div class="mt">prototipar no Tinkercad</div></div><div class="mb" id="b4"></div></div>
      <div class="mcard m5" id="c5"><div class="mh"><div class="mn">5</div><div class="mt">transferir e avaliar</div></div><div class="mb" id="b5"></div></div>
    </div>
  </div>
</div>

<script>
let imgB64=null, imgMime='image/jpeg', result=null;

document.getElementById('fi').addEventListener('change', e=>{
  const f=e.target.files[0]; if(!f) return;
  imgMime=['image/jpeg','image/png','image/gif','image/webp'].includes(f.type)?f.type:'image/jpeg';
  const r=new FileReader();
  r.onload=ev=>{
    imgB64=ev.target.result.split(',')[1];
    const p=document.getElementById('prevImg');
    p.src=ev.target.result; p.style.display='block';
    document.getElementById('btnUp').style.display='none';
    document.getElementById('btnGo').disabled=false;
    document.getElementById('errMsg').style.display='none';
  };
  r.readAsDataURL(f);
});

document.querySelectorAll('.pill').forEach(p=>{
  p.addEventListener('click',()=>{if(result) showM(parseInt(p.dataset.m));});
});

function showM(m){
  document.querySelectorAll('.pill').forEach(p=>p.classList.toggle('active',parseInt(p.dataset.m)===m));
  document.querySelectorAll('.mcard').forEach(c=>c.classList.remove('on'));
  document.getElementById('c'+m).classList.add('on');
}

function cbBlocks(blocks){
  if(!blocks||!blocks.length) return '';
  const map={set:'cs',repeat:'cr',fn:'cf',move:'cm'};
  return blocks.map(b=>`<div class="cbl">
    <span class="cbb ${map[b.type]||'cs'}">${b.keyword||'Set'}</span>
    ${b.variable?`<span class="cbb cv">${b.variable}</span>`:''}
    ${b.value!=null?`<span style="font-size:10px;color:#2038A660">→</span><span class="cbb cval">${b.value}</span>`:''}
  </div>`).join('');
}

document.getElementById('btnGo').addEventListener('click', async()=>{
  if(!imgB64) return;
  const level=document.getElementById('lvl').value;
  const err=document.getElementById('errMsg');
  err.style.display='none';
  document.getElementById('btnGo').disabled=true;
  document.getElementById('btnGo').innerHTML='<div class="lds"><span></span><span></span><span></span></div>';

  try {
    const res=await fetch('/analyze', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({image_b64:imgB64, mime_type:imgMime, level:level})
    });
    if(!res.ok) throw new Error(`Servidor: ${res.status}`);
    const d=await res.json();
    if(d.error) throw new Error(d.error);
    result=d;

    document.getElementById('empt').style.display='none';
    document.getElementById('mnav').style.display='flex';

    document.getElementById('b1').innerHTML=`<p style="margin-bottom:8px">${d.momento1.texto}</p><div>${(d.momento1.caracteristicas||[]).map(c=>`<span class="chip">${c}</span>`).join('')}</div>`;

    document.getElementById('b2').innerHTML=`<p style="margin-bottom:10px">${d.momento2.texto}</p>${(d.momento2.variaveis||[]).map(v=>`<div class="vcard"><div style="display:flex;align-items:center;gap:8px;margin-bottom:3px"><span class="vtag">${v.nome}</span><span style="font-size:13px;font-weight:700;color:#FA6415">${v.valor_tipico} ${v.unidade}</span></div><p style="font-size:11px;color:#2038A6aa;line-height:1.5">${v.explicacao}</p></div>`).join('')}`;

    document.getElementById('b3').innerHTML=`<p style="margin-bottom:8px">${d.momento3.texto}</p><div class="cbv">${cbBlocks(d.momento3.blocos)}</div>`;

    document.getElementById('b4').innerHTML=`<ol style="padding-left:16px;display:flex;flex-direction:column;gap:7px">${(d.momento4.passos||[]).map((p,i)=>`<li style="font-size:12px;line-height:1.5;color:#2038A6cc"><span style="font-weight:700;color:#2038A6">${i+1}.</span> ${p}</li>`).join('')}</ol>`;

    document.getElementById('b5').innerHTML=`<div style="margin-bottom:10px"><div class="label" style="margin-bottom:5px">na natureza</div><div>${(d.momento5.outros_exemplos||[]).map(e=>`<span class="chip">${e}</span>`).join('')}</div></div><div style="margin-bottom:10px"><div class="label" style="margin-bottom:5px;color:#FA6415">feito por humanos</div><div>${(d.momento5.aplicacoes_humanas||[]).map(e=>`<span class="chip-o">${e}</span>`).join('')}</div></div><div style="background:#FCB51520;border-radius:6px;padding:10px 12px;border-left:3px solid #FCB515"><div style="font-size:10px;font-weight:700;color:#996600;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px">para pensar</div><p style="font-size:13px;color:#2038A6;font-weight:600;line-height:1.5">${d.momento5.pergunta_reflexao}</p></div>`;

    showM(1);
  } catch(e){
    console.error(e);
    err.textContent='Erro: '+e.message;
    err.style.display='block';
  }

  document.getElementById('btnGo').disabled=false;
  document.getElementById('btnGo').innerHTML='<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/><path d="M5 8l2 2 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg> analisar outro padrão';
});
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    if not data or "image_b64" not in data:
        return jsonify({"error": "Imagem em falta"}), 400

    level = data.get("level", "intermediate")
    level_map = {
        "basic": "basic (6-7 anos, linguagem muito simples)",
        "intermediate": "intermediate (8-9 anos, acessível)",
        "advanced": "advanced (9-10 anos, mais técnico)"
    }

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1500,
            system=SYSTEM_PROMPT + f"\n\nNível do aluno: {level_map.get(level, level)}",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": data.get("mime_type", "image/jpeg"),
                            "data": data["image_b64"]
                        }
                    },
                    {
                        "type": "text",
                        "text": "Analisa este padrão natural e devolve o JSON pedagógico completo."
                    }
                ]
            }]
        )

        raw = response.content[0].text.strip()
        # Extrair JSON mesmo que haja texto extra
        s, e = raw.find("{"), raw.rfind("}")
        if s < 0 or e < 0:
            return jsonify({"error": "Resposta inválida do modelo"}), 500

        result = json.loads(raw[s:e+1])
        return jsonify(result)

    except json.JSONDecodeError as ex:
        return jsonify({"error": f"JSON inválido: {ex}"}), 500
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
