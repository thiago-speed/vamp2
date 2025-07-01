import pygame
import math
import random
from config import *
from utils import *

class Projetil:
    def __init__(self, x, y, alvo_x, alvo_y, dano, velocidade, alcance, atravessar=0):
        self.pos = [x, y]
        self.pos_inicial = [x, y]
        self.raio = PROJETIL_RAIO
        self.dano = dano
        self.velocidade = velocidade
        self.alcance = alcance
        self.atravessar = atravessar
        self.inimigos_atingidos = []
        
        # Calcular direção
        dx = alvo_x - x
        dy = alvo_y - y
        self.direcao_x, self.direcao_y = normalizar_vetor(dx, dy)
        
        self.ativo = True
    
    def atualizar(self):
        if not self.ativo:
            return
        
        # Mover projétil
        self.pos[0] += self.direcao_x * self.velocidade
        self.pos[1] += self.direcao_y * self.velocidade
        
        # Verificar alcance
        distancia_percorrida = calcular_distancia(self.pos, self.pos_inicial)
        if distancia_percorrida > self.alcance:
            self.ativo = False
        
        # Verificar limites do mapa
        if (self.pos[0] < 0 or self.pos[0] > LARGURA_MAPA or 
            self.pos[1] < 0 or self.pos[1] > ALTURA_MAPA):
            self.ativo = False
    
    def colidir_com_inimigo(self, inimigo):
        if not self.ativo:
            return False
        
        # Verificar se já atingiu este inimigo
        if inimigo in self.inimigos_atingidos:
            return False
        
        # Verificar colisão
        distancia = calcular_distancia(self.pos, inimigo.pos)
        if distancia < self.raio + inimigo.raio:
            # Causar dano
            inimigo.receber_dano(self.dano)
            self.inimigos_atingidos.append(inimigo)
            
            # Verificar se deve ser destruído
            if len(self.inimigos_atingidos) > self.atravessar:
                self.ativo = False
            
            return True
        
        return False
    
    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        
        pos_tela = posicao_na_tela(self.pos, camera)
        
        # Só desenhar se estiver na tela
        if esta_na_tela(self.pos, camera):
            pygame.draw.circle(tela, AMARELO, (int(pos_tela[0]), int(pos_tela[1])), self.raio)

class XP:
    def __init__(self, x, y, valor=XP_VALOR):
        self.pos = [x, y]
        self.raio = XP_RAIO
        self.valor = valor
        self.ativo = True
        self.magnetico = False
        self.velocidade_magnetica = 8
    
    def atualizar(self, jogador_pos):
        if not self.ativo:
            return
        
        # Movimento magnético se ativado
        if self.magnetico:
            dx = jogador_pos[0] - self.pos[0]
            dy = jogador_pos[1] - self.pos[1]
            
            if dx != 0 or dy != 0:
                dir_x, dir_y = normalizar_vetor(dx, dy)
                self.pos[0] += dir_x * self.velocidade_magnetica
                self.pos[1] += dir_y * self.velocidade_magnetica
    
    def colidir_com_jogador(self, jogador):
        if not self.ativo:
            return False
        
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < jogador.raio_coleta:
            self.ativo = False
            return True
        
        return False
    
    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        
        pos_tela = posicao_na_tela(self.pos, camera)
        
        if esta_na_tela(self.pos, camera):
            pygame.draw.circle(tela, VERDE, (int(pos_tela[0]), int(pos_tela[1])), self.raio)

