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
XP_VALOR = 1

def calcular_xp_para_level(level):
    """Calcula XP necessário para subir para o próximo nível - progressão mais equilibrada"""
    # Progressão mais suave que acompanha a dificuldade:
    # Level 1->2: 25 XP (muito fácil)
    # Level 2->3: 40 XP 
    # Level 3->4: 60 XP
    # Level 4->5: 85 XP
    # Level 5->6: 115 XP
    # Level 6->7: 150 XP
    # Level 7->8: 190 XP
    # Level 8+: continua crescendo mais devagar
    
    if level == 1:
        return 25
    elif level == 2:
        return 40
    elif level == 3:
        return 60
    elif level == 4:
        return 85
    elif level == 5:
        return 115
    elif level == 6:
        return 150
    elif level == 7:
        return 190
    else:
        # Para níveis 8+, crescimento mais moderado
        base = 190
        incremento = (level - 7) * 35  # +35 XP por nível após o 7º
        return base + incremento

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