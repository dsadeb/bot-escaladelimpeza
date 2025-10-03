from keep_alive import keep_alive
from dotenv import load_dotenv
import os
import discord
from discord.ext import tasks, commands
from datetime import datetime
import pytz

# ========= CONFIGURAÇÃO =========
load_dotenv() 

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0")) 
ESTADO_ARQUIVO = "/data/estado_rodizio.txt"

# Lista dos nomes em ordem de rodízio
rodizio = [
    "Julia Kliemann", "Kauê Kazuo Kubo", "Lucas Sadoski", "Maria Fernanda","Maria Júlia", "Mateus Silverio", "Matheus Belizário",
    "Matheus Mello", "Milene Lopes", "Paulo Nogueira", "Pedro Balieiro", "Rodrigo",
    "Agata Kojiio", "Aline Lima", "Arthur Tormena", "Cindy Grasiely", "Débora Sanches Aroca",
    "Enzo Vieira", "Érica Doneux", "Fabio", "Hemilly Silva Barbosa", "João Birtche"
]

# Fuso-horário de Brasília
timezone = pytz.timezone('America/Sao_Paulo')

# Iniciação do bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ========= FUNÇÕES DE ESTADO (PARA SALVAR E CARREGAR O ÍNDICE) =========

def carregar_index():
    """Lê o índice atual do arquivo de estado."""
    try:
        with open(ESTADO_ARQUIVO, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0 

def salvar_index(index):
    """Salva o índice atual no arquivo de estado."""
    try:
        with open(ESTADO_ARQUIVO, "w") as f:
            f.write(str(index))
    except Exception as e:
        print(f"ERRO CRÍTICO AO SALVAR ESTADO: {e}")
        print("Verifique se o Volume está montado corretamente em /data no Railway.")

index_atual = carregar_index()

# ========= FUNÇÕES DO BOT =========

async def encontrar_membro(guild, nome_alvo):
    """Encontra um membro no servidor com base no nome da lista."""
    nome_limpo = nome_alvo.lower().strip().replace(" ", "")
    for member in guild.members:
        member_name_clean = member.display_name.lower().replace(" ", "")
        if nome_limpo in member_name_clean or member_name_clean in nome_limpo:
            return member
    return None

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    print(f"Canal de avisos configurado: {CHANNEL_ID}")
    print(f"Índice de rodízio carregado: {index_atual}")
    print(f"Próxima pessoa no rodízio: {rodizio[index_atual % len(rodizio)]}")
    enviar_lembrete.start()

@tasks.loop(minutes=1)
async def enviar_lembrete():
    global index_atual
    agora = datetime.now(timezone)
    
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        if agora.minute == 0: 
             print(f"ERRO: Canal com ID {CHANNEL_ID} não encontrado. Verifique a variável de ambiente.")
        return

    nome_da_vez = rodizio[index_atual % len(rodizio)]
    
    # Lembrete da semana na Segunda-feira às 09:00
    if agora.weekday() == 0 and agora.hour == 9 and agora.minute == 0:
        guild = channel.guild
        membro = await encontrar_membro(guild, nome_da_vez)
        
        if membro:
            mensagem = f"🗓️ Bom dia, {membro.mention}! Passando para lembrar que esta semana é a sua vez de cuidar da limpeza do escritório. Lembre-se de tirar o lixo na sexta-feira! ✨🧹"
            await channel.send(mensagem)
            print(f"Lembrete semanal enviado para {membro.display_name}")
        else:
            # LINHA CORRIGIDA
            await channel.send(f"⚠️ Não encontrei o usuário `{nome_da_vez}` no servidor para o lembrete semanal.")
            print(f"Membro não encontrado para lembrete semanal: {nome_da_vez}")

    # Lembrete para tirar o lixo na Sexta-feira às 17:00
    if agora.weekday() == 4 and agora.hour == 17 and agora.minute == 0:
        guild = channel.guild
        membro = await encontrar_membro(guild, nome_da_vez)

        if membro:
            mensagem = f"🚩 Oi, {membro.mention}! Hora de tirar o lixo do escritório! ✨🗑️"
            await channel.send(mensagem)
            print(f"Mensagem de 'tirar o lixo' enviada para {membro.display_name}")
            
            index_atual += 1
            salvar_index(index_atual)
            
            proxima_pessoa = rodizio[index_atual % len(rodizio)]
            print(f"Rodízio avançou. Próxima pessoa: {proxima_pessoa} (índice: {index_atual})")
        else:
            # LINHA CORRIGIDA
            await channel.send(f"⚠️ Não encontrei o usuário `{nome_da_vez}` no servidor para o lembrete de tirar o lixo.")
            print(f"Membro não encontrado: {nome_da_vez}")

# ========= COMANDOS EXTRAS =========

@bot.command(name='proximo')
async def proximo(ctx):
    """Mostra quem é a pessoa da vez no rodízio."""
    pessoa_atual = rodizio[index_atual % len(rodizio)]
    await ctx.send(f"A pessoa da vez é: **{pessoa_atual}** (índice: {index_atual}).")

@bot.command(name='forcared')
async def forcar_rodizio(ctx):
    """Força o rodízio para a próxima pessoa."""
    global index_atual
    index_atual += 1
    salvar_index(index_atual)
    
    proxima_pessoa = rodizio[index_atual % len(rodizio)]
    await ctx.send(f"✅ Rodízio avançado manualmente. A próxima pessoa é: **{proxima_pessoa}**.")
    print(f"Rodízio avançado manualmente por {ctx.author}. Próxima pessoa: {proxima_pessoa}")

# ========= INICIALIZAÇÃO =========
def main():
    keep_alive()
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    main()
