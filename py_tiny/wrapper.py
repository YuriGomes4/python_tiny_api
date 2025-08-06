import json
from time import sleep, time
import requests

dados_requests = {}

def rate_limiter(func):
    """Rate limiter decorator to handle API rate limits."""
    def wrapper(*args, **kwargs):
        global dados_requests
    
        access_token = args[0].access_token if args else None
        if access_token and access_token in dados_requests:
            # Check if the rate limit has been reached
            if dados_requests[access_token]['uso_api'] >= int(dados_requests[access_token]['limite']) and dados_requests[access_token]['hora_primeira_requisicao'] + 60 > time():
                elapsed_time = time() - dados_requests[access_token]['hora_primeira_requisicao']
                if elapsed_time < 60:
                    print(f"Rate limit reached for access token {access_token}. Waiting for {60 - elapsed_time:.2f} seconds.")
                    sleep(60 - elapsed_time)

        return func(*args, **kwargs)  # Executa normalmente
    return wrapper


class auth():

    def __init__(self, access_token="", print_error=True):
        self.access_token = access_token
        self.base_url = "https://api.tiny.com.br/api2"
        self.print_error = print_error

    @rate_limiter
    def request(self, method="GET", url="", headers=None, params=None, data=None):

        req_params = params if params != None else {}
        req_headers = headers if headers != None else {}
        req_data = data if data != None else {}

        if self.access_token != "" and self.access_token != None:
            req_params['token'] = self.access_token

        req_params['formato'] = 'json'

        while True:

            match method:
                case "GET":
                    response = requests.get(url=url, params=req_params, headers=req_headers, data=req_data)
                case "PUT":
                    response = requests.put(url=url, params=req_params, headers=req_headers, data=req_data)
                case "POST":
                    response = requests.post(url=url, params=req_params, headers=req_headers, data=req_data)
                case "DELETE":
                    response = requests.delete(url=url, params=req_params, headers=req_headers, data=req_data)
                case "HEAD":
                    response = requests.head(url=url, params=req_params, headers=req_headers, data=req_data)
                case "OPTIONS":
                    response = requests.options(url=url, params=req_params, headers=req_headers, data=req_data)

            if response.status_code == 200 or response.status_code == 201:
                global dados_requests
                # Capture rate limit headers and update last_request
                if self.access_token not in dados_requests:
                    dados_requests[self.access_token] = {
                        'limite': response.headers.get('x-limit-api', 0),
                        'hora_primeira_requisicao': time(),
                        'uso_api': 1,
                    }
                else:
                    if dados_requests[self.access_token]['hora_primeira_requisicao'] + 60 < time():
                        dados_requests[self.access_token]['uso_api'] = 1
                        dados_requests[self.access_token]['hora_primeira_requisicao'] = time()
                    else:
                        dados_requests[self.access_token]['uso_api'] += 1
                return response
            elif response.status_code != 429:
                if self.print_error:
                    try:
                        response_json = response.json()
                        message = response_json['message'] if 'message' in response_json else ""
                        json_content = response_json
                    except:
                        message = ""
                        json_content = response.text
                    
                    print(f"""Erro no retorno da API do Tiny
Mensagem: {message}
URL: {url}
Metodo: {method}
Parametros: {req_params}
Headers: {req_headers}
Data: {req_data}
Resposta JSON: {json_content}""")
                if response.status_code == 403 or response.status_code == 404:
                    return None
                else:
                    break
            else:
                sleep(10)

class conta(auth):

    def ver_dados(self, **kwargs):
        """
        View the account information.
        """
        #Descrição da função

        asct = True #Acesso Só Com Token

        if asct and (self.access_token == "" or self.access_token == None or type(self.access_token) != str):
            print("Token inválido")
            return {}

        url = self.base_url+f"/info.php"

        params = {}

        # Adicionar parâmetros opcionais
        if kwargs:
            for key, value in kwargs.items():
                params[key] = value

        response = self.request("GET", url=url, params=params)

        if response:

            return response.json()
        
        else:
            return {}
        
