import subprocess
import os
import threading
import time
import psutil
import schedule


bot_process = None

def update_terminal(output):
    print(output)

def execute_subprocess(command, update_func, is_bot=True):
    def run_process():
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
            if is_bot:
                global bot_process
                bot_process = process
            for line in process.stdout:
                update_func(line.strip())
        except Exception as e:
            update_func(f"Erro ao executar subprocesso: {e}")
    threading.Thread(target=run_process).start()

def terminate_bot_process():
    global bot_process
    if bot_process is not None:
        try:
            parent = psutil.Process(bot_process.pid)
            for child in parent.children(recursive=True): 
                child.terminate()
            bot_process.terminate()
            bot_process.wait()
            update_terminal("Processo do bot encerrado.")
        except psutil.NoSuchProcess:
            update_terminal("Não foi possível encontrar o processo do bot para encerrá-lo.")
        finally:
            bot_process = None

def run_bot_file():
    update_terminal("Iniciando bot...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "teste.py")
    python_path = "/usr/bin/python3"  
    command = [python_path, "-u", file_path]
    execute_subprocess(command, update_terminal, is_bot=True)

def run_telegram_script():
    update_terminal("Iniciando script do Telegram...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "telegram.py")
    python_path = "/usr/bin/python3" 
    command = [python_path, "-u", file_path]
    execute_subprocess(command, update_terminal, is_bot=False)

def restart_bot():
    update_terminal("Reiniciando bot...")
    terminate_bot_process()
    time.sleep(5)  
    run_bot_file()

def schedule_bot_restart():
    threading.Thread(target=restart_bot).start()

update_terminal('-------------------- BEM VINDO AO SSS GAMES BOT --------------------')

run_bot_file()  
run_telegram_script()  

execution_times = ["12:20", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00",]
for exec_time in execution_times:
    schedule.every().day.at(exec_time).do(schedule_bot_restart)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=run_scheduler, daemon=True).start()

# Mantém o programa em execução indefinidamente
while True:
    time.sleep(1)
