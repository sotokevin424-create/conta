import streamlit as st
import sqlite3
import hashlib
import secrets
import json
import uuid
import io
import html
import unicodedata
import inspect
import os
import re
import zipfile
from datetime import date, datetime
from xml.sax.saxutils import escape as xesc
from collections import OrderedDict

import pandas as pd
import plotly.express as px
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)

APP_TITLE = "FINOVA | Análisis Financiero"
DB_PATH = "finova.db"
SPANISH_MONTHS = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)

# --------------------------- Sistema de diseño ---------------------------
# Tokens (CSS custom properties), componentes HTML reutilizables y tema de gráficas.
# Paleta derivada del logotipo de D.E.M.I. MEX (azul #013E8F + rojo señal) con neutros fríos.

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
:root{
  --brand:#013E8F; --brand-d:#012E6B; --navy:#0A2147; --ink:#0F1B2D; --muted:#55657D;
  --bg:#F4F6FA; --surface:#FFFFFF; --line:#DDE3EC; --accent:#C8102E; --signal:#F2183A;
  --ok:#0B7A4F; --ok-bg:#E6F4EE; --warn:#8A5300; --warn-bg:#FFF3D6;
  --err:#B3261E; --err-bg:#FDECEA; --info-bg:#E8EFFA;
  --r:14px; --sh:0 1px 2px rgba(10,33,71,.06),0 4px 14px rgba(10,33,71,.05);
  --display:'Barlow Condensed','Arial Narrow',sans-serif;
  --mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
}
.stApp{background:var(--bg);color:var(--ink)}
.stApp,.stApp p,.stApp li,.stApp label,.stApp input,.stApp textarea,.stApp button,
.stApp [data-baseweb="select"] div,.stApp [data-testid="stCaptionContainer"]{
  font-family:'IBM Plex Sans',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}
.stApp h1,.stApp h2,.stApp h3{font-family:var(--display);color:var(--navy);font-weight:700;letter-spacing:-.005em}
.stApp h2{font-size:1.7rem;margin-top:1.4rem}.stApp h3{font-size:1.3rem}
[data-testid="stHeaderActionElements"],footer{display:none!important}
header[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1240px;padding:2rem 2rem 4rem}

/* Encabezado de página */
.pg-head{margin:0 0 1.4rem;padding-bottom:1.1rem;border-bottom:1px solid var(--line)}
.eyebrow{font-size:.74rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--brand);
  display:flex;align-items:center;gap:.55rem;margin-bottom:.35rem}
.eyebrow:before{content:"";width:22px;height:3px;background:var(--signal);border-radius:2px}
.pg-head h1{font-size:clamp(2rem,4vw,2.8rem);line-height:1.05;margin:0;padding:0;overflow-wrap:anywhere}
.pg-head p{color:var(--muted);margin:.45rem 0 0;font-size:1rem;overflow-wrap:anywhere}

