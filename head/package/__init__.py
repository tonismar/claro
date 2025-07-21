import streamlit.components.v1 as components

def head():
  components.html(
    open("head/frontend/index.html","r").read(),
    height=200,
  )
