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
        self.tempo_vida = pygame.time.get_ticks() + 30000  # 30 segundos
        self.animacao = 0
        
        # Configurar por tipo
        if tipo == "xp_magnetico":
            self.cor = (0, 255, 255)  # Ciano
            self.pulso = True
        elif tipo == "bomba_tela":
            self.cor = (255, 100, 0)  # Laranja
            self.pulso = True
        elif tipo == "coracao":
            self.cor = (255, 50, 100)  # Rosa/Vermelho
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
                # Desenhar coração com efeito pulsante
                intensidade = int(128 + 127 * math.sin(self.animacao * 0.2))
                cor_pulso = (255, intensidade // 2, intensidade // 2)
                
                # Desenhar formato de coração (dois círculos + triângulo)
                raio_coracao = self.raio + int(3 * math.sin(self.animacao * 0.15))
                
                # Círculos superiores do coração
                pygame.draw.circle(tela, cor_pulso, 
                                 (int(pos_tela[0] - raio_coracao//2), int(pos_tela[1] - raio_coracao//3)), 
                                 raio_coracao//2)
                pygame.draw.circle(tela, cor_pulso, 
                                 (int(pos_tela[0] + raio_coracao//2), int(pos_tela[1] - raio_coracao//3)), 
                                 raio_coracao//2)
                
                # Triângulo inferior do coração
                pontos = [
                    (int(pos_tela[0] - raio_coracao), int(pos_tela[1])),
                    (int(pos_tela[0] + raio_coracao), int(pos_tela[1])),
                    (int(pos_tela[0]), int(pos_tela[1] + raio_coracao))
                ]
                pygame.draw.polygon(tela, cor_pulso, pontos)
                
                # Brilho adicional
                pygame.draw.circle(tela, (255, 255, 255), 
                                 (int(pos_tela[0]), int(pos_tela[1])), 
                                 raio_coracao//3, 1)
            else:
                # Outros itens - efeito pulsante normal
                if self.pulso:
                    raio_atual = self.raio + int(3 * math.sin(self.animacao * 0.2))
                    pygame.draw.circle(tela, self.cor, (int(pos_tela[0]), int(pos_tela[1])), raio_atual)
                    pygame.draw.circle(tela, BRANCO, (int(pos_tela[0]), int(pos_tela[1])), raio_atual, 2)
                else:
                    pygame.draw.circle(tela, self.cor, (int(pos_tela[0]), int(pos_tela[1])), self.raio)

def gerar_item_aleatorio(jogador_pos):
    """Gera um item em posição aleatória próxima ao jogador"""
    
    # Tipos de itens e suas probabilidades
    tipos = ["xp_magnetico", "bomba_tela", "coracao"]
    pesos = [0.4, 0.4, 0.2]  # 20% chance de coração
    
    tipo = random.choices(tipos, weights=pesos)[0]
    
    # Posição aleatória próxima ao jogador
    angulo = random.uniform(0, 2 * math.pi)
    distancia = random.uniform(100, 300)
    
    x = jogador_pos[0] + math.cos(angulo) * distancia
    y = jogador_pos[1] + math.sin(angulo) * distancia
    
    # Limitar ao mapa
    x = max(50, min(LARGURA_MAPA - 50, x))
    y = max(50, min(ALTURA_MAPA - 50, y))
    
    return Item(x, y, tipo)

def usar_item_xp_magnetico(xps):
    """Ativa efeito magnético em todos os XPs"""
    for xp in xps:
        xp.magnetico = True

def usar_item_bomba_tela(inimigos, jogador_pos, camera):
    """Mata todos os inimigos na tela e gera XP"""
    novos_xps = []
    
    for inimigo in inimigos[:]:
        if esta_na_tela(inimigo.pos, camera):
            xp = inimigo.morrer()
            if xp:
                novos_xps.append(xp)
            inimigo.ativo = False
    
    return novos_xps

def usar_item_coracao(jogador):
    """Restaura 60% da vida atual do jogador"""
    cura = int(jogador.hp_max * 0.6)
    jogador.curar(cura)
    return cura 