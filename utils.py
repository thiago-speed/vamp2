import math
import pygame
import random
from config import *


def calcular_distancia(pos1, pos2):
    dx = pos1[0] - pos2[0]
    dy = pos1[1] - pos2[1]
    return math.sqrt(dx*dx + dy*dy)


def normalizar_vetor(dx, dy):
    magnitude = math.sqrt(dx*dx + dy*dy)
    if magnitude == 0:
        return 0, 0
    return dx/magnitude, dy/magnitude


def posicao_na_tela(pos_mundo, camera):
    return pos_mundo[0] - camera[0], pos_mundo[1] - camera[1]


def esta_na_tela(pos_mundo, camera, margem=50):
    x, y = posicao_na_tela(pos_mundo, camera)
    return -margem <= x <= LARGURA_TELA + margem and -margem <= y <= ALTURA_TELA + margem


def limitar_posicao(pos):
    x = max(0, min(LARGURA_MAPA, pos[0]))
    y = max(0, min(ALTURA_MAPA, pos[1]))
    return [x, y]


def obter_inimigo_mais_proximo(jogador_pos, inimigos):
    if not inimigos:
        return None

    inimigo_mais_proximo = None
    menor_distancia = float('inf')

    for inimigo in inimigos:
        distancia = calcular_distancia(jogador_pos, inimigo.pos)
        if distancia < menor_distancia:
            menor_distancia = distancia
            inimigo_mais_proximo = inimigo

    return inimigo_mais_proximo


pygame.font.init()

try:
    fonte_pequena = pygame.font.Font(None, 18)
    fonte_media = pygame.font.Font(None, 24)
    fonte_grande = pygame.font.Font(None, 36)
    fonte_titulo = pygame.font.Font(None, 48)
    fonte_gigante = pygame.font.Font(None, 72)

    try:
        fonte_elegante = pygame.font.SysFont('arial', 24, bold=True)
        fonte_titulo_elegante = pygame.font.SysFont('arial', 48, bold=True)
    except:
        fonte_elegante = fonte_media
        fonte_titulo_elegante = fonte_titulo
except pygame.error:
    fonte_pequena = pygame.font.Font(None, 18)
    fonte_media = pygame.font.Font(None, 24)
    fonte_grande = pygame.font.Font(None, 36)
    fonte_titulo = pygame.font.Font(None, 48)
    fonte_gigante = pygame.font.Font(None, 72)
    fonte_elegante = fonte_media
    fonte_titulo_elegante = fonte_titulo


