#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script aprimorado para buscar imagens de plantas/frutas por nome científico
Fontes: Wikipedia/Wikimedia → iNaturalist
- Salva TODAS as imagens encontradas
- Usa múltiplas fontes para maior cobertura
- Identifica a melhor imagem para destaque
"""

import json
import re
import os
import sys
import requests
from datetime import datetime
from urllib.parse import quote, urlparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from functools import partial

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlantImageFinder:
    """Classe aprimorada para buscar múltiplas imagens de plantas usando nome científico"""

    def __init__(self, input_file='data.js', output_file='data_updated.js', max_workers=5):
        self.input_file = input_file
        self.output_file = output_file
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.images_found = 0
        self.images_failed = 0
        self.max_workers = max_workers
        self.delay_between_requests = 0.5  # Segundos entre requisições para evitar sobrecarga

    def extract_js_data(self):
        """Extrai o array JavaScript do arquivo"""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Encontrar o array data
            match = re.search(r'const data = \[(.*?)\];', content, re.DOTALL)
            if not match:
                raise ValueError("Não foi encontrado 'const data' no arquivo")

            array_content = match.group(1)

            # Converter JavaScript para JSON válido
            # Remover comentários de linha
            json_content = re.sub(r'//.*?$', '', array_content, flags=re.MULTILINE)
            
            # Remover comentários de bloco
            json_content = re.sub(r'/\*.*?\*/', '', json_content, flags=re.DOTALL)

            # Adicionar aspas nas chaves (converter JS object para JSON)
            # Padrão: palavra seguida de dois pontos
            json_content = re.sub(r'(\w+):', r'"\1":', json_content)
            
            # Corrigir aspas simples para duplas em strings
            # Primeiro, proteger aspas simples dentro de strings já com aspas duplas
            json_content = re.sub(r"'([^']*)'", lambda m: '"' + m.group(1).replace('"', '\\"') + '"', json_content)

            # Adicionar colchetes para formar array JSON
            json_str = f'[{json_content}]'

            # Parsear JSON
            items = json.loads(json_str)
            logger.info(f"✓ Carregados {len(items)} itens do arquivo")
            return items

        except FileNotFoundError:
            logger.error(f"Arquivo não encontrado: {self.input_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON: {e}")
            logger.error(f"Conteúdo problemático (primeiros 500 chars): {json_str[:500]}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            sys.exit(1)

    def search_wikimedia(self, scientific_name):
        """Busca múltiplas imagens na Wikimedia Commons"""
        images = []
        try:
            # Construir URL para Wikimedia Commons API
            url = "https://commons.wikimedia.org/w/api.php"
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': scientific_name,
                'srnamespace': '6',  # File namespace
                'srlimit': '10',  # Aumentado para buscar mais imagens
                'srprop': 'url|size|snippet'
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('query', {}).get('search'):
                for result in data['query']['search']:
                    file_title = result['title'].replace('File:', '')
                    
                    # Buscar URL da imagem
                    image_url = self._get_wikimedia_image_url(file_title)
                    if image_url:
                        images.append({
                            'source': 'wikimedia',
                            'url': image_url,
                            'title': result['title'],
                            'size': result.get('size', 0),
                            'snippet': result.get('snippet', ''),
                            'score': self._calculate_wikimedia_score(result)
                        })
            
            if images:
                logger.info(f"  ✓ Wikimedia: {scientific_name} - {len(images)} imagens encontradas")
            return images

        except requests.RequestException as e:
            logger.warning(f"  ✗ Erro Wikimedia para {scientific_name}: {e}")
            return []

    def _get_wikimedia_image_url(self, file_title):
        """Obtém URL direto da imagem no Wikimedia"""
        try:
            url = "https://commons.wikimedia.org/w/api.php"
            params = {
                'action': 'query',
                'format': 'json',
                'titles': f'File:{file_title}',
                'prop': 'imageinfo',
                'iiprop': 'url|size|dimensions|extmetadata'
            }

            response = self.session.get(url, params=params, timeout=10)
            data = response.json()

            pages = data.get('query', {}).get('pages', {})
            for page_id, page_data in pages.items():
                if 'imageinfo' in page_data:
                    info = page_data['imageinfo'][0]
                    return {
                        'url': info.get('url'),
                        'width': info.get('width', 0),
                        'height': info.get('height', 0),
                        'size': info.get('size', 0),
                        'description': info.get('extmetadata', {}).get('ImageDescription', {}).get('value', ''),
                        'license': info.get('extmetadata', {}).get('License', {}).get('value', ''),
                        'artist': info.get('extmetadata', {}).get('Artist', {}).get('value', '')
                    }

            return None
        except Exception as e:
            logger.warning(f"  ✗ Erro ao obter URL Wikimedia: {e}")
            return None

    def _calculate_wikimedia_score(self, result):
        """Calcula uma pontuação para a imagem do Wikimedia com base em vários fatores"""
        score = 0
        
        # Tamanho do arquivo (maior geralmente é melhor)
        size = result.get('size', 0)
        if size > 1000000:  # > 1MB
            score += 5
        elif size > 500000:  # > 500KB
            score += 3
        elif size > 100000:  # > 100KB
            score += 1
            
        # Verificar se o snippet contém termos relevantes
        snippet = result.get('snippet', '').lower()
        if any(term in snippet for term in ['plant', 'flower', 'leaf', 'fruit', 'tree']):
            score += 3
            
        # Verificar se o título é descritivo
        title = result.get('title', '').lower()
        if any(term in title for term in ['plant', 'flower', 'leaf', 'fruit', 'tree']):
            score += 2
            
        return score

    def search_tela_botanica(self, scientific_name):
        """Fallback: Busca múltiplas imagens na API Flora Tela Botânica (Flora Brasilis)"""
        # API Tela Botânica está com problemas (500 errors), desabilitada temporariamente
        return []

    def search_inaturalist(self, scientific_name):
        """Fallback alternativo: iNaturalist API (público, sem API key)"""
        images = []
        try:
            url = "https://api.inaturalist.org/v1/taxa/autocomplete"
            params = {
                'q': scientific_name,
                'per_page': '3'  # Aumentado para buscar mais opções
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('results'):
                for taxon in data['results']:
                    if taxon.get('default_photo'):
                        photo_url = taxon['default_photo'].get('medium_url')
                        if photo_url:
                            images.append({
                                'source': 'inaturalist',
                                'url': photo_url,
                                'taxon_id': taxon.get('id'),
                                'score': self._calculate_inaturalist_score(taxon)
                            })
            
            if images:
                logger.info(f"  ✓ iNaturalist: {scientific_name} - {len(images)} imagens encontradas")
            return images

        except Exception as e:
            logger.warning(f"  ✗ Erro iNaturalist para {scientific_name}: {e}")
            return []

    def _calculate_inaturalist_score(self, taxon):
        """Calcula uma pontuação para a imagem do iNaturalist com base em vários fatores"""
        score = 0
        
        # Verificar se há confirmações da identificação
        if taxon.get('observations_count', 0) > 10:
            score += 3
        elif taxon.get('observations_count', 0) > 5:
            score += 2
            
        # Verificar se é um rank de espécie (mais específico)
        if taxon.get('rank') == 'species':
            score += 2
        elif taxon.get('rank') == 'genus':
            score += 1
            
        # Verificar se há foto de qualidade
        if taxon.get('default_photo', {}).get('quality_grade') == 'research':
            score += 3
            
        return score

    def find_images(self, scientific_name, item_id):
        """Procura múltiplas imagens com fallbacks em todas as fontes"""
        logger.info(f"[{item_id}] Procurando: {scientific_name}")

        all_images = []
        
        # 1. Buscar em Wikimedia
        wikimedia_images = self.search_wikimedia(scientific_name)
        all_images.extend(wikimedia_images)
        
        # Pequeno atraso para não sobrecarregar as APIs
        time.sleep(self.delay_between_requests)
        
        # 2. Buscar em iNaturalist (mesmo que já tenha encontrado em Wikimedia)
        inaturalist_images = self.search_inaturalist(scientific_name)
        all_images.extend(inaturalist_images)
        
        # Processar as imagens encontradas
        if all_images:
            # Identificar a melhor imagem para destaque
            featured_image = self._select_featured_image(all_images)
            
            # Normalizar as URLs e adicionar informações adicionais
            processed_images = []
            for img in all_images:
                # Se a imagem veio do Wikimedia, precisamos extrair a URL do dicionário
                if img['source'] == 'wikimedia' and isinstance(img['url'], dict):
                    img_data = img['url']
                    processed_img = {
                        'source': img['source'],
                        'url': img_data.get('url'),
                        'title': img.get('title', ''),
                        'width': img_data.get('width', 0),
                        'height': img_data.get('height', 0),
                        'size': img_data.get('size', 0),
                        'description': img_data.get('description', ''),
                        'license': img_data.get('license', ''),
                        'artist': img_data.get('artist', ''),
                        'score': img.get('score', 0)
                    }
                else:
                    processed_img = img.copy()
                
                # Adicionar timestamp de quando foi encontrada
                processed_img['found_at'] = datetime.now().isoformat()
                
                # Marcar se é a imagem em destaque
                processed_img['featured'] = (processed_img == featured_image)
                
                processed_images.append(processed_img)
            
            self.images_found += len(processed_images)
            return {
                'images': processed_images,
                'featured_image': featured_image,
                'total_images': len(processed_images)
            }

        logger.warning(f"  ✗ Nenhuma imagem encontrada para {scientific_name}")
        self.images_failed += 1
        return None

    def _select_featured_image(self, images):
        """Seleciona a melhor imagem para destaque com base em critérios de qualidade"""
        if not images:
            return None
            
        # Ordenar por pontuação (maior primeiro)
        sorted_images = sorted(images, key=lambda x: x.get('score', 0), reverse=True)
        
        # A imagem com maior pontuação é a destacada
        featured = sorted_images[0]
        
        # Se a imagem veio do Wikimedia, precisamos extrair a URL do dicionário
        if featured['source'] == 'wikimedia' and isinstance(featured['url'], dict):
            featured_copy = featured.copy()
            featured_copy['url'] = featured['url'].get('url')
            return featured_copy
            
        return featured

    def update_items(self, items):
        """Atualiza items com múltiplas URLs de imagens e destaca a melhor"""
        # Usar ThreadPoolExecutor para processar em paralelo (com limite para evitar sobrecarga)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Criar uma função parcial que inclui o item_id
            find_images_partial = partial(self._find_images_with_id, items)
            
            # Enviar todas as tarefas para o executor
            future_to_index = {
                executor.submit(find_images_partial, item): index 
                for index, item in enumerate(items)
                if item.get('scientificName')
            }
            
            # Processar os resultados conforme forem concluídos
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    if result:
                        items[index]['images'] = result['images']
                        items[index]['featured_image'] = result['featured_image']
                        items[index]['total_images'] = result['total_images']
                        items[index]['images_updated'] = datetime.now().isoformat()
                except Exception as e:
                    logger.error(f"Erro ao processar item {index}: {e}")
        
        return items

    def _find_images_with_id(self, items, item):
        """Função auxiliar para passar o item_id junto com a busca de imagens"""
        item_id = item.get('id', items.index(item))
        scientific_name = item.get('scientificName')
        return self.find_images(scientific_name, item_id)

    def save_updated_file(self, items):
        """Salva items atualizados com múltiplas imagens em arquivo JavaScript"""
        try:
            # Converter para JSON formatado com indentação de 2 espaços
            json_content = json.dumps(items, ensure_ascii=False, indent=2)

            # Criar conteúdo JavaScript (mantém compatibilidade com data.js)
            js_content = f"""const allItems = {json_content};