class ProjetilInimigo:
    def __init__(self, x, y, alvo_x, alvo_y, dano=1, velocidade=3):
        self.pos = [x, y]
        self.dano = dano
        self.velocidade = velocidade
        self.ativo = True
        self.raio = 8  # Maior para ser mais visível
        
        # Calcular direção
        dx = alvo_x - x
        dy = alvo_y - y
        distancia = math.sqrt(dx*dx + dy*dy)
        if distancia > 0:
            self.dir_x = dx / distancia
            self.dir_y = dy / distancia
        else:
            self.dir_x = 0
            self.dir_y = 0
        
        # Efeitos visuais melhorados
        self.animacao = 0
        self.particulas_rastro = []
        self.brilho = 1.0
        
        # Tempo de vida
        self.tempo_vida = pygame.time.get_ticks() + 4000  # 4 segundos
        
    def atualizar(self):
        if not self.ativo:
            return
        
        # Mover projétil
        self.pos[0] += self.dir_x * self.velocidade
        self.pos[1] += self.dir_y * self.velocidade
        
        # Verificar limites do mapa
        if (self.pos[0] < 0 or self.pos[0] > LARGURA_MAPA or 
            self.pos[1] < 0 or self.pos[1] > ALTURA_MAPA):
            self.ativo = False
            return
        
        # Verificar tempo de vida
        if pygame.time.get_ticks() > self.tempo_vida:
            self.ativo = False
            return
        
        # Atualizar animação
        self.animacao += 1
        self.brilho = 0.8 + 0.4 * math.sin(self.animacao * 0.2)
        
        # Gerar partículas de rastro
        if self.animacao % 3 == 0:  # A cada 3 frames
            self.particulas_rastro.append({
                'pos': list(self.pos),
                'vida': 15,
                'vida_max': 15,
                'tamanho': random.randint(2, 4)
            })
        
        # Atualizar partículas
        for particula in self.particulas_rastro[:]:
            particula['vida'] -= 1
            if particula['vida'] <= 0:
                self.particulas_rastro.remove(particula)
        
        # Limitar número de partículas
        if len(self.particulas_rastro) > 8:
            self.particulas_rastro.pop(0)
    
    def colidir_com_jogador(self, jogador):
        if not self.ativo:
            return False
        
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < self.raio + jogador.raio:
            if jogador.receber_dano(self.dano):
                self.ativo = False
                return True
        return False
    
    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        
        pos_tela = posicao_na_tela(self.pos, camera)
        if esta_na_tela(self.pos, camera):
            # Desenhar rastro de partículas
            for particula in self.particulas_rastro:
                vida_prop = particula['vida'] / particula['vida_max']
                part_pos = posicao_na_tela(particula['pos'], camera)
                alpha = vida_prop * 0.6
                tamanho = int(particula['tamanho'] * vida_prop)
                
                if tamanho > 0:
                    cor_rastro = tuple(max(0, min(255, int(c * alpha))) for c in (255, 100, 100))
                    pygame.draw.circle(tela, cor_rastro, (int(part_pos[0]), int(part_pos[1])), tamanho)
            
            # Desenhar aura do projétil
            raio_aura = int(self.raio * (1.2 + 0.3 * self.brilho))
            cor_aura = tuple(max(0, min(255, int(c * 0.3 * self.brilho))) for c in (255, 0, 0))
            pygame.draw.circle(tela, cor_aura, (int(pos_tela[0]), int(pos_tela[1])), raio_aura)
            
            # Desenhar projétil principal com múltiplas camadas
            # Camada externa vermelha escura
            pygame.draw.circle(tela, (150, 0, 0), (int(pos_tela[0]), int(pos_tela[1])), self.raio)
            
            # Camada média vermelha brilhante
            raio_medio = int(self.raio * 0.7)
            cor_media = tuple(max(0, min(255, int(c * self.brilho))) for c in (255, 50, 50))
            pygame.draw.circle(tela, cor_media, (int(pos_tela[0]), int(pos_tela[1])), raio_medio)
            
            # Centro brilhante
            raio_centro = int(self.raio * 0.4)
            cor_centro = tuple(max(0, min(255, int(c * self.brilho))) for c in (255, 200, 200))
            pygame.draw.circle(tela, cor_centro, (int(pos_tela[0]), int(pos_tela[1])), raio_centro)
            
            # Efeito de pulsação
            if int(self.animacao / 5) % 2 == 0:
                raio_pulso = int(self.raio * 1.3)
                cor_pulso = tuple(max(0, min(255, int(c * 0.4))) for c in (255, 0, 0))
                pygame.draw.circle(tela, cor_pulso, (int(pos_tela[0]), int(pos_tela[1])), raio_pulso, 2) 