.dashboard-heading{margin:0}
.dashboard-heading-kicker{display:inline-flex;align-items:center;gap:8px;margin-bottom:.45rem;padding:5px 10px;
  border:1px solid #DCE6F2;border-radius:999px;background:linear-gradient(110deg,#F8FAFD,#EDF3FA);
  color:#315F9A;font-size:.66rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase}
.dashboard-heading-kicker:before{content:"";width:6px;height:6px;border-radius:50%;background:var(--signal)}
.dashboard-heading h1{margin:0;color:var(--navy);font-family:'IBM Plex Sans',system-ui,sans-serif;
  font-size:clamp(1.9rem,3vw,2.45rem);font-weight:600;line-height:1.1;letter-spacing:-.04em;
  overflow-wrap:anywhere}
.dashboard-heading-line{display:flex;align-items:baseline;flex-wrap:wrap;gap:8px 14px}
.dashboard-heading time{display:inline-flex;align-items:center;padding:4px 9px;border:1px solid #E2E8F0;
  border-radius:999px;background:rgba(255,255,255,.74);color:var(--muted);font-size:.74rem;font-weight:500;white-space:nowrap}
.dashboard-heading p{max-width:58ch;margin:.4rem 0 0;color:var(--muted);font-size:.91rem;line-height:1.5}
.stApp [data-testid="stMain"] .st-key-dashboard_create_analysis button,
.stApp [data-testid="stMain"] .st-key-dashboard_continue_analysis button,
.stApp [data-testid="stMain"] .st-key-dashboard_lookup_analysis button{
  min-height:38px!important;padding-top:.35rem!important;padding-bottom:.35rem!important}
.stApp [data-testid="stMain"] .st-key-dashboard_create_analysis button{
  border:1px solid rgba(255,255,255,.18)!important;
  background:linear-gradient(135deg,#0B4B9D,#013E8F)!important;
  box-shadow:0 7px 16px rgba(1,62,143,.2);font-weight:600}
.stApp [data-testid="stMain"] .st-key-dashboard_create_analysis button:hover{
  box-shadow:0 10px 20px rgba(1,62,143,.27);transform:translateY(-1px)}
.stApp [data-testid="stMain"] .st-key-dashboard_continue_analysis button{
  border-color:#C7D4E5!important;background:rgba(255,255,255,.82)!important}
div[data-testid="stHorizontalBlock"]:has(.dashboard-heading):has(.st-key-dashboard_create_analysis){
  position:relative;isolation:isolate;align-items:center!important;gap:14px;margin:.2rem 0 1.15rem;
  padding:18px 22px;overflow:hidden;border:1px solid #DCE6F2;border-radius:20px;
  background:radial-gradient(circle at 91% 10%,rgba(49,95,154,.1),transparent 27%),
    linear-gradient(112deg,#FFFFFF 0%,#F9FBFE 58%,#EEF4FB 100%);
  box-shadow:0 12px 30px rgba(10,33,71,.065)}
div[data-testid="stHorizontalBlock"]:has(.dashboard-heading):has(.st-key-dashboard_create_analysis):before{
  content:"";position:absolute;left:0;top:17px;bottom:17px;width:3px;border-radius:0 4px 4px 0;
  background:linear-gradient(180deg,var(--brand),var(--signal))}
div[data-testid="stHorizontalBlock"]:has(.dashboard-heading):has(.st-key-dashboard_create_analysis):after{
  content:"";position:absolute;z-index:-1;top:-126px;right:-28px;width:250px;height:250px;
  border:1px solid rgba(49,95,154,.1);border-radius:50%;
  box-shadow:0 0 0 20px rgba(49,95,154,.025),0 0 0 44px rgba(49,95,154,.018);
  pointer-events:none}
div[data-testid="stHorizontalBlock"]:has(.dashboard-heading):has(.st-key-dashboard_create_analysis)>div[data-testid="stColumn"]{
  position:relative;z-index:1}
/* KPIs */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:0 0 1.4rem}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:16px 18px;box-shadow:var(--sh)}
.kpi.brand{border-top:3px solid var(--brand)}.kpi.up{border-top:3px solid var(--ok)}
.kpi.down{border-top:3px solid var(--accent)}.kpi.warn{border-top:3px solid #E0A100}
.dashboard-summary{position:relative;isolation:isolate;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0;
  overflow:hidden;margin:1.15rem 0 1.45rem;padding:16px 18px;
  border:1px solid rgba(255,255,255,.13);border-radius:18px;
  background:linear-gradient(112deg,#091D3E 0%,#0D2C59 53%,#16477F 100%);
  box-shadow:0 14px 28px rgba(10,33,71,.14)}
.dashboard-summary:after{content:"";position:absolute;z-index:-1;top:-104px;right:9%;
  width:220px;height:220px;border:1px solid rgba(220,235,255,.12);border-radius:50%;
  box-shadow:0 0 0 24px rgba(220,235,255,.035),0 0 0 50px rgba(220,235,255,.025);
  pointer-events:none}
.dashboard-summary-item{display:grid;grid-template-columns:28px minmax(0,1fr);grid-template-rows:auto auto auto;
  position:relative;z-index:1;align-content:start;column-gap:9px;min-width:0;padding:2px 18px;
  border-left:1px solid rgba(222,235,251,.16)}
.dashboard-summary-item:first-child{padding-left:0;border-left:0}
.dashboard-summary-icon{grid-column:1;grid-row:1 / 4;display:grid;place-items:center;width:28px;height:28px;
  border:1px solid rgba(227,238,252,.2);border-radius:9px;
  background:linear-gradient(145deg,rgba(255,255,255,.16),rgba(255,255,255,.07));color:#D8E8FB}
.dashboard-summary-icon svg{display:block;width:15px;height:15px}
.dashboard-summary-item.is-pending .dashboard-summary-icon{border-color:rgba(255,217,137,.32);
  background:rgba(255,217,137,.12);color:#FFD989}
.dashboard-summary-label{grid-column:2;color:#C4D2E5;font-size:.66rem;font-weight:600;line-height:1.3;
  letter-spacing:.075em;text-transform:uppercase}
.dashboard-summary-value{grid-column:2;display:block;margin-top:4px;color:#FFF;font-size:1.2rem;
  font-weight:600;line-height:1.25;overflow-wrap:anywhere;font-variant-numeric:tabular-nums}
.dashboard-summary-detail{grid-column:2;display:block;margin-top:3px;color:#B5C6DD;font-size:.72rem;line-height:1.35}
.dashboard-summary-item.is-pending .dashboard-summary-value{color:#FFD989}
.stApp h2.dashboard-section-title{display:flex;align-items:center;gap:14px;margin:1.6rem 0 .45rem;font-family:'IBM Plex Sans',system-ui,sans-serif;
  font-size:1.12rem;font-weight:600;letter-spacing:-.02em}
.stApp h2.dashboard-section-title:before{content:"";flex:none;width:17px;height:3px;border-radius:3px;
  background:linear-gradient(90deg,var(--brand),#7395C2)}
.stApp h2.dashboard-section-title:after{content:"";height:1px;flex:1;
  background:linear-gradient(90deg,#DCE4EF,rgba(220,228,239,0))}
.kpi-label{font-size:.76rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.kpi-value{font-family:var(--display);font-weight:700;font-size:clamp(1.6rem,2.3vw,2.2rem);line-height:1.15;
  color:var(--navy);margin-top:.3rem;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.kpi-value.sm{font-size:1.4rem}
.kpi-unit{font-family:'IBM Plex Sans',sans-serif;font-size:.72rem;font-weight:600;color:var(--muted);margin-left:.4rem;letter-spacing:.05em}
.kpi-hint{font-size:.8rem;color:var(--muted);margin-top:.15rem;overflow-wrap:anywhere}

/* Insignias, estados vacíos, pasos */
.badge{display:inline-block;font-size:.72rem;font-weight:600;padding:2px 9px;border-radius:999px;background:var(--info-bg);color:var(--brand)}
.badge.ok{background:var(--ok-bg);color:var(--ok)}.badge.warn{background:var(--warn-bg);color:var(--warn)}
.badge.err{background:var(--err-bg);color:var(--err)}.badge.muted{background:#EEF1F6;color:var(--muted)}
.empty{background:var(--surface);border:1px dashed #B9C4D6;border-radius:16px;padding:2.2rem 1.5rem;text-align:center;margin:.5rem 0 1.2rem}
.empty-ic{width:54px;height:54px;border-radius:14px;background:var(--info-bg);color:var(--brand);display:inline-flex;align-items:center;justify-content:center;margin-bottom:.7rem}
.empty h3{margin:0 0 .25rem}.empty p{color:var(--muted);margin:0;max-width:46ch;margin-inline:auto}
.stepper{list-style:none;display:flex;flex-wrap:wrap;gap:10px 28px;padding:0;margin:0 0 1.3rem}
.step{display:flex;align-items:center;gap:.55rem;font-weight:500;color:var(--muted)}
.step-dot{width:26px;height:26px;border-radius:50%;border:2px solid #B9C4D6;display:inline-flex;align-items:center;justify-content:center;font-size:.78rem;font-weight:600;background:#fff}
.step.now{color:var(--navy);font-weight:600}.step.now .step-dot{border-color:var(--brand);background:var(--brand);color:#fff}
.step.done{color:var(--ok)}.step.done .step-dot{border-color:var(--ok);background:var(--ok);color:#fff}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 1rem}
.chip{background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:.84rem;color:var(--ink)}
.mono{font-family:var(--mono);font-size:.82rem;color:var(--muted)}
.th{font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.row-sep{border:0;border-top:1px solid var(--line);margin:.35rem 0}

.dashboard-record-folio{color:#62728A;font-family:var(--mono);font-size:.72rem;overflow-wrap:anywhere}
.dashboard-row-title{display:flex;align-items:center;min-width:0}
.dashboard-row-title strong{color:var(--navy);font-size:.96rem;font-weight:600;line-height:1.3;
  letter-spacing:-.015em;overflow-wrap:anywhere}
.dashboard-company-lockup{display:flex;align-items:center;gap:11px;min-width:0}
.dashboard-company-avatar{display:grid;place-items:center;flex:none;width:34px;height:34px;border:1px solid #DCE6F3;
  border-radius:11px;background:linear-gradient(145deg,#F5F8FD,#E5EDF8);color:#315F9A;
  font-size:.78rem;font-weight:700;box-shadow:inset 0 1px 0 rgba(255,255,255,.9)}
.dashboard-company-copy{min-width:0}
.dashboard-recent-row,.dashboard-portfolio-row{min-width:0;padding:4px 0}
.dashboard-recent-row{position:relative;padding-left:23px}
.dashboard-recent-row:before{content:"";position:absolute;left:0;top:9px;width:9px;height:9px;
  border:2px solid #A8B9CE;border-radius:50%;background:#fff}
.dashboard-recent-row.is-latest:before{border-color:var(--brand);background:var(--brand);
  box-shadow:0 0 0 4px rgba(1,62,143,.1)}
.dashboard-row-subline,.dashboard-row-details{display:flex;flex-wrap:wrap;gap:4px 14px;
  margin-top:5px;color:var(--muted);font-size:.75rem;line-height:1.4}
.dashboard-row-subline span:first-child{max-width:38ch;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dashboard-row-subline span:last-child{color:#64748B;font-variant-numeric:tabular-nums;white-space:nowrap}
.dashboard-row-details strong{margin-right:4px;color:#42516A;font-size:.68rem;font-weight:600}
div[data-testid="stHorizontalBlock"]:has(.dashboard-recent-row){
  align-items:center!important;margin:5px 0;padding:10px 12px;border:1px solid #E8EEF5;border-radius:14px;
  background:rgba(255,255,255,.86);box-shadow:0 2px 8px rgba(10,33,71,.025);
  transition:background .15s ease,border-color .15s ease,box-shadow .15s ease,transform .15s ease}
div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-row){
  align-items:center!important;padding:10px 0;border-bottom:1px solid #E8ECF2;
  transition:background .15s ease,border-color .15s ease}
div[data-testid="stHorizontalBlock"]:has(.dashboard-recent-row):hover{
  border-color:#D7E3F1;background:#F9FBFE;box-shadow:0 6px 16px rgba(10,33,71,.06);
  transform:translateY(-1px)}
div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-row):hover{background:#FAFBFD}
div[data-testid="stHorizontalBlock"]:has(.dashboard-recent-row.is-latest){
  border-color:#D6E3F2;border-radius:14px;
  background:linear-gradient(105deg,#EAF2FC 0%,#F8FBFF 46%,#FFFFFF 100%);
  box-shadow:inset 3px 0 0 #315F9A,0 5px 14px rgba(10,33,71,.055)}
div[data-testid="stHorizontalBlock"]:has(.dashboard-recent-row)>div[data-testid="stColumn"]:first-child{
  border-left:1px solid #E4EAF2;padding-left:14px!important}
div[data-testid="stHorizontalBlock"]:has(.dashboard-recent-row.is-latest)>div[data-testid="stColumn"]:first-child{
  border-left-color:transparent}
div[data-testid="stHorizontalBlock"]:has(.dashboard-recent-row) .badge,
div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-row) .badge{
  padding:4px 10px;font-size:.68rem;letter-spacing:.015em}
div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-row)>div[data-testid="stColumn"]:last-child button{
  min-height:36px!important;padding-left:.5rem!important;padding-right:.5rem!important;font-size:.82rem!important}
div[data-testid="stHorizontalBlock"]:has(.dashboard-recent-row)>div[data-testid="stColumn"]:last-child button{
  min-height:36px!important;padding-left:.55rem!important;padding-right:.55rem!important;font-size:.82rem!important}
.dashboard-portfolio-head{display:block;padding:0 2px;color:var(--muted);font-size:.64rem;
  font-weight:600;letter-spacing:.075em;text-transform:uppercase;white-space:nowrap}
div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-head){
  padding:0 0 8px;border-bottom:1px solid #DDE4ED}
div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-head)>div[data-testid="stColumn"]{
  min-width:0}

/* Razones */
.ratios{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px;margin:.6rem 0 1.2rem}
.ratio{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:18px;box-shadow:var(--sh)}
.ratio-top{display:flex;justify-content:space-between;align-items:center;gap:8px}
.ratio-name{font-weight:600;color:var(--navy)}
.ratio-value{font-family:var(--display);font-weight:700;font-size:2.3rem;line-height:1.1;color:var(--brand);margin:.35rem 0 .6rem;font-variant-numeric:tabular-nums}
.ratio-value small{font-family:'IBM Plex Sans',sans-serif;font-size:.8rem;color:var(--muted);font-weight:600;margin-left:.35rem}
.ratio dl{margin:0 0 .5rem;display:grid;grid-template-columns:auto 1fr;gap:.2rem .8rem;font-size:.86rem}
.ratio dt{color:var(--muted)}.ratio dd{margin:0;overflow-wrap:anywhere}
.ratio p{margin:0;font-size:.88rem;color:#2A3A52;border-top:1px solid var(--line);padding-top:.6rem}

/* Decisiones */
.decision-hero{position:relative;display:flex;align-items:center;justify-content:space-between;gap:24px;
  overflow:hidden;margin:.2rem 0 1rem;padding:24px 28px;border-radius:20px;
  background:linear-gradient(115deg,#0A2147 0%,#123E79 62%,#1855A0 100%);
  color:#fff;box-shadow:0 12px 28px rgba(10,33,71,.16)}
.decision-hero:after{content:"";position:absolute;width:240px;height:240px;right:80px;top:-150px;
  border:1px solid rgba(255,255,255,.12);border-radius:50%;box-shadow:0 0 0 28px rgba(255,255,255,.035),0 0 0 58px rgba(255,255,255,.025)}
.decision-hero-copy{position:relative;z-index:1;max-width:76%}
.decision-hero-label{color:#B8D3FA;font-size:.7rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
.decision-hero h2{margin:.4rem 0 .25rem!important;color:#fff!important;font-size:1.8rem!important}
.decision-hero p{margin:0;color:#E0EAF8;font-size:.94rem;line-height:1.5}
.decision-hero-total{position:relative;z-index:1;display:flex;align-items:center;justify-content:center;gap:10px;
  flex:none;width:128px;height:88px;border:1px solid rgba(255,255,255,.23);border-radius:16px;
  background:rgba(255,255,255,.1);backdrop-filter:blur(8px)}
.decision-hero-total strong{font-family:var(--display);font-size:2.6rem;line-height:1;color:#fff}
.decision-hero-total span{font-size:.72rem;line-height:1.25;color:#D8E6FA;font-weight:600}
.decision-stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,190px),1fr));gap:12px;margin:.8rem 0 1.1rem}
.decision-stat{display:flex;align-items:center;gap:14px;padding:15px 17px;border:1px solid var(--decision-border);
  border-left:4px solid var(--decision-accent);border-radius:14px;background:var(--surface);box-shadow:var(--sh)}
.decision-stat.danger,.decision-choice.danger,.decision-card.danger{
  --decision-accent:#B3261E;--decision-bg:#FDECEA;--decision-border:#F2C2BF;--decision-text:#6F1D19}
.decision-stat.review,.decision-choice.review,.decision-card.review{
  --decision-accent:#A66A00;--decision-bg:#FFF5D9;--decision-border:#EBD393;--decision-text:#694300}
.decision-stat.good,.decision-choice.good,.decision-card.good{
  --decision-accent:#0B7A4F;--decision-bg:#E6F4EE;--decision-border:#B7DDCA;--decision-text:#084F36}
.decision-focus-heading.danger,.decision-focus-heading.review,.decision-focus-heading.good{
  --decision-accent:#78B8E8;--decision-bg:#EEF7FF;--decision-border:#D1E6F7;--decision-text:#244B6C}
.decision-stat-mark{display:grid;place-items:center;flex:none;width:38px;height:38px;border-radius:12px;
  background:var(--decision-bg);color:var(--decision-accent);font-size:1.15rem;font-weight:700}
.decision-stat-copy{min-width:0}
.decision-stat-copy span,.decision-stat-copy small{display:block;color:var(--muted)}
.decision-stat-copy span{font-size:.72rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase}
.decision-stat-copy strong{display:block;color:var(--navy);font-family:var(--display);font-size:1.8rem;line-height:1.1}
.decision-stat-copy small{font-size:.74rem;line-height:1.35}
.decision-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:12px;margin:.85rem 0 1rem}
.decision-card{min-height:100%;padding:17px;border:1px solid var(--decision-border);
  border-top:4px solid var(--decision-accent);border-radius:15px;background:var(--decision-bg)}
.decision-card-head{display:flex;align-items:center;gap:9px;margin:0 0 12px;color:var(--decision-text);
  font-size:.88rem;font-weight:700}
.decision-card-step{display:inline-flex;align-items:center;justify-content:center;flex:none;width:27px;height:27px;
  border-radius:9px;background:var(--decision-accent);color:#fff;font-size:.72rem}
.decision-card p{margin:0;color:#24354C;font-size:.9rem;line-height:1.55;overflow-wrap:anywhere}
.decision-workspace-title{margin:0 0 .25rem;color:var(--navy);font-size:1.1rem;font-weight:700}
.decision-workspace-caption{margin:0 0 .8rem;color:var(--muted);font-size:.84rem}
.decision-choice{padding:12px 13px;border:1px solid var(--decision-border);border-left:4px solid var(--decision-accent);
  border-radius:12px;background:var(--decision-bg)}
.decision-choice.danger .decision-choice-priority{background:#FDECEA;border-color:#F2C2BF;color:#6F1D19}
.decision-choice.review .decision-choice-priority{background:#FFF5D9;border-color:#EBD393;color:#694300}
.decision-choice.good .decision-choice-priority{background:#E6F4EE;border-color:#B7DDCA;color:#084F36}
.decision-choice-head{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px}
.decision-choice-priority{display:inline-flex;align-items:center;padding:3px 8px;border:1px solid #DDE8F1;
  border-radius:999px;background:#F5F9FC;color:#496982;font-size:.66rem;font-weight:700;
  letter-spacing:.07em;text-transform:uppercase}
.decision-choice-source{color:var(--muted);font-size:.7rem}
.decision-choice-title{margin:0;color:var(--ink);font-size:.87rem;font-weight:600;line-height:1.4;overflow-wrap:anywhere}
.decision-focus-heading{padding:17px 19px;border:0;border-radius:12px;
  background:#F6FAFE;margin-bottom:.75rem;scroll-margin-top:1.25rem}
.decision-focus-overline{display:flex;align-items:center;gap:7px;color:#54728E;
  font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase}
.decision-focus-heading h3{margin:.5rem 0 .15rem;color:var(--navy);font-size:1.25rem}
.decision-focus-heading p{margin:0;color:var(--muted);font-size:.82rem}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.decision-focus-heading){
  border:1px solid #D56A7A!important;border-radius:17px;background:#fff;
  box-shadow:0 4px 18px rgba(10,33,71,.055)}
.decision-route{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:.4rem}
.decision-route-label{color:var(--muted);font-size:.84rem}
.decision-evidence{margin:.65rem 0 1rem}
.decision-evidence-title{margin:0 0 .45rem;color:var(--navy);font-size:.82rem;font-weight:700}
.decision-evidence-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:8px}
.decision-evidence-card{padding:11px 12px;border:1px solid #E5EDF5;border-radius:12px;background:#F8FBFE}
.decision-evidence-card>strong{display:block;margin:0 0 7px;color:#344E68;font-size:.82rem}
.decision-evidence-values{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.decision-evidence-values span{display:block;color:#71849A;font-size:.66rem;text-transform:uppercase;letter-spacing:.04em}
.decision-evidence-values b{display:block;color:#263E57;font-size:.78rem;overflow-wrap:anywhere}
.decision-value{padding:1px 5px;border:1px solid #C4DFF3;border-radius:5px;background:#EAF5FF;
  color:#17456C;font-weight:700;white-space:normal;overflow-wrap:anywhere}
.stmt tr.decision-focus td{background:#EAF5FF!important;color:#244B6C;border-top:1px solid #C4DFF3;
  border-bottom:1px solid #C4DFF3;font-weight:700}
.stmt tr.decision-focus td:first-child:before{content:"◆";margin-right:8px;color:#4E8BB8;font-size:.68rem}
.ratio.decision-focus{border:2px solid #7FB5DB;box-shadow:0 0 0 4px rgba(127,181,219,.14)}
.ratio.decision-focus .ratio-value{display:table;padding:3px 8px;border-radius:8px;background:#EAF5FF;color:#24567B}

/* Sidebar */
section[data-testid="stSidebar"]{background:var(--navy);border-right:1px solid #14336A}
section[data-testid="stSidebar"] .stMarkdown,section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#C9D6EC}
.side-brand{display:flex;align-items:center;gap:12px;padding:.2rem .2rem 1rem}
.side-brand .wordmark{font-family:var(--display);font-weight:700;font-size:1.7rem;color:#fff;line-height:1}
.side-brand small{display:block;font-size:.64rem;letter-spacing:.16em;color:#8FA6CB;font-weight:600;margin-top:3px}
.side-user{display:flex;align-items:center;gap:10px;background:rgba(255,255,255,.06);border-radius:12px;padding:10px 12px}
.avatar{width:34px;height:34px;border-radius:50%;background:var(--brand);color:#fff;font-weight:600;display:inline-flex;align-items:center;justify-content:center;border:1px solid rgba(255,255,255,.25)}
.side-user b{color:#fff;display:block;font-size:.92rem;line-height:1.2;overflow-wrap:anywhere}.side-user span{color:#9FB3D4;font-size:.76rem}
.side-ctx{margin-top:10px;border-left:3px solid var(--signal);background:rgba(255,255,255,.06);border-radius:0 10px 10px 0;padding:8px 12px}
.side-ctx small{color:#9FB3D4;font-size:.66rem;letter-spacing:.1em;font-weight:600;text-transform:uppercase}
.side-ctx b{display:block;color:#fff;font-size:.88rem;overflow-wrap:anywhere}.side-ctx span{font-family:var(--mono);font-size:.7rem;color:#9FB3D4}
.nav-label{font-size:.66rem;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:#7F97C0;margin:1.5rem 0 .3rem .4rem}
section[data-testid="stSidebar"] button{width:100%;justify-content:flex-start;border:0;box-shadow:none;border-radius:10px;
  min-height:42px;background:transparent;color:#D5E0F2;font-weight:500;transition:background .15s}
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.15rem}
section[data-testid="stSidebar"] button>div,section[data-testid="stSidebar"] button [data-testid="stMarkdownContainer"]{justify-content:flex-start;text-align:left}
section[data-testid="stSidebar"] button{padding-left:.8rem}
section[data-testid="stSidebar"] button p,section[data-testid="stSidebar"] button span{color:inherit!important}
section[data-testid="stSidebar"] button:hover{background:rgba(255,255,255,.09);color:#fff}
section[data-testid="stSidebar"] button[kind="primary"],section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]{
  background:rgba(255,255,255,.14);color:#fff;font-weight:600;box-shadow:inset 3px 0 0 var(--signal)}
section[data-testid="stSidebar"] :focus-visible{outline:3px solid #fff!important;outline-offset:2px}

/* Controles */
.stApp .stButton>button,.stApp .stDownloadButton>button,.stApp [data-testid="stFormSubmitButton"]>button{
  border-radius:10px;min-height:44px;font-weight:600;transition:background .15s,border-color .15s,box-shadow .15s}
.stApp [data-testid="stMain"] button[kind="secondary"],.stApp [data-testid="stMain"] button[data-testid="stBaseButton-secondary"]{
  background:var(--surface);border:1px solid #C3CDDD;color:var(--navy)}
.stApp [data-testid="stMain"] button[kind="secondary"]:hover{border-color:var(--brand);color:var(--brand)}
.stApp [data-testid="stMain"] button[kind="primary"]:hover,.stApp [data-testid="stMain"] button[data-testid="stBaseButton-primary"]:hover{background:var(--brand-d)}
.stApp [data-testid="stMain"] :focus-visible{outline:3px solid var(--brand);outline-offset:2px}
.stApp label p{font-weight:600;font-size:.86rem;color:var(--ink)}
.stApp [data-baseweb="input"],.stApp [data-baseweb="base-input"],.stApp [data-baseweb="select"]>div{border-radius:10px}
[data-testid="stForm"]{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:1.4rem;box-shadow:var(--sh)}
[data-testid="stExpander"]{background:var(--surface);border:1px solid var(--line);border-radius:12px}
[data-testid="stExpander"] summary p{font-weight:600;color:var(--navy)}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:12px;overflow:hidden}
[data-testid="stAlert"]{border-radius:12px}

/* Acceso */
.auth-brand{text-align:center;margin:2.5rem 0 1.4rem}
.auth-brand .wordmark{font-family:var(--display);font-weight:700;font-size:2.8rem;color:var(--navy);line-height:1;margin-top:.6rem;letter-spacing:.02em}
.auth-brand p{color:var(--muted);margin:.3rem 0 0}
.auth-note{background:var(--info-bg);color:var(--navy);border-radius:12px;padding:.8rem 1rem;margin-bottom:1rem;font-size:.92rem}
.auth-points{list-style:none;padding:0;margin:1.4rem 0 0;display:grid;gap:.55rem;color:var(--muted);font-size:.9rem}
.auth-points li{display:flex;gap:.6rem;align-items:center}.auth-points svg{color:var(--brand);flex:none}

/* Estados financieros */
.stmt-wrap{background:var(--surface);border:1px solid var(--line);border-radius:12px;overflow-x:auto;margin:.4rem 0 1rem}
.stmt{width:100%;border-collapse:collapse;font-size:.92rem}
.stmt th{background:#F0F3F9;color:var(--muted);font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;text-align:left;padding:10px 14px;border-bottom:1px solid var(--line)}
.stmt th.num,.stmt td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.stmt td{padding:8px 14px;border-bottom:1px solid #EEF1F6}
.stmt tr.sec td{background:var(--info-bg);color:var(--navy);font-weight:600;font-size:.8rem;letter-spacing:.04em;text-transform:uppercase}
.stmt tr.item td:first-child{padding-left:30px}
.stmt tr.tot td{font-weight:600;border-top:1px solid #C3CDDD}
.stmt tr.grand td{font-weight:700;background:#F0F3F9;color:var(--navy);border-top:2px solid var(--navy)}
.sign-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:0 0 1rem}
.sign{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:14px 16px}
.sign small{font-size:.7rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);display:block}
.sign b{display:block;margin-top:.3rem;color:var(--navy);overflow-wrap:anywhere}
.lock{display:flex;gap:.65rem;align-items:flex-start;background:var(--warn-bg);color:#5C3A00;border-radius:12px;padding:.8rem 1rem;margin:0 0 1rem;font-size:.92rem}
.lock svg{flex:none;margin-top:2px}
.gloss{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.gloss>div{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:.88rem}
.gloss b{color:var(--navy);display:block}.gloss span{color:var(--muted);font-size:.78rem;display:block;margin:.1rem 0 .4rem}
.gloss em{color:var(--muted)}

@media (max-width:640px){
  .block-container{padding:1.2rem 1rem 3rem}
  .kpis{grid-template-columns:1fr 1fr}.ratios{grid-template-columns:1fr}
  .decision-hero{align-items:flex-start;padding:20px;gap:12px}
  .decision-hero-copy{max-width:100%}.decision-hero-total{width:88px;height:72px;gap:5px}
  .decision-hero-total strong{font-size:2rem}.decision-hero-total span{font-size:.64rem}
  .decision-stat-grid,.decision-grid{grid-template-columns:1fr}
  .stepper{gap:8px 16px}
}
@media (max-width:760px){
  .dashboard-heading p{max-width:60ch}
  .dashboard-summary{grid-template-columns:repeat(2,minmax(0,1fr));row-gap:14px}
  .dashboard-summary-item:nth-child(odd){padding-left:0;border-left:0}
  div[data-testid="stHorizontalBlock"]:has(.st-key-panel_activity_search){flex-wrap:wrap!important}
  div[data-testid="stHorizontalBlock"]:has(.st-key-panel_activity_search)>div[data-testid="stColumn"]{
    flex:1 1 185px!important;width:auto!important;min-width:min(100%,185px)!important}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-recent-row)>div[data-testid="stColumn"]:first-child{
    flex:1 1 100%!important;width:auto!important;min-width:100%!important}
}
@media (max-width:900px){
  div[data-testid="stHorizontalBlock"]:has(.dashboard-heading):has(.st-key-dashboard_create_analysis){
    flex-wrap:wrap!important}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-heading):has(.st-key-dashboard_create_analysis)>div[data-testid="stColumn"]:first-child{
    flex:1 1 380px!important;width:auto!important;min-width:min(100%,380px)!important}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-heading):has(.st-key-dashboard_create_analysis)>div[data-testid="stColumn"]:last-child{
    flex:1 1 300px!important;width:auto!important;min-width:min(100%,300px)!important}
}
@media (max-width:480px){
  div[data-testid="stHorizontalBlock"]:has(.dashboard-heading):has(.st-key-dashboard_create_analysis){
    padding:15px 14px}
  .dashboard-summary-item{padding-right:10px;padding-left:10px}
  .dashboard-summary-value{font-size:1rem}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-recent-row)>div[data-testid="stColumn"]:last-child button,
  div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-row)>div[data-testid="stColumn"]:last-child button{
    min-height:44px!important}
}
@media (max-width:1100px){
  div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-head){flex-wrap:wrap!important}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-head)>div[data-testid="stColumn"]:first-child{
    flex:3.7 1 250px!important;width:auto!important;min-width:min(100%,250px)!important}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-head)>div[data-testid="stColumn"]:nth-child(2){
    flex:4 1 240px!important;width:auto!important;min-width:min(100%,240px)!important}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-head)>div[data-testid="stColumn"]:nth-child(3){
    flex:1.15 1 90px!important;width:auto!important;min-width:min(100%,90px)!important}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-head)>div[data-testid="stColumn"]:last-child{
    flex:1.7 1 130px!important;width:auto!important;min-width:min(100%,130px)!important}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-recent-row){flex-wrap:wrap!important}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-recent-row)>div[data-testid="stColumn"]:first-child{
    flex:5 1 270px!important;width:auto!important;min-width:min(100%,270px)!important}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-recent-row)>div[data-testid="stColumn"]:nth-child(2){
    flex:1.2 1 90px!important;width:auto!important;min-width:min(100%,90px)!important}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-recent-row)>div[data-testid="stColumn"]:last-child{
    flex:1.3 1 110px!important;width:auto!important;min-width:min(100%,110px)!important}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-row){flex-wrap:wrap!important}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-row)>div[data-testid="stColumn"]:first-child{
    flex:3.7 1 250px!important;width:auto!important;min-width:min(100%,250px)!important}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-row)>div[data-testid="stColumn"]:nth-child(2){
    flex:4 1 240px!important;width:auto!important;min-width:min(100%,240px)!important}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-row)>div[data-testid="stColumn"]:nth-child(3){
    flex:1.15 1 90px!important;width:auto!important;min-width:min(100%,90px)!important}
  div[data-testid="stHorizontalBlock"]:has(.dashboard-portfolio-row)>div[data-testid="stColumn"]:last-child{
    flex:1.7 1 130px!important;width:auto!important;min-width:min(100%,130px)!important}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>
"""

ICONS = {
    "dashboard": '<rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>',
    "file-plus": '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="12" x2="12" y1="18" y2="12"/><line x1="9" x2="15" y1="15" y2="15"/>',
    "table": '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18M3 15h18M12 3v18"/>',
    "percent": '<line x1="19" x2="5" y1="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>',
    "bar-chart": '<line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/>',
    "file-text": '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/>',
    "checklist": '<path d="M9 6h11M9 12h11M9 18h11"/><path d="m3 6 1 1 2-2M3 12l1 1 2-2M3 18l1 1 2-2"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "lock": '<rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "folder": '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
    "edit": '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "scale": '<path d="M12 3v18M5 21h14M5 7h14M5 7l-3 7a4 4 0 0 0 6 0L5 7zM19 7l-3 7a4 4 0 0 0 6 0l-3-7z"/>',
}

LOGO = (
    '<svg width="44" height="44" viewBox="0 0 128 128" role="img" aria-label="FINOVA">'
    '<rect x="8" y="8" width="112" height="112" rx="24" fill="#013E8F" stroke="rgba(255,255,255,.22)" stroke-width="2"/>'
    '<rect x="32" y="68" width="16" height="24" fill="#fff"/><rect x="54" y="50" width="16" height="42" fill="#fff"/>'
    '<rect x="76" y="32" width="16" height="60" fill="#fff"/><rect x="28" y="100" width="72" height="8" fill="#F2183A"/></svg>'
)

COLORWAY = ["#013E8F", "#8FA3C0", "#C8102E", "#0B7A4F", "#E0A100", "#5C7CBA", "#293241", "#7A4FA0"]
PERIOD_COLORS = {"Anterior": "#9DB0CC", "Reciente": "#013E8F"}
MOVE_COLORS = {"Aumento": "#0B7A4F", "Disminucion": "#C8102E"}

_V = tuple(int(x) for x in st.__version__.split(".")[:2] if x.isdigit())
STRETCH = {"width": "stretch"} if _V >= (1, 50) else {"use_container_width": True}
_BTN_ICON = "icon" in inspect.signature(st.button).parameters
_COL_VA = {"vertical_alignment": "center"} if "vertical_alignment" in inspect.signature(st.columns).parameters else {}


def H(markup, target=st):
    """Renderiza HTML en una sola línea (evita que Markdown lo trate como bloque de código)."""
    target.markdown("".join(line.strip() for line in markup.strip().splitlines()), unsafe_allow_html=True)


def scroll_to_element(element_id, block="center"):
    st.html(
        '<script>window.setTimeout(() => {'
        f'const target = document.getElementById({json.dumps(element_id)});'
        f'if (target) target.scrollIntoView({{behavior: "auto", block: "{block}"}});'
        '}, 180);</script>',
        unsafe_allow_javascript=True,
    )


def esc(value):
    return html.escape("" if value is None else str(value))


def icon(name, size=20):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


def btn(label, material=None, **kwargs):
    """Botón con icono Material cuando la versión de Streamlit lo soporta."""
    if _BTN_ICON and material:
        kwargs["icon"] = f":material/{material}:"
    return st.button(label, **kwargs)


def go(page_name):
    if page_name != "Decisiones":
        st.session_state["decision_detail_index"] = None
    st.session_state["decision_scroll_to_detail"] = False
    st.session_state.page = page_name
    st.rerun()


def fmt_money(value):
    try:
        v = float(value)
        return f"-${abs(v):,.2f}" if v < 0 else f"${v:,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def badge(text, tone=""):
    return f'<span class="badge {tone}">{esc(text)}</span>'


def page_header(title, subtitle="", eyebrow=""):
    eb = f'<div class="eyebrow">{esc(eyebrow)}</div>' if eyebrow else ""
    sub = f"<p>{esc(subtitle)}</p>" if subtitle else ""
    H(f'<div class="pg-head">{eb}<h1>{esc(title)}</h1>{sub}</div>')


def kpi_row(items, class_name=""):
    """items: (etiqueta, valor, unidad, nota, tono)"""
    cells = ""
    for it in items:
        label, value = it[0], it[1]
        unit = it[2] if len(it) > 2 else ""
        hint = it[3] if len(it) > 3 else ""
        tone = it[4] if len(it) > 4 else ""
        size = " sm" if len(str(value)) > 18 else ""
        unit_html = f'<span class="kpi-unit">{esc(unit)}</span>' if unit else ""
        hint_html = f'<div class="kpi-hint">{esc(hint)}</div>' if hint else ""
        cells += (f'<div class="kpi {tone}"><div class="kpi-label">{esc(label)}</div>'
                  f'<div class="kpi-value{size}">{esc(value)}{unit_html}</div>{hint_html}</div>')
    H(f'<div class="kpis {esc(class_name)}">{cells}</div>')


def panel_date_label(timestamp):
    value = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00")).date()
    return f"{value.day} {SPANISH_MONTHS[value.month - 1][:3]}. {value.year}"


def panel_relative_date(timestamp):
    activity_date = datetime.fromisoformat(
        str(timestamp).replace("Z", "+00:00")
    ).date()
    days_since = max((date.today() - activity_date).days, 0)
    if days_since == 0:
        return "Hoy"
    if days_since == 1:
        return "Ayer"
    if days_since < 7:
        return f"Hace {days_since} días"
    if days_since < 30:
        weeks = days_since // 7
        return f"Hace {weeks} semana" + ("s" if weeks != 1 else "")
    if days_since < 365:
        months = days_since // 30
        return f"Hace {months} mes" + ("es" if months != 1 else "")
    years = days_since // 365
    return f"Hace {years} año" + ("s" if years != 1 else "")


def render_panel_records(records, active_folio, variant, key_prefix):
    for index, record in enumerate(records):
        folio = record["folio"]
        company_initial = (record["company"] or "?")[:1].upper()
        is_active = folio == active_folio
        status_html = badge("Activo", "ok") if is_active else badge("Guardado", "muted")
        date_label = panel_date_label(record["last_activity_at"])

        if variant == "recent":
            info_column, status_column, action_column = st.columns(
                [5, 1.2, 1.3],
                **_COL_VA,
            )
            with info_column:
                H(
                    '<div class="dashboard-recent-row'
                    f'{" is-latest" if index == 0 else ""}">'
                    '<div class="dashboard-company-lockup">'
                    f'<span class="dashboard-company-avatar" aria-hidden="true">{esc(company_initial)}</span>'
                    '<div class="dashboard-company-copy">'
                    f'<div class="dashboard-row-title"><strong>{esc(record["company"])}</strong></div>'
                    f'<div class="dashboard-record-folio">{esc(folio)}</div></div></div>'
                    '<div class="dashboard-row-subline">'
                    f'<span>{esc(record["last_activity_action"] or "Sin actividad registrada")}</span>'
                    f'<span>{esc(date_label)}</span></div></div>'
                )
            with status_column:
                H(status_html)
            with action_column:
                action_label = "Continuar" if is_active else "Abrir"
                if st.button(
                    action_label,
                    key=f"{key_prefix}_open_{folio}",
                    type="secondary",
                ):
                    st.session_state.current_folio = folio
                    go("Decisiones" if is_active else "Hoja verde")
            continue

        info_column, detail_column, status_column, actions_column = st.columns(
            [3.7, 4, 1.15, 1.7],
            **_COL_VA,
        )
        with info_column:
            H(
                '<div class="dashboard-portfolio-row">'
                '<div class="dashboard-company-lockup">'
                f'<span class="dashboard-company-avatar" aria-hidden="true">{esc(company_initial)}</span>'
                '<div class="dashboard-company-copy">'
                f'<div class="dashboard-row-title"><strong>{esc(record["company"])}</strong></div>'
                f'<div class="dashboard-record-folio">{esc(folio)}</div></div></div></div>'
            )
        with detail_column:
            activity_label = "Actividad" if record["last_activity_action"] else "Creado"
            H(
                '<div class="dashboard-row-details">'
                f'<span><strong>Periodo</strong> {esc(record["old_date"])} → {esc(record["new_date"])}</span>'
                f'<span><strong>Responsable</strong> {esc(record["owner_name"])}</span>'
                f'<span><strong>{activity_label}</strong> {esc(date_label)}</span></div>'
            )
        with status_column:
            H(status_html)
        with actions_column:
            action_columns = st.columns([1.1, 1])
            with action_columns[0]:
                if st.button(
                    "Abrir",
                    key=f"{key_prefix}_open_{folio}",
                    type="secondary",
                ):
                    st.session_state.current_folio = folio
                    go("Hoja verde")
            with action_columns[1]:
                actions = ["Decisiones", "Estados financieros", "Reporte gerencial"]
                if hasattr(st, "menu_button"):
                    secondary_action = st.menu_button(
                        "Más",
                        actions,
                        key=f"{key_prefix}_actions_{folio}",
                        help="Abrir otra sección de este análisis",
                        type="tertiary",
                        icon=":material/more_horiz:",
                    )
                else:
                    secondary_action = st.selectbox(
                        "Más acciones",
                        ["Selecciona"] + actions,
                        key=f"{key_prefix}_actions_{folio}",
                        label_visibility="collapsed",
                    )
                    if secondary_action == "Selecciona":
                        secondary_action = None
                if secondary_action:
                    st.session_state.current_folio = folio
                    go(secondary_action)


def empty_state(icon_name, title, text):
    H(f'<div class="empty"><div class="empty-ic">{icon(icon_name, 26)}</div><h3>{esc(title)}</h3><p>{esc(text)}</p></div>')


def stepper_html(current, steps):
    items = ""
    for i, name in enumerate(steps, 1):
        state = "done" if i < current else "now" if i == current else "todo"
        mark = icon("check", 14) if state == "done" else str(i)
        aria = ' aria-current="step"' if state == "now" else ""
        items += f'<li class="step {state}"{aria}><span class="step-dot">{mark}</span>{esc(name)}</li>'
    return f'<ol class="stepper" aria-label="Progreso del análisis">{items}</ol>'


def show_chart(fig, height=470):
    fig.update_layout(
        template="plotly_white", height=height, colorway=COLORWAY,
        font=dict(family="IBM Plex Sans, system-ui, sans-serif", color="#0F1B2D", size=13),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=84, b=8),
        title=dict(x=0, font=dict(size=20, family="Barlow Condensed, Arial Narrow, sans-serif", color="#0A2147")),
        legend=dict(orientation="h", yanchor="bottom", y=1.07, x=0, title_text=""),
        hoverlabel=dict(font_family="IBM Plex Sans, sans-serif"),
    )
    fig.update_xaxes(gridcolor="#E8ECF3", linecolor="#C3CDDD", zeroline=False)
    fig.update_yaxes(gridcolor="#E8ECF3", zeroline=False)
    st.plotly_chart(fig, **STRETCH, config={"displaylogo": False})


def brand_icon():
    """Icono de pestaña generado en código (sin emoji ni archivos externos)."""
    try:
        from PIL import Image, ImageDraw
        im = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((8, 8, 120, 120), radius=24, fill="#013E8F")
        for x, h in ((32, 24), (54, 42), (76, 60)):
            d.rectangle((x, 92 - h, x + 16, 92), fill="white")
        d.rectangle((28, 100, 100, 108), fill="#F2183A")
        return im
    except Exception:
        return None


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=brand_icon(),
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(THEME_CSS, unsafe_allow_html=True)

# Catálogo base basado en las cuentas que aparecen en la hoja verde.
CATALOGO = OrderedDict({
    "Activo circulante": [
        "Caja", "Bancos", "Inversiones temporales", "Clientes",
        "Documentos por cobrar", "Deudores diversos", "Inventarios",
        "Almacén", "Anticipo a proveedores", "IVA acreditable",
        "Pagos anticipados", "Otros activos circulantes"
    ],
    "Activo no circulante": [
        "Terrenos", "Edificios", "Maquinaria", "Mobiliario y equipo",
        "Equipo de cómputo", "Equipo de transporte", "Herramientas",
        "Depreciación acumulada", "Amortización acumulada", "Patentes",
        "Marcas", "Software", "Depósitos en garantía",
        "Inversiones permanentes", "Otros activos no circulantes"
    ],
    "Pasivo circulante": [
        "Proveedores", "Acreedores diversos", "Documentos por pagar",
        "Préstamos bancarios a corto plazo", "Impuestos por pagar",
        "IVA trasladado", "Sueldos por pagar", "Intereses por pagar",
        "Anticipos de clientes", "Otros pasivos circulantes"
    ],
    "Pasivo no circulante": [
        "Préstamos bancarios a largo plazo", "Hipotecas por pagar",
        "Documentos por pagar a largo plazo", "Obligaciones por pagar",
        "Arrendamientos a largo plazo", "Otros pasivos no circulantes"
    ],
    "Capital contable": [
        "Capital social", "Aportaciones para futuros aumentos",
        "Prima en emisión de acciones", "Reserva legal",
        "Utilidades retenidas", "Resultado del ejercicio",
        "Pérdidas acumuladas", "Otros componentes del capital"
    ],
    "Estado de resultados (opcional)": [
        "Ventas", "Devoluciones sobre ventas", "Costo de ventas",
        "Gastos de venta", "Gastos de administración",
        "Otros ingresos", "Otros gastos", "Gastos por intereses",
        "Impuestos a la utilidad", "Utilidad bruta",
        "Utilidad operativa", "Utilidad neta"
    ]
})

CATEGORIAS_BALANCE = [
    "Activo circulante", "Activo no circulante", "Pasivo circulante",
    "Pasivo no circulante", "Capital contable"
]
CUENTAS_CONTRA_ACTIVO = {"Depreciación acumulada", "Amortización acumulada"}
CUENTAS_RESULTADO = set(CATALOGO["Estado de resultados (opcional)"])

# --------------------------- Roles, archivos y bitácora ---------------------------

ROLE_LABEL = {"usuario": "Contador", "admin": "Administrador"}
DOC_KINDS = ["Estado financiero", "Balanza de comprobación", "Comprobante o soporte", "Otro"]
ALLOWED_EXT = {"pdf", "xlsx", "xls", "csv", "docx", "png", "jpg", "jpeg"}
MAX_MB = 10

NEW_TABLES = """
CREATE TABLE IF NOT EXISTS attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folio TEXT NOT NULL,
    filename TEXT NOT NULL,
    kind TEXT NOT NULL,
    size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    data BLOB NOT NULL,
    uploaded_by INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(folio) REFERENCES analyses(folio)
);
CREATE TABLE IF NOT EXISTS change_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folio TEXT NOT NULL,
    requester_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pendiente',
    resolver_id INTEGER,
    resolution_note TEXT,
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    FOREIGN KEY(folio) REFERENCES analyses(folio)
);
CREATE TABLE IF NOT EXISTS analysis_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folio TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL
);
"""


def analysis_for(folio, user):
    """El contador solo accede a sus análisis; el administrador, a todos."""
    if not folio:
        return None
    sql = ("SELECT a.*, u.username AS owner_name FROM analyses a "
           "JOIN users u ON u.id=a.owner_id WHERE a.folio=?")
    args = [str(folio).strip()]
    if user["role"] != "admin":
        sql += " AND a.owner_id=?"
        args.append(user["id"])
    with db() as con:
        return con.execute(sql, args).fetchone()


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def log_event(folio, user_id, action, detail="", con=None):
    sql = "INSERT INTO analysis_log(folio,user_id,action,detail,created_at) VALUES(?,?,?,?,?)"
    args = (folio, user_id, action, str(detail)[:1500], now_iso())
    if con is not None:
        con.execute(sql, args)
    else:
        with db() as c:
            c.execute(sql, args)


def safe_name(name):
    base = os.path.basename(str(name).replace("\\", "/"))
    return re.sub(r"[^\w.\- ()]", "_", base)[:120] or "archivo"


def validate_upload(f):
    """Devuelve un mensaje de error, o cadena vacía si el archivo es válido."""
    ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""
    if ext not in ALLOWED_EXT:
        return f"{f.name}: tipo de archivo no permitido."
    if f.size == 0:
        return f"{f.name}: el archivo está vacío."
    if f.size > MAX_MB * 1024 * 1024:
        return f"{f.name}: excede el máximo de {MAX_MB} MB."
    if ext == "pdf" and bytes(f.getbuffer()[:5]) != b"%PDF-":
        return f"{f.name}: no es un PDF válido."
    return ""


def add_attachment(con, folio, f, kind, user_id):
    data = f.getvalue()
    con.execute(
        "INSERT INTO attachments(folio,filename,kind,size,sha256,data,uploaded_by,created_at) VALUES(?,?,?,?,?,?,?,?)",
        (folio, safe_name(f.name), kind, len(data), hashlib.sha256(data).hexdigest(), data, user_id, now_iso())
    )
    log_event(folio, user_id, "Documento agregado", f"{safe_name(f.name)} ({kind})", con)


def flash():
    msg = st.session_state.pop("flash", None)
    if msg:
        (st.warning if st.session_state.pop("flash_warn", False) else st.success)(msg)


# --------------------------- Qué es cada razón financiera ---------------------------

RATIO_INFO = {
    "Razón circulante": ("Mide la capacidad de la empresa para pagar sus deudas de corto plazo con sus activos de corto plazo.",
                         "Mayor a 1: el activo circulante cubre el pasivo circulante. Un valor muy alto puede indicar recursos ociosos."),
    "Prueba ácida": ("Igual que la razón circulante, pero sin contar los inventarios, que son lo más lento de convertir en efectivo.",
                     "Mayor a 1: puede pagar sus deudas de corto plazo sin vender inventario."),
    "Razón de efectivo": ("Mide cuánto del pasivo de corto plazo podría pagarse hoy solo con caja y bancos.",
                          "Es la medida de liquidez más estricta; un valor bajo no es grave si la cobranza es constante."),
    "Capital de trabajo": ("Dinero que queda para operar después de pagar las deudas de corto plazo con los activos de corto plazo.",
                           "Positivo indica holgura operativa; negativo, presión de liquidez."),
    "Endeudamiento": ("Porcentaje de los activos que está financiado con deudas (pasivo total).",
                      "Entre más alto, mayor dependencia de acreedores y mayor riesgo financiero."),
    "Autonomía financiera": ("Porcentaje de los activos que está financiado con recursos propios (capital contable).",
                             "Entre más alto, mayor independencia de acreedores. Complementa al endeudamiento."),
    "Deuda a capital": ("Cuántos pesos de deuda tiene la empresa por cada peso de capital propio.",
                        "Mayor a 1: se debe más de lo que aportan los dueños."),
    "Margen bruto": ("Porcentaje de las ventas que queda después de pagar el costo de lo vendido.",
                     "Refleja la rentabilidad de los productos antes de los gastos de operación."),
    "Margen operativo": ("Porcentaje de las ventas que queda después del costo de ventas y los gastos de operación, antes de intereses e impuestos.",
                         "Indica qué tan rentable es la operación normal del negocio."),
    "Margen neto": ("Porcentaje de las ventas que se convierte en utilidad final, ya descontados costos, gastos, intereses e impuestos.",
                    "Indica cuánto gana la empresa por cada 100 pesos vendidos."),
    "ROA": ("Rendimiento sobre los activos: utilidad neta generada por cada 100 pesos invertidos en activos.",
            "Mide qué tan bien se aprovechan los activos para generar utilidades."),
    "ROE": ("Rendimiento sobre el capital: utilidad neta generada por cada 100 pesos aportados por los dueños.",
            "Mide el retorno para los propietarios; debe leerse junto con el endeudamiento."),
    "Rotación de activos": ("Cuántas veces las ventas del periodo equivalen al total de activos.",
                            "Mayor valor: la empresa usa sus activos con más eficiencia para vender."),
    "Rotación de inventarios": ("Cuántas veces se renueva el inventario en el periodo (costo de ventas entre inventarios).",
                                "Mayor valor: el inventario se vende más rápido. Muy bajo puede indicar mercancía detenida."),
    "Rotación de cuentas por cobrar": ("Cuántas veces en el periodo se cobra el saldo de clientes (ventas entre clientes).",
                                       "Mayor valor: cobranza más ágil."),
    "Rotación de proveedores": ("Cuántas veces en el periodo se paga el saldo de proveedores (aproximado con el costo de ventas).",
                                "Mayor valor: pagos más rápidos; menor valor: más plazo financiado por proveedores."),
    "Cobertura de intereses": ("Cuántas veces la utilidad operativa alcanza para pagar los intereses de la deuda.",
                               "Mayor a 1: la operación cubre los intereses. Valores bajos señalan riesgo."),
    "Solidez": ("Cuántos pesos de activo respaldan cada peso de deuda.",
                "Mayor a 1: los activos superan las deudas."),
    "Inmovilización de activos": ("Porcentaje del activo total que está invertido en activos de largo plazo (no circulantes).",
                                  "Un valor alto implica menos flexibilidad; depende mucho del giro de la empresa."),
}


# --------------------------- Flujo de efectivo (método indirecto) ---------------------------

CF_CASH = {"Caja", "Bancos"}
CF_FIN_CORTO = {"Préstamos bancarios a corto plazo"}


def cash_flow(df):
    """Estado de flujo de efectivo por método indirecto desde las variaciones del balance.

    Operación: utilidad neta + depreciación/amortización + cambios en capital de trabajo.
    Inversión: cambios en activos no circulantes e inversiones temporales.
    Financiamiento: deuda de largo plazo, préstamos de corto plazo y movimientos de capital.
    Efectivo = Caja + Bancos. Concilia solo si el balance cuadra en ambos periodos.
    """
    d = df.copy()
    d["Cambio"] = d["Reciente"] - d["Anterior"]
    ni = float(d.loc[d["Concepto"].str.casefold() == "utilidad neta", "Reciente"].sum())
    op, inv, fin = [], [], []
    if abs(ni) >= 0.005:
        op.append(("Utilidad neta del periodo", ni))

    contra = d[(d["Categoria"] == "Activo no circulante") & d["Concepto"].isin(CUENTAS_CONTRA_ACTIVO)]
    dep = float(contra["Reciente"].abs().sum() - contra["Anterior"].abs().sum())
    if abs(dep) >= 0.005:
        op.append(("Depreciación y amortización (sin efecto en efectivo)", dep))

    for _, r in d.iterrows():
        c, cat, ch = r["Concepto"], r["Categoria"], float(r["Cambio"])
        if abs(ch) < 0.005 or c in CF_CASH:
            continue
        word = "Aumento" if ch > 0 else "Disminución"
        if cat == "Activo circulante":
            (inv if c == "Inversiones temporales" else op).append((f"{word} en {c}", -ch))
        elif cat == "Activo no circulante" and c not in CUENTAS_CONTRA_ACTIVO:
            inv.append((f"{word} en {c}", -ch))
        elif cat == "Pasivo circulante":
            (fin if c in CF_FIN_CORTO else op).append((f"{word} en {c}", ch))
        elif cat == "Pasivo no circulante":
            fin.append((f"{word} en {c}", ch))

    d_cap = float(d.loc[d["Categoria"] == "Capital contable", "Cambio"].sum())
    other_cap = d_cap - ni
    if abs(other_cap) >= 0.005:
        label = ("Aportaciones, dividendos y otros movimientos de capital" if abs(ni) >= 0.005
                 else "Movimientos de capital (incluyen el resultado del periodo)")
        fin.append((label, other_cap))

    sections = []
    for title, items, sub_label in (
        ("Actividades de operación", op, "Flujo neto de actividades de operación"),
        ("Actividades de inversión", inv, "Flujo neto de actividades de inversión"),
        ("Actividades de financiamiento", fin, "Flujo neto de actividades de financiamiento"),
    ):
        sections.append((title, items, sub_label, float(sum(v for _, v in items))))
    net = sum(s[3] for s in sections)
    start = float(d.loc[d["Concepto"].isin(CF_CASH), "Anterior"].sum())
    end = float(d.loc[d["Concepto"].isin(CF_CASH), "Reciente"].sum())
    return {"sections": sections, "net": net, "start": start, "end": end,
            "diff": (end - start) - net, "ni": ni}


def acct(v):
    """Formato contable: negativos entre paréntesis."""
    return f"({abs(v):,.2f})" if v < -0.004 else f"{v:,.2f}"


def statement_table(rows, headers, focus_labels=None, focus_id=None):
    """rows: (tipo, etiqueta, [valores]); tipo = sec | item | tot | grand."""
    head = '<th scope="col">Concepto</th>' + "".join(f'<th scope="col" class="num">{esc(h)}</th>' for h in headers)
    body = ""
    normalized_focus = [_norm(label) for label in (focus_labels or [])]
    focus_id_written = False
    for kind, label, vals in rows:
        if kind == "sec":
            body += f'<tr class="sec"><td colspan="{len(headers) + 1}">{esc(label)}</td></tr>'
        else:
            cells = "".join(f'<td class="num">{"" if v is None else acct(v)}</td>' for v in vals)
            normalized_label = _norm(label)
            is_focus = any(
                normalized_label == focus or normalized_label.endswith(focus)
                for focus in normalized_focus
            )
            focus_class = " decision-focus" if is_focus else ""
            focus_aria = ' aria-label="Valor que originó la decisión"' if is_focus else ""
            row_id = (
                f' id="{esc(focus_id)}"'
                if is_focus and focus_id and not focus_id_written else ""
            )
            focus_id_written = focus_id_written or bool(row_id)
            body += f'<tr class="{kind}{focus_class}"{row_id}{focus_aria}><td>{esc(label)}</td>{cells}</tr>'
    H(f'<div class="stmt-wrap"><table class="stmt"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')


def cash_flow_pdf(sheet):
    cf = cash_flow(sheet)
    styles = getSampleStyleSheet()
    rows, bold = [["Concepto", "Importe"]], []
    for title, items, sub_label, sub in cf["sections"]:
        bold.append(len(rows)); rows.append([title, ""])
        for label, amt in items or [("Sin movimientos", None)]:
            rows.append(["    " + str(label)[:80], "" if amt is None else acct(amt)])
        bold.append(len(rows)); rows.append([sub_label, acct(sub)])
    for label, v in (("Aumento (disminución) neto de efectivo", cf["net"]),
                     ("Efectivo al inicio del periodo", cf["start"]),
                     ("Efectivo al final del periodo", cf["start"] + cf["net"])):
        bold.append(len(rows)); rows.append([label, acct(v)])
    t = Table(rows, colWidths=[6.4 * inch, 1.5 * inch], repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0A2147")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#DDE3EC")), ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ] + [("FONTNAME", (0, i), (-1, i), "Helvetica-Bold") for i in bold]
    t.setStyle(TableStyle(style))
    note = "Efectivo = Caja + Bancos. " + (
        "El flujo concilia con el balance." if abs(cf["diff"]) < 0.01
        else f"El flujo NO concilia con el balance (diferencia {cf['diff']:,.2f}).")
    return [Spacer(1, 14), Paragraph("Estado de flujo de efectivo (método indirecto)", styles["Heading2"]),
            t, Paragraph(note, styles["Italic"])]


def signature_block(record):
    names = [record["elaboro"] or record["owner_name"], record["reviso"] or "", record["autorizo"] or ""]
    data = [["", "", "", "", ""], [names[0], "", names[1], "", names[2]],
            ["Elaboró", "", "Revisó", "", "Autorizó"]]
    t = Table(data, colWidths=[2.6 * inch, .4 * inch, 2.6 * inch, .4 * inch, 2.6 * inch], rowHeights=[30, None, None])
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LINEABOVE", (0, 1), (0, 1), .6, colors.black), ("LINEABOVE", (2, 1), (2, 1), .6, colors.black),
        ("LINEABOVE", (4, 1), (4, 1), .6, colors.black),
        ("TEXTCOLOR", (0, 2), (-1, 2), colors.HexColor("#55657D")),
    ]))
    return KeepTogether([t])


# --------------------------- Base de datos y seguridad ---------------------------

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'usuario',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folio TEXT UNIQUE NOT NULL,
            owner_id INTEGER NOT NULL,
            company TEXT NOT NULL,
            rfc TEXT,
            activity TEXT,
            currency TEXT NOT NULL,
            comparison_type TEXT NOT NULL,
            old_date TEXT NOT NULL,
            new_date TEXT NOT NULL,
            accounts_json TEXT NOT NULL,
            adjustments_json TEXT NOT NULL DEFAULT '{}',
            ratios_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            FOREIGN KEY(owner_id) REFERENCES users(id)
        );
        """)
        cols = {r["name"] for r in con.execute("PRAGMA table_info(analyses)")}
        for col in ("elaboro", "reviso", "autorizo"):
            if col not in cols:
                con.execute(f"ALTER TABLE analyses ADD COLUMN {col} TEXT NOT NULL DEFAULT ''")
        con.executescript(NEW_TABLES)


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 400000
    ).hex()
    return hashed, salt


def check_password(password, stored_hash, salt):
    computed, _ = password_hash(password, salt)
    return secrets.compare_digest(computed, stored_hash)


def get_user(username):
    with db() as con:
        return con.execute(
            "SELECT * FROM users WHERE username=? AND active=1",
            (username.strip(),)
        ).fetchone()


def add_user(username, password, role="usuario"):
    username = username.strip()
    if len(username) < 3:
        raise ValueError("El usuario debe tener al menos 3 caracteres.")
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")
    hashed, salt = password_hash(password)
    with db() as con:
        con.execute(
            "INSERT INTO users(username,password_hash,salt,role,created_at) VALUES(?,?,?,?,?)",
            (username, hashed, salt, role, datetime.now().isoformat(timespec="seconds"))
        )


def owner_analysis(folio, owner_id):
    with db() as con:
        return con.execute(
            "SELECT * FROM analyses WHERE folio=? AND owner_id=?",
            (folio.strip(), owner_id)
        ).fetchone()


# --------------------------- Funciones financieras ---------------------------

def money(value, currency="MXN"):
    try:
        return f"{currency} ${float(value):,.2f}"
    except (TypeError, ValueError):
        return f"{currency} $0.00"


def base_accounts():
    return [
        {"Concepto": concept, "Categoria": category, "Anterior": 0.0, "Reciente": 0.0}
        for category, concepts in CATALOGO.items()
        for concept in concepts
    ]


def clean_accounts(data):
    df = pd.DataFrame(data).copy()
    for col in ["Concepto", "Categoria"]:
        if col not in df:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str).str.strip()
    for col in ["Anterior", "Reciente"]:
        if col not in df:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df = df[df["Concepto"] != ""].copy()
    df = df[df["Categoria"].isin(CATALOGO.keys())].copy()
    # Si se repite un concepto, se conserva la última captura.
    df = df.drop_duplicates(subset=["Concepto"], keep="last")
    df["Cambio"] = df["Reciente"] - df["Anterior"]
    df["Aumento"] = df["Cambio"].clip(lower=0)
    df["Disminucion"] = (-df["Cambio"]).clip(lower=0)
    return df.reset_index(drop=True)

# --------------------------- Lectura automática de archivos ---------------------------

def _norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = re.sub(r"\(\s*[-−]\s*\)", " ", s)
    s = re.sub(r"[^a-zA-Z0-9 ]", " ", s).lower()
    return re.sub(r"\s+", " ", s).strip()


_ALIAS = {
    "cuentas por cobrar": "Clientes", "cuentas por pagar": "Proveedores", "inventario": "Inventarios",
    "efectivo": "Caja", "ventas netas": "Ventas", "ingresos": "Ventas", "iva por acreditar": "IVA acreditable",
    "equipo de computo": "Equipo de cómputo", "gastos de operacion": "Gastos de administración",
    "ingresos por servicios": "Ventas", "costo de venta": "Costo de ventas",
    "gastos de renta": "Gastos de administración", "gastos de sueldos": "Gastos de administración",
    "gastos de servicio": "Gastos de administración", "gastos de servicios": "Gastos de administración",
    "gastos de depreciacion": "Gastos de administración", "gastos de depreciacin": "Gastos de administración",
    "utilidad perdida neta": "Utilidad neta", "perdida del ejercicio": "Resultado del ejercicio",
    "utilidad prdida neta": "Utilidad neta", "prdida del ejercicio": "Resultado del ejercicio",
    "prestamos bancarios por pagar": "Préstamos bancarios a corto plazo",
    "prstamos bancarios por pagar": "Préstamos bancarios a corto plazo",
    "depreciacion acumulada de mobiliario y equipo": "Depreciación acumulada",
    "depreciacion acum de mobiliario y equipo": "Depreciación acumulada",
    "depreciacin acum de mobiliario y equipo": "Depreciación acumulada",
    "eq de transporte": "Equipo de transporte",
}
LOOKUP = {_norm(c): c for cs in CATALOGO.values() for c in cs}
LOOKUP.update({_norm(k): v for k, v in _ALIAS.items()})


def _to_num(tok):
    t = str(tok).strip().replace("$", "").replace("MXN", "").strip()
    if t in {"-", "—", "–"}:
        return 0.0
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").replace(",", "").strip()
    if t.startswith("-"):
        neg, t = True, t[1:]
    if not re.fullmatch(r"\d+(\.\d+)?", t):
        return None
    return -float(t) if neg else float(t)


def _from_cells(cells):
    """Fila de tabla: primera celda de texto = concepto; celdas numéricas siguientes = saldos."""
    label, nums = "", []
    for c in cells:
        v = _to_num(c)
        if v is None:
            label = label or c
        elif label:
            nums.append(v)
    return label, nums


def _from_line(line):
    """Línea de texto (PDF): el concepto va primero y los importes al final."""
    toks = [t for t in line.split() if t not in {"$", "MXN"}]
    nums = []
    while toks and _to_num(toks[-1]) is not None:
        nums.insert(0, _to_num(toks.pop()))
    return " ".join(toks), nums


def _stitch(lines):
    """Algunos PDF entregan cada columna en su propia línea: une el concepto con sus importes."""
    out = []
    for ln in lines:
        label, nums = _from_line(ln)
        if out:
            prev_label, prev_nums = _from_line(out[-1])
            prev_words = _norm(prev_label).split()
            ends_midphrase = bool(prev_words and prev_words[-1] in {"de", "del", "por", "a", "y", "con"})
            if prev_label and ends_midphrase and label and not nums and prev_nums:
                parts = out[-1].split()
                first_amount = next(i for i, part in enumerate(parts) if _to_num(part) is not None)
                parts[first_amount:first_amount] = ln.strip().split()
                out[-1] = " ".join(parts)
                continue
            if prev_label and ends_midphrase and nums and not prev_nums:
                out[-1] += " " + ln.strip()
                continue
            if nums and not label and prev_label and len(prev_nums) < 3:
                out[-1] += " " + ln.strip()
                continue
        out.append(ln)
    return out


def _read_pdf_statements(page_texts):
    """Prioriza estados comparativos e ignora pólizas, balanzas y flujos repetidos."""
    balance_accounts = set().union(*(set(CATALOGO[c]) for c in CATEGORIAS_BALANCE))
    income_accounts = set(CATALOGO["Estado de resultados (opcional)"])
    balances = []
    income_by_year = {}

    for text in page_texts:
        page_lines = _stitch(text.splitlines())
        normalized_page = _norm(text)
        if (
            "comparativo" in normalized_page
            and "balance" in normalized_page
            and "situacion financiera" in normalized_page
            and "total activo" in normalized_page
            and "capital contable" in normalized_page
        ):
            header = next(
                (line for line in page_lines if "comparativo" in _norm(line) and "balance" in _norm(line)),
                "",
            )
            years = re.findall(r"\b(?:19|20)\d{2}\b", _norm(header))
            recent_first = len(years) > 1 and int(years[0]) > int(years[1])
            page_rows, matched = [], set()
            for line in page_lines:
                label, nums = _from_line(line)
                key = LOOKUP.get(_norm(label))
                if key not in balance_accounts or len(nums) < 2 or key in matched:
                    continue
                old, new = (nums[1], nums[0]) if recent_first else (nums[0], nums[1])
                page_rows.append((label, [old, new]))
                matched.add(key)
            if len(matched) >= 3:
                balances.append((len(matched), page_rows))

        heading_index = None
        year = None
        for i, line in enumerate(page_lines):
            year_match = re.match(r"estado de resultados\s+(19\d{2}|20\d{2})\b", _norm(line))
            if year_match:
                heading_index = i
                year = int(year_match.group(1))
                break
        if heading_index is None or year is None:
            continue
        page_values = {}
        for line in page_lines[heading_index + 1:]:
            label, nums = _from_line(line)
            key = LOOKUP.get(_norm(label))
            if key not in income_accounts or not nums:
                continue
            value = nums[-1]
            if key in {"Ventas", "Gastos de administración"}:
                page_values[key] = page_values.get(key, 0.0) + value
            else:
                page_values[key] = value
        if len(page_values) >= 3:
            current = income_by_year.get(year)
            if current is None or len(page_values) > len(current):
                income_by_year[year] = page_values

    rows = []
    if balances:
        rows.extend(max(balances, key=lambda item: item[0])[1])

    years = sorted(income_by_year)
    if years:
        for year in years:
            values = income_by_year[year]
            if "Utilidad bruta" not in values and {"Ventas", "Costo de ventas"} <= values.keys():
                values["Utilidad bruta"] = (
                    values["Ventas"] - values.get("Devoluciones sobre ventas", 0.0)
                    - values["Costo de ventas"]
                )
            if "Utilidad operativa" not in values and "Utilidad bruta" in values:
                values["Utilidad operativa"] = (
                    values["Utilidad bruta"] - values.get("Gastos de venta", 0.0)
                    - values.get("Gastos de administración", 0.0)
                    + values.get("Otros ingresos", 0.0) - values.get("Otros gastos", 0.0)
                )
            if "Utilidad neta" not in values and "Utilidad operativa" in values:
                values["Utilidad neta"] = (
                    values["Utilidad operativa"] - values.get("Gastos por intereses", 0.0)
                    - values.get("Impuestos a la utilidad", 0.0)
                )
        old_year, new_year = (years[0], years[-1]) if len(years) > 1 else (None, years[0])
        concepts = set().union(*(income_by_year[year].keys() for year in years))
        for concept in sorted(concepts):
            old = income_by_year.get(old_year, {}).get(concept, 0.0) if old_year is not None else 0.0
            new = income_by_year.get(new_year, {}).get(concept, 0.0)
            rows.append((concept, [old, new]))

    return (rows, ["Anterior Reciente"]) if rows else None


def _read_rows(f):
    ext = f.name.rsplit(".", 1)[-1].lower()
    data = f.getvalue()
    rows, lines = [], []

    def add_cells(cells):
        cells = [str(c).strip() for c in cells if pd.notna(c) and str(c).strip()]
        if cells:
            rows.append(_from_cells(cells))
            lines.append(" ".join(cells))

    def add_line(line):
        if line.strip():
            rows.append(_from_line(line))
            lines.append(line)

    if ext in ("xlsx", "xls"):
        workbook = pd.read_excel(io.BytesIO(data), sheet_name=None, header=None)
        ignored_sheets = ("comprobacion", "indicadores", "razon", "ratio", "resumen", "variacion")
        selected_sheets = [
            (name, sheet) for name, sheet in workbook.items()
            if not any(term in _norm(name) for term in ignored_sheets)
        ] or list(workbook.items())
        candidates = []
        for name, sheet in selected_sheets:
            sheet_rows, sheet_lines, matched = [], [], set()
            for row in sheet.itertuples(index=False):
                cells = [str(cell).strip() for cell in row if pd.notna(cell) and str(cell).strip()]
                if not cells:
                    continue
                parsed = _from_cells(cells)
                sheet_rows.append(parsed)
                sheet_lines.append(" ".join(cells))
                key = LOOKUP.get(_norm(parsed[0]))
                if key and parsed[1]:
                    matched.add(key)
            preferred_name = _norm(name) in {"datos", "data", "balance", "estados financieros"}
            candidates.append((len(matched), preferred_name, sheet_rows, sheet_lines))
        candidates.sort(key=lambda candidate: (candidate[0], candidate[1]), reverse=True)
        for _, _, sheet_rows, sheet_lines in candidates:
            rows.extend(sheet_rows)
            lines.extend(sheet_lines)
    elif ext == "csv":
        text = data.decode("utf-8-sig", errors="replace")
        sheet = pd.read_csv(io.StringIO(text), header=None, sep=None, engine="python", dtype=str)
        for row in sheet.itertuples(index=False):
            add_cells(row)
    elif ext == "pdf":
        from pypdf import PdfReader
        page_texts = []
        for page in PdfReader(io.BytesIO(data)).pages:
            try:
                text = page.extract_text(extraction_mode="layout") or ""
            except TypeError:  # versiones antiguas de pypdf
                text = page.extract_text() or ""
            page_texts.append(text)
        statement_rows = _read_pdf_statements(page_texts)
        if statement_rows:
            rows, lines = statement_rows
        else:
            raw = [line for text in page_texts for line in text.splitlines()]
            for line in _stitch(raw):
                add_line(line)
    elif ext == "docx":
        from docx import Document
        d = Document(io.BytesIO(data))
        for p in d.paragraphs:
            add_line(p.text)
        for t in d.tables:
            for r in t.rows:
                add_cells([c.text for c in r.cells])
    else:
        raise ValueError("las imágenes no se pueden leer automáticamente")
    return rows, lines


def _recent_first(lines):
    """True si el encabezado del archivo pone la columna reciente antes que la anterior."""
    for line in lines:
        n = _norm(line)
        a, b = re.search(r"\b(reciente|actual)\b", n), re.search(r"\banterior\b", n)
        if a and b:
            return a.start() < b.start()
        years = re.findall(r"\b(?:19|20)\d{2}\b", n)
        if len(years) > 1:
            return int(years[0]) > int(years[1])
    return False


def extract_accounts(files):
    """Lee los archivos y devuelve (cuentas, n_leidas, no_reconocidas, avisos).
    Toma por cada concepto del catálogo los dos primeros importes: anterior y reciente."""
    found, unknown, warns = {}, [], []
    for f in files:
        try:
            rows, lines = _read_rows(f)
        except Exception as e:
            warns.append(f"{f.name}: no se pudo leer ({e}).")
            continue
        swap = _recent_first(lines)
        for label, nums in rows:
            key = LOOKUP.get(_norm(label))
            if not key:
                n = _norm(label)
                if nums and len(n) > 2 and not n.startswith("total"):
                    unknown.append(label)
                continue
            if not nums:
                continue
            old, new = (0.0, nums[0]) if len(nums) == 1 else (nums[0], nums[1])
            if swap and len(nums) > 1:
                old, new = new, old
            if key == "Resultado del ejercicio" and "perdida del ejercicio" in _norm(label):
                values = (-abs(old), -abs(new))
            elif key in {"Utilidad bruta", "Utilidad operativa", "Utilidad neta"}:
                values = (old if old < 0 else abs(old), new if new < 0 else abs(new))
            else:
                values = (abs(old), abs(new))
            if key in found:
                if any(abs(a - b) >= 0.01 for a, b in zip(found[key], values)):
                    warns.append(
                        f"{key}: aparece más de una vez con importes distintos; "
                        "se conservó la primera lectura."
                    )
                continue
            found[key] = values
    accounts = base_accounts()
    for a in accounts:
        if a["Concepto"] in found:
            a["Anterior"], a["Reciente"] = found[a["Concepto"]]
    return accounts, len(found), unknown, warns


def merge_imported_accounts(existing, imported):
    """Aplica saldos importados sin borrar cuentas manuales ni conceptos personalizados."""
    merged = [dict(account) for account in existing]
    positions = {account["Concepto"].casefold(): i for i, account in enumerate(merged)}
    applied = 0
    for account in imported:
        old, new = float(account["Anterior"]), float(account["Reciente"])
        if not old and not new:
            continue
        key = account["Concepto"].casefold()
        if key in positions:
            merged[positions[key]]["Anterior"] = old
            merged[positions[key]]["Reciente"] = new
        else:
            positions[key] = len(merged)
            merged.append(dict(account))
        applied += 1
    return merged, applied


def read_workbook_support(files):
    support = {"checks": [], "indicators": [], "warnings": []}
    for upload in files:
        if upload.name.rsplit(".", 1)[-1].lower() not in ("xlsx", "xls"):
            continue
        try:
            workbook = pd.read_excel(io.BytesIO(upload.getvalue()), sheet_name=None, header=None)
        except (ValueError, OSError, zipfile.BadZipFile) as exc:
            support["warnings"].append(f"{upload.name}: no se pudieron leer las hojas auxiliares ({exc}).")
            continue

        for sheet_name, sheet in workbook.items():
            sheet_key = _norm(sheet_name)
            if "comprobacion" in sheet_key:
                sheet_type = "checks"
            elif "indicador" in sheet_key:
                sheet_type = "indicators"
            else:
                continue

            header_index = None
            headers = []
            for index, row in sheet.iterrows():
                candidate = ["" if pd.isna(value) else str(value).strip() for value in row.tolist()]
                candidate_keys = [_norm(value) for value in candidate]
                has_label = candidate_keys and candidate_keys[0] in {"concepto", "indicador"}
                period_columns = [
                    i for i, value in enumerate(candidate_keys)
                    if i and (
                        re.search(r"\b(?:19|20)\d{2}\b", value)
                        or value in {"anterior", "reciente", "actual"}
                    )
                ]
                if has_label and len(period_columns) >= 2:
                    header_index, headers = index, candidate
                    break

            if header_index is None:
                support["warnings"].append(
                    f"{upload.name}, hoja {sheet_name}: no se encontró el encabezado de periodos."
                )
                continue

            period_columns = [
                i for i, value in enumerate(headers)
                if i and (
                    re.search(r"\b(?:19|20)\d{2}\b", _norm(value))
                    or _norm(value) in {"anterior", "reciente", "actual"}
                )
            ][:2]
            variation_column = next(
                (i for i, value in enumerate(headers) if "variacion" in _norm(value)), None
            )
            state_column = next(
                (i for i, value in enumerate(headers) if "estado" in _norm(value)), None
            )
            reading_column = next(
                (i for i, value in enumerate(headers) if "lectura" in _norm(value)), None
            )

            for _, row in sheet.iloc[header_index + 1:].iterrows():
                cells = row.tolist()
                label = "" if not cells or pd.isna(cells[0]) else str(cells[0]).strip()
                if not label or len(cells) <= max(period_columns):
                    continue
                old, recent = (_to_num(cells[i]) for i in period_columns)
                if old is None or recent is None:
                    continue
                if sheet_type == "checks":
                    state = ""
                    if state_column is not None and state_column < len(cells) and not pd.isna(cells[state_column]):
                        state = str(cells[state_column]).strip()
                    support["checks"].append({
                        "Archivo": upload.name,
                        "Comprobación": label,
                        "Anterior": old,
                        "Reciente": recent,
                        "Estado del archivo": state,
                    })
                else:
                    variation = (
                        _to_num(cells[variation_column])
                        if variation_column is not None and variation_column < len(cells)
                        else None
                    )
                    reading = (
                        str(cells[reading_column]).strip()
                        if reading_column is not None
                        and reading_column < len(cells)
                        and not pd.isna(cells[reading_column])
                        else ""
                    )
                    support["indicators"].append({
                        "Archivo": upload.name,
                        "Indicador": label,
                        "Anterior": old,
                        "Reciente": recent,
                        "Variación": variation,
                        "Lectura del archivo": reading,
                    })
    return support


def validate_workbook_support(support, accounts):
    df = clean_accounts(accounts)
    periods = {period: totals(df, period) for period in ("Anterior", "Reciente")}

    def account_value(name, period):
        matching = df.loc[df["Concepto"].str.casefold() == name.casefold(), period]
        return float(matching.sum()) if not matching.empty else 0.0

    def derived_values(period):
        current = periods[period]
        sales = current["Ventas"]
        returns = account_value("Devoluciones sobre ventas", period)
        selling_expenses = account_value("Gastos de venta", period)
        admin_expenses = account_value("Gastos de administración", period)
        other_income = account_value("Otros ingresos", period)
        other_expenses = account_value("Otros gastos", period)
        taxes = account_value("Impuestos a la utilidad", period)
        gross = sales - returns - current["Costo de ventas"]
        operating = (
            gross - selling_expenses - admin_expenses + other_income - other_expenses
        )
        net = operating - current["Gastos por intereses"] - taxes
        return {
            "Activo circulante": current["Activo circulante"],
            "Activo no circulante": current["Activo no circulante"],
            "Activo total": current["Activo total"],
            "Pasivo circulante": current["Pasivo circulante"],
            "Pasivo no circulante": current["Pasivo no circulante"],
            "Pasivo total": current["Pasivo total"],
            "Capital contable": current["Capital total"],
            "Pasivo total + Capital contable": current["Pasivo más capital"],
            "Diferencia (Activo total − Pasivo − Capital)": (
                current["Activo total"] - current["Pasivo más capital"]
            ),
            "Utilidad bruta calculada (Ventas − Devoluciones − Costo)": gross,
            "Utilidad bruta en Datos": current["Utilidad bruta"],
            "Diferencia utilidad bruta": gross - current["Utilidad bruta"],
            "Utilidad operativa calculada": operating,
            "Utilidad operativa en Datos": current["Utilidad operativa"],
            "Diferencia utilidad operativa": operating - current["Utilidad operativa"],
            "Utilidad neta calculada": net,
            "Utilidad neta en Datos": current["Utilidad neta"],
            "Diferencia utilidad neta": net - current["Utilidad neta"],
            "Diferencia Resultado del ejercicio − Utilidad neta": (
                account_value("Resultado del ejercicio", period) - current["Utilidad neta"]
            ),
        }

    check_values = {
        period: {_norm(label): value for label, value in derived_values(period).items()}
        for period in periods
    }

    def close(actual, expected, tolerance=0.01):
        return abs(actual - expected) <= max(tolerance, abs(expected) * 1e-9)

    checks = []
    for check in support["checks"]:
        key = _norm(check["Comprobación"])
        expected_old = check_values["Anterior"].get(key)
        expected_recent = check_values["Reciente"].get(key)
        state = _norm(check["Estado del archivo"])
        state_ok = not state or state in {"ok", "correcto", "correcta", "cuadra", "cuadrado"}
        if expected_old is None or expected_recent is None:
            validation = "Sin cotejo"
        elif (
            close(check["Anterior"], expected_old)
            and close(check["Reciente"], expected_recent)
            and state_ok
        ):
            validation = "Coincide"
        else:
            validation = "Revisar"
        checks.append({**check, "Cotejo FINOVA": validation})

    def indicator_values(period):
        current = periods[period]
        sales = current["Ventas"]
        short_debt = account_value("Préstamos bancarios a corto plazo", period)
        long_debt = account_value("Préstamos bancarios a largo plazo", period)
        return {
            "razon circulante veces": (
                current["Activo circulante"] / current["Pasivo circulante"]
                if current["Pasivo circulante"] else 0.0
            ),
            "efectivo caja bancos": current["Efectivo"],
            "clientes": account_value("Clientes", period),
            "inventarios": account_value("Inventarios", period),
            "deuda bancaria total": short_debt + long_debt,
            "prestamos a corto plazo": short_debt,
            "ventas": sales,
            "costo de ventas ventas": current["Costo de ventas"] / sales if sales else 0.0,
            "margen bruto utilidad bruta ventas": current["Utilidad bruta"] / sales if sales else 0.0,
            "devoluciones ventas": (
                account_value("Devoluciones sobre ventas", period) / sales if sales else 0.0
            ),
            "margen operativo": current["Utilidad operativa"] / sales if sales else 0.0,
            "margen neto": current["Utilidad neta"] / sales if sales else 0.0,
            "gastos por intereses": current["Gastos por intereses"],
        }

    expected_indicators = {
        period: indicator_values(period) for period in periods
    }
    ratio_keys = {
        "razon circulante veces", "costo de ventas ventas",
        "margen bruto utilidad bruta ventas", "devoluciones ventas",
        "margen operativo", "margen neto",
    }
    indicators = []
    for indicator in support["indicators"]:
        key = _norm(indicator["Indicador"])
        old_value = expected_indicators["Anterior"].get(key)
        recent_value = expected_indicators["Reciente"].get(key)
        if old_value is None or recent_value is None:
            validation = "Sin cotejo"
        else:
            variation = (
                recent_value - old_value if key in ratio_keys
                else (recent_value - old_value) / abs(old_value) if old_value else 0.0
            )
            tolerance = 1e-6 if key in ratio_keys else 0.01
            source_variation = indicator["Variación"]
            validation = (
                "Coincide"
                if close(indicator["Anterior"], old_value, tolerance)
                and close(indicator["Reciente"], recent_value, tolerance)
                and source_variation is not None
                and close(source_variation, variation, 1e-6)
                else "Revisar"
            )
        indicators.append({**indicator, "Cotejo FINOVA": validation})

    return {**support, "checks": checks, "indicators": indicators}


def import_draft_uploads(upload_key):
    uploads = st.session_state.get(upload_key) or []
    if not uploads:
        return False

    upload_errors = [error for error in (validate_upload(upload) for upload in uploads) if error]
    if upload_errors:
        st.session_state.draft_import_feedback = {
            "error": " ".join(upload_errors),
            "unknown": [],
            "warnings": [],
        }
        return False

    imported, n_found, unknown, warns = extract_accounts(uploads)
    if not n_found:
        st.session_state.draft_import_feedback = {
            "error": "No se encontraron cuentas reconocibles en los archivos. "
                     "Verifica que incluyan nombres de cuentas y sus saldos.",
            "unknown": unknown[:5],
            "warnings": warns[:5],
        }
        return False

    existing = st.session_state.get("draft_accounts", base_accounts())
    merged, applied = merge_imported_accounts(existing, imported)
    support = validate_workbook_support(
        read_workbook_support(uploads), imported)
    st.session_state.draft_accounts = merged
    st.session_state.draft_workbook_support = support
    st.session_state.draft_edit_version = st.session_state.get("draft_edit_version", 0) + 1
    st.session_state.draft_import_feedback = {
        "found": n_found,
        "applied": applied,
        "missing": max(0, len(imported) - n_found),
        "unknown": unknown[:5],
        "warnings": warns[:5],
    }
    return True


def totals(df, period):
    """Totales calculados desde las cuentas individuales; evita sumar totales duplicados."""
    result = {}
    for cat in CATALOGO:
        result[cat] = float(df.loc[df["Categoria"] == cat, period].sum())

    # Depreciación/amortización acumulada son cuentas correctoras: reducen el activo no
    # circulante aunque se capturen con signo positivo (la categoría las sumó, por eso se
    # retira su valor firmado y se resta su valor absoluto).
    is_contra = (df["Categoria"] == "Activo no circulante") & df["Concepto"].isin(CUENTAS_CONTRA_ACTIVO)
    result["Activo no circulante"] -= float(df.loc[is_contra, period].sum() + df.loc[is_contra, period].abs().sum())
    result["Activo total"] = result["Activo circulante"] + result["Activo no circulante"]
    result["Pasivo total"] = result["Pasivo circulante"] + result["Pasivo no circulante"]
    result["Capital total"] = result["Capital contable"]
    result["Pasivo más capital"] = result["Pasivo total"] + result["Capital total"]
    result["Capital de trabajo"] = result["Activo circulante"] - result["Pasivo circulante"]

    def account(name):
        found = df.loc[df["Concepto"].str.casefold() == name.casefold(), period]
        return float(found.sum()) if not found.empty else 0.0

    result["Caja"] = account("Caja")
    result["Bancos"] = account("Bancos")
    result["Clientes"] = account("Clientes")
    result["Inventarios"] = account("Inventarios") + account("Almacén")
    result["Proveedores"] = account("Proveedores")
    result["Ventas"] = account("Ventas")
    result["Costo de ventas"] = account("Costo de ventas")
    result["Utilidad bruta"] = account("Utilidad bruta")
    result["Utilidad operativa"] = account("Utilidad operativa")
    result["Utilidad neta"] = account("Utilidad neta")
    result["Gastos por intereses"] = account("Gastos por intereses")
    result["Efectivo"] = result["Caja"] + result["Bancos"]
    return result


def intelligent_recommendations(df, old_totals, new_totals, currency="MXN"):
    """Genera recomendaciones transparentes a partir de cambios en cuentas y totales."""
    recommendations = []
    old_sales, sales = old_totals["Ventas"], new_totals["Ventas"]
    old_assets, assets = old_totals["Activo total"], new_totals["Activo total"]
    old_liabilities, liabilities = old_totals["Pasivo total"], new_totals["Pasivo total"]
    materiality = max(1.0, max(abs(assets), abs(sales), abs(liabilities)) * 0.01)

    def amount(value):
        return money(value, currency)

    def growth(old_value, new_value):
        if abs(old_value) < 0.01:
            return None
        return (new_value - old_value) / abs(old_value) * 100

    def trend(old_value, new_value):
        pct = growth(old_value, new_value)
        if pct is None:
            return f"pasó de {amount(old_value)} a {amount(new_value)}"
        return f"cambió de {amount(old_value)} a {amount(new_value)} ({pct:+.1f}%)"

    def add(priority, title, detection, importance, decision):
        recommendations.append({
            "Prioridad": priority,
            "Recomendación": title,
            "Qué detectó": detection,
            "Por qué importa": importance,
            "Decisión sugerida": decision,
        })

    # La consistencia del balance debe verificarse antes de tomar decisiones.
    balance_gaps = []
    for label, totals_for_period in (("anterior", old_totals), ("reciente", new_totals)):
        gap = totals_for_period["Activo total"] - totals_for_period["Pasivo más capital"]
        if abs(gap) >= 0.01:
            balance_gaps.append(f"periodo {label}: diferencia de {amount(gap)}")
    if balance_gaps:
        add(
            "Atención", "Conciliar el balance antes de decidir",
            "El balance no cuadra (" + "; ".join(balance_gaps) + ").",
            "Un saldo mal clasificado o incompleto puede distorsionar liquidez, deuda y rentabilidad.",
            "Revisar captura, clasificación y saldos de apertura; confirmar que activo = pasivo + capital.",
        )

    if sales > 0 and old_sales > 0 and sales < old_sales and old_sales - sales >= materiality:
        add(
            "Atención", "Recuperar ventas",
            f"Las ventas {trend(old_sales, sales)}.",
            "Una reducción relevante de ingresos puede presionar márgenes y flujo para cubrir costos fijos.",
            "Identificar productos, clientes o canales que explican la caída y acordar acciones comerciales medibles.",
        )
    elif sales > old_sales and sales - old_sales >= materiality:
        add(
            "Oportunidad", "Aprovechar el crecimiento de ventas",
            f"Las ventas {trend(old_sales, sales)}.",
            "El crecimiento es sostenible solo si se convierte en margen y efectivo, no únicamente en saldos por cobrar.",
            "Replicar los canales o productos que crecieron y monitorear su margen, cobranza y capacidad operativa.",
        )

    old_inventory, inventory = old_totals["Inventarios"], new_totals["Inventarios"]
    sales_growth = growth(old_sales, sales)
    inventory_growth = growth(old_inventory, inventory)
    if inventory - old_inventory >= materiality and (
        (sales_growth is not None and inventory_growth is not None and inventory_growth > sales_growth + 5)
        or (sales_growth is None and sales <= materiality)
        or (sales_growth is not None and sales_growth < 0)
    ):
        add(
            "Atención", "Ajustar compras y niveles de inventario",
            f"Inventarios {trend(old_inventory, inventory)}; las ventas {trend(old_sales, sales)}.",
            "El inventario que crece más rápido que la venta inmoviliza recursos y puede elevar costos de almacenamiento u obsolescencia.",
            "Revisar antigüedad y rotación por producto; reducir compras de lento movimiento y definir mínimos según demanda.",
        )

    old_receivables, receivables = old_totals["Clientes"], new_totals["Clientes"]
    if (receivables - old_receivables >= materiality
            and (sales - old_sales < 0 or receivables - old_receivables > max(0, sales - old_sales))):
        add(
            "Atención", "Acelerar la cobranza",
            f"Clientes {trend(old_receivables, receivables)}, frente a ventas {trend(old_sales, sales)}.",
            "El aumento de cuentas por cobrar absorbe efectivo y puede convertir ventas registradas en problemas de liquidez.",
            "Priorizar saldos vencidos, confirmar fechas de pago y revisar límites de crédito y condiciones para nuevos pedidos.",
        )
    elif old_receivables - receivables >= materiality and sales >= old_sales:
        add(
            "Oportunidad", "Conservar la mejora en cobranza",
            f"El saldo de clientes disminuyó de {amount(old_receivables)} a {amount(receivables)} mientras las ventas no bajaron.",
            "Cobrar sin frenar ventas libera efectivo para la operación.",
            "Mantener el seguimiento y las condiciones de crédito que produjeron la reducción del saldo.",
        )

    working_capital = new_totals["Capital de trabajo"]
    current_liabilities = new_totals["Pasivo circulante"]
    cash = new_totals["Efectivo"]
    current_ratio = (
        new_totals["Activo circulante"] / current_liabilities
        if current_liabilities > 0 else None
    )
    cash_ratio = cash / current_liabilities if current_liabilities > 0 else None
    if working_capital < 0 or (current_ratio is not None and current_ratio < 1):
        add(
            "Atención", "Proteger la liquidez de corto plazo",
            f"Capital de trabajo de {amount(working_capital)}"
            + (f" y razón circulante de {current_ratio:.2f}." if current_ratio is not None else "."),
            "Los activos circulantes no cubren los compromisos de corto plazo, lo que puede dificultar pagos oportunos.",
            "Preparar un calendario semanal de cobros y pagos; posponer desembolsos no esenciales y negociar plazos antes del vencimiento.",
        )
    elif current_liabilities > 0 and cash < current_liabilities * 0.2:
        add(
            "Atención", "Fortalecer la reserva de efectivo",
            f"Caja y bancos suman {amount(cash)} frente a pasivos circulantes de {amount(current_liabilities)}"
            + (f" (cobertura inmediata {cash_ratio:.2f})." if cash_ratio is not None else "."),
            "Aunque otros activos circulantes puedan cubrir obligaciones en papel, no todos se convierten en efectivo de inmediato.",
            "Proyectar entradas y salidas próximas, acelerar cobros y mantener una reserva para vencimientos prioritarios.",
        )
    if old_totals["Efectivo"] - cash >= materiality and old_totals["Efectivo"] > 0:
        add(
            "Atención", "Investigar la reducción de efectivo",
            f"Caja y bancos {trend(old_totals['Efectivo'], cash)}.",
            "Una reducción de efectivo puede anticipar presión para cubrir nómina, proveedores o deuda.",
            "Conciliar movimientos de caja y bancos y calendarizar pagos con base en los cobros confirmados.",
        )

    if assets > 0:
        debt_ratio = liabilities / assets
        old_debt_ratio = old_liabilities / old_assets if old_assets > 0 else None
        if debt_ratio >= 0.7:
            add(
                "Atención", "Contener el crecimiento de la deuda",
                f"El pasivo representa {debt_ratio:.1%} del activo"
                + (f", frente a {old_debt_ratio:.1%} en el periodo anterior." if old_debt_ratio is not None else "."),
                "Una mayor dependencia de acreedores reduce el margen para absorber caídas de ingresos o alzas de tasas.",
                "Evitar deuda nueva no esencial, revisar tasas y vencimientos, y priorizar el pago de las obligaciones más costosas.",
            )
        elif liabilities - old_liabilities >= materiality and (
            assets - old_assets < liabilities - old_liabilities
        ):
            add(
                "Atención", "Vincular nueva deuda con capacidad de pago",
                f"El pasivo aumentó {amount(liabilities - old_liabilities)} y los activos crecieron menos.",
                "La deuda que no se traduce en capacidad productiva o efectivo puede elevar el riesgo financiero.",
                "Identificar el uso de los recursos y validar que el flujo esperado cubra capital e intereses antes de contratar más.",
            )

    short_loans = {"Préstamos bancarios a corto plazo"}
    short_loan_old = float(df.loc[df["Concepto"].isin(short_loans), "Anterior"].sum())
    short_loan_new = float(df.loc[df["Concepto"].isin(short_loans), "Reciente"].sum())
    if short_loan_new - short_loan_old >= materiality:
        add(
            "Atención", "Revisar el vencimiento de préstamos de corto plazo",
            f"Préstamos bancarios de corto plazo {trend(short_loan_old, short_loan_new)}; "
            f"caja y bancos {trend(old_totals['Efectivo'], cash)}.",
            "Un mayor saldo de deuda inmediata concentra vencimientos y puede presionar el efectivo disponible.",
            "Armar un calendario de pagos y validar la cobertura con flujos previstos; negociar plazos antes del vencimiento.",
        )

    old_suppliers, suppliers = old_totals["Proveedores"], new_totals["Proveedores"]
    supplier_change = suppliers - old_suppliers
    if abs(supplier_change) >= materiality:
        if supplier_change > 0:
            add(
                "Revisar", "Gestionar el saldo con proveedores",
                f"Proveedores {trend(old_suppliers, suppliers)}.",
                "El aumento de cuentas por pagar puede anticipar vencimientos concentrados o dependencia de crédito comercial.",
                "Conciliar facturas y vencimientos; negociar un calendario sostenible sin perder descuentos por pronto pago.",
            )
        else:
            add(
                "Oportunidad", "Conservar la mejora con proveedores",
                f"El saldo de proveedores bajó de {amount(old_suppliers)} a {amount(suppliers)}.",
                "Una reducción relevante puede reflejar pagos oportunos, pero también consume efectivo.",
                "Confirmar que el pago no haya debilitado la caja y conservar las condiciones comerciales favorables.",
            )

    expense_accounts = (
        "Costo de ventas", "Gastos de venta", "Gastos de administración",
        "Otros gastos", "Gastos por intereses", "Impuestos a la utilidad",
    )
    old_expenses = sum(float(df.loc[df["Concepto"] == name, "Anterior"].sum()) for name in expense_accounts)
    expenses = sum(float(df.loc[df["Concepto"] == name, "Reciente"].sum()) for name in expense_accounts)
    expense_increase = expenses - old_expenses
    sales_increase = max(0.0, sales - old_sales)
    expense_growth = growth(old_expenses, expenses)
    expense_growth_outpaces_sales = (
        sales_growth is None
        or expense_growth is None
        or expense_growth > sales_growth + 3
        or expense_increase - sales_increase >= materiality
    )
    if expense_increase >= materiality and expense_growth_outpaces_sales:
        main_expenses = sorted(
            (
                (name, float(df.loc[df["Concepto"] == name, "Reciente"].sum())
                 - float(df.loc[df["Concepto"] == name, "Anterior"].sum()))
                for name in expense_accounts
            ),
            key=lambda item: item[1], reverse=True
        )
        drivers = [f"{name} (+{amount(delta)})" for name, delta in main_expenses if delta > 0]
        add(
            "Atención", "Controlar costos y gastos",
            f"Los costos y gastos incluidos aumentaron de {amount(old_expenses)} a {amount(expenses)}"
            + (f"; mayores aumentos: {', '.join(drivers)}." if drivers else "."),
            "Si el gasto crece más rápido que los ingresos, queda menos margen para operar e invertir.",
            "Comparar cada aumento contra presupuesto, separar gastos recurrentes y renegociar compras o partidas no esenciales.",
        )

    gross_profit = new_totals["Utilidad bruta"]
    operating_profit = new_totals["Utilidad operativa"]
    net_profit = new_totals["Utilidad neta"]
    if sales > 0 and new_totals["Costo de ventas"] > sales:
        add(
            "Atención", "Recuperar margen bruto",
            f"El costo de ventas ({amount(new_totals['Costo de ventas'])}) supera las ventas ({amount(sales)}).",
            "La actividad comercial no alcanza a cubrir el costo directo de lo vendido.",
            "Validar costos y devoluciones; revisar precios, mezcla de productos y condiciones de compra antes de aumentar volumen.",
        )
    elif gross_profit < 0 and sales > 0:
        add(
            "Atención", "Revisar la rentabilidad de los productos",
            f"La utilidad bruta reciente es {amount(gross_profit)} con ventas de {amount(sales)}.",
            "Un margen bruto negativo indica que los ingresos no cubren los costos directos.",
            "Analizar margen por producto y ajustar precio, costo de adquisición o catálogo según la demanda.",
        )
    elif (old_totals["Ventas"] > 0 and sales > 0
          and old_totals["Utilidad bruta"] - gross_profit >= materiality):
        old_gross_margin = old_totals["Utilidad bruta"] / old_totals["Ventas"] * 100
        gross_margin = gross_profit / sales * 100
        add(
            "Atención", "Detener el deterioro del margen bruto",
            f"La utilidad bruta bajó de {amount(old_totals['Utilidad bruta'])} a {amount(gross_profit)}; "
            f"el margen pasó de {old_gross_margin:.1f}% a {gross_margin:.1f}%.",
            "La empresa conserva menos ingreso después de cubrir el costo directo de sus ventas.",
            "Revisar cambios en precios, mezcla de productos, devoluciones y costos de compra para recuperar margen.",
        )
    if operating_profit < 0:
        add(
            "Atención", "Corregir la pérdida operativa",
            f"La utilidad operativa reciente es {amount(operating_profit)}.",
            "La operación ordinaria no genera recursos suficientes antes de intereses e impuestos.",
            "Priorizar acciones sobre los gastos operativos y líneas con margen negativo; dar seguimiento al resultado por periodo.",
        )
    if net_profit < 0:
        add(
            "Atención", "Detener la pérdida neta",
            f"La utilidad neta reciente es {amount(net_profit)}.",
            "Una pérdida sostenida consume capital y reduce la capacidad de financiar la operación.",
            "Desglosar el efecto operativo, financiero y fiscal; aprobar medidas correctivas con responsables y fechas.",
        )
    elif old_totals["Utilidad neta"] > 0 and net_profit < old_totals["Utilidad neta"] - materiality:
        add(
            "Atención", "Investigar la caída de utilidad",
            f"La utilidad neta bajó de {amount(old_totals['Utilidad neta'])} a {amount(net_profit)}.",
            "Menos utilidad limita la reinversión y puede anticipar presión en caja.",
            "Separar el cambio en ventas, costo, gastos e intereses para enfocar la corrección en sus principales causas.",
        )

    interest_change = new_totals["Gastos por intereses"] - old_totals["Gastos por intereses"]
    interest_growth = growth(old_totals["Gastos por intereses"], new_totals["Gastos por intereses"])
    if interest_change >= materiality or (
        interest_change > 0 and interest_growth is not None
        and sales_growth is not None and interest_growth > sales_growth + 3
    ):
        add(
            "Atención", "Reducir el costo financiero",
            f"Los gastos por intereses aumentaron de {amount(old_totals['Gastos por intereses'])} "
            f"a {amount(new_totals['Gastos por intereses'])}.",
            "Más intereses reducen directamente la utilidad y el efectivo disponible para la operación.",
            "Comparar tasas y comisiones vigentes, revisar pagos anticipados viables y negociar condiciones con acreedores.",
        )

    old_assets_noncurrent = old_totals["Activo no circulante"]
    assets_noncurrent = new_totals["Activo no circulante"]
    noncurrent_growth = growth(old_assets_noncurrent, assets_noncurrent)
    if (assets_noncurrent - old_assets_noncurrent >= materiality
            and (sales_growth is None or noncurrent_growth is None or noncurrent_growth > sales_growth + 10)):
        add(
            "Oportunidad", "Aprovechar mejor los activos de largo plazo",
            f"El activo no circulante {trend(old_assets_noncurrent, assets_noncurrent)}.",
            "Una inversión que crece sin un avance proporcional en ventas puede dejar capacidad productiva subutilizada.",
            "Medir utilización y rendimiento de los activos recientes antes de autorizar nuevas inversiones.",
        )

    specifically_reviewed = {
        "Caja", "Bancos", "Clientes", "Inventarios", "Almacén", "Proveedores",
        "Préstamos bancarios a corto plazo", *expense_accounts, "Ventas",
        "Utilidad bruta", "Utilidad operativa", "Utilidad neta",
    }
    other_movements = df[
        (~df["Concepto"].isin(specifically_reviewed))
        & (df["Cambio"].abs() >= materiality)
    ].copy()
    other_movements = other_movements.reindex(
        other_movements["Cambio"].abs().sort_values(ascending=False).index
    )
    for _, row in other_movements.iterrows():
        delta = float(row["Cambio"])
        category = row["Categoria"]
        if category.startswith("Activo"):
            importance = "El cambio modifica recursos comprometidos en activos y puede afectar la flexibilidad financiera."
            decision = "Validar el origen, uso y rendimiento del saldo antes de asignar más recursos a esta cuenta."
        elif category.startswith("Pasivo"):
            importance = "El movimiento puede modificar compromisos y necesidades futuras de pago."
            decision = "Confirmar su causa, vencimiento y costo; ajustar el calendario de pagos con base en el flujo previsto."
        elif category == "Capital contable":
            importance = "Los cambios de capital afectan el respaldo patrimonial y la capacidad de absorber pérdidas."
            decision = "Conciliar aportaciones, retiros y resultados para confirmar que el movimiento esté autorizado y correctamente registrado."
        else:
            importance = "El movimiento puede cambiar el resultado del periodo y merece explicación frente al presupuesto."
            decision = "Validar el soporte y su recurrencia; ajustar el presupuesto o la decisión operativa asociada."
        direction = "aumentó" if delta > 0 else "disminuyó"
        add(
            "Revisar", f"Validar el movimiento de {row['Concepto']}",
            f"{row['Concepto']} {direction} en {amount(abs(delta))} ({category}).",
            importance,
            decision,
        )

    return recommendations


def classify_flow(row, overrides):
    """Clasificación orientativa por naturaleza de la cuenta, editable por el usuario."""
    concept = row["Concepto"]
    category = row["Categoria"]
    change = float(row["Cambio"])
    if abs(change) < 0.005:
        return "Sin movimiento", "Sin movimiento"

    override = overrides.get(concept, "Automático")
    if override != "Automático":
        parts = override.split(" | ", 1)
        return parts[0], parts[1] if len(parts) > 1 else "Revisar"

    # Origen/aplicación por variación del balance:
    # activos: disminución = origen, aumento = aplicación.
    # pasivos/capital: aumento = origen, disminución = aplicación.
    if category.startswith("Activo"):
        origin = change < 0
    elif category.startswith("Pasivo") or category == "Capital contable":
        origin = change > 0
    else:
        # Estado de resultados no se clasifica como cambio de balance.
        return "Revisar", "Revisar"

    source_use = "Origen" if origin else "Aplicación"

    # Actividad por naturaleza de la cuenta.
    if category == "Activo no circulante":
        activity = "Inversión"
    elif category == "Pasivo no circulante":
        activity = "Financiamiento"
    elif category == "Capital contable":
        activity = "Financiamiento"
    elif category in ("Activo circulante", "Pasivo circulante"):
        activity = "Operación"
    else:
        activity = "Revisar"

    if concept in CUENTAS_CONTRA_ACTIVO:
        activity = "Inversión"
    return source_use, activity


def green_sheet(df, overrides):
    out = df.copy()
    classifications = out.apply(lambda r: classify_flow(r, overrides), axis=1)
    out["Origen / Aplicación"] = [x[0] for x in classifications]
    out["Actividad"] = [x[1] for x in classifications]
    return out


RATIO_DEFS = OrderedDict({
    "Razón circulante": ("Activo circulante / Pasivo circulante", "veces"),
    "Prueba ácida": ("(Activo circulante - Inventarios) / Pasivo circulante", "veces"),
    "Razón de efectivo": ("(Caja + Bancos) / Pasivo circulante", "veces"),
    "Capital de trabajo": ("Activo circulante - Pasivo circulante", "moneda"),
    "Endeudamiento": ("Pasivo total / Activo total × 100", "%"),
    "Autonomía financiera": ("Capital contable / Activo total × 100", "%"),
    "Deuda a capital": ("Pasivo total / Capital contable", "veces"),
    "Margen bruto": ("Utilidad bruta / Ventas × 100", "%"),
    "Margen operativo": ("Utilidad operativa / Ventas × 100", "%"),
    "Margen neto": ("Utilidad neta / Ventas × 100", "%"),
    "ROA": ("Utilidad neta / Activo total × 100", "%"),
    "ROE": ("Utilidad neta / Capital contable × 100", "%"),
    "Rotación de activos": ("Ventas / Activo total", "veces"),
    "Rotación de inventarios": ("Costo de ventas / Inventarios", "veces"),
    "Rotación de cuentas por cobrar": ("Ventas / Clientes", "veces"),
    "Rotación de proveedores": ("Costo de ventas / Proveedores (aproximación)", "veces"),
    "Cobertura de intereses": ("Utilidad operativa / Gastos por intereses", "veces"),
    "Solidez": ("Activo total / Pasivo total", "veces"),
    "Inmovilización de activos": ("Activo no circulante / Activo total × 100", "%")
})


def ratio_recommendation(name, value, period_totals, currency="MXN"):
    if value is None:
        return {
            "Qué detectó": "La razón no se pudo calcular porque su denominador es cero o falta información.",
            "Por qué importa": "Sin un resultado válido no se puede evaluar esta dimensión financiera.",
            "Decisión sugerida": "Completar y validar las cuentas que intervienen en la fórmula antes de tomar decisiones.",
        }

    unit = RATIO_DEFS[name][1]
    displayed = money(value, currency) if unit == "moneda" else f"{value:,.2f} {unit}"
    if name == "Razón circulante":
        if value < 1:
            return {
                "Qué detectó": f"Hay {value:.2f} de activo circulante por cada peso de pasivo circulante.",
                "Por qué importa": "La cobertura contable de corto plazo es menor que las obligaciones registradas.",
                "Decisión sugerida": "Calendarizar cobros y pagos, acelerar cobranza y negociar vencimientos antes de adquirir deuda nueva.",
            }
        return {
            "Qué detectó": f"El activo circulante equivale a {value:.2f} veces el pasivo circulante.",
            "Por qué importa": "La cobertura total no confirma que los activos sean líquidos ni que estén disponibles al vencimiento.",
            "Decisión sugerida": "Revisar antigüedad de clientes e inventarios y cotejar fechas de cobro con vencimientos.",
        }
    if name == "Prueba ácida":
        if value < 1:
            return {
                "Qué detectó": f"Sin inventarios hay {value:.2f} de activo disponible por cada peso de pasivo circulante.",
                "Por qué importa": "La empresa depende de vender inventario para cubrir compromisos de corto plazo.",
                "Decisión sugerida": "Priorizar cobranza y efectivo; ajustar compras de lento movimiento y prever pagos próximos.",
            }
        return {
            "Qué detectó": f"El activo circulante sin inventarios equivale a {value:.2f} veces el pasivo circulante.",
            "Por qué importa": "La cobertura no depende por completo de vender existencias, pero los saldos por cobrar también deben ser cobrables.",
            "Decisión sugerida": "Mantener el seguimiento de vencimientos y validar la recuperabilidad de clientes y otros activos circulantes.",
        }
    if name == "Razón de efectivo":
        if value < 1:
            return {
                "Qué detectó": f"Caja y bancos cubren {value:.2f} veces el pasivo circulante.",
                "Por qué importa": "El efectivo disponible por sí solo no alcanza para liquidar todos los pasivos de corto plazo.",
                "Decisión sugerida": "Proyectar flujo semanal, asegurar cobros y reservar efectivo para nómina, impuestos y vencimientos prioritarios.",
            }
        return {
            "Qué detectó": f"Caja y bancos cubren {value:.2f} veces el pasivo circulante.",
            "Por qué importa": "Una cobertura alta brinda margen de pago, aunque mantener excedentes sin uso puede restar rendimiento.",
            "Decisión sugerida": "Separar la reserva operativa y destinar excedentes solo después de confirmar pagos e inversiones necesarias.",
        }
    if name == "Capital de trabajo":
        if value < 0:
            return {
                "Qué detectó": f"El capital de trabajo es negativo: {displayed}.",
                "Por qué importa": "Los pasivos circulantes superan los activos circulantes y pueden presionar la operación diaria.",
                "Decisión sugerida": "Reducir salidas no esenciales, acelerar cobranza y renegociar plazos para alinear pagos con entradas.",
            }
        return {
            "Qué detectó": f"El capital de trabajo es positivo: {displayed}.",
            "Por qué importa": "Este margen sostiene la operación, pero puede quedar inmovilizado en inventario o saldos vencidos.",
            "Decisión sugerida": "Asignar el excedente a necesidades operativas prioritarias y vigilar rotación de inventario y cobranza.",
        }
    if name == "Endeudamiento":
        if value >= 70:
            return {
                "Qué detectó": f"El pasivo financia {value:.2f}% del activo.",
                "Por qué importa": "La alta dependencia de acreedores reduce el margen para absorber caídas de ingresos o alzas de tasas.",
                "Decisión sugerida": "Limitar deuda no esencial, revisar vencimientos y tasas, y comparar el nivel con el sector y los contratos vigentes.",
            }
        return {
            "Qué detectó": f"El pasivo financia {value:.2f}% del activo.",
            "Por qué importa": "El porcentaje debe leerse junto con el costo, vencimiento y capacidad de pago de cada obligación.",
            "Decisión sugerida": "Monitorear deuda y flujo previsto; antes de financiar inversiones, validar que generen recursos para pagarla.",
        }
    if name == "Autonomía financiera":
        if period_totals["Capital total"] <= 0:
            return {
                "Qué detectó": f"La autonomía financiera es {value:.2f}% y el capital contable no es positivo.",
                "Por qué importa": "La falta de respaldo patrimonial puede limitar crédito y capacidad para absorber pérdidas.",
                "Decisión sugerida": "Conciliar pérdidas y aportaciones; preparar un plan de recuperación patrimonial antes de asumir nuevos compromisos.",
            }
        return {
            "Qué detectó": f"El capital contable financia {value:.2f}% del activo.",
            "Por qué importa": "Una base propia mayor reduce dependencia de acreedores, aunque su suficiencia depende del giro y riesgo del negocio.",
            "Decisión sugerida": "Comparar con periodos y empresas del sector y conservar utilidades para inversiones con rendimiento comprobable.",
        }
    if name == "Deuda a capital":
        if period_totals["Capital total"] <= 0:
            return {
                "Qué detectó": f"El capital contable es no positivo y la razón deuda a capital resulta {value:.2f}.",
                "Por qué importa": "La razón deja de ser una comparación útil cuando el patrimonio es nulo o negativo.",
                "Decisión sugerida": "Revisar pérdidas acumuladas y aportaciones; fortalecer capital y evaluar deuda con un flujo de pago realista.",
            }
        if value > 1:
            return {
                "Qué detectó": f"Hay {value:.2f} de pasivo por cada peso de capital contable.",
                "Por qué importa": "La deuda supera el respaldo de los propietarios y aumenta la exposición financiera.",
                "Decisión sugerida": "Priorizar obligaciones de mayor costo y evitar nuevos créditos salvo que su rendimiento y cobertura estén demostrados.",
            }
        return {
            "Qué detectó": f"Hay {value:.2f} de pasivo por cada peso de capital contable.",
            "Por qué importa": "La relación debe evaluarse junto con intereses, vencimientos y estabilidad del flujo.",
            "Decisión sugerida": "Mantener un calendario de servicio de deuda y comparar esta relación con el sector.",
        }
    if name in {"Margen bruto", "Margen operativo", "Margen neto"}:
        margin_type = {
            "Margen bruto": ("bruto", "precios y costos directos por producto"),
            "Margen operativo": ("operativo", "costos y gastos de operación"),
            "Margen neto": ("neto", "costos, gastos, intereses e impuestos"),
        }[name]
        if value < 0:
            return {
                "Qué detectó": f"El margen {margin_type[0]} es negativo: {value:.2f}%.",
                "Por qué importa": "Las ventas no están dejando el resultado positivo esperado en esta etapa del negocio.",
                "Decisión sugerida": f"Desglosar ventas y partidas que forman el margen; corregir {margin_type[1]} antes de impulsar volumen.",
            }
        return {
            "Qué detectó": f"El margen {margin_type[0]} es {value:.2f}%.",
            "Por qué importa": "El porcentaje muestra cuánto de cada venta queda en esta etapa y puede erosionarse con cambios de mezcla o costos.",
            "Decisión sugerida": f"Dar seguimiento por producto y periodo y controlar {margin_type[1]} contra presupuesto.",
        }
    if name == "ROA":
        if value < 0:
            return {
                "Qué detectó": f"El rendimiento sobre activos es negativo: {value:.2f}%.",
                "Por qué importa": "Los activos no están generando utilidad neta en el periodo medido.",
                "Decisión sugerida": "Identificar activos o líneas con bajo rendimiento y corregir margen y utilización antes de ampliar capacidad.",
            }
        return {
            "Qué detectó": f"El rendimiento sobre activos es {value:.2f}%.",
            "Por qué importa": "Mide el resultado obtenido con los recursos invertidos y debe compararse con periodos y sector.",
            "Decisión sugerida": "Revisar productividad de activos y priorizar inversiones cuyo rendimiento esperado supere su costo.",
        }
    if name == "ROE":
        if period_totals["Capital total"] <= 0:
            return {
                "Qué detectó": f"El capital contable no es positivo; el ROE de {value:.2f}% puede ser engañoso.",
                "Por qué importa": "Con patrimonio nulo o negativo, el rendimiento sobre capital no representa un retorno normal para los propietarios.",
                "Decisión sugerida": "Validar el patrimonio y las pérdidas acumuladas; no usar el ROE aislado para autorizar dividendos o deuda.",
            }
        if value < 0:
            return {
                "Qué detectó": f"El rendimiento sobre capital es negativo: {value:.2f}%.",
                "Por qué importa": "El resultado del periodo reduce el retorno para los propietarios y puede debilitar el patrimonio.",
                "Decisión sugerida": "Separar las causas de la pérdida y acordar medidas de recuperación con responsables y fechas.",
            }
        return {
            "Qué detectó": f"El rendimiento sobre capital es {value:.2f}%.",
            "Por qué importa": "El retorno debe interpretarse junto con el riesgo y el nivel de deuda.",
            "Decisión sugerida": "Comparar con periodos y sector y confirmar que el resultado provenga de operación sostenible, no de apalancamiento excesivo.",
        }
    if name == "Rotación de activos":
        return {
            "Qué detectó": f"Las ventas equivalen a {value:.2f} veces el activo total.",
            "Por qué importa": "La rotación indica cuánto ingreso se obtiene de los activos, pero depende del giro y del periodo.",
            "Decisión sugerida": "Comparar con el historial y el sector; identificar activos subutilizados y mejorar su uso antes de invertir en nuevos.",
        }
    if name == "Rotación de inventarios":
        return {
            "Qué detectó": f"El costo de ventas equivale a {value:.2f} veces el inventario.",
            "Por qué importa": "Una rotación lenta puede inmovilizar efectivo y aumentar riesgo de obsolescencia; la adecuada depende del ciclo del producto.",
            "Decisión sugerida": "Revisar antigüedad y rotación por producto y ajustar compras y niveles mínimos a la demanda y tiempos de reposición.",
        }
    if name == "Rotación de cuentas por cobrar":
        return {
            "Qué detectó": f"Las ventas equivalen a {value:.2f} veces el saldo de clientes.",
            "Por qué importa": "Una cobranza lenta absorbe efectivo; una comparación anual puede estar distorsionada si hay saldos finales en lugar de promedios.",
            "Decisión sugerida": "Comparar con los plazos de crédito y antigüedad de saldos; dar seguimiento a vencidos sin frenar ventas rentables.",
        }
    if name == "Rotación de proveedores":
        return {
            "Qué detectó": f"El costo de ventas equivale a {value:.2f} veces el saldo de proveedores.",
            "Por qué importa": "El indicador aproxima la velocidad de pago, pero el costo de ventas no sustituye las compras netas.",
            "Decisión sugerida": "Conciliar compras y vencimientos; pagar según flujo y preservar descuentos sin deteriorar la relación comercial.",
        }
    if name == "Cobertura de intereses":
        if value < 1:
            return {
                "Qué detectó": f"La utilidad operativa cubre {value:.2f} veces los gastos por intereses.",
                "Por qué importa": "La operación no genera suficiente resultado para cubrir el costo financiero del periodo.",
                "Decisión sugerida": "Negociar tasas o plazos, frenar deuda nueva no esencial y corregir gastos o márgenes que reducen la utilidad operativa.",
            }
        return {
            "Qué detectó": f"La utilidad operativa cubre {value:.2f} veces los gastos por intereses.",
            "Por qué importa": "La cobertura puede reducirse si caen ventas, suben tasas o vencen créditos.",
            "Decisión sugerida": "Mantener una proyección de servicio de deuda y probar escenarios de menor venta o mayor costo financiero.",
        }
    if name == "Solidez":
        if value < 1:
            return {
                "Qué detectó": f"Hay {value:.2f} de activo por cada peso de pasivo.",
                "Por qué importa": "El activo contable es menor que las obligaciones y aumenta el riesgo de solvencia.",
                "Decisión sugerida": "Conciliar pasivos y activos recuperables, proteger flujo y acordar un plan de reducción o reestructura de deuda.",
            }
        return {
            "Qué detectó": f"Hay {value:.2f} de activo por cada peso de pasivo.",
            "Por qué importa": "La cobertura patrimonial no garantiza que los activos puedan convertirse en efectivo a tiempo.",
            "Decisión sugerida": "Validar valor y liquidez de activos y planear pagos por vencimiento antes de comprometer recursos.",
        }
    return {
        "Qué detectó": f"Los activos no circulantes representan {value:.2f}% del activo total.",
        "Por qué importa": "Una mayor inversión de largo plazo reduce flexibilidad inmediata; el nivel adecuado depende del giro.",
        "Decisión sugerida": "Comparar con el sector y medir utilización y rendimiento antes de aprobar nuevas inversiones de largo plazo.",
    }


def enrich_ratio_recommendations(ratios, old_totals, new_totals, currency="MXN"):
    for ratio in ratios:
        recommendation = ratio.pop("Análisis inteligente", None)
        if not isinstance(ratio.get("Recomendación"), dict):
            period_totals = old_totals if ratio.get("Periodo") == "Anterior" else new_totals
            ratio["Recomendación"] = recommendation or ratio_recommendation(
                ratio["Razón"], ratio.get("Resultado"), period_totals, currency)
    return ratios


def decision_destination(recommendation):
    title = recommendation["Recomendación"].casefold()
    statement_keywords = (
        "balance", "venta", "margen", "utilidad", "pérdida",
        "costo", "gasto", "rentabilidad",
    )
    if any(keyword in title for keyword in statement_keywords):
        return "Estados financieros"
    return "Hoja verde"


def decision_highlight_context(recommendation, df):
    if recommendation.get("Indicador"):
        return [], []

    text = _norm(
        f"{recommendation['Recomendación']} {recommendation['Qué detectó']}"
    )
    words = set(text.split())
    stop_words = {"a", "al", "de", "del", "el", "la", "las", "los", "por", "y"}
    accounts = []
    for concept in df["Concepto"]:
        concept_words = set(_norm(concept).split()) - stop_words
        if concept_words and concept_words.issubset(words):
            accounts.append(concept)

    labels = list(accounts)
    title = _norm(recommendation["Recomendación"])
    if not accounts:
        if "balance" in title:
            labels.extend([
                "Total activo", "Total pasivo", "Total capital contable",
                "Total pasivo + capital contable",
            ])
        elif any(term in title for term in ("liquidez", "efectivo", "capital de trabajo")):
            current_accounts = df[df["Categoria"].isin(
                ["Activo circulante", "Pasivo circulante"]
            )]["Concepto"].tolist()
            accounts.extend(current_accounts)
            labels.extend(current_accounts)
            labels.extend(["Total activo circulante", "Total pasivo circulante"])
        elif any(term in title for term in ("deuda", "prestamo", "vencimiento")):
            liability_accounts = df[df["Categoria"].str.startswith("Pasivo")]["Concepto"].tolist()
            accounts.extend(liability_accounts)
            labels.extend(liability_accounts)
            labels.append("Total pasivo")
        elif any(term in title for term in ("activo", "inversion")):
            asset_accounts = df[df["Categoria"] == "Activo no circulante"]["Concepto"].tolist()
            accounts.extend(asset_accounts)
            labels.extend(asset_accounts)

    return list(dict.fromkeys(accounts)), list(dict.fromkeys(labels))


def highlight_decision_values(value):
    safe_value = esc(value)
    pattern = re.compile(
        r"(?<![\w])(?:MXN\s*)?\$?[-+]?\d[\d,]*(?:\.\d+)?%?(?![\w])",
        re.IGNORECASE,
    )
    return pattern.sub(
        lambda match: f'<mark class="decision-value">{match.group(0)}</mark>',
        safe_value,
    )


def calc_ratio(name, t, period_label, currency="MXN"):
    formulas = {
        "Razón circulante": (t["Activo circulante"], t["Pasivo circulante"]),
        "Prueba ácida": (t["Activo circulante"] - t["Inventarios"], t["Pasivo circulante"]),
        "Razón de efectivo": (t["Efectivo"], t["Pasivo circulante"]),
        "Capital de trabajo": (t["Capital de trabajo"], None),
        "Endeudamiento": (t["Pasivo total"], t["Activo total"]),
        "Autonomía financiera": (t["Capital total"], t["Activo total"]),
        "Deuda a capital": (t["Pasivo total"], t["Capital total"]),
        "Margen bruto": (t["Utilidad bruta"], t["Ventas"]),
        "Margen operativo": (t["Utilidad operativa"], t["Ventas"]),
        "Margen neto": (t["Utilidad neta"], t["Ventas"]),
        "ROA": (t["Utilidad neta"], t["Activo total"]),
        "ROE": (t["Utilidad neta"], t["Capital total"]),
        "Rotación de activos": (t["Ventas"], t["Activo total"]),
        "Rotación de inventarios": (t["Costo de ventas"], t["Inventarios"]),
        "Rotación de cuentas por cobrar": (t["Ventas"], t["Clientes"]),
        "Rotación de proveedores": (t["Costo de ventas"], t["Proveedores"]),
        "Cobertura de intereses": (t["Utilidad operativa"], t["Gastos por intereses"]),
        "Solidez": (t["Activo total"], t["Pasivo total"]),
        "Inmovilización de activos": (t["Activo no circulante"], t["Activo total"])
    }
    a, b = formulas[name]
    unit = RATIO_DEFS[name][1]
    if b is None:
        value = a
        substitution = f"{a:,.2f}"
    elif abs(b) < 1e-9:
        value = None
        substitution = f"{a:,.2f} / {b:,.2f}"
    else:
        value = a / b
        substitution = f"{a:,.2f} / {b:,.2f}"
        if unit == "%":
            value *= 100
            substitution += " × 100"

    if value is None:
        interpretation = "No calculable: el denominador es cero o falta información."
        display = "No calculable"
    else:
        display = f"{value:,.2f} {unit}"
        if name == "Razón circulante":
            interpretation = (
                f"Los activos circulantes equivalen a {value:.2f} veces el pasivo circulante. "
                + ("La cobertura contable es superior a 1. " if value >= 1 else
                   "La cobertura contable es inferior a 1; conviene revisar la liquidez. ")
                + "La conclusión debe considerar vencimientos y calidad de los activos."
            )
        elif name == "Prueba ácida":
            interpretation = (
                f"La cobertura excluyendo inventarios es de {value:.2f} veces. "
                "Un valor bajo puede indicar dependencia de la venta de inventarios."
            )
        elif unit == "%":
            interpretation = f"El indicador es {value:.2f}%. Su evaluación depende del sector, periodo y políticas contables."
        elif unit == "moneda":
            interpretation = f"Los recursos circulantes netos ascienden a {value:,.2f}."
        else:
            interpretation = f"El indicador es {value:.2f} veces. Compáralo con periodos anteriores y con empresas del mismo sector."

    result = {
        "Razón": name,
        "Periodo": period_label,
        "Fórmula": RATIO_DEFS[name][0],
        "Sustitución": substitution,
        "Resultado": value,
        "Unidad": unit,
        "Interpretación": interpretation,
        "Resultado mostrado": display
    }
    return result


def make_pdf(record, sheet, ratios, totals_recent):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(letter),
        rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("FINOVA | REPORTE GERENCIAL FINANCIERO", styles["Title"]),
        Spacer(1, 8),
        Paragraph(f"<b>Empresa:</b> {xesc(record['company'])} &nbsp;&nbsp; <b>RFC:</b> {xesc(record['rfc'] or 'No indicado')}", styles["Normal"]),
        Paragraph(f"<b>Folio:</b> {record['folio']} &nbsp;&nbsp; <b>Comparativo:</b> {record['old_date']} vs {record['new_date']}", styles["Normal"]),
        Paragraph(f"<b>Moneda:</b> {record['currency']} &nbsp;&nbsp; <b>Generado:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Resumen ejecutivo", styles["Heading2"]),
    ]
    kpi_data = [
        ["Activo total", "Pasivo total", "Capital contable", "Capital de trabajo"],
        [
            f"{totals_recent['Activo total']:,.2f}",
            f"{totals_recent['Pasivo total']:,.2f}",
            f"{totals_recent['Capital total']:,.2f}",
            f"{totals_recent['Capital de trabajo']:,.2f}"
        ]
    ]
    kpi = Table(kpi_data, colWidths=[2.3*inch]*4)
    kpi.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0A2147")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("BACKGROUND", (0,1), (-1,1), colors.HexColor("#F4F6FA")),
        ("GRID", (0,0), (-1,-1), .4, colors.HexColor("#DDE3EC")),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7)
    ]))
    story.extend([kpi, Spacer(1, 12), Paragraph("Hoja verde comparativa", styles["Heading2"])])

    rows = [["Concepto", "Categoría", "Anterior", "Reciente", "Aumentó", "Disminuyó", "Origen / Aplicación", "Actividad"]]
    for _, r in sheet.iterrows():
        rows.append([
            str(r["Concepto"])[:27], str(r["Categoria"])[:21],
            f"{r['Anterior']:,.2f}", f"{r['Reciente']:,.2f}",
            f"{r['Aumento']:,.2f}", f"{r['Disminucion']:,.2f}",
            str(r["Origen / Aplicación"]), str(r["Actividad"])
        ])
    table = Table(rows, repeatRows=1, colWidths=[1.55*inch,1.2*inch,.85*inch,.85*inch,.8*inch,.8*inch,1.05*inch,1.0*inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0A2147")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 6.5),
        ("GRID", (0,0), (-1,-1), .3, colors.HexColor("#DDE3EC")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F4F6FA")]),
        ("ALIGN", (2,1), (5,-1), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4)
    ]))
    story.append(table)
    story.extend(cash_flow_pdf(sheet))

    if ratios:
        story.extend([Spacer(1, 14), Paragraph("Razones financieras", styles["Heading2"])])
        for r in ratios:
            story.append(KeepTogether([
                Paragraph(f"<b>{r['Razón']} — {r['Periodo']}</b>", styles["Heading3"]),
                Paragraph(f"Qué es: {xesc(RATIO_INFO.get(r['Razón'], ('', ''))[0])}", styles["Normal"]),
                Paragraph(f"Fórmula: {r['Fórmula']}", styles["Normal"]),
                Paragraph(f"Sustitución: {r['Sustitución']}", styles["Normal"]),
                Paragraph(f"Resultado: {r['Resultado mostrado']}", styles["Normal"]),
                Paragraph(f"Interpretación: {r['Interpretación']}", styles["Normal"]),
                Spacer(1, 6),
            ]))
    story.extend([Spacer(1, 18), signature_block(record)])
    story.extend([
        Spacer(1, 12),
        Paragraph(
            "Nota: clasificación preliminar basada en la naturaleza general de las cuentas. "
            "El estado de flujo de efectivo formal requiere validar movimientos reales de efectivo, "
            "ajustes no monetarios y la información complementaria del periodo.",
            styles["Italic"]
        )
    ])
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# --------------------------- Inicio y sesión ---------------------------

init_db()
for _key, _val in (("user", None), ("page", "Panel"), ("current_folio", None), ("lookup_folio", None)):
    if _key not in st.session_state:
        st.session_state[_key] = _val

with db() as con:
    user_count = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def login_screen():
    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        H(f'<div class="auth-brand">{LOGO}<div class="wordmark">FINOVA</div><p>Plataforma de análisis financiero</p></div>')

        if user_count == 0:
            H('<div class="auth-note">Configuración inicial: crea la cuenta administradora. '
              'Esta opción solo aparece cuando no existen usuarios.</div>')
            with st.form("first_admin"):
                username = st.text_input("Usuario administrador")
                password = st.text_input("Contraseña (mínimo 8 caracteres)", type="password")
                confirm = st.text_input("Confirmar contraseña", type="password")
                submitted = st.form_submit_button("Crear administrador", type="primary", **STRETCH)
                if submitted:
                    if password != confirm:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        try:
                            add_user(username, password, "admin")
                            st.success("Administrador creado. Ya puedes iniciar sesión.")
                            st.rerun()
                        except (ValueError, sqlite3.IntegrityError) as e:
                            st.error(str(e))
            return

        with st.form("login_form"):
            username = st.text_input("Usuario", autocomplete="username")
            password = st.text_input("Contraseña", type="password", autocomplete="current-password")
            submitted = st.form_submit_button("Ingresar", type="primary", **STRETCH)
            if submitted:
                user = get_user(username)
                if user and check_password(password, user["password_hash"], user["salt"]):
                    st.session_state.user = dict(user)
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
        H(f'<ul class="auth-points">'
          f'<li>{icon("table", 18)}Compara dos balances y detecta orígenes y aplicaciones</li>'
          f'<li>{icon("percent", 18)}Razones financieras con fórmula e interpretación</li>'
          f'<li>{icon("file-text", 18)}Reporte gerencial listo para exportar en PDF</li></ul>')


if not st.session_state.user:
    login_screen()
    st.stop()

user = st.session_state.user
is_admin = user["role"] == "admin"

active = analysis_for(st.session_state.current_folio, user)
if st.session_state.current_folio and not active:
    st.session_state.current_folio = None

NAV = [
    ("Análisis", [("Panel", "dashboard"), ("Nuevo análisis", "note_add"), ("Consulta por folio", "search")]),
    ("Resultados", [("Decisiones", "checklist"), ("Estados financieros", "account_balance"), ("Hoja verde", "table_view"),
                    ("Razones financieras", "percent"), ("Gráficas", "bar_chart"),
                    ("Reporte gerencial", "description")]),
    ("Control", [("Documentos", "folder_open"), ("Solicitudes de cambio", "edit_note")]),
]
if is_admin:
    NAV.append(("Sistema", [("Administrar usuarios", "group"), ("Editar estados", "edit")]))
with db() as con:
    pending = con.execute("SELECT COUNT(*) FROM change_requests WHERE status='pendiente'").fetchone()[0] if is_admin else 0

with st.sidebar:
    H(f'<div class="side-brand">{LOGO}<div><div class="wordmark">FINOVA</div><small>INTELIGENCIA FINANCIERA</small></div></div>')
    H(f'<div class="side-user"><span class="avatar" aria-hidden="true">{esc(user["username"][:1].upper())}</span>'
      f'<div><b>{esc(user["username"])}</b><span>{"Administrador" if is_admin else "Contador"}</span></div></div>')
    if active:
        H(f'<div class="side-ctx"><small>Análisis activo</small><b>{esc(active["company"])}</b><span>{esc(active["folio"])}</span></div>')
    for group_label, items in NAV:
        H(f'<div class="nav-label">{group_label}</div>')
        for name, mat in items:
            label = f"{name} ({pending})" if name == "Solicitudes de cambio" and pending else name
            if btn(label, mat, key="nav_" + name, **STRETCH,
                   type="primary" if st.session_state.page == name else "secondary"):
                go(name)
    H('<div class="nav-label">Sesión</div>')
    if btn("Cerrar sesión", "logout", key="logout", **STRETCH):
        st.session_state.user = None
        st.session_state.current_folio = None
        st.session_state.lookup_folio = None
        st.rerun()
    st.caption("FINOVA · Versión académica")

page = st.session_state.page


# --------------------------- Panel ---------------------------
def save_new_analysis(df, uploads, doc_kind, pending_capture=False, note=""):
    folio = "FIN-" + datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:8].upper()
    now = now_iso()
    with db() as con:
        con.execute("""
            INSERT INTO analyses(
              folio,owner_id,company,rfc,activity,currency,comparison_type,
              old_date,new_date,accounts_json,adjustments_json,ratios_json,created_at,elaboro,reviso,autorizo
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            folio, user["id"], st.session_state.draft_company,
            st.session_state.get("draft_rfc", ""),
            st.session_state.get("draft_activity", ""),
            st.session_state.draft_currency,
            st.session_state.draft_comparison_type,
            st.session_state.draft_old_date,
            st.session_state.draft_new_date,
            json.dumps(df.to_dict("records"), ensure_ascii=False),
            "{}", "[]", now,
            user["username"], st.session_state.get("draft_reviso", ""), st.session_state.get("draft_autorizo", "")
        ))
        for u in uploads or []:
            add_attachment(con, folio, u, doc_kind, user["id"])
        log_event(folio, user["id"], "Análisis creado",
                  f"{len(uploads or [])} documento(s) adjunto(s). {note}".strip(), con)
        if pending_capture:
            cur_ = con.execute(
                "INSERT INTO change_requests(folio,requester_id,reason,created_at) VALUES(?,?,?,?)",
                (folio, user["id"],
                 "Captura inicial de saldos: el contador subió su archivo de estados financieros "
                 "y los importes están pendientes de captura.", now))
            log_event(folio, user["id"], "Captura pendiente", f"Solicitud #{cur_.lastrowid}", con)
    return folio

if page == "Panel":
    if st.session_state.get("_panel_dashboard_version") != 3:
        chart_company = st.session_state.get("panel_chart_company")
        if chart_company and st.session_state.get("panel_company_filter") == chart_company:
            st.session_state["panel_company_filter"] = "Todas"
        for key in ("panel_chart_company", "panel_chart_previous_view", "panel_chart_version", "panel_chart_view"):
            st.session_state.pop(key, None)
        st.session_state["_panel_dashboard_version"] = 3

    with db() as con:
        base_q = """
            SELECT a.*, u.username AS owner_name,
                   COALESCE(latest_log.created_at, a.created_at) AS last_activity_at,
                   latest_log.action AS last_activity_action
            FROM analyses a
            JOIN users u ON u.id=a.owner_id
            LEFT JOIN analysis_log latest_log ON latest_log.id=(
                SELECT l.id FROM analysis_log l
                WHERE l.folio=a.folio ORDER BY l.id DESC LIMIT 1
            )
        """
        records = (
            con.execute(base_q + "ORDER BY last_activity_at DESC, a.id DESC").fetchall()
            if is_admin else
            con.execute(
                base_q + "WHERE a.owner_id=? ORDER BY last_activity_at DESC, a.id DESC",
                (user["id"],),
            ).fetchall()
        )
        panel_pending = (
            pending if is_admin else
            con.execute(
                "SELECT COUNT(*) FROM change_requests "
                "WHERE status='pendiente' AND requester_id=?",
                (user["id"],),
            ).fetchone()[0]
        )

    latest_record = records[0] if records else None
    focus_record = active or latest_record
    hour = datetime.now().hour
    greeting = "Buenos días" if hour < 12 else "Buenas tardes" if hour < 19 else "Buenas noches"
    dashboard_intro, dashboard_actions = st.columns([1.8, 1.2], **_COL_VA)
    with dashboard_intro:
        today_label = panel_date_label(date.today().isoformat())
        H(
            '<header class="dashboard-heading">'
            '<span class="dashboard-heading-kicker">FINOVA · Panel</span>'
            '<div class="dashboard-heading-line">'
            f'<h1>{greeting}, {esc(user["username"])}</h1>'
            f'<time>{esc(today_label)}</time></div>'
            '<p>Tu cartera financiera, en un solo lugar.</p></header>'
        )
    with dashboard_actions:
        action_columns = st.columns([1, 1.1])
        with action_columns[0]:
            if btn(
                "Crear análisis",
                "note_add",
                type="primary",
                key="dashboard_create_analysis",
            ):
                go("Nuevo análisis")
        with action_columns[1]:
            if focus_record:
                if btn(
                    "Continuar análisis",
                    "arrow_forward",
                    type="secondary",
                    key="dashboard_continue_analysis",
                ):
                    st.session_state.current_folio = focus_record["folio"]
                    go("Decisiones")
            elif btn(
                    "Consultar por folio",
                "search",
                type="secondary",
                key="dashboard_lookup_analysis",
            ):
                go("Consulta por folio")

    summary_items = [
        ("Total de análisis", str(len(records)), "En tu cartera", "", "folder"),
        (
            "Análisis activos",
            "1" if active else "0",
            active["company"] if active else "Ninguno abierto",
            "",
            "check",
        ),
        (
            "Solicitudes pendientes",
            str(panel_pending),
            "Requieren atención" if panel_pending else "Al día",
            "is-pending" if panel_pending else "",
            "edit",
        ),
        (
            "Última actividad",
            panel_relative_date(latest_record["last_activity_at"]) if latest_record else "Sin actividad",
            panel_date_label(latest_record["last_activity_at"]) if latest_record else "Aún no hay registros",
            "",
            "bar-chart",
        ),
    ]
    summary_html = '<section class="dashboard-summary" aria-label="Resumen general">'
    for label, value, detail, tone, icon_name in summary_items:
        summary_html += (
            f'<div class="dashboard-summary-item {tone}">'
            f'<span class="dashboard-summary-icon">{icon(icon_name, 16)}</span>'
            f'<span class="dashboard-summary-label">{esc(label)}</span>'
            f'<strong class="dashboard-summary-value">{esc(value)}</strong>'
            f'<small class="dashboard-summary-detail">{esc(detail)}</small></div>'
        )
    H(summary_html + "</section>")

    if not records:
        H('<h2 class="dashboard-section-title">Actividad reciente</h2>')
        st.caption("Los análisis recientes aparecerán aquí.")
        empty_state(
            "file-plus",
            "Tu cartera aparecerá aquí",
            "Crea tu primer análisis para comparar dos periodos y consultar sus resultados.",
        )
    else:
        H('<h2 class="dashboard-section-title">Actividad reciente</h2>')
        st.caption("Ordenados por actividad registrada o fecha de creación.")
        render_panel_records(records[:5], active["folio"] if active else None, "recent", "recent")

        H('<h2 class="dashboard-section-title">Cartera de análisis</h2>')
        filter_columns = st.columns([2.2, 1.15, 1, 1, 1.2] if is_admin else [2.5, 1.2, 1, 1.2])
        with filter_columns[0]:
            activity_query = st.text_input(
                "Buscar",
                placeholder="Empresa, folio o responsable",
                key="panel_activity_search",
            ).strip().casefold()
        with filter_columns[1]:
            company_options = ["Todas"] + sorted(
                {record["company"] for record in records},
                key=str.casefold,
            )
            if st.session_state.get("panel_company_filter", "Todas") not in company_options:
                st.session_state["panel_company_filter"] = "Todas"
            company_filter = st.selectbox(
                "Empresa",
                company_options,
                key="panel_company_filter",
            )
        with filter_columns[2]:
            status_filter = st.selectbox(
                "Estado",
                ["Todos", "Activo", "Guardado"],
                key="panel_analysis_status",
            )
        if is_admin:
            with filter_columns[3]:
                owner_options = ["Todos"] + sorted(
                    {record["owner_name"] for record in records},
                    key=str.casefold,
                )
                owner_filter = st.selectbox(
                    "Responsable",
                    owner_options,
                    key="panel_owner_filter",
                )
            sort_column = filter_columns[4]
        else:
            owner_filter = "Todos"
            sort_column = filter_columns[3]
        with sort_column:
            sort_options = [
                "Actividad reciente",
                "Creación reciente",
                "Creación más antigua",
                "Empresa A-Z",
            ] + (["Responsable A-Z"] if is_admin else [])
            if st.session_state.get("panel_activity_sort") not in sort_options:
                st.session_state["panel_activity_sort"] = "Actividad reciente"
            sort_order = st.selectbox(
                "Ordenar por",
                sort_options,
                key="panel_activity_sort",
            )

        filtered_records = [
            record for record in records
            if (not activity_query or activity_query in (
                f'{record["company"]} {record["folio"]} {record["owner_name"]}'
            ).casefold())
            and (company_filter == "Todas" or record["company"] == company_filter)
            and (status_filter == "Todos"
                 or (status_filter == "Activo" and active and record["folio"] == active["folio"])
                 or (status_filter == "Guardado" and (not active or record["folio"] != active["folio"])))
            and (owner_filter == "Todos" or record["owner_name"] == owner_filter)
        ]
        if sort_order == "Creación más antigua":
            filtered_records.sort(key=lambda record: record["created_at"])
        elif sort_order == "Creación reciente":
            filtered_records.sort(key=lambda record: record["created_at"], reverse=True)
        elif sort_order == "Empresa A-Z":
            filtered_records.sort(key=lambda record: record["company"].casefold())
        elif sort_order == "Responsable A-Z":
            filtered_records.sort(key=lambda record: record["owner_name"].casefold())
        else:
            filtered_records.sort(key=lambda record: record["last_activity_at"], reverse=True)

        result_count = len(filtered_records)
        result_label = f"{result_count} expediente" + ("s" if result_count != 1 else "")
        st.caption(
            result_label if filtered_records else "No hay expedientes con estos filtros."
        )

        if not filtered_records:
            st.info("Prueba con otra búsqueda o cambia los filtros para encontrar un expediente.")
        else:
            portfolio_headers = st.columns([3.7, 4, 1.15, 1.7], **_COL_VA)
            for label, column in zip(
                ["Empresa / folio", "Periodo · responsable · actividad", "Estado", "Acciones"],
                portfolio_headers,
            ):
                H(f'<span class="dashboard-portfolio-head">{esc(label)}</span>', column)
            render_panel_records(
                filtered_records,
                active["folio"] if active else None,
                "portfolio",
                "portfolio",
            )

# --------------------------- Administración ---------------------------

elif page == "Administrar usuarios":
    page_header("Administración de usuarios", "Registra cuentas y controla quién puede ingresar.", "Sistema")
    if not is_admin:
        st.error("Acceso exclusivo para administradores.")
        st.stop()

    with st.expander("Registrar nuevo usuario", expanded=False):
        with st.form("new_user_form", border=False):
            c1, c2 = st.columns(2)
            username = c1.text_input("Nuevo usuario")
            role = c2.selectbox("Rol", ["usuario", "admin"], format_func=ROLE_LABEL.get)
            password = c1.text_input("Contraseña (mínimo 8 caracteres)", type="password")
            confirm = c2.text_input("Confirmar contraseña", type="password")
            submitted = st.form_submit_button("Registrar usuario", type="primary")
            if submitted:
                if password != confirm:
                    st.error("Las contraseñas no coinciden.")
                else:
                    try:
                        add_user(username, password, role)
                        st.success("Usuario registrado.")
                        st.rerun()
                    except (ValueError, sqlite3.IntegrityError) as e:
                        st.error(str(e))

    with db() as con:
        users = con.execute("SELECT id,username,role,active,created_at FROM users ORDER BY id").fetchall()

    st.subheader("Usuarios")
    st.dataframe(
        [{"ID": u["id"], "Usuario": u["username"], "Rol": ROLE_LABEL.get(u["role"], u["role"]),
          "Estado": "Activo" if u["active"] else "Inactivo", "Creado": u["created_at"]} for u in users],
        **STRETCH, hide_index=True
    )

    st.subheader("Cambiar estado de una cuenta")
    others = {f'{u["username"]} · {ROLE_LABEL.get(u["role"], u["role"])} · {"activo" if u["active"] else "inactivo"}': u["id"] for u in users}
    with st.form("user_status_form"):
        c1, c2 = st.columns(2)
        target_label = c1.selectbox("Usuario", list(others.keys()))
        status = c2.selectbox("Estado", ["Activo", "Desactivar"])
        submitted = st.form_submit_button("Actualizar estado")
        if submitted:
            target_id = others[target_label]
            with db() as con:
                target = con.execute("SELECT * FROM users WHERE id=?", (target_id,)).fetchone()
                if not target:
                    st.error("Usuario no encontrado.")
                elif target["id"] == user["id"]:
                    st.error("No puedes cambiar tu propio estado.")
                elif target["role"] == "admin" and status == "Desactivar":
                    st.error("No desactives cuentas administradoras desde este formulario.")
                else:
                    con.execute("UPDATE users SET active=? WHERE id=?", (1 if status == "Activo" else 0, target_id))
                    st.success("Estado actualizado.")
                    st.rerun()


# --------------------------- Nuevo análisis ---------------------------

elif page == "Nuevo análisis":
    page_header("Nuevo análisis financiero", "Confirma los datos de la empresa, captura los saldos y guarda.", "Análisis")
    stepper_slot = st.empty()

    with st.form("company_form"):
        c1, c2 = st.columns(2)
        company = c1.text_input("Razón social *", value=st.session_state.get("draft_company", ""))
        rfc = c2.text_input("RFC", value=st.session_state.get("draft_rfc", ""))
        activity = c1.text_input("Actividad económica", value=st.session_state.get("draft_activity", ""))
        currency = c2.selectbox("Moneda", ["MXN", "USD", "EUR"])
        reviso = c1.text_input("Revisó (nombre)", value=st.session_state.get("draft_reviso", ""),
                               help="Quién revisa los estados financieros. Opcional.")
        autorizo = c2.text_input("Autorizó (nombre)", value=st.session_state.get("draft_autorizo", ""),
                                 help="Quién autoriza los estados financieros. Opcional.")
        comparison_type = st.selectbox("Tipo de comparación", ["Mes contra mes", "Año contra año", "Fecha contra fecha"])
        if comparison_type == "Año contra año":
            c3, c4 = st.columns(2)
            year_old = c3.number_input("Año anterior", 1900, 2200, max(1900, date.today().year - 1))
            year_new = c4.number_input("Año reciente", 1900, 2200, date.today().year)
            old_date = date(int(year_old), 12, 31)
            new_date = date(int(year_new), 12, 31)
        elif comparison_type == "Mes contra mes":
            c3, c4 = st.columns(2)
            old_date = c3.date_input("Fecha de cierre anterior", date(date.today().year - 1, 12, 31))
            new_date = c4.date_input("Fecha de cierre reciente", date.today())
        else:
            c3, c4 = st.columns(2)
            old_date = c3.date_input("Fecha anterior", date(date.today().year - 1, 12, 31))
            new_date = c4.date_input("Fecha reciente", date.today())
        save_company = st.form_submit_button("Confirmar datos generales", type="primary")

    if save_company:
        if not company.strip():
            st.error("La razón social es obligatoria.")
        elif new_date <= old_date:
            st.error("La fecha reciente debe ser posterior a la anterior.")
        else:
            st.session_state.draft_company = company.strip()
            st.session_state.draft_rfc = rfc.strip()
            st.session_state.draft_activity = activity.strip()
            st.session_state.draft_reviso = reviso.strip()
            st.session_state.draft_autorizo = autorizo.strip()
            st.session_state.draft_currency = currency
            st.session_state.draft_comparison_type = comparison_type
            st.session_state.draft_old_date = old_date.isoformat()
            st.session_state.draft_new_date = new_date.isoformat()
            st.success("Datos generales confirmados.")

    required_keys = ["draft_company", "draft_currency", "draft_old_date", "draft_new_date", "draft_comparison_type"]
    ready = all(k in st.session_state for k in required_keys)
    H(stepper_html(2 if ready else 1, ["Datos generales",
                                       "Captura de cuentas" if is_admin else "Subir archivo",
                                       "Guardar y analizar"]), stepper_slot)
    if not ready:
        st.info("Confirma los datos generales para abrir la captura de cuentas.")
        st.stop()
    if not is_admin:
        upl_n = st.session_state.get("upl_n", 0)
        st.subheader("Sube tu archivo")
        H(f'<div class="chips"><span class="chip"><b>{esc(st.session_state.draft_company)}</b></span>'
          f'<span class="chip">{esc(st.session_state.draft_old_date)} → {esc(st.session_state.draft_new_date)}</span>'
          f'<span class="chip">{esc(st.session_state.draft_currency)}</span>'
          f'<span class="chip">Elaboró: {esc(user["username"])}</span></div>')
        st.info("Como contador solo subes el archivo de los estados financieros. "
                "Los saldos los captura y valida el administrador; tú no puedes modificar cantidades.")
        doc_kind = st.selectbox("Tipo de documento", DOC_KINDS, key=f"draft_kind_{upl_n}")
        uploads = st.file_uploader(f"Archivos (máx. {MAX_MB} MB c/u)", accept_multiple_files=True,
                                   type=sorted(ALLOWED_EXT), key=f"draft_files_{upl_n}")
        confirm_send = st.checkbox(
            "Confirmo que el archivo es el correcto. Entiendo que no podré modificarlo ni cambiar cantidades; "
            "cualquier corrección se solicita al administrador.", key=f"confirm_send_{upl_n}")
        if st.button("Enviar archivo y guardar análisis", type="primary", disabled=not confirm_send):
            upload_errors = [e for e in (validate_upload(u) for u in (uploads or [])) if e]
            if not uploads:
                st.error("Sube al menos un archivo.")
            elif upload_errors:
                for e in upload_errors:
                    st.error(e)
            else:
                accounts, n_found, unknown, warns = extract_accounts(uploads)
                if n_found >= 3:
                    df_new = clean_accounts(accounts)
                    folio = save_new_analysis(df_new, uploads, doc_kind,
                                              note=f"Captura automática: {n_found} cuenta(s) leída(s).")
                    gap = totals(df_new, "Reciente")["Activo total"] - totals(df_new, "Reciente")["Pasivo más capital"]
                    msg = f"Se leyeron {n_found} cuenta(s) del archivo y se generaron los estados. "
                    if abs(gap) < 0.01:
                        msg += "El balance reciente cuadra."
                    else:
                        msg += (f"El balance reciente NO cuadra (diferencia {gap:,.2f}): revisa que los saldos "
                                "leídos sean correctos y, si hay un error, solicita el cambio.")
                    if unknown:
                        msg += f" No se reconocieron {len(unknown)} renglón(es), p. ej.: {', '.join(unknown[:3])}."
                    if warns:
                        msg += f" Avisos de lectura ({len(warns)}): {'; '.join(warns[:2])}"
                    st.session_state.flash_warn = abs(gap) >= 0.01 or bool(unknown) or bool(warns)
                    st.session_state.page = "Estados financieros"
                else:
                    folio = save_new_analysis(clean_accounts(base_accounts()), uploads, doc_kind,
                                              pending_capture=True, note="No se pudieron leer saldos.")
                    msg = ("No se pudieron leer saldos del archivo (puede ser un PDF escaneado o una imagen). "
                           "Se guardó y el administrador capturará los saldos.")
                    if warns:
                        msg += f" Avisos de lectura ({len(warns)}): {'; '.join(warns[:2])}"
                    st.session_state.flash_warn = True
                    st.session_state.page = "Documentos"
                st.session_state.upl_n = upl_n + 1
                st.session_state.current_folio = folio
                st.session_state.flash = msg
                st.rerun()
        st.stop()

    st.subheader("Captura del balance y cuentas complementarias")
    H(f'<div class="chips"><span class="chip"><b>{esc(st.session_state.draft_company)}</b></span>'
      f'<span class="chip">{esc(st.session_state.draft_old_date)} → {esc(st.session_state.draft_new_date)}</span>'
      f'<span class="chip">{esc(st.session_state.draft_currency)}</span>'
      f'<span class="chip">Elaboró: {esc(user["username"])}</span></div>')
    st.info("Sube tu archivo de estados financieros (Excel, CSV, PDF con texto o Word); "
        "al adjuntarlo se leerán los importes automáticamente. Revisa los saldos antes de guardar. "
        "Después no podrás modificar cantidades: cualquier corrección se solicita al administrador.")

    if "draft_accounts" not in st.session_state:
        st.session_state.draft_accounts = base_accounts()

    with st.expander("Agregar un concepto que no está en el catálogo"):
        with st.form("add_account_form", border=False):
            c1, c2 = st.columns([2, 2])
            new_concept = c1.text_input("Nombre del concepto")
            new_category = c2.selectbox("Tipo de cuenta", list(CATALOGO.keys()))
            add_account = st.form_submit_button("Agregar concepto")
            if add_account:
                if not new_concept.strip():
                    st.warning("Escribe el nombre del concepto.")
                elif any(x["Concepto"].casefold() == new_concept.strip().casefold() for x in st.session_state.draft_accounts):
                    st.warning("Ese concepto ya existe.")
                else:
                    st.session_state.draft_accounts.append({
                        "Concepto": new_concept.strip(), "Categoria": new_category,
                        "Anterior": 0.0, "Reciente": 0.0
                    })
                    st.rerun()

    for category in CATALOGO:
        with st.expander(category, expanded=(category == "Activo circulante")):
            all_df = pd.DataFrame(st.session_state.draft_accounts)
            sub = all_df[all_df["Categoria"] == category][["Concepto", "Anterior", "Reciente"]].copy()
            edit_version = st.session_state.get("draft_edit_version", 0)
            edited = st.data_editor(
                sub, key=f"edit_{category}_{edit_version}", num_rows="dynamic",
                **STRETCH, hide_index=True,
                column_config={
                    "Concepto": st.column_config.TextColumn("Concepto", required=True),
                    "Anterior": st.column_config.NumberColumn(st.session_state.draft_old_date, min_value=0.0, step=100.0, format="%.2f"),
                    "Reciente": st.column_config.NumberColumn(st.session_state.draft_new_date, min_value=0.0, step=100.0, format="%.2f")
                }
            )
            if st.button("Aplicar cambios · " + category, key="apply_" + category):
                remaining = [x for x in st.session_state.draft_accounts if x["Categoria"] != category]
                for _, row in edited.iterrows():
                    concept = str(row.get("Concepto", "")).strip()
                    if concept:
                        remaining.append({
                            "Concepto": concept, "Categoria": category,
                            "Anterior": max(0.0, float(row.get("Anterior", 0) or 0)),
                            "Reciente": max(0.0, float(row.get("Reciente", 0) or 0))
                        })
                # Rechaza nombres duplicados para evitar saldos ambiguos.
                names = [x["Concepto"].casefold() for x in remaining]
                if len(names) != len(set(names)):
                    st.error("Hay conceptos duplicados. Corrígelos antes de aplicar.")
                else:
                    st.session_state.draft_accounts = remaining
                    st.success("Cambios aplicados.")
                    st.rerun()

    st.divider()
    upl_n = st.session_state.get("upl_n", 0)
    st.subheader("Documentos de respaldo")
    st.caption(f"Adjunta los estados financieros para importarlos y guardarlos (máx. {MAX_MB} MB c/u).")
    doc_kind = st.selectbox("Tipo de documento", DOC_KINDS, key=f"draft_kind_{upl_n}")
    upload_key = f"draft_files_{upl_n}"
    uploads = st.file_uploader(
        "Archivos", accept_multiple_files=True, type=sorted(ALLOWED_EXT),
        key=upload_key, on_change=import_draft_uploads, args=(upload_key,))
    if st.button("Leer saldos de archivo", key=f"read_draft_accounts_{upl_n}", disabled=not uploads):
        if import_draft_uploads(upload_key):
            st.rerun()

    feedback = st.session_state.pop("draft_import_feedback", None)
    if feedback:
        if feedback.get("error"):
            st.error(feedback["error"])
        else:
            st.success(f"Se identificaron {feedback['found']} cuentas y se aplicaron saldos "
                       f"a {feedback['applied']}. {feedback['missing']} cuentas del catálogo no "
                       "aparecen en el archivo y quedan sin saldo; no se inventaron importes.")
        if feedback.get("unknown"):
            st.warning("Conceptos no reconocidos: " + ", ".join(feedback["unknown"]))
        for warning in feedback.get("warnings", []):
            st.warning(warning)

    support = st.session_state.get("draft_workbook_support")
    if support and (support["checks"] or support["indicators"] or support["warnings"]):
        checked = sum(row["Cotejo FINOVA"] == "Coincide" for row in support["checks"])
        compared = sum(row["Cotejo FINOVA"] == "Coincide" for row in support["indicators"])
        with st.expander("Comprobaciones e indicadores del archivo"):
            st.caption(
                f"Comprobaciones conciliadas: {checked} de {len(support['checks'])}. "
                f"Indicadores que coinciden con FINOVA: {compared} de {len(support['indicators'])}."
            )
            if support["checks"]:
                st.dataframe(pd.DataFrame(support["checks"]), **STRETCH, hide_index=True)
            if support["indicators"]:
                st.dataframe(pd.DataFrame(support["indicators"]), **STRETCH, hide_index=True)
            for warning in support["warnings"]:
                st.warning(warning)

    filled = sum(1 for x in st.session_state.draft_accounts if x["Anterior"] or x["Reciente"])
    H(f'<div class="chips"><span class="chip"><b>{filled}</b> de {len(st.session_state.draft_accounts)} cuentas con saldo aplicado</span></div>')

    confirm_lock = st.checkbox(
        "Confirmo que revisé los saldos. Entiendo que, una vez guardado, solo el administrador puede modificar los estados financieros.",
        key=f"confirm_lock_{upl_n}_{st.session_state.get('draft_edit_version', 0)}")
    if st.button("Generar hoja verde y guardar análisis", type="primary", disabled=not confirm_lock):
        df = clean_accounts(st.session_state.draft_accounts)
        upload_errors = [e for e in (validate_upload(u) for u in (uploads or [])) if e]
        if df.empty:
            st.error("Captura al menos una cuenta.")
        elif upload_errors:
            for e in upload_errors:
                st.error(e)
        else:
            folio = save_new_analysis(df, uploads, doc_kind)
            st.session_state.upl_n = upl_n + 1
            st.session_state.current_folio = folio
            st.session_state.page = "Hoja verde"
            st.rerun()
            st.session_state.current_folio = folio
            st.session_state.page = "Hoja verde"
            st.rerun()


# --------------------------- Cargar análisis actual ---------------------------

elif page in ["Decisiones", "Estados financieros", "Hoja verde", "Razones financieras", "Gráficas", "Reporte gerencial", "Documentos", "Editar estados"]:
    folio = st.session_state.get("current_folio")
    record = analysis_for(folio, user)
    if not record:
        page_header(page, "Esta sección trabaja sobre un análisis guardado.", "Resultados")
        empty_state("file-plus", "No hay un análisis abierto",
                    "Crea uno nuevo o recupera uno guardado con su folio.")
        c1, c2, _ = st.columns([1, 1, 2])
        if c1.button("Nuevo análisis", type="primary", **STRETCH, key="empty_new"):
            go("Nuevo análisis")
        if c2.button("Consulta por folio", **STRETCH, key="empty_lookup"):
            go("Consulta por folio")
        st.stop()

    df = clean_accounts(json.loads(record["accounts_json"]))
    overrides = json.loads(record["adjustments_json"] or "{}")
    sheet = green_sheet(df, overrides)
    old_totals = totals(df, "Anterior")
    new_totals = totals(df, "Reciente")
    cur = record["currency"]

    if page == "Decisiones":
        page_header("Decisiones a tomar",
                    f"{record['company']} · Folio {record['folio']} · {record['old_date']} → {record['new_date']}",
                    "Decisiones")
    else:
        page_header(record["company"],
                    f"Folio {record['folio']} · {record['old_date']} → {record['new_date']} · {cur}", page)
    if not (df["Anterior"].abs().sum() or df["Reciente"].abs().sum()) and page != "Editar estados":
        if is_admin:
            st.warning("Este análisis aún no tiene saldos. Captúralos en «Editar estados» "
                        "usando el archivo que subió el contador (sección «Documentos»).")
        else:
            st.info("Tu archivo fue recibido. El administrador capturará los saldos y cuando termine "
                    "verás aquí los resultados.")
    decision_focus_accounts = st.session_state.pop("decision_focus_accounts", [])
    decision_focus_labels = set(st.session_state.pop("decision_focus_labels", []))
    decision_focus_ratio = st.session_state.pop("decision_focus_ratio", None)
    decision_focus_period = st.session_state.pop("decision_focus_period", None)
    decision_focus_tab = st.session_state.pop("decision_focus_tab", None)
    decision_scroll_to_source = st.session_state.pop("decision_scroll_to_source", False)

    if page == "Decisiones":
        decisions = intelligent_recommendations(df, old_totals, new_totals, cur)
        ratios = enrich_ratio_recommendations(
            json.loads(record["ratios_json"] or "[]"), old_totals, new_totals, cur)
        for ratio in ratios:
            advice = ratio["Recomendación"]
            decisions.append({
                "Prioridad": "Revisar",
                "Recomendación": f"{ratio['Razón']} · {ratio['Periodo']}",
                "Qué detectó": advice["Qué detectó"],
                "Por qué importa": advice["Por qué importa"],
                "Decisión sugerida": advice["Decisión sugerida"],
                "Sección": "Razones financieras",
                "Fuente": "Razón financiera",
                "Indicador": ratio["Razón"],
                "Valor clave": ratio.get("Resultado mostrado", "No calculable"),
                "Periodo": ratio["Periodo"],
            })
        for decision in decisions:
            decision.setdefault("Sección", decision_destination(decision))
            decision.setdefault("Fuente", "Variaciones y saldos")
            decision["Cuentas foco"], decision["Etiquetas foco"] = decision_highlight_context(
                decision, df
            )

        attention_count = sum(item["Prioridad"] == "Atención" for item in decisions)
        review_count = sum(item["Prioridad"] == "Revisar" for item in decisions)
        opportunity_count = sum(item["Prioridad"] == "Oportunidad" for item in decisions)
        H(
            '<section class="decision-hero" aria-label="Resumen del centro de decisiones">'
            '<div class="decision-hero-copy">'
            '<span class="decision-hero-label">Tu mapa de acción · '
            f'{esc(record["company"])}</span>'
            '<h2>De la señal a la acción</h2>'
            '<p>Atiende primero las alertas rojas, valida las amarillas y convierte las verdes en oportunidades.</p>'
            '</div>'
            '<div class="decision-hero-total"><strong>'
            f'{len(decisions)}</strong><span>puntos<br>detectados</span></div></section>'
        )
        status_summaries = (
            ("Atención", attention_count, "Actúa primero", "danger", "!"),
            ("Revisar", review_count, "Valida antes de decidir", "review", "?"),
            ("Oportunidad", opportunity_count, "Impulsa lo que funciona", "good", "✓"),
        )
        status_cards = "".join(
            f'<article class="decision-stat {tone}"><span class="decision-stat-mark">{mark}</span>'
            f'<div class="decision-stat-copy"><span>{esc(label)}</span><strong>{count}</strong>'
            f'<small>{esc(hint)}</small></div></article>'
            for label, count, hint, tone, mark in status_summaries
        )
        H(f'<div class="decision-stat-grid" aria-label="Resumen por prioridad">{status_cards}</div>')
        filter_labels = {
            "Todas": f"Todas · {len(decisions)}",
            "Atención": f"Atención · {attention_count}",
            "Revisar": f"Revisar · {review_count}",
            "Oportunidad": f"Oportunidad · {opportunity_count}",
        }
        priority_filter = st.segmented_control(
            "Filtrar por prioridad",
            options=list(filter_labels),
            format_func=lambda value: filter_labels[value],
            default="Todas",
            required=True,
            key="decision_priority_control",
            width="stretch",
            wrap=True,
        )
        priority_filter = priority_filter or "Todas"
        visible_decisions = [
            (index, item) for index, item in enumerate(decisions)
            if priority_filter == "Todas" or item["Prioridad"] == priority_filter
        ]
        if not decisions:
            st.info(
                "No se detectaron asuntos para decidir con estos saldos. "
                "Aprovecha este espacio para confirmar que la captura esté completa."
            )
        elif not visible_decisions:
            st.info("No hay decisiones con esta prioridad. Prueba otra categoría.")
        else:
            if st.session_state.get("decision_detail_folio") != folio:
                st.session_state["decision_detail_index"] = None
                st.session_state["decision_detail_folio"] = folio
                st.session_state["decision_scroll_to_detail"] = False
            visible_indices = {index for index, _ in visible_decisions}
            selected_index = st.session_state.get("decision_detail_index")
            if selected_index not in visible_indices:
                selected_index = None
                st.session_state["decision_detail_index"] = None
                st.session_state["decision_scroll_to_detail"] = False

            def render_decision_choice(index, decision):
                is_selected = index == selected_index
                tone = {
                    "Atención": "danger",
                    "Revisar": "review",
                    "Oportunidad": "good",
                }.get(decision["Prioridad"], "review")
                with st.container(border=True):
                    H(
                        f'<article class="decision-choice {tone}{" is-selected" if is_selected else ""}">'
                        f'<div class="decision-choice-head">'
                        f'<span class="decision-choice-priority">{esc(decision["Prioridad"])}</span>'
                        f'<span class="decision-choice-source">{esc(decision["Fuente"])}</span></div>'
                        f'<p class="decision-choice-title">{esc(decision["Recomendación"])}</p>'
                        '</article>'
                    )
                    if btn(
                        "Ocultar detalle" if is_selected else "Ver detalle",
                        "visibility",
                        key=f"select_decision_{index}",
                        type="primary" if is_selected else "secondary",
                        **STRETCH,
                    ):
                        st.session_state["decision_detail_index"] = (
                            None if is_selected else index
                        )
                        st.session_state["decision_scroll_to_detail"] = not is_selected
                        st.rerun()

            if selected_index is None:
                st.markdown("#### Bandeja de decisiones")
                st.caption(
                    f"{len(visible_decisions)} asuntos · abre «Ver detalle» para consultar los valores "
                    "que originaron cada decisión"
                )
                for start in range(0, len(visible_decisions), 2):
                    columns = st.columns(2)
                    for column, (index, decision) in zip(
                        columns, visible_decisions[start:start + 2]
                    ):
                        with column:
                            render_decision_choice(index, decision)
            else:
                list_column, detail_column = st.columns([0.88, 1.12], gap="large")
                with list_column:
                    st.markdown("#### Bandeja de decisiones")
                    st.caption(
                        f"{len(visible_decisions)} asuntos · elige otra decisión para cambiar el detalle"
                    )
                    for index, decision in visible_decisions:
                        render_decision_choice(index, decision)

                selected_decision = next(
                    item for index, item in visible_decisions if index == selected_index
                )
                status_class = {
                    "Atención": "danger",
                    "Revisar": "review",
                    "Oportunidad": "good",
                }.get(selected_decision["Prioridad"], "review")
                status_label = {
                    "Atención": "Requiere atención prioritaria",
                    "Revisar": "Conviene validar antes de actuar",
                    "Oportunidad": "Oportunidad para impulsar",
                }.get(selected_decision["Prioridad"], "Punto por revisar")
                with detail_column:
                    with st.container(border=True):
                        H(
                            f'<header id="decision-detail-focus" class="decision-focus-heading {status_class}">'
                            f'<span class="decision-focus-overline">{esc(status_label)} · '
                            f'{esc(selected_decision["Fuente"])}</span>'
                            f'<h3>{esc(selected_decision["Recomendación"])}</h3>'
                            f'<p>Lectura ejecutiva para el análisis de {esc(record["company"])}</p>'
                            '</header>'
                        )
                        details = (
                            ("01", "Qué detectó", selected_decision["Qué detectó"]),
                            ("02", "Por qué importa", selected_decision["Por qué importa"]),
                            ("03", "Decisión sugerida", selected_decision["Decisión sugerida"]),
                        )
                        cards = "".join(
                            f'<article class="decision-card {status_class}">'
                            f'<div class="decision-card-head"><span class="decision-card-step">{step}</span>'
                            f'<span>{esc(title)}</span></div>'
                            f'<p>{highlight_decision_values(text) if title == "Qué detectó" else esc(text)}</p>'
                            '</article>'
                            for step, title, text in details
                        )
                        H(
                            f'<div class="decision-grid" role="group" '
                            f'aria-label="Detalle de la decisión">{cards}</div>'
                        )

                        focus_rows = df[
                            df["Concepto"].isin(selected_decision["Cuentas foco"])
                            & ((df["Anterior"] != 0) | (df["Reciente"] != 0))
                        ].copy()
                        if not focus_rows.empty:
                            focus_rows["_magnitud"] = focus_rows["Cambio"].abs()
                            focus_rows = focus_rows.sort_values("_magnitud", ascending=False).head(4)
                            evidence_cards = "".join(
                                f'<article class="decision-evidence-card">'
                                f'<strong>{esc(row["Concepto"])}</strong>'
                                f'<div class="decision-evidence-values">'
                                f'<div><span>Anterior</span><b>{esc(money(row["Anterior"], cur))}</b></div>'
                                f'<div><span>Reciente · marcado</span><b><mark class="decision-value">'
                                f'{esc(money(row["Reciente"], cur))}</mark></b></div>'
                                f'<div><span>Variación</span><b>{esc(money(row["Cambio"], cur))}</b></div>'
                                '</div></article>'
                                for _, row in focus_rows.iterrows()
                            )
                            H(
                                '<section class="decision-evidence">'
                                '<h4 class="decision-evidence-title">Valores que originan esta decisión</h4>'
                                f'<div class="decision-evidence-grid">{evidence_cards}</div></section>'
                            )
                        elif selected_decision.get("Indicador"):
                            H(
                                '<section class="decision-evidence">'
                                '<h4 class="decision-evidence-title">Indicador que origina esta decisión</h4>'
                                f'<article class="decision-evidence-card"><strong>'
                                f'{esc(selected_decision["Indicador"])} · {esc(selected_decision["Periodo"])}'
                                f'</strong><mark class="decision-value">'
                                f'{esc(selected_decision["Valor clave"])}</mark></article></section>'
                            )
                        else:
                            H(
                                '<section class="decision-evidence">'
                                '<h4 class="decision-evidence-title">Señal cuantitativa</h4>'
                                f'<article class="decision-evidence-card">'
                                f'{highlight_decision_values(selected_decision["Qué detectó"])}</article>'
                                '</section>'
                            )

                        target = selected_decision["Sección"]
                        H(
                            f'<div class="decision-route"><span class="decision-route-label">'
                            f'El valor también quedará resaltado en <b>{esc(target)}</b>.</span></div>'
                        )
                        if btn(
                            f"Abrir {target}",
                            "arrow_forward",
                            key="open_selected_decision_section",
                            type="primary",
                            **STRETCH,
                        ):
                            st.session_state["decision_focus_accounts"] = selected_decision["Cuentas foco"]
                            st.session_state["decision_focus_labels"] = selected_decision["Etiquetas foco"]
                            st.session_state["decision_focus_ratio"] = selected_decision.get("Indicador")
                            st.session_state["decision_focus_period"] = selected_decision.get("Periodo")
                            if target == "Estados financieros":
                                focus_categories = set(
                                    df.loc[
                                        df["Concepto"].isin(selected_decision["Cuentas foco"]),
                                        "Categoria",
                                    ]
                                )
                                result_words = (
                                    "utilidad", "perdida", "costo", "gasto", "venta", "margen"
                                )
                                focus_text = _norm(
                                    selected_decision["Recomendación"] + " "
                                    + " ".join(selected_decision["Etiquetas foco"])
                                )
                                focus_tab = (
                                    "Estado de resultados"
                                    if "Estado de resultados (opcional)" in focus_categories
                                    or any(word in focus_text for word in result_words)
                                    else "Balance general"
                                )
                                st.session_state["decision_focus_tab"] = focus_tab
                                st.session_state["financial_statement_tabs"] = focus_tab
                            st.session_state["decision_scroll_to_source"] = True
                            go(target)
                    if st.session_state.pop("decision_scroll_to_detail", False):
                        scroll_to_element("decision-detail-focus", "start")

    # ----- Hoja verde -----
    elif page == "Hoja verde":
        kpi_row([
            ("Aumentos acumulados", fmt_money(sheet["Aumento"].sum()), cur, "", "up"),
            ("Disminuciones acumuladas", fmt_money(sheet["Disminucion"].sum()), cur, "", "down"),
            ("Cambio neto de cuentas", fmt_money(sheet["Cambio"].sum()), cur, "", "brand"),
        ])

        st.subheader("Hoja verde comparativa")
        view = sheet[["Concepto", "Categoria", "Anterior", "Reciente", "Aumento", "Disminucion",
                      "Origen / Aplicación", "Actividad"]].rename(
            columns={"Categoria": "Categoría", "Disminucion": "Disminución"})
        if decision_focus_accounts:
            focus_account_set = set(decision_focus_accounts)
            source_rows = view[view["Concepto"].isin(focus_account_set)].copy()
            if not source_rows.empty:
                source_rows["_focus_magnitude"] = (
                    source_rows["Reciente"] - source_rows["Anterior"]
                ).abs()
                source_rows = source_rows.sort_values(
                    "_focus_magnitude", ascending=False
                ).drop(columns="_focus_magnitude")
                view = pd.concat(
                    [source_rows, view[~view["Concepto"].isin(focus_account_set)]],
                    ignore_index=True,
                )
        flow_styles = {
            "Origen": "background-color:#E6F4EE;color:#0B5D3B;font-weight:600",
            "Aplicación": "background-color:#E8EFFA;color:#0A2A5E;font-weight:600",
            "Revisar": "background-color:#FFF3D6;color:#6B4000;font-weight:600",
        }
        styler = view.style.format("{:,.2f}", subset=["Anterior", "Reciente", "Aumento", "Disminución"])
        styler = (getattr(styler, "map", None) or styler.applymap)(
            lambda v: flow_styles.get(v, "color:#55657D"), subset=["Origen / Aplicación"])
        if decision_focus_accounts:
            styler = styler.apply(
                lambda row: [
                    "background-color:#EAF5FF;color:#244B6C;font-weight:700;border-top:1px solid #C4DFF3;border-bottom:1px solid #C4DFF3"
                    if row["Concepto"] in focus_account_set else ""
                    for _ in row
                ],
                axis=1,
            )
        if decision_scroll_to_source:
            H('<div id="decision-source-sheet"></div>')
        st.dataframe(styler, **STRETCH, hide_index=True)
        if decision_scroll_to_source:
            scroll_to_element("decision-source-sheet", "start")
        st.caption("Origen: fuente de recursos · Aplicación: uso de recursos · Revisar: requiere tu criterio.")

        st.subheader("Resumen por actividad")
        flow_summary = sheet[sheet["Actividad"] != "Sin movimiento"].groupby(
            ["Actividad", "Origen / Aplicación"], as_index=False)["Cambio"].sum()
        if flow_summary.empty:
            st.info("Aún no hay variaciones entre los dos periodos.")
        else:
            st.dataframe(flow_summary.style.format({"Cambio": "{:,.2f}"}),
                         **STRETCH, hide_index=True)

        with st.expander("Revisar clasificación por concepto"):
            st.caption(
                "El sistema propone la actividad según la naturaleza de la cuenta. "
                "Corrígela cuando la operación real tenga otra naturaleza. Solo se listan cuentas con movimiento."
            )
            options = [
                "Automático",
                "Origen | Operación", "Aplicación | Operación",
                "Origen | Inversión", "Aplicación | Inversión",
                "Origen | Financiamiento", "Aplicación | Financiamiento",
                "Origen | Revisar", "Aplicación | Revisar"
            ]
            moving = sheet.loc[sheet["Cambio"].abs() >= 0.005, "Concepto"].tolist()
            if not moving:
                st.info("No hay cuentas con movimiento para clasificar.")
            else:
                with st.form("override_form", border=False):
                    selected = {}
                    cols = st.columns(2)
                    for i, concept in enumerate(moving):
                        current = overrides.get(concept, "Automático")
                        selected[concept] = cols[i % 2].selectbox(
                            concept, options,
                            index=options.index(current) if current in options else 0,
                            key="override_" + concept
                        )
                    save_overrides = st.form_submit_button("Guardar clasificaciones", type="primary")
                if save_overrides:
                    with db() as con:
                        con.execute(
                            "UPDATE analyses SET adjustments_json=? WHERE folio=? AND owner_id=?",
                            (json.dumps({**overrides, **selected}, ensure_ascii=False), folio, record["owner_id"])
                        )
                    st.success("Clasificaciones guardadas.")
                    st.rerun()

        st.info(
            "La hoja verde identifica fuentes y usos de recursos por variaciones de cuentas. "
            "El flujo formal de efectivo requiere información adicional sobre operaciones "
            "reales de caja/bancos, ajustes no monetarios y el estado de resultados."
        )
        st.download_button(
            "Exportar hoja verde a CSV",
            sheet.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{folio}_hoja_verde.csv", mime="text/csv"
        )

    # ----- Razones financieras -----
    elif page == "Razones financieras":
        st.info(
            "Para rentabilidad y rotaciones captura las cuentas del estado de resultados. "
            "Las rotaciones con saldos finales son aproximaciones; idealmente se usan saldos promedio y compras netas."
        )
        with st.expander("¿Qué mide cada razón financiera?"):
            H('<div class="gloss">' + "".join(
                f'<div><b>{esc(n)}</b><span>{esc(RATIO_DEFS[n][0])}</span>{esc(RATIO_INFO[n][0])}<br><em>{esc(RATIO_INFO[n][1])}</em></div>'
                for n in RATIO_DEFS) + '</div>')
        c1, c2 = st.columns([3, 1])
        chosen = c1.multiselect("Razones a calcular", list(RATIO_DEFS.keys()), default=["Razón circulante"])
        period = c2.radio("Periodo", ["Anterior", "Reciente"], horizontal=True)
        if st.button("Calcular y guardar razones", type="primary", disabled=not chosen):
            t = old_totals if period == "Anterior" else new_totals
            existing = json.loads(record["ratios_json"] or "[]")
            for name in chosen:
                result = calc_ratio(name, t, period, cur)
                existing = [r for r in existing if not (r["Razón"] == name and r["Periodo"] == period)]
                existing.append(result)
            with db() as con:
                con.execute(
                    "UPDATE analyses SET ratios_json=? WHERE folio=? AND owner_id=?",
                    (json.dumps(existing, ensure_ascii=False), folio, record["owner_id"])
                )
            st.success("Razones guardadas.")
            st.rerun()

        ratios = json.loads(record["ratios_json"] or "[]")
        if not ratios:
            empty_state("percent", "Aún no has calculado razones",
                        "Elige una o varias razones, el periodo y pulsa «Calcular y guardar razones».")
        else:
            st.subheader(f"Resultados guardados ({len(ratios)})")
            cards = ""
            for ratio in ratios:
                value = ratio.get("Resultado")
                unit = ratio.get("Unidad", "")
                if value is None:
                    big, small = "No calculable", ""
                elif unit == "moneda":
                    big, small = fmt_money(value), cur
                else:
                    big, small = f"{value:,.2f}", ("%" if unit == "%" else unit)
                tone = "warn" if value is None else ""
                focus_class = (
                    " decision-focus"
                    if decision_focus_ratio == ratio.get("Razón")
                    and (
                        not decision_focus_period
                        or decision_focus_period == ratio.get("Periodo")
                    ) else ""
                )
                focus_id = ' id="decision-source-ratio"' if focus_class else ""
                cards += (
                    f'<div{focus_id} class="ratio{focus_class}"><div class="ratio-top"><span class="ratio-name">{esc(ratio["Razón"])}</span>'
                    f'{badge(ratio["Periodo"], tone or "")}</div>'
                    f'<div class="ratio-value">{esc(big)}<small>{esc(small)}</small></div>'
                    f'<dl><dt>Qué es</dt><dd>{esc(RATIO_INFO.get(ratio["Razón"], ("", ""))[0])}</dd><dt>Fórmula</dt><dd>{esc(ratio["Fórmula"])}</dd>'
                    f'<dt>Sustitución</dt><dd class="mono">{esc(ratio["Sustitución"])}</dd></dl>'
                    f'<p>{esc(ratio["Interpretación"])}</p></div>'
                )
            H(f'<div class="ratios">{cards}</div>')
            if decision_scroll_to_source and decision_focus_ratio:
                scroll_to_element("decision-source-ratio")
            with st.expander("Ver tabla de razones"):
                ratio_table = pd.DataFrame(ratios).drop(
                    columns=["Análisis inteligente", "Recomendación"], errors="ignore")
                st.dataframe(ratio_table, **STRETCH, hide_index=True)

            if not st.session_state.get("confirm_delete_ratios"):
                if st.button("Eliminar todas las razones guardadas"):
                    st.session_state.confirm_delete_ratios = True
                    st.rerun()
            else:
                st.warning("Se eliminarán todas las razones guardadas de este análisis. Esta acción no se puede deshacer.")
                c1, c2, _ = st.columns([1, 1, 2])
                if c1.button("Sí, eliminar", type="primary", **STRETCH):
                    with db() as con:
                        con.execute("UPDATE analyses SET ratios_json='[]' WHERE folio=? AND owner_id=?",
                                    (folio, record["owner_id"]))
                    st.session_state.confirm_delete_ratios = False
                    st.rerun()
                if c2.button("Cancelar", **STRETCH):
                    st.session_state.confirm_delete_ratios = False
                    st.rerun()

    # ----- Gráficas -----
    elif page == "Gráficas":
        c1, c2 = st.columns([2, 1])
        chart_type = c1.selectbox("Tipo de gráfica", [
            "Barras comparativas", "Líneas comparativas",
            "Dispersión de puntos", "Histograma de variaciones",
            "Composición por categoría", "Aumentos y disminuciones"
        ])
        period = None
        if chart_type == "Composición por categoría":
            period = c2.radio("Periodo", ["Anterior", "Reciente"], horizontal=True)

        # Se omiten cuentas sin saldo en ambos periodos para que la gráfica sea legible.
        base = df[(df["Anterior"] != 0) | (df["Reciente"] != 0)]
        if base.empty:
            empty_state("bar-chart", "Sin saldos para graficar",
                        "Captura importes distintos de cero para ver las gráficas.")
        elif chart_type == "Composición por categoría":
            chart_df = df.groupby("Categoria", as_index=False)[period].sum()
            chart_df = chart_df[chart_df[period] > 0]
            if chart_df.empty:
                st.warning("No hay importes positivos para esta gráfica.")
            else:
                fig = px.pie(chart_df, names="Categoria", values=period, hole=0.58, title="Composición por categoría")
                fig.update_traces(textposition="outside", textinfo="percent+label", marker=dict(line=dict(color="#fff", width=2)))
                fig.update_layout(showlegend=False)
                show_chart(fig)
        elif chart_type == "Histograma de variaciones":
            fig = px.histogram(base, x="Cambio", nbins=15, title="Distribución de variaciones por cuenta")
            fig.update_traces(marker_color="#013E8F", marker_line_color="#fff", marker_line_width=1)
            show_chart(fig)
        elif chart_type == "Dispersión de puntos":
            fig = px.scatter(base, x="Anterior", y="Reciente", color="Categoria",
                             hover_name="Concepto", title="Saldo anterior frente a saldo reciente")
            low = min(float(base["Anterior"].min()), float(base["Reciente"].min()))
            high = max(float(base["Anterior"].max()), float(base["Reciente"].max()))
            fig.add_shape(type="line", x0=low, y0=low, x1=high, y1=high, line=dict(dash="dash", color="#8FA3C0"))
            fig.update_traces(marker=dict(size=10, line=dict(color="#fff", width=1)))
            show_chart(fig)
            st.caption("Sobre la diagonal: sin cambio. Arriba: aumentó. Abajo: disminuyó.")
        elif chart_type == "Líneas comparativas":
            long_df = base.melt(id_vars=["Concepto"], value_vars=["Anterior", "Reciente"],
                                var_name="Periodo", value_name="Saldo")
            fig = px.line(long_df, x="Periodo", y="Saldo", color="Concepto", markers=True, title="Saldos por periodo")
            show_chart(fig)
        elif chart_type == "Aumentos y disminuciones":
            long_df = base.melt(id_vars=["Concepto"], value_vars=["Aumento", "Disminucion"],
                                var_name="Movimiento", value_name="Importe")
            fig = px.bar(long_df, x="Concepto", y="Importe", color="Movimiento", barmode="group",
                         color_discrete_map=MOVE_COLORS, title="Aumentos y disminuciones")
            fig.update_xaxes(tickangle=-35)
            show_chart(fig)
        else:
            long_df = base.melt(id_vars=["Concepto", "Categoria"], value_vars=["Anterior", "Reciente"],
                                var_name="Periodo", value_name="Saldo")
            fig = px.bar(long_df, x="Concepto", y="Saldo", color="Periodo", barmode="group",
                         color_discrete_map=PERIOD_COLORS, hover_data=["Categoria"], title="Comparación de saldos")
            fig.update_xaxes(tickangle=-35)
            show_chart(fig)

        with st.expander("Ver datos de la gráfica"):
            st.dataframe(df[["Concepto", "Categoria", "Anterior", "Reciente", "Cambio"]],
                         **STRETCH, hide_index=True)

    # ----- Reporte gerencial -----
    elif page == "Reporte gerencial":
        kpi_row([
            ("Activo total reciente", fmt_money(new_totals["Activo total"]), cur, "", "brand"),
            ("Pasivo total reciente", fmt_money(new_totals["Pasivo total"]), cur),
            ("Capital contable", fmt_money(new_totals["Capital total"]), cur),
            ("Capital de trabajo", fmt_money(new_totals["Capital de trabajo"]), cur, "",
             "up" if new_totals["Capital de trabajo"] > 0 else "down" if new_totals["Capital de trabajo"] < 0 else ""),
        ])

        st.subheader("Observaciones automáticas")
        difference = new_totals["Activo total"] - new_totals["Pasivo más capital"]
        if abs(difference) < 0.01:
            st.success("El balance reciente cuadra aritméticamente.")
        else:
            st.warning(
                f"El balance reciente no cuadra: activo total menos pasivo y capital = "
                f"{money(difference, cur)}. Revisa las cuentas capturadas."
            )
        if new_totals["Activo total"] != 0:
            debt_pct = new_totals["Pasivo total"] / new_totals["Activo total"] * 100
            st.write(f"El pasivo representa {debt_pct:.2f}% del activo total.")
        else:
            st.write("No es posible calcular endeudamiento porque el activo total es cero.")
        st.write(
            "El capital de trabajo es "
            + ("positivo" if new_totals["Capital de trabajo"] > 0 else "negativo" if new_totals["Capital de trabajo"] < 0 else "igual a cero")
            + f": {money(new_totals['Capital de trabajo'], cur)}."
        )

        ratios = json.loads(record["ratios_json"] or "[]")
        st.subheader("Exportar")
        st.caption(
            f"El PDF incluye la hoja verde y {len(ratios)} razón(es) financiera(s) guardada(s)."
            if ratios else
            "El PDF incluye la hoja verde. Calcula razones en «Razones financieras» para añadirlas al reporte."
        )
        pdf = make_pdf(record, sheet, ratios, new_totals)
        st.download_button(
            "Descargar reporte gerencial PDF", pdf,
            file_name=f"{folio}_reporte_gerencial.pdf",
            mime="application/pdf", type="primary"
        )


    # ----- Estados financieros -----
    elif page == "Estados financieros":
        who = record["elaboro"] or record["owner_name"]

        def sign(role, name):
            return f'<div class="sign"><small>{role}</small><b>{esc(name) if name else "Pendiente"}</b></div>'

        H(f'<div class="sign-grid">{sign("Elaboró", who)}{sign("Revisó", record["reviso"])}'
          f'{sign("Autorizó", record["autorizo"])}</div>')
        if is_admin:
            H(f'<div class="lock">{icon("lock", 18)}<div>Estados protegidos para los contadores. '
              'Como administrador puedes modificarlos desde «Editar estados».</div></div>')
        else:
            H(f'<div class="lock">{icon("lock", 18)}<div>Estos estados financieros están protegidos. '
              'Para modificarlos, envía una solicitud al administrador desde «Solicitudes de cambio».</div></div>')

        headers = [record["old_date"], record["new_date"]]
        statement_tabs = ["Balance general", "Estado de resultados", "Flujo de efectivo"]
        if decision_scroll_to_source and decision_focus_tab:
            st.session_state["financial_statement_tabs"] = decision_focus_tab
        tab_bal, tab_res, tab_cf = st.tabs(
            statement_tabs,
            default=decision_focus_tab,
            key="financial_statement_tabs",
        )

        with tab_bal:
            rows = []
            for title, cats, tot_label, tot_key in (
                ("Activo", ("Activo circulante", "Activo no circulante"), "Total activo", "Activo total"),
                ("Pasivo", ("Pasivo circulante", "Pasivo no circulante"), "Total pasivo", "Pasivo total"),
                ("Capital contable", ("Capital contable",), "Total capital contable", "Capital total"),
            ):
                rows.append(("sec", title, []))
                for cat in cats:
                    sub = df[(df["Categoria"] == cat) & ((df["Anterior"] != 0) | (df["Reciente"] != 0))]
                    for _, r in sub.iterrows():
                        sign_ = -1 if r["Concepto"] in CUENTAS_CONTRA_ACTIVO else 1
                        name = ("(−) " if sign_ < 0 else "") + r["Concepto"]
                        rows.append(("item", name, [sign_ * abs(r["Anterior"]), sign_ * abs(r["Reciente"])]))
                    if len(cats) > 1:
                        rows.append(("tot", f"Total {cat.lower()}", [old_totals[cat], new_totals[cat]]))
                rows.append(("grand", tot_label, [old_totals[tot_key], new_totals[tot_key]]))
            rows.append(("grand", "Total pasivo + capital contable",
                         [old_totals["Pasivo más capital"], new_totals["Pasivo más capital"]]))
            statement_table(
                rows, headers, decision_focus_labels, "decision-source-row-balance"
            )
            if decision_scroll_to_source and decision_focus_tab == "Balance general":
                scroll_to_element("decision-source-row-balance")
            gap = new_totals["Activo total"] - new_totals["Pasivo más capital"]
            if abs(gap) < 0.01:
                st.success("El balance reciente cuadra: activo = pasivo + capital.")
            else:
                st.warning(f"El balance reciente no cuadra (diferencia {money(gap, cur)}).")

        with tab_res:
            res = df[(df["Categoria"] == "Estado de resultados (opcional)") & ((df["Anterior"] != 0) | (df["Reciente"] != 0))]
            if res.empty:
                st.info("No hay cuentas del estado de resultados con saldo.")
            else:
                totals_names = {"Utilidad bruta", "Utilidad operativa", "Utilidad neta"}
                statement_table(
                    [("tot" if r["Concepto"] in totals_names else "item", r["Concepto"], [r["Anterior"], r["Reciente"]])
                     for _, r in res.iterrows()],
                    headers,
                    decision_focus_labels,
                    "decision-source-row-results",
                )
                if decision_scroll_to_source and decision_focus_tab == "Estado de resultados":
                    scroll_to_element("decision-source-row-results")

        with tab_cf:
            cf = cash_flow(df)
            op_t, inv_t, fin_t = (s[3] for s in cf["sections"])
            kpi_row([
                ("Operación", fmt_money(op_t), cur, "", "up" if op_t >= 0 else "down"),
                ("Inversión", fmt_money(inv_t), cur, "", "up" if inv_t >= 0 else "down"),
                ("Financiamiento", fmt_money(fin_t), cur, "", "up" if fin_t >= 0 else "down"),
                ("Variación de efectivo", fmt_money(cf["net"]), cur,
                 f"{fmt_money(cf['start'])} → {fmt_money(cf['start'] + cf['net'])}", "brand"),
            ])
            rows = []
            for title, items, sub_label, sub in cf["sections"]:
                rows.append(("sec", title, []))
                rows += [("item", label, [v]) for label, v in items] or [("item", "Sin movimientos", [None])]
                rows.append(("tot", sub_label, [sub]))
            rows += [("grand", "Aumento (disminución) neto de efectivo", [cf["net"]]),
                     ("item", "Efectivo al inicio del periodo", [cf["start"]]),
                     ("grand", "Efectivo al final del periodo", [cf["start"] + cf["net"]])]
            statement_table(
                rows,
                [f"{record['old_date']} → {record['new_date']}"],
                decision_focus_labels,
                "decision-source-row-cashflow",
            )
            if decision_scroll_to_source and decision_focus_tab == "Flujo de efectivo":
                scroll_to_element("decision-source-row-cashflow")
            if abs(cf["diff"]) < 0.01:
                st.success("El flujo concilia con el efectivo (Caja + Bancos) del balance.")
            else:
                st.warning(
                    f"El flujo no concilia: el efectivo final del balance es {money(cf['end'], cur)} y el flujo da "
                    f"{money(cf['start'] + cf['net'], cur)} (diferencia {money(cf['diff'], cur)}). "
                    "Normalmente se debe a que el balance no cuadra en alguno de los dos periodos."
                )
            if abs(cf["ni"]) < 0.005:
                st.info("No capturaste «Utilidad neta»: sin ella no se separa el resultado del periodo de los "
                        "movimientos de capital y la clasificación entre operación y financiamiento será imprecisa.")
            st.caption("Método indirecto, calculado con las variaciones entre ambos balances. "
                       "Efectivo = Caja + Bancos. Es un estado preliminar sujeto a revisión del contador.")

        with st.expander("Historial de cambios"):
            with db() as con:
                log = con.execute(
                    "SELECT l.created_at, u.username, l.action, l.detail FROM analysis_log l "
                    "JOIN users u ON u.id=l.user_id WHERE l.folio=? ORDER BY l.id DESC", (folio,)).fetchall()
            if log:
                st.dataframe([{"Fecha": x["created_at"].replace("T", " "), "Usuario": x["username"],
                               "Acción": x["action"], "Detalle": x["detail"]} for x in log],
                             **STRETCH, hide_index=True)
            else:
                st.caption("Sin eventos registrados todavía.")

    # ----- Documentos -----
    elif page == "Documentos":
        flash()
        st.info("Los documentos subidos no se pueden reemplazar ni eliminar por los contadores. "
                "Para corregir uno, solicita el cambio al administrador.")
        with db() as con:
            files = con.execute(
                "SELECT f.id, f.filename, f.kind, f.size, f.sha256, f.created_at, f.data, u.username "
                "FROM attachments f JOIN users u ON u.id=f.uploaded_by WHERE f.folio=? ORDER BY f.id DESC",
                (folio,)).fetchall()

        pending_del = st.session_state.get("confirm_del_file")
        if is_admin and pending_del:
            st.warning("¿Eliminar este documento? Esta acción no se puede deshacer.")
            c1, c2, _ = st.columns([1, 1, 2])
            if c1.button("Sí, eliminar", type="primary", **STRETCH, key="del_yes"):
                with db() as con:
                    name = con.execute("SELECT filename FROM attachments WHERE id=? AND folio=?", (pending_del, folio)).fetchone()
                    con.execute("DELETE FROM attachments WHERE id=? AND folio=?", (pending_del, folio))
                    log_event(folio, user["id"], "Documento eliminado", name["filename"] if name else "", con)
                st.session_state.confirm_del_file = None
                st.session_state.flash = "Documento eliminado."
                st.rerun()
            if c2.button("Cancelar", **STRETCH, key="del_no"):
                st.session_state.confirm_del_file = None
                st.rerun()

        st.subheader(f"Archivos ({len(files)})")
        if not files:
            empty_state("file-text", "Aún no hay documentos", "Sube aquí los estados financieros en PDF u otros archivos de respaldo.")
        for f in files:
            c = st.columns([3.4, 2.2, 1.5, 1.2] if is_admin else [3.4, 2.2, 1.5], **_COL_VA)
            H(f'<b>{esc(f["filename"])}</b><br>{badge(f["kind"])}', c[0])
            H(f'<span class="mono">{f["size"] / 1024:,.0f} KB · SHA-256 {esc(f["sha256"][:12])}…</span><br>'
              f'<span class="mono">{esc(f["username"])} · {esc(f["created_at"][:16].replace("T", " "))}</span>', c[1])
            c[2].download_button("Descargar", bytes(f["data"]), file_name=f["filename"],
                                 key=f"dl_{f['id']}", **STRETCH)
            if is_admin and c[3].button("Eliminar", key=f"del_{f['id']}", **STRETCH):
                st.session_state.confirm_del_file = f["id"]
                st.rerun()
            H('<hr class="row-sep">')

        st.subheader("Agregar documentos")
        with st.form("upload_form", clear_on_submit=True):
            kind = st.selectbox("Tipo de documento", DOC_KINDS)
            ups = st.file_uploader(f"Archivos (máx. {MAX_MB} MB c/u)", accept_multiple_files=True, type=sorted(ALLOWED_EXT))
            go_up = st.form_submit_button("Subir documentos", type="primary")
        if go_up:
            errors = [e for e in (validate_upload(u) for u in ups) if e]
            if not ups:
                st.warning("Selecciona al menos un archivo.")
            elif errors:
                for e in errors:
                    st.error(e)
            else:
                with db() as con:
                    for u in ups:
                        add_attachment(con, folio, u, kind, user["id"])
                st.session_state.flash = f"{len(ups)} documento(s) agregado(s)."
                st.rerun()

    # ----- Editar estados (solo administrador) -----
    elif page == "Editar estados":
        if not is_admin:
            st.error("Acceso exclusivo para administradores.")
            st.stop()
        flash()
        with db() as con:
            open_reqs = con.execute(
                "SELECT r.id, r.reason, u.username FROM change_requests r JOIN users u ON u.id=r.requester_id "
                "WHERE r.folio=? AND r.status='pendiente' ORDER BY r.id", (folio,)).fetchall()
        st.info("Todo cambio queda registrado en el historial con tu usuario y el motivo. "
                "Los importes no pueden ser negativos.")
        ver = st.session_state.get("edit_ver", 0)
        with st.form("edit_statements"):
            c1, c2, c3 = st.columns(3)
            elaboro = c1.text_input("Elaboró", value=record["elaboro"] or record["owner_name"])
            reviso = c2.text_input("Revisó", value=record["reviso"] or "")
            autorizo = c3.text_input("Autorizó", value=record["autorizo"] or "")
            edits = {}
            for cat in CATALOGO:
                sub = df[df["Categoria"] == cat][["Concepto", "Anterior", "Reciente"]]
                if sub.empty:
                    continue
                with st.expander(cat):
                    edits[cat] = st.data_editor(
                        sub, key=f"adm_{cat}_{ver}", hide_index=True, disabled=["Concepto"], **STRETCH,
                        column_config={
                            "Anterior": st.column_config.NumberColumn(record["old_date"], min_value=0.0, step=100.0, format="%.2f"),
                            "Reciente": st.column_config.NumberColumn(record["new_date"], min_value=0.0, step=100.0, format="%.2f"),
                        })
            reason = st.text_input("Motivo del cambio *")
            req_opts = {"Ninguna": None, **{f"#{r['id']} · {r['username']}: {r['reason'][:70]}": r["id"] for r in open_reqs}}
            linked = st.selectbox("Solicitud que atiende este cambio", list(req_opts))
            submitted = st.form_submit_button("Guardar cambios", type="primary")
        if submitted:
            if not reason.strip():
                st.error("Indica el motivo del cambio.")
            else:
                work = df.set_index("Concepto")
                changes = []
                for cat, ed in edits.items():
                    for _, row in ed.iterrows():
                        a = max(0.0, float(row["Anterior"] or 0))
                        r_ = max(0.0, float(row["Reciente"] or 0))
                        old = work.loc[row["Concepto"]]
                        if abs(old["Anterior"] - a) >= 0.005 or abs(old["Reciente"] - r_) >= 0.005:
                            changes.append(f"{row['Concepto']}: {old['Anterior']:,.2f}→{a:,.2f} / {old['Reciente']:,.2f}→{r_:,.2f}")
                            work.loc[row["Concepto"], ["Anterior", "Reciente"]] = [a, r_]
                meta_old = (record["elaboro"] or record["owner_name"], record["reviso"] or "", record["autorizo"] or "")
                meta_new = (elaboro.strip(), reviso.strip(), autorizo.strip())
                if not changes and meta_old == meta_new:
                    st.info("No hay cambios que guardar.")
                else:
                    updated = clean_accounts(work.reset_index()[["Concepto", "Categoria", "Anterior", "Reciente"]])
                    detail = reason.strip() + " | " + "; ".join(changes[:15]) + (" …" if len(changes) > 15 else "")
                    if meta_old != meta_new:
                        detail += f" | Firmas: elaboró={meta_new[0]}, revisó={meta_new[1]}, autorizó={meta_new[2]}"
                    with db() as con:
                        con.execute("UPDATE analyses SET accounts_json=?, elaboro=?, reviso=?, autorizo=? WHERE folio=?",
                                    (json.dumps(updated.to_dict("records"), ensure_ascii=False), *meta_new, folio))
                        log_event(folio, user["id"], "Cambio de estados financieros", detail, con)
                        rid = req_opts[linked]
                        if rid:
                            con.execute("UPDATE change_requests SET status='atendida', resolver_id=?, resolution_note=?, resolved_at=? WHERE id=?",
                                        (user["id"], reason.strip(), now_iso(), rid))
                            log_event(folio, user["id"], "Solicitud atendida", f"#{rid}", con)
                    st.session_state.edit_ver = ver + 1
                    st.session_state.flash = f"Cambios guardados ({len(changes)} cuenta(s) modificada(s))."
                    st.rerun()


# --------------------------- Solicitudes de cambio ---------------------------

elif page == "Solicitudes de cambio":
    page_header("Solicitudes de cambio",
                "Revisa y atiende las solicitudes de los contadores." if is_admin
                else "Los estados guardados solo los modifica el administrador: pide aquí el cambio.", "Control")
    flash()
    badge_tone = {"pendiente": "warn", "atendida": "ok", "rechazada": "err"}
    q_base = ("SELECT r.*, a.company, u.username AS requester, v.username AS resolver FROM change_requests r "
              "JOIN analyses a ON a.folio=r.folio JOIN users u ON u.id=r.requester_id "
              "LEFT JOIN users v ON v.id=r.resolver_id ")

    if is_admin:
        with db() as con:
            pend = con.execute(q_base + "WHERE r.status='pendiente' ORDER BY r.id").fetchall()
            done = con.execute(q_base + "WHERE r.status!='pendiente' ORDER BY r.resolved_at DESC LIMIT 30").fetchall()
        st.subheader(f"Pendientes ({len(pend)})")
        if not pend:
            empty_state("check", "Sin solicitudes pendientes", "Cuando un contador pida un cambio, aparecerá aquí.")
        for r in pend:
            with st.container(border=True):
                H(f'<b>{esc(r["company"])}</b> <span class="mono">{esc(r["folio"])}</span> {badge("Pendiente", "warn")}<br>'
                  f'<span class="mono">Solicitó {esc(r["requester"])} · {esc(r["created_at"][:16].replace("T", " "))}</span>')
                st.text(r["reason"])
                if st.button("Abrir y editar estados", key=f"req_open_{r['id']}"):
                    st.session_state.current_folio = r["folio"]
                    go("Editar estados")
                with st.expander("Responder solicitud"):
                    with st.form(f"req_res_{r['id']}", border=False):
                        note = st.text_input("Nota para el contador", key=f"req_note_{r['id']}")
                        a, b = st.columns(2)
                        ok_btn = a.form_submit_button("Marcar como atendida", type="primary")
                        no_btn = b.form_submit_button("Rechazar")
                    if ok_btn or no_btn:
                        if no_btn and not note.strip():
                            st.error("Indica el motivo del rechazo en la nota.")
                        else:
                            status = "atendida" if ok_btn else "rechazada"
                            with db() as con:
                                con.execute("UPDATE change_requests SET status=?, resolver_id=?, resolution_note=?, resolved_at=? WHERE id=?",
                                            (status, user["id"], note.strip(), now_iso(), r["id"]))
                                log_event(r["folio"], user["id"], f"Solicitud {status}", f"#{r['id']} {note.strip()}", con)
                            st.session_state.flash = f"Solicitud {status}."
                            st.rerun()
        if done:
            st.subheader("Historial")
            st.dataframe([{"Folio": x["folio"], "Empresa": x["company"], "Solicitó": x["requester"],
                           "Estado": x["status"].capitalize(), "Atendió": x["resolver"] or "—",
                           "Nota": x["resolution_note"] or "", "Fecha": (x["resolved_at"] or "")[:16].replace("T", " ")}
                          for x in done], **STRETCH, hide_index=True)
    else:
        if active:
            st.subheader(f"Nueva solicitud · {active['company']}")
            with st.form("new_request"):
                reason = st.text_area("¿Qué debe cambiar y por qué? *", height=110,
                                      placeholder="Ej.: El saldo de Bancos del periodo reciente debe ser 125,400.00 según el estado de cuenta.")
                sent = st.form_submit_button("Enviar solicitud al administrador", type="primary")
            if sent:
                if len(reason.strip()) < 15:
                    st.error("Describe el cambio con al menos 15 caracteres.")
                else:
                    with db() as con:
                        cur_ = con.execute("INSERT INTO change_requests(folio,requester_id,reason,created_at) VALUES(?,?,?,?)",
                                           (active["folio"], user["id"], reason.strip(), now_iso()))
                        log_event(active["folio"], user["id"], "Solicitud de cambio", f"#{cur_.lastrowid} {reason.strip()[:200]}", con)
                    st.session_state.flash = "Solicitud enviada. El administrador la revisará."
                    st.rerun()
        else:
            st.info("Abre un análisis desde el Panel para solicitar un cambio sobre él.")
        with db() as con:
            mine = con.execute(q_base + "WHERE r.requester_id=? ORDER BY r.id DESC", (user["id"],)).fetchall()
        st.subheader("Mis solicitudes")
        if not mine:
            st.caption("Aún no has enviado solicitudes.")
        for r in mine:
            with st.container(border=True):
                H(f'<b>{esc(r["company"])}</b> <span class="mono">{esc(r["folio"])}</span> '
                  f'{badge(r["status"].capitalize(), badge_tone.get(r["status"], ""))}')
                st.text(r["reason"])
                if r["resolution_note"]:
                    H(f'<span class="mono">Respuesta de {esc(r["resolver"] or "—")}: {esc(r["resolution_note"])}</span>')


# --------------------------- Consulta por folio ---------------------------

elif page == "Consulta por folio":
    page_header("Consulta por folio", "Como administrador puedes abrir cualquier análisis." if is_admin else "Solo puedes abrir los análisis asociados a tu usuario.", "Análisis")
    with st.form("lookup_form"):
        search_folio = st.text_input("Folio completo", placeholder="FIN-20260101-AB12CD34")
        searched = st.form_submit_button("Consultar análisis", type="primary")
    if searched:
        found = analysis_for(search_folio.strip().upper(), user)
        if not found:
            st.session_state.lookup_folio = None
            st.error("Folio no encontrado o no tienes permiso para consultarlo.")
        else:
            st.session_state.lookup_folio = found["folio"]
            st.session_state.current_folio = found["folio"]
            st.rerun()

    lookup = st.session_state.get("lookup_folio")
    record = analysis_for(lookup, user)
    if record:
        H(f'<div class="chips">{badge("Análisis recuperado", "ok")}</div>')
        kpi_row([
            ("Empresa", record["company"], "", "", "brand"),
            ("RFC", record["rfc"] or "No indicado"),
            ("Comparación", f"{record['old_date']} → {record['new_date']}"),
            ("Creado", record["created_at"].replace("T", " ")),
        ] + ([("Contador", record["owner_name"])] if is_admin else []))
        if btn("Abrir hoja verde", "table_view", type="primary", key="lookup_open"):
            go("Hoja verde")
        st.subheader("Cuentas capturadas")
        st.dataframe(pd.DataFrame(json.loads(record["accounts_json"])), **STRETCH, hide_index=True)