from datetime import datetime
import time
import streamlit as st
import pandas as pd
import numpy as np
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError, RequestException
import json
import pandas as pd
import pytz
from head import head

def get_unixtimestamp(data, fuso='America/Sao_Paulo'):
  formato = "%Y-%m-%d %H:%M:%S"
  tz = pytz.timezone(fuso)
  return int(tz.localize(datetime.strptime(data, formato)).timestamp())

def get_programacao(uf, cidade, data_inicio, data_fim):
  url = "https://www.clarotvmais.com.br/avsclient/1.2/epg/livechannels"
  timeout_seconds = 3

  parametros = {
    "startTime" : data_inicio,
    "endTime" : data_fim,
    "location" : cidade + "," + uf,
    "channel" : "PCTV"
  }

  try:
    response = requests.get(url, params=parametros, timeout=timeout_seconds)
    response.raise_for_status()
    return response.json()
  except requests.exceptions.HTTPError as e:
    print(f"Erro HTTP: {e}")
  except requests.exceptions.ConnectionError as e:
    print(f"Erro de Conexão: {e}")
  except requests.exceptions.Timeout as e:
    print(f"Tempo de Espera Excedido: {e}")
  except requests.exceptions.RequestException as e:
    print(f"Ocorreu um erro inesperado: {e}")

def get_estados():
  path = 'data/states.json'
  try:
    estados = pd.read_json(path)
    return estados['name']
  except FileNotFoundError:
    print(f"Erro: O arquivo '{path}' não foi encontrado.")
  except json.JSONDecodeError:
    print(f"Erro: O arquivo '{path}' não é um JSON válido.")
  except Exception as e:
    print(f"Ocorreu um erro: {e}")

def get_cidades(estado):
  path = 'data/cities.json'
  try:
    cidades = pd.read_json(path)
    cidades_estado = cidades[cidades['UF-nome'] == estado]
    return cidades_estado['name']
  except FileNotFoundError:
    print(f"Erro: O arquivo '{path}' não foi encontrado.")
  except json.JSONDecodeError:
    print(f"Erro: O arquivo '{path}' não é um JSON válido.")
  except Exception as e:
    print(f"Ocorreu um erro: {e}")
  
def show_table(db):
  colunas = ['title', 'formattedTime']

  col1_header, col2_header = st.columns([0.2, 0.8])
  with col1_header:
    st.markdown("### **Canais**")
  with col2_header:
    st.markdown("### **Programas**")
  st.markdown("---")
  canais = db['response']['liveChannels']

  for canal in canais:
    col1, col2 = st.columns([0.2, 0.8], vertical_alignment="center")

    with col1:
      st.image(
        f"http://mondrian.claro.com.br/channels/inverse/{canal['mondrianLogo']}@2x.png",
        width=50
      )

    with col2:
      programas = pd.DataFrame(canal['schedules'])
      with st.expander(f"Programas do {canal['name']}"):
        st.dataframe(
          programas[['title','formattedTime']],
          column_config={
            'title' : 'Título',
            'formattedTime' : 'Horário',
          }, 
          use_container_width=True, 
          hide_index=True
        )
    st.markdown("---")

st.title("Programação TV Claro")

head()

estados = st.selectbox(
  "Estados",
  get_estados(),
  index=None,
  placeholder="Selecione um estado",
)

if estados:
  cidades_filtrada = get_cidades(estados)
  
  if len(cidades_filtrada) > 0:
    cidades = st.selectbox(
      "Cidades",
      cidades_filtrada,
      index=None,
      placeholder="Selecione uma cidade",      
    )
else:
  st.selectbox(
    "Cidades",
    ["Selecione uma cidade"],
    disabled=True
  )

col1, col2 = st.columns(2, vertical_alignment="bottom", gap="small")
with col1:
  data_inicio = st.date_input("Dia inicial", "today", format="DD/MM/YYYY")
  data_fim = st.date_input("Dia final", "today", format="DD/MM/YYYY")
with col2:
  hora_inicio = st.time_input("Hora inicial", "now", label_visibility="hidden", key="inicio")
  hora_fim = st.time_input("Hora final", "now", label_visibility="hidden", key="fim")

dt_ini = f"{data_inicio} {hora_inicio}"
dt_fim = f"{data_fim} {hora_fim}"
periodo_inicio = get_unixtimestamp(dt_ini)
periodo_fim = get_unixtimestamp(dt_fim)

if periodo_fim > periodo_inicio:

  if estados and cidades and periodo_inicio and periodo_fim: 
    if st.button("Carregar programação", icon="🤓", use_container_width=True, disabled=False):
      programacao = get_programacao(estados, cidades, periodo_inicio, periodo_fim)
      dados = pd.DataFrame(programacao)
      show_table(dados)
  else:
    st.button("Carregar programação", icon="🤓", use_container_width=True, disabled=True)
else:
  st.error("Data de inicio não pode ser inferior ou igual a data fim.")
