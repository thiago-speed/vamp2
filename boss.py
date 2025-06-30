import pygame
import math
import random
from config import *
from utils import *

class Boss:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.raio = BOSS_RAIO
        self.hp_max = BOSS_HP
        self.hp = self.hp_max
        self.velocidade = 1
        self.dano = 5
        self.ativo = True
        self.cor = ROXO
        
        # Estados de ataque
        self.ultimo_ataque = 0
        self.intervalo_ataque = 3000  # 3 segundos entre ataques
        self.tipo_ataque_atual = 0
        self.executando_ataque = False
        self.tempo_ataque = 0
        
        # Ataques específicos
        self.ataques = ["laser", "pulo", "espinhos", "dash", "soco"]
        self.laser_duracao = 2000
        self.pulo_altura = 100
        self.espinhos_quantidade = 8
        self.dash_velocidade = 8
        self.soco_alcance = 150
        
        # Posições para alguns ataques
        self.pos_original = [x, y]
        self.alvo_dash = None
        self.no_ar = False
    
    def atualizar(self, jogador_pos):
        if not self.ativo:
            return []
        
        projéteis_criados = []
        tempo_atual = pygame.time.get_ticks()
        
        # Lógica de movimento básico (quando não atacando)
        if not self.executando_ataque:
            # Mover em direção ao jogador lentamente
            dx = jogador_pos[0] - self.pos[0]
            dy = jogador_pos[1] - self.pos[1]
            
            if dx != 0 or dy != 0:
                dir_x, dir_y = normalizar_vetor(dx, dy)
                self.pos[0] += dir_x * self.velocidade
                self.pos[1] += dir_y * self.velocidade
            
            # Verificar se pode atacar
            if tempo_atual - self.ultimo_ataque > self.intervalo_ataque:
                self.iniciar_ataque(jogador_pos)
        
        # Executar ataque atual
        else:
            projéteis_criados = self.executar_ataque(jogador_pos)
        
        # Limitar posição ao mapa
        self.pos = list(limitar_posicao(self.pos))
        
        return projéteis_criados
    
    def iniciar_ataque(self, jogador_pos):
        """Inicia um ataque aleatório"""
        self.executando_ataque = True
        self.tempo_ataque = pygame.time.get_ticks()
        self.ultimo_ataque = pygame.time.get_ticks()
        self.tipo_ataque_atual = random.randint(0, len(self.ataques) - 1)
        
        # Preparações específicas por ataque
        if self.ataques[self.tipo_ataque_atual] == "pulo":
            self.no_ar = True
        elif self.ataques[self.tipo_ataque_atual] == "dash":
            self.alvo_dash = jogador_pos.copy()
        
    def executar_ataque(self, jogador_pos):
        """Executa o ataque atual"""
        tempo_atual = pygame.time.get_ticks()
        tempo_decorrido = tempo_atual - self.tempo_ataque
        ataque = self.ataques[self.tipo_ataque_atual]
        projéteis = []
        
        if ataque == "laser":
            projéteis = self.ataque_laser(jogador_pos, tempo_decorrido)
        elif ataque == "pulo":
            projéteis = self.ataque_pulo(jogador_pos, tempo_decorrido)
        elif ataque == "espinhos":
            projéteis = self.ataque_espinhos(tempo_decorrido)
        elif ataque == "dash":
            projéteis = self.ataque_dash(tempo_decorrido)
        elif ataque == "soco":
            projéteis = self.ataque_soco(jogador_pos, tempo_decorrido)
        
        # Verificar se o ataque terminou
        if tempo_decorrido > 2500:  # 2.5 segundos de duração
            self.executando_ataque = False
            self.no_ar = False
            self.alvo_dash = None
        
        return projéteis
    
    def ataque_laser(self, jogador_pos, tempo):
        """Raio laser que segue o jogador"""
        if tempo % 100 == 0:  # Criar projétil a cada 100ms
            return [ProjetilBoss(self.pos[0], self.pos[1], jogador_pos[0], jogador_pos[1], 
                               self.dano, 10, 400, "laser")]
        return []
    
    def ataque_pulo(self, jogador_pos, tempo):
        """Pula e cria ondas de choque"""
        if tempo == 1000:  # No meio do pulo
            return [ProjetilBoss(self.pos[0], self.pos[1], 0, 0, self.dano, 0, 200, "onda")]
        return []
    
    def ataque_espinhos(self, tempo):
        """Espinhos saem do chão em todas as direções"""
        if tempo == 500:  # Após 0.5s
            projéteis = []
            for i in range(self.espinhos_quantidade):
                angulo = (2 * math.pi * i) / self.espinhos_quantidade
                x_alvo = self.pos[0] + math.cos(angulo) * 150
                y_alvo = self.pos[1] + math.sin(angulo) * 150
                projéteis.append(ProjetilBoss(self.pos[0], self.pos[1], x_alvo, y_alvo, 
                                            self.dano, 6, 300, "espinho"))
            return projéteis
        return []
    
    def ataque_dash(self, tempo):
        """Dash rápido em direção ao último local do jogador"""
        if self.alvo_dash and tempo < 1000:
            dx = self.alvo_dash[0] - self.pos[0]
            dy = self.alvo_dash[1] - self.pos[1]
            
            if dx != 0 or dy != 0:
                dir_x, dir_y = normalizar_vetor(dx, dy)
                self.pos[0] += dir_x * self.dash_velocidade
                self.pos[1] += dir_y * self.dash_velocidade
        return []
    
    def ataque_soco(self, jogador_pos, tempo):
        """Soco com área de efeito"""
        if tempo == 800:  # Após 0.8s
            return [ProjetilBoss(self.pos[0], self.pos[1], jogador_pos[0], jogador_pos[1], 
                               self.dano * 2, 0, self.soco_alcance, "soco")]
        return []
    
    def receber_dano(self, dano):
        self.hp -= dano
        if self.hp <= 0:
            self.ativo = False
    
    def colidir_com_jogador(self, jogador):
        """Verifica colisão direta com o jogador"""
        if not self.ativo or self.no_ar:
            return False
        
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < self.raio + jogador.raio:
            return jogador.receber_dano(self.dano)
        
        return False
    
    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        
        pos_tela = posicao_na_tela(self.pos, camera)
        
        if esta_na_tela(self.pos, camera):
            # Cor especial se atacando
            cor = DOURADO if self.executando_ataque else self.cor
            
            # Desenhar menor se no ar
            raio_atual = self.raio // 2 if self.no_ar else self.raio
            
            pygame.draw.circle(tela, cor, (int(pos_tela[0]), int(pos_tela[1])), raio_atual)
            pygame.draw.circle(tela, BRANCO, (int(pos_tela[0]), int(pos_tela[1])), raio_atual, 3)
            
            # Barra de vida
            desenhar_barra_vida(tela, pos_tela, self.hp, self.hp_max, 80, 8)
            
            # Indicador de ataque
            if self.executando_ataque:
                ataque_nome = self.ataques[self.tipo_ataque_atual].upper()
                desenhar_texto(tela, ataque_nome, (pos_tela[0] - 30, pos_tela[1] - 70), 
                              AMARELO, 20)

