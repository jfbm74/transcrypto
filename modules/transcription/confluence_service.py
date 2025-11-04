"""
Servicio de integración con Confluence API
Maneja la autenticación y publicación de documentos en Confluence Cloud
"""

import requests
import base64
from datetime import datetime
from flask import current_app
import re


class ConfluenceService:
    """Servicio para interactuar con la API de Confluence Cloud"""

    def __init__(self, email, api_token, base_url):
        """
        Inicializa el servicio de Confluence

        Args:
            email: Email de la cuenta de Atlassian
            api_token: API Token generado desde Atlassian
            base_url: URL base de Confluence (ej: https://zentratek.atlassian.net/wiki)
        """
        self.email = email
        self.api_token = api_token
        self.base_url = base_url.rstrip('/')

        # Remover /wiki si está al final de la URL para la API
        if self.base_url.endswith('/wiki'):
            self.api_base_url = self.base_url.replace('/wiki', '') + '/wiki/rest/api'
        else:
            self.api_base_url = self.base_url + '/rest/api'

        # Crear autenticación básica
        auth_string = f"{self.email}:{self.api_token}"
        self.auth_header = base64.b64encode(auth_string.encode()).decode()

        self.headers = {
            'Authorization': f'Basic {self.auth_header}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def test_connection(self):
        """
        Prueba la conexión con Confluence

        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            response = requests.get(
                f"{self.api_base_url}/space",
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                return {'success': True, 'message': 'Conexión exitosa con Confluence'}
            elif response.status_code == 401:
                return {'success': False, 'message': 'Credenciales inválidas. Verifica tu email y API token'}
            else:
                return {'success': False, 'message': f'Error de conexión: {response.status_code}'}

        except requests.exceptions.Timeout:
            return {'success': False, 'message': 'Tiempo de espera agotado. Verifica la URL de Confluence'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'message': 'No se pudo conectar a Confluence. Verifica la URL'}
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}

    def get_spaces(self):
        """
        Obtiene la lista de espacios de Confluence disponibles

        Returns:
            dict: {'success': bool, 'spaces': list, 'error': str}
        """
        try:
            response = requests.get(
                f"{self.api_base_url}/space",
                headers=self.headers,
                params={'limit': 100},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                spaces = [
                    {
                        'key': space['key'],
                        'name': space['name'],
                        'id': space['id']
                    }
                    for space in data.get('results', [])
                ]
                return {'success': True, 'spaces': spaces}
            else:
                return {'success': False, 'error': f'Error {response.status_code}: {response.text}', 'spaces': []}

        except Exception as e:
            current_app.logger.error(f"Error al obtener espacios de Confluence: {str(e)}")
            return {'success': False, 'error': str(e), 'spaces': []}

    def get_pages_in_space(self, space_key, limit=50):
        """
        Obtiene las páginas de un espacio específico

        Args:
            space_key: Clave del espacio
            limit: Número máximo de páginas a obtener

        Returns:
            dict: {'success': bool, 'pages': list, 'error': str}
        """
        try:
            response = requests.get(
                f"{self.api_base_url}/space/{space_key}/content/page",
                headers=self.headers,
                params={'limit': limit},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                pages = [
                    {
                        'id': page['id'],
                        'title': page['title'],
                        'type': page['type']
                    }
                    for page in data.get('results', [])
                ]
                return {'success': True, 'pages': pages}
            else:
                return {'success': False, 'error': f'Error {response.status_code}', 'pages': []}

        except Exception as e:
            current_app.logger.error(f"Error al obtener páginas: {str(e)}")
            return {'success': False, 'error': str(e), 'pages': []}

    def convert_to_storage_format(self, text):
        """
        Convierte texto plano a Confluence Storage Format (HTML)

        Args:
            text: Texto a convertir

        Returns:
            str: HTML en formato Storage de Confluence
        """
        # Escapar caracteres especiales HTML
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Convertir saltos de línea a párrafos
        paragraphs = text.split('\n\n')
        html_parts = []

        for para in paragraphs:
            if para.strip():
                # Detectar títulos (líneas que terminan en ':' o están en mayúsculas)
                lines = para.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Título si termina con ':'
                    if line.endswith(':') and len(line) < 100:
                        html_parts.append(f'<h2>{line[:-1]}</h2>')
                    # Detectar listas con viñetas (- o *)
                    elif line.startswith('- ') or line.startswith('* '):
                        html_parts.append(f'<li>{line[2:]}</li>')
                    # Párrafo normal
                    else:
                        # Reemplazar saltos de línea simples por <br/>
                        line_with_br = line.replace('\n', '<br/>')
                        html_parts.append(f'<p>{line_with_br}</p>')

        return ''.join(html_parts)

    def search_page_by_title(self, space_key, title):
        """
        Busca una página por título en un espacio

        Args:
            space_key: Clave del espacio
            title: Título de la página a buscar

        Returns:
            dict: Información de la página si existe, None si no existe
        """
        try:
            response = requests.get(
                f"{self.api_base_url}/content",
                headers=self.headers,
                params={
                    'spaceKey': space_key,
                    'title': title,
                    'type': 'page',
                    'status': 'current',
                    'expand': 'version'
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('results') and len(data['results']) > 0:
                    return data['results'][0]
            return None

        except Exception as e:
            current_app.logger.error(f"Error al buscar página: {str(e)}")
            return None

    def create_page(self, space_key, title, content, parent_id=None):
        """
        Crea una nueva página en Confluence

        Args:
            space_key: Clave del espacio donde crear la página
            title: Título de la página
            content: Contenido en Storage Format
            parent_id: ID de la página padre (opcional)

        Returns:
            dict: {'success': bool, 'page_id': str, 'page_url': str, 'error': str}
        """
        try:
            # Convertir contenido a Storage Format
            storage_content = self.convert_to_storage_format(content)

            page_data = {
                'type': 'page',
                'title': title,
                'space': {'key': space_key},
                'body': {
                    'storage': {
                        'value': storage_content,
                        'representation': 'storage'
                    }
                }
            }

            # Agregar página padre si se especifica
            if parent_id:
                page_data['ancestors'] = [{'id': parent_id}]

            response = requests.post(
                f"{self.api_base_url}/content",
                headers=self.headers,
                json=page_data,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                page_url = f"{self.base_url}/spaces/{space_key}/pages/{data['id']}"
                return {
                    'success': True,
                    'page_id': data['id'],
                    'page_url': page_url,
                    'message': 'Página creada exitosamente'
                }
            else:
                error_message = response.text
                current_app.logger.error(f"Error al crear página: {response.status_code} - {error_message}")
                return {
                    'success': False,
                    'error': f'Error {response.status_code}: {error_message}'
                }

        except Exception as e:
            current_app.logger.error(f"Excepción al crear página: {str(e)}")
            return {'success': False, 'error': str(e)}

    def update_page(self, page_id, title, content, current_version):
        """
        Actualiza una página existente en Confluence

        Args:
            page_id: ID de la página a actualizar
            title: Nuevo título de la página
            content: Nuevo contenido en Storage Format
            current_version: Versión actual de la página

        Returns:
            dict: {'success': bool, 'page_id': str, 'page_url': str, 'error': str}
        """
        try:
            # Convertir contenido a Storage Format
            storage_content = self.convert_to_storage_format(content)

            page_data = {
                'version': {'number': current_version + 1},
                'title': title,
                'type': 'page',
                'body': {
                    'storage': {
                        'value': storage_content,
                        'representation': 'storage'
                    }
                }
            }

            response = requests.put(
                f"{self.api_base_url}/content/{page_id}",
                headers=self.headers,
                json=page_data,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                page_url = data.get('_links', {}).get('webui', '')
                if page_url:
                    page_url = self.base_url.replace('/wiki', '') + page_url

                return {
                    'success': True,
                    'page_id': data['id'],
                    'page_url': page_url,
                    'message': 'Página actualizada exitosamente'
                }
            else:
                return {
                    'success': False,
                    'error': f'Error {response.status_code}: {response.text}'
                }

        except Exception as e:
            current_app.logger.error(f"Error al actualizar página: {str(e)}")
            return {'success': False, 'error': str(e)}

    def publish_or_update_page(self, space_key, title, content, parent_id=None, labels=None):
        """
        Publica o actualiza una página en Confluence.
        Si la página existe, la actualiza. Si no, la crea.

        Args:
            space_key: Clave del espacio
            title: Título de la página
            content: Contenido de la página
            parent_id: ID de la página padre (opcional)
            labels: Lista de etiquetas/labels (opcional)

        Returns:
            dict: Resultado de la operación
        """
        # Buscar si la página ya existe
        existing_page = self.search_page_by_title(space_key, title)

        if existing_page:
            # Actualizar página existente
            current_app.logger.info(f"Actualizando página existente: {title}")
            current_version = existing_page['version']['number']
            result = self.update_page(
                existing_page['id'],
                title,
                content,
                current_version
            )
        else:
            # Crear nueva página
            current_app.logger.info(f"Creando nueva página: {title}")
            result = self.create_page(space_key, title, content, parent_id)

        # Agregar labels si se especificaron y la operación fue exitosa
        if result['success'] and labels:
            self.add_labels(result['page_id'], labels)

        return result

    def add_labels(self, page_id, labels):
        """
        Agrega etiquetas/labels a una página

        Args:
            page_id: ID de la página
            labels: Lista de etiquetas (strings)
        """
        try:
            for label in labels:
                label_data = {
                    'prefix': 'global',
                    'name': label.lower().replace(' ', '-')
                }

                requests.post(
                    f"{self.api_base_url}/content/{page_id}/label",
                    headers=self.headers,
                    json=label_data,
                    timeout=10
                )
        except Exception as e:
            current_app.logger.warning(f"Error al agregar labels: {str(e)}")
