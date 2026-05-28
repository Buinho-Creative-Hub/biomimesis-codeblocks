import os
import json
import anthropic
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPTS = {
    "pt": "És especialista em biomimética e educação maker para crianças do 1º ciclo. Analisa a imagem de um padrão natural e gera orientações pedagógicas para reproduzir no Tinkercad Codeblocks. Responde APENAS com JSON válido, sem markdown nem texto extra. TODOS OS TEXTOS DO JSON DEVEM ESTAR EM PORTUGUÊS EUROPEU.",
    "en": "You are a specialist in biomimicry and maker education for primary school children. Analyse the image of a natural pattern and generate pedagogical guidance to reproduce it in Tinkercad Codeblocks. Respond ONLY with valid JSON, no markdown or extra text. ALL TEXT VALUES IN THE JSON MUST BE IN ENGLISH. Do not use Portuguese or Spanish.",
    "es": "Eres especialista en biomimética y educación maker para niños de primaria. Analiza la imagen de un patrón natural y genera orientaciones pedagógicas para reproducirlo en Tinkercad Codeblocks. Responde SOLO con JSON válido, sin markdown ni texto extra. TODOS LOS TEXTOS DEL JSON DEBEN ESTAR EN ESPAÑOL. No uses portugués ni inglés."
}

JSON_SCHEMA = """
Devolve APENAS este JSON (textos na língua pedida):
{
  "padrao": "nome do padrão identificado",
  "momento1": {
    "texto": "2-3 frases simples descrevendo o padrão para crianças.",
    "caracteristicas": ["3 a 4 características observáveis"]
  },
  "momento2": {
    "texto": "Explica as variáveis em linguagem muito simples.",
    "variaveis": [
      {"nome": "nome da variável", "valor_tipico": "valor numérico", "unidade": "unidade", "explicacao": "porque existe na natureza"}
    ]
  },
  "momento3": {
    "texto": "Explica o que o código vai fazer, passo a passo, para uma criança de 8 anos.",
    "blocos": [
      {"type": "set", "keyword": "Set", "variable": "Ângulo", "value": "137"},
      {"type": "set", "keyword": "Set", "variable": "Raio Base", "value": "2"},
      {"type": "set", "keyword": "Set", "variable": "Crescimento", "value": "1.08"},
      {"type": "set", "keyword": "Set", "variable": "Passos", "value": "60"},
      {"type": "set", "keyword": "Set", "variable": "i", "value": "1"},
      {"type": "repeat", "keyword": "Repeat", "variable": "Passos", "value": null},
      {"type": "set", "keyword": "Set", "variable": "Raio Atual", "value": "Raio Base * (Crescimento ^ i)"},
      {"type": "set", "keyword": "Set", "variable": "Ang Atual", "value": "Ângulo * i"},
      {"type": "fn", "keyword": "Add Sphere", "variable": "Radius 5", "value": null},
      {"type": "move", "keyword": "Move X", "variable": "cos(Ang Atual) * i", "value": null},
      {"type": "move", "keyword": "Move Y", "variable": "sin(Ang Atual) * i", "value": null},
      {"type": "move", "keyword": "Move Z", "variable": "i * 0.3", "value": null},
      {"type": "change", "keyword": "Change i", "variable": "by", "value": "+1"}
    ]
  },
  "momento4": {
    "passos": [
      "5 a 6 passos muito detalhados para uma criança de 8 anos, com os nomes exactos dos blocos Tinkercad. O último passo DEVE mencionar o bloco Change i by 1 e explicar que sem ele nada se move."
    ],
    "troubleshooting": [
      {
        "sintoma": "descrição curta e visual do problema que o aluno vê no Tinkercad (ex: as esferas estão muito afastadas)",
        "dica": "pergunta ou pista pedagógica que leva o aluno a raciocinar — NÃO dá a resposta directa. Específica para este padrão.",
        "solucao": "a solução concreta para este padrão específico, em linguagem simples"
      }
    ]
  },
  "momento5": {
    "outros_exemplos": ["2 exemplos do mesmo padrão noutros seres vivos"],
    "aplicacoes_humanas": ["2 aplicações humanas inspiradas neste padrão"],
    "pergunta_reflexao": "Uma pergunta aberta para o aluno explorar."
  }
}

Para o campo troubleshooting, gera 3 a 4 problemas ESPECÍFICOS para este padrão — pensa nos erros mais comuns que uma criança cometeria ao tentar reproduzi-lo no Tinkercad Codeblocks. Os sintomas devem descrever o que o aluno VÊ no ecrã, não o erro técnico."""

LEVELS = {
    "pt": {"basic": "iniciante (6-7 anos)", "intermediate": "intermédio (8-9 anos)", "advanced": "avançado (9-10 anos)"},
    "en": {"basic": "beginner (6-7 years)", "intermediate": "intermediate (8-9 years)", "advanced": "advanced (9-10 years)"},
    "es": {"basic": "iniciante (6-7 años)", "intermediate": "intermedio (8-9 años)", "advanced": "avanzado (9-10 años)"}
}