class ProjetilBoss:
    def __init__(self, x, y, alvo_x, alvo_y, dano, velocidade, alcance, tipo):
        self.pos = [x, y]
        self.pos_inicial = [x, y]
        self.dano = dano
        self.velocidade = velocidade
        self.alcance = alcance
        self.tipo = tipo
        self.ativo = True
        self.raio = 5
        
        # Configurar por tipo
        if tipo == "laser":
            self.cor = ROXO
            self.raio = 3
        elif tipo == "onda":
            self.cor = AZUL
            self.raio = 100  # Área grande
            self.velocidade = 0
        elif tipo == "espinho":
            self.cor = VERDE
            self.raio = 4
        elif tipo == "soco":
            self.cor = LARANJA
            self.raio = 80  # Área grande
            self.velocidade = 0
        
        # Calcular direção se necessário
        if velocidade > 0:
            dx = alvo_x - x
            dy = alvo_y - y
            self.direcao_x, self.direcao_y = normalizar_vetor(dx, dy)
        else:
            self.direcao_x, self.direcao_y = 0, 0
    
    def atualizar(self):
        if not self.ativo:
            return
        
        # Mover se tiver velocidade
        if self.velocidade > 0:
            self.pos[0] += self.direcao_x * self.velocidade
            self.pos[1] += self.direcao_y * self.velocidade
        
        # Verificar alcance
        distancia_percorrida = calcular_distancia(self.pos, self.pos_inicial)
        if distancia_percorrida > self.alcance:
            self.ativo = False
        
        # Tipos especiais
        if self.tipo in ["onda", "soco"]:
            # Projéteis de área desaparecem rapidamente
            if pygame.time.get_ticks() % 500 == 0:
                self.ativo = False
    
    def colidir_com_jogador(self, jogador):
        if not self.ativo:
            return False
        
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < self.raio + jogador.raio:
            self.ativo = False
            return jogador.receber_dano(self.dano)
        
        return False
    
    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        
        pos_tela = posicao_na_tela(self.pos, camera)
        
        if esta_na_tela(self.pos, camera):
            if self.tipo in ["onda", "soco"]:
                # Desenhar área de efeito semi-transparente
                surf = pygame.Surface((self.raio * 2, self.raio * 2))
                surf.set_alpha(100)
                surf.fill(self.cor)
                tela.blit(surf, (pos_tela[0] - self.raio, pos_tela[1] - self.raio))
            else:
                pygame.draw.circle(tela, self.cor, (int(pos_tela[0]), int(pos_tela[1])), self.raio) 