class produtos(auth):

    def pesquisar(self, pesquisa, idTag=None, idListaPreco=None, pagina=None, gtin=None, situacao=None, dataCriacao=None, **kwargs):
        """
        Pesquisar produtos no Tiny ERP.
        
        Args:
            pesquisa (str): Nome ou código (ou parte) do produto que deseja consultar (obrigatório)
            idTag (int, optional): Número de identificação da tag no Tiny
            idListaPreco (int, optional): Número de identificação da lista de preço no Tiny
            pagina (int, optional): Número da página (padrão são listados 100 registros por página)
            gtin (str, optional): GTIN/EAN do produto
            situacao (str, optional): Situação dos produtos ("A" - Ativo, "I" - Inativo ou "E" - Excluído)
            dataCriacao (str, optional): Data de criação do produto. Formato dd/mm/aaaa hh:mm:ss
            **kwargs: Parâmetros adicionais
            
        Returns:
            dict: Resposta da API com os produtos encontrados
        """
        
        asct = True  # Acesso Só Com Token

        if asct and (self.access_token == "" or self.access_token == None or type(self.access_token) != str):
            print("Token inválido")
            return {}

        url = self.base_url + "/produtos.pesquisa.php"

        params = {
            'pesquisa': pesquisa,
            'pagina': 1
        }

        # Adicionar parâmetros opcionais se fornecidos
        if idTag is not None:
            params['idTag'] = idTag
        if idListaPreco is not None:
            params['idListaPreco'] = idListaPreco
        if pagina is not None:
            params['pagina'] = pagina
        if gtin is not None:
            params['gtin'] = gtin
        if situacao is not None:
            params['situacao'] = situacao
        if dataCriacao is not None:
            params['dataCriacao'] = dataCriacao

        # Adicionar parâmetros extras do kwargs
        if kwargs:
            for key, value in kwargs.items():
                params[key] = value

        response = self.request("GET", url=url, params=params)

        if response:
            if response.json()['retorno']['status_processamento'] == '3':
                pagina_atual = int(response.json()['retorno']['pagina'])
                numero_paginas = response.json()['retorno']['numero_paginas']

                produtos = []

                for produto in response.json()['retorno']['produtos']:
                    produtos.append(produto['produto'])

                tentativas = 0
                max_tentativas = 5

                while pagina_atual < numero_paginas:
                    pagina_atual += 1
                    params['pagina'] = pagina_atual

                    response2 = self.request("GET", url=url, params=params)

                    if response2:
                        if response2.json()['retorno']['status_processamento'] == '3':
                            for produto in response2.json()['retorno']['produtos']:
                                produtos.append(produto['produto'])
                            tentativas = 0
                        else:
                            if tentativas >= max_tentativas:
                                print(f"Erro ao obter mais produtos: {response2.json()['retorno']['status_processamento']}")
                                break
                            tentativas += 1
                            sleep(1)  # Espera um pouco antes de tentar novamente

                return produtos
            else:
                return []

        else:
            return []

    def obter(self, id, **kwargs):
        """
        Obter dados detalhados de um produto específico no Tiny ERP.
        
        Args:
            id (int): Número de identificação do produto no Tiny (obrigatório)
            **kwargs: Parâmetros adicionais
            
        Returns:
            dict: Resposta da API com os dados completos do produto
        """
        
        asct = True  # Acesso Só Com Token

        if asct and (self.access_token == "" or self.access_token == None or type(self.access_token) != str):
            print("Token inválido")
            return {}

        url = self.base_url + "/produto.obter.php"

        params = {
            'id': id
        }

        # Adicionar parâmetros extras do kwargs
        if kwargs:
            for key, value in kwargs.items():
                params[key] = value

        response = self.request("GET", url=url, params=params)

        if response:
            return response.json()
        else:
            return {}

    def alterar(self, produto, **kwargs):
        """
        Alterar um produto existente no Tiny ERP.
        
        Args:
            produto (dict): Dados do produto conforme layout da API (obrigatório)
                          Deve conter pelo menos o campo 'id' para identificar o produto
            **kwargs: Parâmetros adicionais
            
        Returns:
            dict: Resposta da API com o resultado da alteração
        """
        
        asct = True  # Acesso Só Com Token

        if asct and (self.access_token == "" or self.access_token == None or type(self.access_token) != str):
            print("Token inválido")
            return {}

        url = self.base_url + "/produto.alterar.php"

        params = {}

        # Adicionar parâmetros extras do kwargs
        if kwargs:
            for key, value in kwargs.items():
                params[key] = value

        # Converter produto para JSON se for um dict
        if isinstance(produto, dict):
            produto_json = json.dumps(produto, ensure_ascii=False)
        else:
            produto_json = produto

        data = {
            'produto': produto_json
        }

        response = self.request("POST", url=url, params=params, data=data)

        if response:
            return response.json()
        else:
            return {}

    def obter_estoque(self, id, **kwargs):
        """
        Obter informações de estoque de um produto específico no Tiny ERP.
        
        Args:
            id (int): Número de identificação do produto no Tiny (obrigatório)
            **kwargs: Parâmetros adicionais
            
        Returns:
            dict: Resposta da API com as informações de estoque do produto
        """
        
        asct = True  # Acesso Só Com Token

        if asct and (self.access_token == "" or self.access_token == None or type(self.access_token) != str):
            print("Token inválido")
            return {}

        url = self.base_url + "/produto.obter.estoque.php"

        params = {
            'id': id
        }

        # Adicionar parâmetros extras do kwargs
        if kwargs:
            for key, value in kwargs.items():
                params[key] = value

        response = self.request("GET", url=url, params=params)

        if response:
            return response.json()
        else:
            return {}

    def obter_estrutura(self, id, **kwargs):
        """
        Obter a estrutura/composição de um produto no Tiny ERP.
        
        Args:
            id (int): Número de identificação do produto no Tiny (obrigatório)
            **kwargs: Parâmetros adicionais
            
        Returns:
            dict: Resposta da API com a estrutura/composição do produto
        """
        
        asct = True  # Acesso Só Com Token

        if asct and (self.access_token == "" or self.access_token == None or type(self.access_token) != str):
            print("Token inválido")
            return {}

        url = self.base_url + "/produto.obter.estrutura.php"

        params = {
            'id': id
        }

        # Adicionar parâmetros extras do kwargs
        if kwargs:
            for key, value in kwargs.items():
                params[key] = value

        response = self.request("GET", url=url, params=params)

        if response:
            return response.json()
        else:
            return {}

