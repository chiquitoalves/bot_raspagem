from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import cv2
import numpy as np
import base64
import os
from threading import Thread, Lock
import time
import socket
from threading import Event
import datetime
import threading


codigo_disponivel = Event()
navegadores = {}
lock_navegadores = Lock()
codigos_cupom = {}
lock_codigos = Lock()

def obter_credenciais():
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(diretorio_atual, 'credenciais.txt')

    with open(caminho_arquivo, 'r') as arquivo:
        linhas = arquivo.readlines()
    
    credenciais = []
    for linha in linhas:
        email, senha = linha.strip().split(' ')
        credenciais.append((email, senha))

    return credenciais

def abrir_navegador():
    mobile_emulation = {
        "deviceMetrics": {"width": 360, "height": 640, "pixelRatio": 3.0},
        "userAgent": "Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Mobile Safari/537.36",
    }
    chrome_options = Options()
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    chrome_options.add_experimental_option("detach", True)
    
    navegador = webdriver.Chrome(options=chrome_options)
    return navegador
def esperar_carregamento_pagina(navegador):
    while True:
        estado_pronto = navegador.execute_script('return document.readyState;')
        if estado_pronto == 'complete':
            return navegador.current_url
        else:
            time.sleep(1)
def pagina_carregada(navegador):
    state = navegador.execute_script('return document.readyState;')
    return state == 'complete'

def inicia_secao(email, senha):
    print(f"Abrindo navegador para a conta {email}...")
    global navegadores
    sucesso = False
    try:
        with lock_navegadores:
            if email not in navegadores:
                navegador = abrir_navegador()
                navegadores[email] = navegador
            else:
                navegador = navegadores[email]

        navegador.get('https://www.sssgame.com/signin')
        sucesso = log(navegador, email, senha)
    except Exception as e:
        print(f"Erro ao tentar logar {email}: {e}")

    return sucesso

def log(navegador, email, senha):
    url_esperada = 'https://www.sssgame.com/signin'
    nome = navegador.find_element('css selector', 'input[type="text"]')
    nome.click()
    nome.send_keys(email)
    time.sleep(1)

    
    campo_senha = navegador.find_element('css selector', 'input[type="password"]')
    campo_senha.click()
    campo_senha.send_keys(senha)
    time.sleep(1)
                    
    cap = resolver_captcha(navegador)
    if cap:
        botao_logar = navegador.find_element('css selector', '.btn')
        time.sleep(3)
        botao_logar.click()
        time.sleep(10)
        url_logado = esperar_carregamento_pagina(navegador)
        if url_logado != url_esperada:
            print("Login bem-sucedido.")
            return True
        else:
            print("Login falhou. Tentando novamente.")
            return False
    return False

def aguardar_proximo_horario():
    horarios = [datetime.time(hour=h, minute=29, second=40) for h in range(12, 22)]
    agora = datetime.datetime.now()
    horarios_hoje = [datetime.datetime.combine(agora.date(), h) for h in horarios]

    
    horarios_hoje = [h if h > agora else h + datetime.timedelta(days=1) for h in horarios_hoje]
    proximo_horario = min(horarios_hoje) 

    segundos_espera = (proximo_horario - agora).total_seconds()
    print(f"Aguardando o cupom ou o horário {proximo_horario.strftime('%H:%M:%S')} para resolver o captcha... ({segundos_espera} segundos)")
    time.sleep(segundos_espera)



def processar_pagina_cupom(email, navegador, senha):
    try:
        navegador.get('https://www.sssgame.com/activity/activityDetail?id=247')
        time.sleep(3)

       
        thread_horario = threading.Thread(target=aguardar_proximo_horario)
        thread_horario.start()

        
        while not codigo_disponivel.is_set() and thread_horario.is_alive():
            time.sleep(1)  

        
        modalcod = navegador.find_element('css selector', '.buttonBox span')
        modalcod.click()
        time.sleep(2)
        capt = resolver_captcha(navegador)

        if capt:
            areadocodigo = navegador.find_element('css selector', 'input[type="text"]')
            areadocodigo.click()
            
            if not codigo_disponivel.is_set():
                print(f"Aguardando código do cupom para a conta {email} após o horário específico...")
                codigo_disponivel.wait()

            
            with lock_codigos:
                codigo_cupom = codigos_cupom.pop(email, None) 

            if codigo_cupom:
                agora = datetime.datetime.now()
                hora_formatada = agora.strftime('%H:%M:%S:%f')[:-3]
                print(f'Inserindo código do cupom para a conta {email} as {hora_formatada}')
                areadocodigo.send_keys(codigo_cupom)
                btn_claro = navegador.find_element('css selector', '.van-dialog__confirm')
                btn_claro.click()
                agora = datetime.datetime.now()
                hora_formatada = agora.strftime('%H:%M:%S:%f')[:-3]
                print(f'Código do cupom processado para a conta {email} as {hora_formatada}')
        else:
            print(f"Falha ao resolver captcha para a conta {email}.")

    except Exception as e:
        print(f"Erro ao processar a página de cupom para {email}: {str(e)}")

    finally:
        time.sleep(20)
        print(f"Retornando para area do cupom {email}.")
        navegador.get('https://www.sssgame.com/activity/activityDetail?id=247')
        time.sleep(5)
        codigo_disponivel.clear()
        processar_pagina_cupom(email, navegador, senha)

