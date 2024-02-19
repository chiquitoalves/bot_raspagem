import datetime
from telethon import TelegramClient, events
import re
import asyncio
import socket

sessao = 'Repassar Mensagem'
api_id = '25681670'
api_hash = '288568f2650588bd843390b2d0d91fdc'
#-1001957189051
async def enviar_servidor(codigo):
    HOST = '127.0.0.1'
    PORT = 65432
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
        writer.write(f'codigo:{codigo}'.encode())
        await writer.drain()
        data = await reader.read(1024)
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f"Erro ao enviar código para o servidor: {e}")

async def main():
    print('INICIANDO MONITORAMENTO DO TELEGRAM....')
    client = TelegramClient(sessao, api_id, api_hash)

    @client.on(events.NewMessage(chats=[-4197613140, -4162969594]))
    async def enviar_codigo(event):
        pattern = r'SSSGAME\w+'
        matches = re.findall(pattern, event.raw_text)
        if matches:
            codigo = matches[0]
            if len(codigo) > 14:
                agora = datetime.datetime.now()
                hora_formatada = agora.strftime('%H:%M:%S:%f')[:-3]
                print(f'Enviando o codigo do telegram as {hora_formatada}')
                await enviar_servidor(codigo)

    await client.start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
