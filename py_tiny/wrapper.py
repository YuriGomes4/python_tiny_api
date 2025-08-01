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
            if dados_requests[access_token]['uso_api'] >= int(dados_requests[access_token]['limite']):
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