def desenhar_texto(tela, texto, pos, cor, tamanho, centralizado=False, sombra=True):
    if tamanho <= 18:
        fonte = fonte_pequena
    elif tamanho <= 24:
        fonte = fonte_elegante
    elif tamanho <= 36:
        fonte = fonte_grande
    elif tamanho <= 48:
        fonte = fonte_titulo_elegante
    else:
        fonte = fonte_gigante

    try:
        superficie_texto = fonte.render(str(texto), True, cor)

        if centralizado:
            rect = superficie_texto.get_rect()
            pos_final = (pos[0] - rect.width // 2, pos[1] - rect.height // 2)
        else:
            pos_final = pos

        if sombra and cor != (0, 0, 0):
            sombra_superficie = fonte.render(str(texto), True, (0, 0, 0))
            tela.blit(sombra_superficie, (pos_final[0] + 2, pos_final[1] + 2))

        tela.blit(superficie_texto, pos_final)
    except pygame.error:
        pygame.draw.rect(tela, cor, (*pos, len(str(texto)) * tamanho // 2, tamanho))


def desenhar_barra_vida(tela, pos, hp_atual, hp_max, largura=40, altura=6):
    if hp_max <= 0:
        return

    x = pos[0] - largura // 2
    y = pos[1] - 25
    porcentagem = hp_atual / hp_max

    if porcentagem > 0.6:
        cor_vida = (0, 255, 0)
    elif porcentagem > 0.3:
        cor_vida = (255, 255, 0)
    else:
        cor_vida = (255, 0, 0)

    pygame.draw.rect(tela, (60, 0, 0), (x - 1, y - 1, largura + 2, altura + 2))
    pygame.draw.rect(tela, (40, 40, 40), (x, y, largura, altura))

    largura_vida = int(largura * porcentagem)
    if largura_vida > 0:
        pygame.draw.rect(tela, cor_vida, (x, y, largura_vida, altura))

    pygame.draw.rect(tela, BRANCO, (x - 1, y - 1, largura + 2, altura + 2), 1)


class ParticulaCenario:
    def __init__(self, x, y, tipo):
        self.x = x
        self.y = y
        self.tipo = tipo
        self.vida = random.randint(200, 400)
        self.vida_max = self.vida
        self.velocidade_x = random.uniform(-0.5, 0.5)
        self.velocidade_y = random.uniform(-0.5, 0.5)
        self.tamanho = random.randint(1, 3)
        self.brilho = random.uniform(0.3, 1.0)

    def atualizar(self):
        self.x += self.velocidade_x
        self.y += self.velocidade_y
        self.vida -= 1
        self.brilho = 0.3 + 0.7 * (1 + math.sin(self.vida * 0.05)) / 2

    def esta_vivo(self):
        return self.vida > 0

    def desenhar(self, tela, camera):
        if not esta_na_tela([self.x, self.y], camera):
            return

        pos_tela = posicao_na_tela([self.x, self.y], camera)
        alpha = self.vida / self.vida_max

        if self.tipo == "estrela":
            cor = tuple(int(c * alpha * self.brilho) for c in (255, 255, 200))
            if cor != (0, 0, 0):
                pygame.draw.circle(tela, cor, (int(pos_tela[0]), int(pos_tela[1])), self.tamanho)
        elif self.tipo == "nebulosa":
            cor = tuple(int(c * alpha * self.brilho * 0.5) for c in (100, 50, 150))
            if cor != (0, 0, 0):
                pygame.draw.circle(tela, cor, (int(pos_tela[0]), int(pos_tela[1])), self.tamanho * 2)


class CenarioEspacial:
    def __init__(self):
        self.particulas = []
        self.tempo_spawn = 0
        self.gerar_fundo_inicial()

    def gerar_fundo_inicial(self):
        for _ in range(200):
            x = random.randint(0, LARGURA_MAPA)
            y = random.randint(0, ALTURA_MAPA)

            if random.random() < 0.7:
                self.particulas.append(ParticulaCenario(x, y, "estrela"))
            else:
                self.particulas.append(ParticulaCenario(x, y, "nebulosa"))

    def atualizar(self):
        self.particulas = [p for p in self.particulas if p.esta_vivo()]

        for particula in self.particulas:
            particula.atualizar()

        self.tempo_spawn += 1
        if self.tempo_spawn > 120:
            self.tempo_spawn = 0
            if len(self.particulas) < 250:
                x = random.randint(0, LARGURA_MAPA)
                y = random.randint(0, ALTURA_MAPA)
                tipo = "estrela" if random.random() < 0.8 else "nebulosa"
                self.particulas.append(ParticulaCenario(x, y, tipo))

    def desenhar(self, tela, camera):
        for i in range(0, ALTURA_TELA, 20):
            intensidade = int(5 + (i / ALTURA_TELA) * 15)
            cor_fundo = (intensidade, intensidade // 2, intensidade + 5)
            pygame.draw.rect(tela, cor_fundo, (0, i, LARGURA_TELA, 20))

        for particula in self.particulas:
            particula.desenhar(tela, camera)

        self.desenhar_elementos_decorativos(tela, camera)

    def desenhar_elementos_decorativos(self, tela, camera):
        posicoes_galaxias = [
            (200, 150), (800, 300), (1500, 100), (2200, 400), (500, 600)
        ]

        for pos in posicoes_galaxias:
            if esta_na_tela(pos, camera, 100):
                pos_tela = posicao_na_tela(pos, camera)

                for i in range(3):
                    raio = 15 + i * 8
                    intensidade = 30 - i * 8
                    cor = (intensidade, intensidade // 2, intensidade + 10)
                    pygame.draw.circle(tela, cor, (int(pos_tela[0]), int(pos_tela[1])), raio, 1)

                pygame.draw.circle(tela, (80, 40, 120), (int(pos_tela[0]), int(pos_tela[1])), 3) 