export default allItems;
"""

            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(js_content)

            logger.info(f"✓ Arquivo atualizado salvo em: {self.output_file}")
            logger.info(f"  Total de itens: {len(items)}")

        except Exception as e:
            logger.error(f"Erro ao salvar arquivo: {e}")
            sys.exit(1)

    def print_summary(self):
        """Exibe resumo da execução"""
        total = self.images_found + self.images_failed
        success_rate = (self.images_found / total * 100) if total > 0 else 0

        print(f"""
╔════════════════════════════════════════╗
║         RESUMO DA EXECUÇÃO             ║
╠════════════════════════════════════════╣
║ Total processado:    {self.images_found + self.images_failed:>20} ║
║ Imagens encontradas: {self.images_found:>20} ║
║ Falhas:              {self.images_failed:>20} ║
║ Taxa de sucesso:     {success_rate:>19.1f}% ║
╚════════════════════════════════════════╝
        """)

    def run(self):
        """Executa o pipeline completo"""
        logger.info("🌿 Iniciando busca de imagens de plantas...")

        # 1. Carregar dados
        items = self.extract_js_data()

        # 2. Buscar imagens
        logger.info("🔍 Buscando imagens...")
        items_updated = self.update_items(items)

        # 3. Salvar arquivo
        logger.info("💾 Salvando arquivo atualizado...")
        self.save_updated_file(items_updated)

        # 4. Exibir resumo
        self.print_summary()

        logger.info("✨ Processo concluído!")


def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    try:
        import requests
        return True
    except ImportError:
        logger.error("❌ Erro: Biblioteca 'requests' não encontrada!")
        logger.error("   Instale com: pip install requests")
        return False


def main():
    # Verificar dependências
    if not check_dependencies():
        sys.exit(1)
    
    # Configurar argumentos
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'src/components/Library/data.js'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'src/components/Library/data_updated.js'
    max_workers = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    # Verificar se arquivo de entrada existe
    if not os.path.exists(input_file):
        logger.error(f"❌ Arquivo não encontrado: {input_file}")
        logger.info("   Uso: python plant_image.py [input_file] [output_file] [max_workers]")
        sys.exit(1)

    # Executar
    logger.info(f"📂 Arquivo de entrada: {input_file}")
    logger.info(f"📂 Arquivo de saída: {output_file}")
    logger.info(f"⚙️  Workers simultâneos: {max_workers}\n")
    
    finder = PlantImageFinder(input_file, output_file, max_workers)
    finder.run()


if __name__ == '__main__':
    main()