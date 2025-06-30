# Configurações do jogo
LARGURA_TELA = 1200
ALTURA_TELA = 800
FPS = 60

# Cores
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
VERMELHO = (255, 0, 0)
VERDE = (0, 255, 0)
AZUL = (0, 0, 255)
AZUL_CLARO = (173, 216, 230)
AMARELO = (255, 255, 0)
ROXO = (128, 0, 128)
LARANJA = (255, 165, 0)
CINZA = (128, 128, 128)
DOURADO = (255, 215, 0)

# Mapa
LARGURA_MAPA = 3000
ALTURA_MAPA = 3000

# Jogador
JOGADOR_RAIO = 15
JOGADOR_VELOCIDADE = 5
JOGADOR_HP_INICIAL = 10
JOGADOR_DANO_INICIAL = 1

# Projétil
PROJETIL_VELOCIDADE = 8
PROJETIL_RAIO = 3
PROJETIL_ALCANCE = 300

# Inimigos
INIMIGO_SPAWN_DISTANCIA = 400
INIMIGO_NORMAL_RAIO = 12
INIMIGO_RAPIDO_RAIO = 8
INIMIGO_TANQUE_RAIO = 20

# XP - Sistema progressivo
XP_RAIO = 5
XP_VALOR = 3

def calcular_xp_para_level(level):
    """Calcula XP necessário para um nível específico - progressivo"""
    if level <= 1:
        return 10
    elif level <= 5:
        return 10 + (level - 1) * 15  # 10, 25, 40, 55, 70
    elif level <= 10:
        return 70 + (level - 5) * 25  # 95, 120, 145, 170, 195
    elif level <= 20:
        return 195 + (level - 10) * 40  # 235, 275, 315, etc.
    elif level <= 35:
        return 595 + (level - 20) * 60  # Cresce mais rápido
    elif level <= 50:
        return 1495 + (level - 35) * 80
    else:
        return 2695 + (level - 50) * 100  # Muito alto para níveis altos

# Itens
ITEM_RAIO = 8

# Boss
BOSS_RAIO = 50
BOSS_HP = 1000

# Minimapa
MINIMAPA_TAMANHO = 150
MINIMAPA_X = LARGURA_TELA - MINIMAPA_TAMANHO - 10
MINIMAPA_Y = 10

# Tempo de jogo
DURACAO_MAXIMA = 600  # 10 minutos em segundos 