TRANSLATIONS = {
    "pt": {
        "pattern_lbl": "padrão natural",
        "upload_btn": "clica aqui para carregar foto",
        "upload_hint": "folha · concha · favo · espiral · casca",
        "level_lbl": "nível do aluno",
        "level_basic": "iniciante — 1º e 2º ano",
        "level_intermediate": "intermédio — 3º e 4º ano",
        "level_advanced": "avançado — com experiência Codeblocks",
        "analyze_btn": "analisar padrão",
        "analyze_btn2": "analisar outro padrão",
        "empty": "clica em \"carregar foto\" e escolhe uma imagem de um padrão da natureza",
        "error": "Erro: ",
        "m1": "observar", "m2": "abstrair", "m3": "emular", "m4": "prototipar", "m5": "transferir",
        "m2_title": "abstrair as variáveis", "m3_title": "emular em Codeblocks",
        "m4_title": "prototipar no Tinkercad", "m5_title": "transferir e avaliar",
        "nature_lbl": "na natureza", "human_lbl": "feito por humanos", "think_lbl": "para pensar",
        "ts_trigger": "o resultado não está certo?",
        "ts_q": "O que vês no Tinkercad?",
        "ts_restart": "recomeçar",
        "ts_other": "tenho outro problema",
        "ts_worked": "funcionou!",
        "ts_solved_title": "Boa! Problema resolvido.",
        "ts_solved_hint": "Continua a experimentar os valores — cada combinação cria um padrão diferente!",
        "ts_fallback_title": "Problemas comuns",
        "ts_fb1_s": "todas as esferas aparecem no mesmo sítio",
        "ts_fb1_d": "O bloco Change i by 1 está dentro do loop Repeat? Se estiver fora, o contador nunca avança e todas as esferas ficam na posição i=1.",
        "ts_fb1_sol": "Move o bloco Change i by 1 para dentro do bloco laranja do Repeat.",
        "ts_fb2_s": "as esferas ficam todas numa linha reta",
        "ts_fb2_d": "Confirma que estás a usar Ângulo * i para calcular o Ângulo Atual. O número 137 é especial — é o ângulo de ouro que cria espirais naturais!",
        "ts_fb2_sol": "Verifica a fórmula do Ângulo Atual: deve ser Ângulo * i, com Ângulo = 137."
    },
    "en": {
        "pattern_lbl": "natural pattern",
        "upload_btn": "click here to upload photo",
        "upload_hint": "leaf · shell · honeycomb · spiral · bark",
        "level_lbl": "student level",
        "level_basic": "beginner — year 1 & 2",
        "level_intermediate": "intermediate — year 3 & 4",
        "level_advanced": "advanced — with Codeblocks experience",
        "analyze_btn": "analyse pattern",
        "analyze_btn2": "analyse another pattern",
        "empty": "click \"upload photo\" and choose an image of a natural pattern",
        "error": "Error: ",
        "m1": "observe", "m2": "abstract", "m3": "emulate", "m4": "prototype", "m5": "transfer",
        "m2_title": "abstract the variables", "m3_title": "emulate in Codeblocks",
        "m4_title": "prototype in Tinkercad", "m5_title": "transfer & evaluate",
        "nature_lbl": "in nature", "human_lbl": "made by humans", "think_lbl": "think about it",
        "ts_trigger": "result doesn't look right?",
        "ts_q": "What do you see in Tinkercad?",
        "ts_restart": "start over",
        "ts_other": "I have another problem",
        "ts_worked": "it worked!",
        "ts_solved_title": "Great! Problem solved.",
        "ts_solved_hint": "Keep experimenting with the values — every combination creates a different pattern!",
        "ts_fallback_title": "Common problems",
        "ts_fb1_s": "all spheres appear in the same place",
        "ts_fb1_d": "Is the Change i by 1 block inside the Repeat loop? If it's outside, the counter never advances and all spheres stay at position i=1.",
        "ts_fb1_sol": "Move the Change i by 1 block inside the orange Repeat block.",
        "ts_fb2_s": "all spheres form a straight line",
        "ts_fb2_d": "Check that you're using Angle * i to calculate Current Angle. The number 137 is special — it's the golden angle that creates natural spirals!",
        "ts_fb2_sol": "Check the Current Angle formula: it should be Angle * i, with Angle = 137."
    },
    "es": {
        "pattern_lbl": "patrón natural",
        "upload_btn": "haz clic aquí para subir foto",
        "upload_hint": "hoja · concha · panal · espiral · corteza",
        "level_lbl": "nivel del alumno",
        "level_basic": "iniciante — 1º y 2º curso",
        "level_intermediate": "intermedio — 3º y 4º curso",
        "level_advanced": "avanzado — con experiencia Codeblocks",
        "analyze_btn": "analizar patrón",
        "analyze_btn2": "analizar otro patrón",
        "empty": "haz clic en \"subir foto\" y elige una imagen de un patrón de la naturaleza",
        "error": "Error: ",
        "m1": "observar", "m2": "abstraer", "m3": "emular", "m4": "prototipar", "m5": "transferir",
        "m2_title": "abstraer las variables", "m3_title": "emular en Codeblocks",
        "m4_title": "prototipar en Tinkercad", "m5_title": "transferir y evaluar",
        "nature_lbl": "en la naturaleza", "human_lbl": "hecho por humanos", "think_lbl": "para reflexionar",
        "ts_trigger": "¿el resultado no está bien?",
        "ts_q": "¿Qué ves en Tinkercad?",
        "ts_restart": "empezar de nuevo",
        "ts_other": "tengo otro problema",
        "ts_worked": "¡funcionó!",
        "ts_solved_title": "¡Muy bien! Problema resuelto.",
        "ts_solved_hint": "Sigue experimentando con los valores — ¡cada combinación crea un patrón diferente!",
        "ts_fallback_title": "Problemas comunes",
        "ts_fb1_s": "todas las esferas aparecen en el mismo sitio",
        "ts_fb1_d": "¿El bloque Change i by 1 está dentro del bucle Repeat? Si está fuera, el contador nunca avanza.",
        "ts_fb1_sol": "Mueve el bloque Change i by 1 dentro del bloque naranja Repeat.",
        "ts_fb2_s": "las esferas forman una línea recta",
        "ts_fb2_d": "Comprueba que usas Ángulo * i para calcular el Ángulo Actual. ¡El número 137 es el ángulo dorado que crea espirales naturales!",
        "ts_fb2_sol": "Verifica la fórmula del Ángulo Actual: debe ser Ángulo * i, con Ángulo = 137."
    }
}

