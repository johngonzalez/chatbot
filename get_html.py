from bs4 import BeautifulSoup
import requests

# URL de la página principal del sitio web
url_banco = 'https://bancodebogota.com'
url_principal = url_banco + '/wps/portal/banco-de-bogota/bogota/mapa-del-sitio'

# Obtener el contenido HTML de la página principal
html = requests.get(url_principal).content

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

def extract_valuable_info_html(url):
    response = requests.get(url).content
    soup = BeautifulSoup(response, 'html.parser')
    contents = soup.find_all('div', class_='grancont-contenido')

    # Structure html
    title = soup.find('title').get_text()
    meta_url = f'<meta name="url" content="{url}">'
    set_html = lambda body: f'<html><head><title>{title}</title>{meta_url}</head>{body}</html>'
    if contents:
        body = '<body>' + ''.join([str(c) for c in contents]) + '</body>'
        return {'html': set_html(body), 'with_content': True}
    else:
        body = '<body>' + '</body>'
        return {'html': set_html(body), 'with_content': False}


for i, url in enumerate(urls):
    html_info = extract_valuable_info_html(url)
    file_name = url.split('/')[-1] or url.split('/')[-2]
    file_path = 'with_content' if html_info['with_content'] else 'no_content'
    with open(f'output/html/{file_path}/{i:0>3}_{file_name}.html', 'w') as f:
        f.write(html_info['html'])



# Notas:
# 1. Algunas urls no traen info y eso está bien, pq solo aparece un banner o no se encuentran
# 2. Algunas urls traen documentos pdf, deberían sacarsen (ver 098_tasas-y-tarifas)
# 3. Algunas páginas no aparecen en el mapa del sitio, tendría que hacerse una búsqueda más profunda (ver 164_impuestos, 012_todas-las-tarjetas-debito.html)
# 4. Algunas veces tenemos información adicional que no está en div.grancont-contenido (ver 164_impuestos)
# 5. La relación entre las urls puede ser importante
