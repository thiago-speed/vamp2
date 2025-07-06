import pygame
import random
import math
from config import *
from utils import *


class Item:
    def __init__(self, x, y, tipo):
        self.pos = [x, y]
        self.raio = ITEM_RAIO
        self.tipo = tipo
        self.ativo = True
        self.tempo_vida = pygame.time.get_ticks() + 30000
        self.animacao = 0
        
        if tipo == "xp_magnetico":
            self.cor = (0, 255, 255)
            self.pulso = True
        elif tipo == "bomba_tela":
            self.cor = (255, 100, 0)
            self.pulso = True
        elif tipo == "coracao":
            self.cor = (255, 50, 100)
            self.pulso = True

    def atualizar(self):
        if pygame.time.get_ticks() > self.tempo_vida:
            self.ativo = False
        self.animacao += 1

    def colidir_com_jogador(self, jogador):
        if not self.ativo:
            return False
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < self.raio + jogador.raio:
            self.ativo = False
            return True
        return False

    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        pos_tela = posicao_na_tela(self.pos, camera)
        if esta_na_tela(self.pos, camera):
            if self.tipo == "coracao":
                intensidade = int(128 + 127 * math.sin(self.animacao * 0.2))
                cor_pulso = (255, intensidade // 2, intensidade // 2)
                raio_coracao = self.raio + int(3 * math.sin(self.animacao * 0.15))
                
                pygame.draw.circle(tela, cor_pulso, 
                                 (int(pos_tela[0] - raio_coracao//2), int(pos_tela[1] - raio_coracao//3)), 
                                 raio_coracao//2)
                pygame.draw.circle(tela, cor_pulso, 
                                 (int(pos_tela[0] + raio_coracao//2), int(pos_tela[1] - raio_coracao//3)), 
                                 raio_coracao//2)
                
                pontos = [
                    (int(pos_tela[0] - raio_coracao), int(pos_tela[1])),
                    (int(pos_tela[0] + raio_coracao), int(pos_tela[1])),
                    (int(pos_tela[0]), int(pos_tela[1] + raio_coracao))
                ]
                pygame.draw.polygon(tela, cor_pulso, pontos)
                pygame.draw.circle(tela, (255, 255, 255), 
                                 (int(pos_tela[0]), int(pos_tela[1])), 
                                 raio_coracao//3, 1)
            else:
                if self.pulso:
                    raio_atual = self.raio + int(3 * math.sin(self.animacao * 0.2))
                    pygame.draw.circle(tela, self.cor, (int(pos_tela[0]), int(pos_tela[1])), raio_atual)
                    pygame.draw.circle(tela, BRANCO, (int(pos_tela[0]), int(pos_tela[1])), raio_atual, 2)
                else:
                    pygame.draw.circle(tela, self.cor, (int(pos_tela[0]), int(pos_tela[1])), self.raio)


def gerar_item_aleatorio(jogador_pos):
    tipos = ["xp_magnetico", "bomba_tela", "coracao"]
    pesos = [0.3, 0.15, 0.01]
    tipo = random.choices(tipos, weights=pesos)[0]
    
    angulo = random.uniform(0, 2 * math.pi)
    distancia = random.uniform(100, 300)
    x = jogador_pos[0] + math.cos(angulo) * distancia
    y = jogador_pos[1] + math.sin(angulo) * distancia
    x = max(50, min(LARGURA_MAPA - 50, x))
    y = max(50, min(ALTURA_MAPA - 50, y))
    
    return Item(x, y, tipo)


def usar_item_xp_magnetico(xps):
    for xp in xps:
        xp.magnetico = True


def usar_item_bomba_tela(inimigos, jogador_pos, camera):
    novos_xps = []
    for inimigo in inimigos[:]:
        if esta_na_tela(inimigo.pos, camera):
            xp = inimigo.morrer()
            if xp:
                novos_xps.append(xp)
            inimigo.ativo = False
    return novos_xps


def usar_item_coracao(jogador):
    cura = int(jogador.hp_max * 0.6)
    jogador.curar(cura)
    return cura 