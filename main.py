import json

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

from dotenv import load_dotenv
import os

load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

DIAS_ANTES_VENCIMENTO = 3 # Enviar lembrete se faltarem X dias para o vencimento

def enviar_email(destinatario, assunto, corpo_email):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = destinatario
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo_email, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() # Inicia a conexão TLS para segurança
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, destinatario, text)
        server.quit()
        print(f"E-mail enviado para: {destinatario} - Assunto: '{assunto}'")
    except Exception as e:
        print(f"Erro ao enviar e-mail para {destinatario}: {e}")
        print("Verifique suas credenciais de e-mail e configurações SMTP.")
        print("Para Gmail, lembre-se de usar 'Senha de App' se tiver verificação em duas etapas.")



def main():
    print("Iniciando verificação de pagamentos...")
    
    try:
        # Carregar os dados do arquivo JSON
        with open('contas.json', 'r', encoding='utf-8') as f:
            pagamentos = json.load(f)
    except FileNotFoundError:
        print("Erro: O arquivo 'contas.json' não foi encontrado. Certifique-se de que ele está na mesma pasta do script.")
        return
    except json.JSONDecodeError:
        print("Erro: O arquivo 'contas.json' não é um JSON válido. Verifique a sintaxe.")
        return

    hoje = datetime.now().date() # Data atual sem a hora

    for pagamento in pagamentos:
        try:
            nome = pagamento['Nome']
            email = pagamento['Email']
            descricao = pagamento['Descricao_Conta']
            valor = pagamento['Valor']
            data_vencimento_str = pagamento['Data_Vencimento']
            data_vencimento = datetime.strptime(data_vencimento_str, '%Y-%m-%d').date() # Converte string para data
        except KeyError as e:
            print(f"Erro: Campo '{e}' ausente em um dos registros JSON. Verifique a estrutura do arquivo.")
            continue # Pula para o próximo registro

        dias_restantes = (data_vencimento - hoje).days

        # Verificando se a conta está vencida (dias_restantes < 0)
        # Ou se está próxima do vencimento (entre 0 e DIAS_ANTES_VENCIMENTO)
        if dias_restantes < 0:
            assunto = f"Atenção: Seu pagamento de {descricao} está VENCIDO!"
            corpo = f"""Prezado(a) {nome},

Informamos que seu pagamento referente a '{descricao}', no valor de R$ {valor:.2f}, com vencimento em {data_vencimento.strftime('%d/%m/%Y')}, encontra-se VENCIDO.

Por favor, regularize sua situação o mais breve possível.

Atenciosamente,
Sua Empresa
"""
            enviar_email(email, assunto, corpo)
        elif 0 <= dias_restantes <= DIAS_ANTES_VENCIMENTO:
            assunto = f"Lembrete: Seu pagamento de {descricao} vence em breve!"
            corpo = f"""Prezado(a) {nome},

Este é um lembrete amigável de que seu pagamento referente a '{descricao}', no valor de R$ {valor:.2f}, vence em {data_vencimento.strftime('%d/%m/%Y')}.

Por favor, efetue o pagamento para evitar interrupções no serviço.

Atenciosamente,
Sua Empresa
"""
            enviar_email(email, assunto, corpo)

            # CRIAR AQUI UM REGISTRO DE LOGS USANDO GOOGLE SHEETS PARA CASO TENHA DADO CERTO O ENVIO COM A SEGUINTE MENSAGEM
            # f"Foi enviado uma mensagem de e-mail de pagamento para o e-mail de {nome}"
        else:
            print(f"Pagamento de {nome} ({descricao}) está em dia ou não se enquadra no lembrete. Vence em {dias_restantes} dias.")
    print("\nVerificação de pagamentos concluída.")

if __name__ == "__main__":
    main()