HTML = r"""<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Buinho · Biomimesis × Codeblocks</title>
<link href="https://fonts.googleapis.com/css2?family=Asap:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Asap',sans-serif;background:#FAF0E1;min-height:100vh}
.hdr{padding:14px 24px 10px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid #2038A6;background:#FAF0E1;gap:12px}
.brand{font-weight:700;font-size:20px;color:#2038A6;letter-spacing:-0.5px;white-space:nowrap}
.brand-sub{font-size:11px;color:#FA6415;font-weight:500;margin-top:2px}
.lang-sw{display:flex;gap:4px;flex-shrink:0}
.lang-btn{background:#FAF0E1;border:1.5px solid #2038A640;border-radius:6px;padding:5px 10px;font-family:'Asap',sans-serif;font-size:11px;font-weight:700;color:#2038A680;cursor:pointer;transition:.15s}
.lang-btn:hover{border-color:#2038A6;color:#2038A6}
.lang-btn.on{background:#2038A6;color:#FAF0E1;border-color:#2038A6}
.main{display:grid;grid-template-columns:1fr 1fr;min-height:calc(100vh - 66px)}
@media(max-width:640px){.main{grid-template-columns:1fr}}
.pl{padding:20px 20px 20px 24px;border-right:1.5px solid #2038A640;display:flex;flex-direction:column;gap:16px}
.pr{padding:20px 36px 20px 20px;display:flex;flex-direction:column;gap:12px;position:relative}
.slbl{font-size:10px;font-weight:700;letter-spacing:1.5px;color:#2038A6;text-transform:uppercase;margin-bottom:4px}
.upzone{display:block;background:#FAF0E1;border:2px dashed #2038A680;border-radius:8px;padding:18px 16px;text-align:center;cursor:pointer;width:100%;transition:.2s;text-decoration:none}
.upzone:hover{border-color:#2038A6;background:#F0E4CC}
.upzone svg{display:block;margin:0 auto 8px}
.up-t{font-size:13px;color:#2038A6;font-weight:600}
.up-h{font-size:11px;color:#2038A680;margin-top:3px}
#prevImg{display:none;width:100%;max-height:160px;object-fit:cover;border-radius:6px;border:1.5px solid #2038A640;margin-top:8px}
select{width:100%;font-family:'Asap',sans-serif;font-size:13px;padding:8px 10px;border:1.5px solid #2038A640;border-radius:6px;background:#FAF0E1;color:#2038A6;font-weight:600}
.btn-go{background:#2038A6;color:#FAF0E1;border:none;border-radius:6px;padding:12px 16px;font-family:'Asap',sans-serif;font-size:14px;font-weight:700;cursor:pointer;width:100%;display:flex;align-items:center;justify-content:center;gap:8px;transition:.15s}
.btn-go:hover{background:#162d85}
.btn-go:disabled{background:#2038A640;cursor:not-allowed}
.mnav{display:none;flex-wrap:wrap;gap:4px;margin-bottom:4px}
.pill{background:#FAF0E1;border:1.5px solid #2038A640;border-radius:20px;padding:4px 10px;font-size:10px;font-weight:700;color:#2038A680;cursor:pointer;transition:.15s}
.pill.on{background:#2038A6;color:#FAF0E1;border-color:#2038A6}
.rarea{flex:1;overflow-y:auto;max-height:calc(100vh - 200px)}
.mcard{border:1.5px solid #2038A640;border-radius:8px;padding:14px 16px;display:none}
.mcard.on{display:block}
.mhd{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.mnum{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0}
.m1 .mnum{background:#2038A6;color:#FAF0E1}.m2 .mnum{background:#FA6415;color:#FAF0E1}
.m3 .mnum{background:#F23A2F;color:#FAF0E1}.m4 .mnum{background:#FCB515;color:#2038A6}.m5 .mnum{background:#2038A6;color:#FAF0E1}
.mtit{font-size:13px;font-weight:700;color:#2038A6}
.mbody{font-size:13px;color:#2038A6cc;line-height:1.6}
.vtag{display:inline-block;background:#2038A620;color:#2038A6;border-radius:4px;padding:1px 7px;font-size:11px;font-weight:700;margin:1px 2px;font-family:monospace}
.cbv{background:#2038A610;border-radius:6px;padding:10px 12px;margin-top:8px;border-left:3px solid #2038A6}
.cbl{font-size:11px;color:#2038A6;line-height:1.9;display:flex;align-items:center;gap:5px;flex-wrap:wrap}
.cbb{display:inline-block;border-radius:3px;padding:1px 7px;font-size:10px;font-weight:700}
.cs{background:#5C9BE6;color:#fff}.cv{background:#5C9BE6bb;color:#fff}
.cval{background:#fff;color:#2038A6;border:1px solid #2038A640}
.cr{background:#FA6415;color:#fff}.cf{background:#4CAF50;color:#fff}.cm{background:#9C6FD6;color:#fff}
.lds{display:inline-flex;gap:4px;align-items:center}
.lds span{width:6px;height:6px;border-radius:50%;background:#FAF0E1;animation:db 1.2s infinite}
.lds span:nth-child(2){animation-delay:.2s}.lds span:nth-child(3){animation-delay:.4s}
@keyframes db{0%,80%,100%{transform:scale(.7);opacity:.5}40%{transform:scale(1);opacity:1}}
.empty{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:40px 20px;text-align:center}
.empty p{font-size:13px;color:#2038A680;font-weight:500;max-width:200px;line-height:1.5}
.edu{position:absolute;right:8px;top:0;bottom:0;width:18px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;padding-bottom:20px;gap:3px;pointer-events:none}
.edu span{font-size:10px;font-weight:500;color:#FA6415;line-height:1}
.errmsg{background:#F23A2F15;border:1.5px solid #F23A2F40;border-radius:6px;padding:10px 12px;font-size:12px;color:#F23A2F;font-weight:500;display:none}
.chip{background:#2038A615;color:#2038A6;font-size:11px;font-weight:600;padding:3px 9px;border-radius:12px;display:inline-block;margin:2px}
.chip-o{background:#FA641515;color:#FA6415;font-size:11px;font-weight:600;padding:3px 9px;border-radius:12px;display:inline-block;margin:2px}
.vcard{margin-bottom:8px;padding:8px 10px;background:#2038A608;border-radius:6px;border-left:3px solid #FA6415}
.ts-divider{border:none;border-top:1.5px dashed #2038A640;margin:14px 0}
.ts-trigger{display:flex;align-items:center;gap:8px;background:#F23A2F0D;border:1.5px solid #F23A2F30;border-radius:8px;padding:10px 12px;cursor:pointer;transition:.15s;width:100%;font-family:'Asap',sans-serif}
.ts-trigger:hover{background:#F23A2F18;border-color:#F23A2F60}
.ts-trigger-icon{font-size:15px;color:#F23A2F}
.ts-trigger-lbl{font-size:12px;font-weight:700;color:#F23A2F;flex:1;text-align:left}
.ts-arr{font-size:11px;color:#F23A2F80}
.ts-panel{display:none;flex-direction:column;gap:0;margin-top:10px}
.ts-panel.open{display:flex}
.ts-bc{display:flex;align-items:center;gap:6px;margin-bottom:8px;min-height:18px}
.ts-back{background:none;border:none;font-family:'Asap',sans-serif;font-size:11px;font-weight:700;color:#FA6415;cursor:pointer;padding:0;display:none}
.ts-back:hover{text-decoration:underline}
.ts-node{display:none;flex-direction:column;gap:8px}
.ts-node.active{display:flex}
.ts-node-q{font-size:12px;font-weight:700;color:#2038A6;margin-bottom:4px}
.ts-opts{display:flex;flex-direction:column;gap:6px}
.ts-opt{background:#FAF0E1;border:1.5px solid #2038A640;border-radius:6px;padding:8px 10px;font-family:'Asap',sans-serif;font-size:11px;font-weight:600;color:#2038A6;cursor:pointer;text-align:left;transition:.15s}
.ts-opt:hover{background:#F0E4CC;border-color:#2038A6}
.ts-detail{background:#fff;border:1.5px solid #F23A2F30;border-radius:8px;padding:10px 12px;border-left:3px solid #F23A2F;display:none;flex-direction:column;gap:6px}
.ts-detail.active{display:flex}
.ts-detail-hint{font-size:11px;color:#2038A6aa;line-height:1.6;background:#2038A608;border-radius:6px;padding:8px 10px;border-left:3px solid #2038A630}
.ts-detail-hint code{background:#2038A615;border-radius:3px;padding:1px 5px;font-family:monospace;font-size:10px;color:#2038A6}
.ts-detail-sol{font-size:11px;color:#2038A6;font-weight:600;background:#FCB51515;border-radius:6px;padding:7px 10px;border-left:3px solid #FCB515}
.ts-detail-btns{display:flex;gap:6px;flex-wrap:wrap}
.ts-btn-ok{background:#2DB87010;border:1.5px solid #2DB87040;border-radius:6px;padding:6px 10px;font-family:'Asap',sans-serif;font-size:11px;font-weight:700;color:#1a7a4a;cursor:pointer;transition:.15s}
.ts-btn-ok:hover{background:#2DB87020}
.ts-btn-more{background:#FAF0E1;border:1.5px solid #2038A640;border-radius:6px;padding:6px 10px;font-family:'Asap',sans-serif;font-size:11px;font-weight:700;color:#2038A6;cursor:pointer;transition:.15s}
.ts-btn-more:hover{background:#F0E4CC}
.ts-solved{background:#2DB87010;border:1.5px solid #2DB87040;border-radius:8px;padding:12px 14px;display:none;flex-direction:column;gap:6px}
.ts-solved.active{display:flex}
.ts-solved-t{font-size:12px;font-weight:700;color:#1a7a4a}
.ts-solved-txt{font-size:11px;color:#1a7a4aaa;line-height:1.5}
.ts-restart{background:none;border:1.5px solid #2DB87060;border-radius:6px;padding:6px 10px;font-family:'Asap',sans-serif;font-size:11px;font-weight:700;color:#1a7a4a;cursor:pointer;margin-top:2px}
.ts-restart:hover{background:#2DB87015}
</style>
</head>
<body>
<div class="hdr">
  <div>
    <div class="brand">Buinho</div>
    <div class="brand-sub">biomimesis × codeblocks</div>
  </div>
  <div class="lang-sw">
    <button class="lang-btn {{ 'on' if lang=='pt' else '' }}" onclick="setLang('pt')">PT</button>
    <button class="lang-btn {{ 'on' if lang=='en' else '' }}" onclick="setLang('en')">EN</button>
    <button class="lang-btn {{ 'on' if lang=='es' else '' }}" onclick="setLang('es')">ES</button>
  </div>
  <svg width="36" height="22" viewBox="0 0 36 22" aria-hidden="true">
    <rect x="0" y="10" width="14" height="12" fill="#FCB515" rx="1" transform="rotate(3 7 16)"/>
    <rect x="11" y="6" width="12" height="10" fill="#FA6415" rx="1" transform="rotate(-2 17 11)"/>
    <rect x="22" y="2" width="13" height="9" fill="#2038A6" rx="1" transform="rotate(4 28 6)"/>
  </svg>
</div>

<div class="main">
  <div class="pl">
    <div>
      <div class="slbl">{{ t.pattern_lbl }}</div>
      <div class="upzone" id="upzone" style="position:relative">
        <input type="file" id="fi" accept="image/*" style="position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%;z-index:2">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <rect x="3" y="7" width="26" height="18" rx="3" fill="#2038A615" stroke="#2038A6" stroke-width="1.5"/>
          <circle cx="12" cy="14" r="3" fill="#2038A630"/>
          <path d="M3 21 l7-7 6 6 4-4 8 5" stroke="#2038A6" stroke-width="1.5" fill="none" stroke-linecap="round"/>
        </svg>
        <div class="up-t">{{ t.upload_btn }}</div>
        <div class="up-h">{{ t.upload_hint }}</div>
      </div>
      <img id="prevImg" alt="pattern">
    </div>
    <div>
      <div class="slbl">{{ t.level_lbl }}</div>
      <select id="lvl">
        <option value="basic">{{ t.level_basic }}</option>
        <option value="intermediate" selected>{{ t.level_intermediate }}</option>
        <option value="advanced">{{ t.level_advanced }}</option>
      </select>
    </div>
    <div id="errmsg" class="errmsg"></div>
    <button class="btn-go" id="btnGo" disabled>
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/><path d="M5 8l2 2 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
      <span id="lbl-go">{{ t.analyze_btn }}</span>
    </button>
  </div>

  <div class="pr">
    <div class="edu" aria-hidden="true">
      <span>o</span><span>v</span><span>i</span><span>t</span><span>a</span><span>c</span><span>u</span><span>d</span><span>e</span>
    </div>
    <div class="mnav" id="mnav">
      <span class="pill on" data-m="1">1 · {{ t.m1 }}</span>
      <span class="pill" data-m="2">2 · {{ t.m2 }}</span>
      <span class="pill" data-m="3">3 · {{ t.m3 }}</span>
      <span class="pill" data-m="4">4 · {{ t.m4 }}</span>
      <span class="pill" data-m="5">5 · {{ t.m5 }}</span>
    </div>
    <div class="rarea" id="rarea">
      <div class="empty" id="empt">
        <svg width="52" height="56" viewBox="0 0 52 56" aria-hidden="true">
          <rect x="10" y="34" width="32" height="20" fill="#FCB515" rx="2" transform="rotate(2 26 44)"/>
          <rect x="12" y="18" width="28" height="18" fill="#FA6415" rx="2" transform="rotate(-2 26 27)"/>
          <circle cx="26" cy="9" r="9" fill="#2038A6"/>
        </svg>
        <p>{{ t.empty }}</p>
      </div>
      <div class="mcard m1" id="c1"><div class="mhd"><div class="mnum">1</div><div class="mtit">{{ t.m1 }}</div></div><div class="mbody" id="b1"></div></div>
      <div class="mcard m2" id="c2"><div class="mhd"><div class="mnum">2</div><div class="mtit">{{ t.m2_title }}</div></div><div class="mbody" id="b2"></div></div>
      <div class="mcard m3" id="c3"><div class="mhd"><div class="mnum">3</div><div class="mtit">{{ t.m3_title }}</div></div><div class="mbody" id="b3"></div></div>
      <div class="mcard m4" id="c4"><div class="mhd"><div class="mnum">4</div><div class="mtit">{{ t.m4_title }}</div></div><div class="mbody" id="b4"></div></div>
      <div class="mcard m5" id="c5"><div class="mhd"><div class="mnum">5</div><div class="mtit">{{ t.m5_title }}</div></div><div class="mbody" id="b5"></div></div>
    </div>
  </div>
</div>

<script>
var LANG = '{{ lang }}';
var ALL_T = {
  pt:{pattern_lbl:"padrão natural",upload_btn:"clica aqui para carregar foto",upload_hint:"folha · concha · favo · espiral · casca",level_lbl:"nível do aluno",level_basic:"iniciante — 1º e 2º ano",level_intermediate:"intermédio — 3º e 4º ano",level_advanced:"avançado — com experiência Codeblocks",analyze_btn:"analisar padrão",analyze_btn2:"analisar outro padrão",empty:"clica em \"carregar foto\" e escolhe uma imagem de um padrão da natureza",error:"Erro: ",m1:"observar",m2:"abstrair",m3:"emular",m4:"prototipar",m5:"transferir",m2_title:"abstrair as variáveis",m3_title:"emular em Codeblocks",m4_title:"prototipar no Tinkercad",m5_title:"transferir e avaliar",nature_lbl:"na natureza",human_lbl:"feito por humanos",think_lbl:"para pensar",ts_trigger:"o resultado não está certo?",ts_q:"O que vês no Tinkercad?",ts_restart:"recomeçar",ts_other:"tenho outro problema",ts_worked:"funcionou!",ts_solved_title:"Boa! Problema resolvido.",ts_solved_hint:"Continua a experimentar — cada combinação cria um padrão diferente!",ts_fb1_s:"todas as esferas aparecem no mesmo sítio",ts_fb1_d:"O bloco <code>Change i by 1</code> está dentro do loop Repeat? Se estiver fora, o contador nunca avança e todas as esferas ficam na posição i=1.",ts_fb1_sol:"Move o bloco <code>Change i by 1</code> para dentro do bloco laranja do Repeat.",ts_fb2_s:"as esferas ficam todas numa linha reta",ts_fb2_d:"Confirma que estás a usar <code>Ângulo * i</code> para calcular o Ângulo Atual. O número 137 é especial — é o ângulo de ouro que cria espirais naturais!",ts_fb2_sol:"Verifica a fórmula do Ângulo Atual: deve ser <code>Ângulo * i</code>, com Ângulo = 137."},
  en:{pattern_lbl:"natural pattern",upload_btn:"click here to upload photo",upload_hint:"leaf · shell · honeycomb · spiral · bark",level_lbl:"student level",level_basic:"beginner — year 1 & 2",level_intermediate:"intermediate — year 3 & 4",level_advanced:"advanced — with Codeblocks experience",analyze_btn:"analyse pattern",analyze_btn2:"analyse another pattern",empty:"click \"upload photo\" and choose an image of a natural pattern",error:"Error: ",m1:"observe",m2:"abstract",m3:"emulate",m4:"prototype",m5:"transfer",m2_title:"abstract the variables",m3_title:"emulate in Codeblocks",m4_title:"prototype in Tinkercad",m5_title:"transfer & evaluate",nature_lbl:"in nature",human_lbl:"made by humans",think_lbl:"think about it",ts_trigger:"result doesn't look right?",ts_q:"What do you see in Tinkercad?",ts_restart:"start over",ts_other:"I have another problem",ts_worked:"it worked!",ts_solved_title:"Great! Problem solved.",ts_solved_hint:"Keep experimenting — every combination creates a different pattern!",ts_fb1_s:"all spheres appear in the same place",ts_fb1_d:"Is the <code>Change i by 1</code> block inside the Repeat loop? If outside, the counter never advances.",ts_fb1_sol:"Move the <code>Change i by 1</code> block inside the orange Repeat block.",ts_fb2_s:"all spheres form a straight line",ts_fb2_d:"Check you're using <code>Angle * i</code> for Current Angle. 137 is the golden angle that creates natural spirals!",ts_fb2_sol:"Check Current Angle formula: it should be <code>Angle * i</code>, with Angle = 137."},
  es:{pattern_lbl:"patrón natural",upload_btn:"haz clic aquí para subir foto",upload_hint:"hoja · concha · panal · espiral · corteza",level_lbl:"nivel del alumno",level_basic:"iniciante — 1º y 2º curso",level_intermediate:"intermedio — 3º y 4º curso",level_advanced:"avanzado — con experiencia Codeblocks",analyze_btn:"analizar patrón",analyze_btn2:"analizar otro patrón",empty:"haz clic en \"subir foto\" y elige una imagen de un patrón de la naturaleza",error:"Error: ",m1:"observar",m2:"abstraer",m3:"emular",m4:"prototipar",m5:"transferir",m2_title:"abstraer las variables",m3_title:"emular en Codeblocks",m4_title:"prototipar en Tinkercad",m5_title:"transferir y evaluar",nature_lbl:"en la naturaleza",human_lbl:"hecho por humanos",think_lbl:"para reflexionar",ts_trigger:"¿el resultado no está bien?",ts_q:"¿Qué ves en Tinkercad?",ts_restart:"empezar de nuevo",ts_other:"tengo otro problema",ts_worked:"¡funcionó!",ts_solved_title:"¡Muy bien! Problema resuelto.",ts_solved_hint:"¡Sigue experimentando — cada combinación crea un patrón diferente!",ts_fb1_s:"todas las esferas aparecen en el mismo sitio",ts_fb1_d:"¿El bloque <code>Change i by 1</code> está dentro del bucle Repeat? Si está fuera, el contador nunca avanza.",ts_fb1_sol:"Mueve el bloque <code>Change i by 1</code> dentro del bloque naranja Repeat.",ts_fb2_s:"las esferas forman una línea recta",ts_fb2_d:"Comprueba que usas <code>Ángulo * i</code> para el Ángulo Actual. ¡137 es el ángulo dorado que crea espirales naturales!",ts_fb2_sol:"Verifica la fórmula del Ángulo Actual: debe ser <code>Ángulo * i</code>, con Ángulo = 137."}
};
var T = ALL_T[LANG];

function setLang(l){
  LANG=l;T=ALL_T[l];
  document.querySelectorAll('.lang-btn').forEach(function(b){b.classList.toggle('on',b.textContent.trim().toLowerCase()===l);});
  document.querySelector('.slbl').textContent=T.pattern_lbl;
  document.querySelector('.up-t').textContent=T.upload_btn;
  document.querySelector('.up-h').textContent=T.upload_hint;
  var lvlLbls=document.querySelectorAll('.slbl');
  if(lvlLbls[1])lvlLbls[1].textContent=T.level_lbl;
  var opts=document.getElementById('lvl').options;
  opts[0].text=T.level_basic;opts[1].text=T.level_intermediate;opts[2].text=T.level_advanced;
  document.getElementById('lbl-go').textContent=T.analyze_btn;
  document.querySelector('.empty p').textContent=T.empty;
  var pillLabels=[T.m1,T.m2,T.m3,T.m4,T.m5];
  document.querySelectorAll('.pill').forEach(function(p,i){p.textContent=(i+1)+' · '+pillLabels[i];});
  var titles=[T.m1,T.m2_title,T.m3_title,T.m4_title,T.m5_title];
  document.querySelectorAll('.mtit').forEach(function(el,i){el.textContent=titles[i];});
  document.documentElement.lang=l;
}

var imgB64=null,imgMime='image/jpeg',result=null;

document.getElementById('fi').addEventListener('change',function(e){
  var f=e.target.files[0];
  if(!f)return;
  imgMime=['image/jpeg','image/png','image/gif','image/webp'].indexOf(f.type)>=0?f.type:'image/jpeg';
  var r=new FileReader();
  r.onload=function(ev){
    imgB64=ev.target.result.split(',')[1];
    var p=document.getElementById('prevImg');
    p.src=ev.target.result;p.style.display='block';
    document.getElementById('upzone').style.display='none';
    document.getElementById('btnGo').disabled=false;
    document.getElementById('errmsg').style.display='none';
  };
  r.readAsDataURL(f);
});

document.querySelectorAll('.pill').forEach(function(p){
  p.addEventListener('click',function(){if(result)showM(parseInt(p.dataset.m));});
});

function showM(m){
  document.querySelectorAll('.pill').forEach(function(p){p.classList.toggle('on',parseInt(p.dataset.m)===m);});
  document.querySelectorAll('.mcard').forEach(function(c){c.classList.remove('on');});
  document.getElementById('c'+m).classList.add('on');
}

function cbBlocks(blocks){
  if(!blocks||!blocks.length)return'';
  var map={set:'cs',repeat:'cr',fn:'cf',move:'cm',change:'cr'};
  return blocks.map(function(b){
    return'<div class="cbl">'+
      '<span class="cbb '+(map[b.type]||'cs')+'">'+(b.keyword||'Set')+'</span>'+
      (b.variable?'<span class="cbb cv">'+b.variable+'</span>':'')+
      (b.value!=null?'<span style="font-size:10px;color:#2038A660">→</span><span class="cbb cval">'+b.value+'</span>':'')+
      '</div>';
  }).join('');
}

/* ── TROUBLESHOOTING ── */
var tsItems=[];
var tsCurrent=-1;
var tsOpen=false;

function tsInit(items){
  tsItems=items||[];
  tsCurrent=-1;
  tsOpen=false;
  var panel=document.getElementById('tsPanel');
  if(panel){panel.classList.remove('open');panel.innerHTML='';}
  var trig=document.getElementById('tsTrigger');
  if(trig)trig.querySelector('.ts-arr').textContent='▾';
}

function tsBuild(){
  var panel=document.getElementById('tsPanel');
  if(!panel)return;
  var fb=[
    {sintoma:T.ts_fb1_s,dica:T.ts_fb1_d,solucao:T.ts_fb1_sol},
    {sintoma:T.ts_fb2_s,dica:T.ts_fb2_d,solucao:T.ts_fb2_sol}
  ];
  var all=tsItems.concat(fb);
  var html='<div style="height:8px"></div>';
  html+='<div id="tsBack" style="min-height:18px;margin-bottom:6px;display:none"><button class="ts-back" id="tsBtnBack" onclick="tsBack()">← '+T.ts_restart+'</button></div>';
  html+='<div id="tsRoot" class="ts-node active">';
  html+='<div class="ts-node-q">'+T.ts_q+'</div><div class="ts-opts">';
  all.forEach(function(item,i){
    html+='<button class="ts-opt" onclick="tsShow('+i+')">'+item.sintoma+'</button>';
  });
  html+='</div></div>';
  all.forEach(function(item,i){
    html+='<div id="tsItem'+i+'" class="ts-detail">';
    html+='<div class="ts-detail-hint">'+item.dica+'</div>';
    html+='<div class="ts-detail-sol">'+item.solucao+'</div>';
    html+='<div class="ts-detail-btns">';
    html+='<button class="ts-btn-ok" onclick="tsSolved()">✓ '+T.ts_worked+'</button>';
    html+='<button class="ts-btn-more" onclick="tsRoot()">'+T.ts_other+'</button>';
    html+='</div></div>';
  });
  html+='<div id="tsSolvedBox" class="ts-solved">';
  html+='<div class="ts-solved-t">'+T.ts_solved_title+'</div>';
  html+='<div class="ts-solved-txt">'+T.ts_solved_hint+'</div>';
  html+='<button class="ts-restart" onclick="tsRoot()">'+T.ts_restart+'</button>';
  html+='</div>';
  panel.innerHTML=html;
}

function tsShow(i){
  tsCurrent=i;
  document.getElementById('tsRoot').classList.remove('active');
  document.querySelectorAll('.ts-detail').forEach(function(el){el.classList.remove('active');});
  document.getElementById('tsSolvedBox').classList.remove('active');
  document.getElementById('tsItem'+i).classList.add('active');
  var back=document.getElementById('tsBack');
  if(back)back.style.display='block';
}

function tsRoot(){
  tsCurrent=-1;
  document.getElementById('tsRoot').classList.add('active');
  document.querySelectorAll('.ts-detail').forEach(function(el){el.classList.remove('active');});
  document.getElementById('tsSolvedBox').classList.remove('active');
  var back=document.getElementById('tsBack');
  if(back)back.style.display='none';
}

function tsBack(){tsRoot();}

function tsSolved(){
  document.getElementById('tsRoot').classList.remove('active');
  document.querySelectorAll('.ts-detail').forEach(function(el){el.classList.remove('active');});
  document.getElementById('tsSolvedBox').classList.add('active');
}

document.addEventListener('click',function(e){
  var trig=e.target.closest('#tsTrigger');
  if(!trig)return;
  tsOpen=!tsOpen;
  var panel=document.getElementById('tsPanel');
  panel.classList.toggle('open',tsOpen);
  trig.querySelector('.ts-arr').textContent=tsOpen?'▴':'▾';
  if(tsOpen&&panel.innerHTML==='')tsBuild();
});
/* ── END TROUBLESHOOTING ── */

document.getElementById('btnGo').addEventListener('click',async function(){
  if(!imgB64)return;
  var level=document.getElementById('lvl').value;
  var err=document.getElementById('errmsg');
  err.style.display='none';
  document.getElementById('btnGo').disabled=true;
  document.getElementById('btnGo').innerHTML='<div class="lds"><span></span><span></span><span></span></div>';

  try{
    var res=await fetch('/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image_b64:imgB64,mime_type:imgMime,level:level,lang:LANG})});
    if(!res.ok)throw new Error(T.error+res.status);
    var d=await res.json();
    if(d.error)throw new Error(d.error);
    result=d;

    document.getElementById('empt').style.display='none';
    document.getElementById('mnav').style.display='flex';

    document.getElementById('b1').innerHTML='<p style="margin-bottom:8px">'+d.momento1.texto+'</p><div>'+
      (d.momento1.caracteristicas||[]).map(function(c){return'<span class="chip">'+c+'</span>';}).join('')+'</div>';

    document.getElementById('b2').innerHTML='<p style="margin-bottom:10px">'+d.momento2.texto+'</p>'+
      (d.momento2.variaveis||[]).map(function(v){return'<div class="vcard"><div style="display:flex;align-items:center;gap:8px;margin-bottom:3px"><span class="vtag">'+v.nome+'</span><span style="font-size:13px;font-weight:700;color:#FA6415">'+v.valor_tipico+' '+v.unidade+'</span></div><p style="font-size:11px;color:#2038A6aa;line-height:1.5">'+v.explicacao+'</p></div>';}).join('');

    document.getElementById('b3').innerHTML='<p style="margin-bottom:8px">'+d.momento3.texto+'</p><div class="cbv">'+cbBlocks(d.momento3.blocos)+'</div>';

    var tsData=d.momento4.troubleshooting||[];
    tsInit(tsData);
    var m4html='<ol style="padding-left:16px;display:flex;flex-direction:column;gap:7px">'+
      (d.momento4.passos||[]).map(function(p,i){return'<li style="font-size:12px;line-height:1.5;color:#2038A6cc"><span style="font-weight:700;color:#2038A6">'+(i+1)+'.</span> '+p+'</li>';}).join('')+
      '</ol>';
    m4html+='<hr class="ts-divider">';
    m4html+='<button class="ts-trigger" id="tsTrigger">';
    m4html+='<span class="ts-trigger-icon">?</span>';
    m4html+='<span class="ts-trigger-lbl">'+T.ts_trigger+'</span>';
    m4html+='<span class="ts-arr">▾</span>';
    m4html+='</button>';
    m4html+='<div class="ts-panel" id="tsPanel"></div>';
    document.getElementById('b4').innerHTML=m4html;

    document.getElementById('b5').innerHTML=
      '<div style="margin-bottom:10px"><div class="slbl" style="margin-bottom:5px">'+T.nature_lbl+'</div><div>'+
      (d.momento5.outros_exemplos||[]).map(function(e){return'<span class="chip">'+e+'</span>';}).join('')+'</div></div>'+
      '<div style="margin-bottom:10px"><div class="slbl" style="margin-bottom:5px;color:#FA6415">'+T.human_lbl+'</div><div>'+
      (d.momento5.aplicacoes_humanas||[]).map(function(e){return'<span class="chip-o">'+e+'</span>';}).join('')+'</div></div>'+
      '<div style="background:#FCB51520;border-radius:6px;padding:10px 12px;border-left:3px solid #FCB515">'+
      '<div style="font-size:10px;font-weight:700;color:#996600;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px">'+T.think_lbl+'</div>'+
      '<p style="font-size:13px;color:#2038A6;font-weight:600;line-height:1.5">'+d.momento5.pergunta_reflexao+'</p></div>';

    showM(1);
  }catch(e){
    err.textContent=T.error+e.message;
    err.style.display='block';
  }

  document.getElementById('btnGo').disabled=false;
  document.getElementById('btnGo').innerHTML='<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/><path d="M5 8l2 2 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg> '+T.analyze_btn2;
});
</script>
</body>
</html>"""


