LARGURA_TELA = 1200
ALTURA_TELA = 800
FPS = 60
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
LARGURA_MAPA = 3000
ALTURA_MAPA = 3000
JOGADOR_RAIO = 15
JOGADOR_VELOCIDADE = 5
JOGADOR_HP_INICIAL = 10
JOGADOR_DANO_INICIAL = 1
PROJETIL_VELOCIDADE = 8
PROJETIL_RAIO = 3
PROJETIL_ALCANCE = 300
INIMIGO_SPAWN_DISTANCIA = 400
INIMIGO_NORMAL_RAIO = 12
INIMIGO_RAPIDO_RAIO = 8
INIMIGO_TANQUE_RAIO = 20
XP_RAIO = 5
XP_VALOR = 1

def calcular_xp_para_level(level):
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
        base = 190
        incremento = (level - 7) * 35
        return base + incremento
        
ITEM_RAIO = 8
BOSS_RAIO = 50
BOSS_HP = 50000
MINIMAPA_TAMANHO = 150
MINIMAPA_X = LARGURA_TELA - MINIMAPA_TAMANHO - 10
MINIMAPA_Y = 10
DURACAO_MAXIMA = 600