def main():
    contas = obter_credenciais()
    threads_login = []

   
    for email, senha in contas:
        thread = Thread(target=tarefa_login, args=(email, senha))
        threads_login.append(thread)
        thread.start()

   
    for thread in threads_login:
        thread.join()

    
    thread_servidor = Thread(target=servidor_socket)
    thread_servidor.start()

    
    threads_cupom = []
    for email, senha in contas:
        if email in navegadores:  
            thread = Thread(target=processar_pagina_cupom, args=(email, navegadores[email], senha))
            threads_cupom.append(thread)
            thread.start()

    
    for thread in threads_cupom:
        thread.join()

    
    thread_servidor.join()

def tarefa_login(email, senha):
    max_tentativas = 5  
    tentativas = 0

    while tentativas < max_tentativas:
        sucesso = inicia_secao(email, senha)
        if sucesso:
            print(f"Login bem-sucedido para {email} após {tentativas + 1} tentativa(s).")
            break
        else:
            tentativas += 1
            print(f"Falha no login para {email}, tentando novamente... Tentativa {tentativas + 1} de {max_tentativas}.")
            time.sleep(1)  

    if tentativas == max_tentativas:
        print(f"Falha no login para {email} após {max_tentativas} tentativas. Não tentando mais.")

def resolver_captcha(navegador):
    
    def dividir_em_quatro_na_largura(imagem):
        altura, largura = imagem.shape[:2]
        partes = []
        largura_parte = largura // 4
        for i in range(4):
            inicio = i * largura_parte
            fim = (i + 1) * largura_parte if i < 3 else largura
            partes.append(imagem[:, inicio:fim])
        return partes

    
    def decode_base64_with_padding(s):
        padding_needed = len(s) % 4
        s += '=' * padding_needed
        return base64.b64decode(s)
    
    base_64 = navegador.find_element('css selector','.regist-yzmImg').get_attribute('src')
    conteudo_base64 = base_64.split(",")[1]
    imagem_base64 = conteudo_base64
    imagem_bytes = decode_base64_with_padding(imagem_base64)
    np_arr = np.frombuffer(imagem_bytes, dtype=np.uint8)
    imagem = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    
    imagem_cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    imagem_negativa = cv2.bitwise_not(imagem_cinza)

   
    partes = dividir_em_quatro_na_largura(imagem_negativa)

    
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    diretorio_novos = os.path.join(diretorio_atual, 'novos')
    diretorio_imagens = os.path.join(diretorio_atual, 'data')
    limiar_similaridade = 0.80
    pastas_encontradas = []
   
    for i, parte in enumerate(partes):
       
        imagem_encontrada = False
        
       
        for root, dirs, files in os.walk(diretorio_imagens):
            for file in files:
                if file.endswith(('.jpg', '.jpeg', '.png')):
                    caminho_imagem = os.path.join(root, file)
                    imagem_comparar = cv2.imread(caminho_imagem, cv2.IMREAD_GRAYSCALE)
                    
                    resultado = cv2.matchTemplate(imagem_comparar, parte, cv2.TM_CCOEFF_NORMED)
                    
                   
                    loc = np.where(resultado >= limiar_similaridade)
                    
                    
                    if len(loc[0]) > 0:
                        pastas_encontradas.append(os.path.basename(os.path.dirname(caminho_imagem)))
                        imagem_encontrada = True
                        break
            if imagem_encontrada:
                break
        

        if not imagem_encontrada:
            nome_arquivo = f"imagem_parte_{i+1}.png"
            caminho_arquivo = os.path.join(diretorio_novos, nome_arquivo)
            cv2.imwrite(caminho_arquivo, parte)
            att_captcha(navegador)
            break
            
     
    nomes_pasta_sequencia = "".join(pastas_encontradas)
    print("CAPTCHA ENCONTRADO:", nomes_pasta_sequencia)
    captcha = navegador.find_element('css selector', '.verifyInput')
    captcha.click()
    captcha.send_keys(nomes_pasta_sequencia)
    return True

def att_captcha(navegador):
    captcha_input = navegador.find_element('css selector', '.verifyInput')
    captcha_input.click()
    time.sleep(2)
    for _ in range(10):
        captcha_input.send_keys(Keys.BACKSPACE)
    time.sleep(2)
    img = navegador.find_element('css selector','.regist-yzmImg')
    img.click()
    time.sleep(2)
    resolver_captcha(navegador)

def servidor_socket():
    HOST = '127.0.0.1'  
    PORT = 65432        

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print("Servidor socket aguardando conexão...")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f'Conectado por {addr}')
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break

                    if "codigo:" in data.decode():
                        codigo = data.decode().split(":")[1].strip()
                        agora = datetime.datetime.now()
                        hora_formatada = agora.strftime('%H:%M:%S:%f')[:-3]
                        print(f'Código recebido: {codigo} as {hora_formatada}')
                        with lock_codigos:
                            for email in navegadores.keys():
                                codigos_cupom[email] = codigo
                            codigo_disponivel.set() 
                    conn.sendall(b'Recebido')


if __name__ == "__main__":
    main()
    
