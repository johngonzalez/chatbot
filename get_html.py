from bs4 import BeautifulSoup
import requests
import re

# URL de la página principal del sitio web
url_banco = 'https://bancodebogota.com'
url = url_banco + '/wps/portal/banco-de-bogota/bogota/mapa-del-sitio'

# Obtener el contenido HTML de la página principal
html = requests.get(url).content

# Crear un objeto BeautifulSoup para analizar el HTML
soup = BeautifulSoup(html, 'html.parser')

# Tomar la seccion principal del mapa del sitio
mapa_sitio = soup.find_all('div', class_='grancont-contenido')[1]

# Encontrar todos los enlaces en la página principal
links = soup.find_all('a')

# Obtener los URLs de todos los enlaces
urls = []
for link in links:
    url_found = link.get('href')

    if url_found and url_found.startswith('/wps/portal'):
        urls.append(url_banco + url_found)

# Eliminar repetidas urls
urls = list(set(urls))


# Iteramos sobre algunas url y revisamos el resultado
for i, url in enumerate(urls[30:40]):
    print('-'*80)
    print(i+1, url)
    print('-'*80)
    response = requests.get(url).content
    soup = BeautifulSoup(response, 'html.parser')
    contenidos = soup.find_all('div', class_='grancont-contenido')
    # tabla = soup.find('table', class_='layoutColumn')
    # contenidos = tabla.find_all('tr')  # Se elimina encabezados y pie de pagina
    contenido = ''.join([c.get_text() for c in contenidos])
    contenido = re.sub('[\n]+', '\n', contenido) 
    print(contenido)


# Notas:
# 1. Algunas urls no traen info y eso está bien, pq solo aparece un banner o no se encuentran
# 2. Algunas urls traen documentos pdf, deberían sacarsen
# 3. La relación entre las urls puede ser muy importante
# 4. Tal vez pasar la salida a markdown sea lo mejor. Cómo le irá a chatgpt con html?