@app.route("/")
def index():
    lang = request.args.get("lang", "pt")
    if lang not in ("pt", "en", "es"):
        lang = "pt"
    t = TRANSLATIONS[lang]
    return render_template_string(HTML, lang=lang, t=t)


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    if not data or "image_b64" not in data:
        return jsonify({"error": "Imagem em falta"}), 400

    lang = data.get("lang", "pt")
    if lang not in ("pt", "en", "es"):
        lang = "pt"

    level = data.get("level", "intermediate")
    level_str = LEVELS.get(lang, LEVELS["pt"]).get(level, level)
    system = SYSTEM_PROMPTS[lang] + "\n\n" + JSON_SCHEMA + f"\n\nNível: {level_str}"

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=system,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": data.get("mime_type", "image/jpeg"), "data": data["image_b64"]}},
                    {"type": "text", "text": f"Analisa este padrão natural e devolve o JSON. Língua de resposta: {lang.upper()}. Todos os campos de texto do JSON devem estar em {['Português','English','Español'][['pt','en','es'].index(lang)]}."}
                ]
            }]
        )
        raw = response.content[0].text.strip()
        s, e = raw.find("{"), raw.rfind("}")
        if s < 0 or e < 0:
            return jsonify({"error": "Resposta inválida"}), 500
        return jsonify(json.loads(raw[s:e+1]))

    except Exception as ex:
        import traceback
        print("ERRO ANALYZE:", str(ex))
        print(traceback.format_exc())
        return jsonify({"error": str(ex)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
