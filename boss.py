

import pygame
import random
import math
from config import *
from utils import *

class ProjetilBoss:
    def __init__(self, x, y, alvo_x, alvo_y, dano, velocidade, cor, tipo="normal"):
        self.pos = [x, y]
        self.alvo = [alvo_x, alvo_y]
        self.dano = dano
        self.velocidade = velocidade * 0.7  
        self.cor = cor
        self.tipo = tipo
        self.ativo = True
        self.raio = 8 if tipo in ["basico", "laser"] else 12
        
        
        dx = alvo_x - x
        dy = alvo_y - y
        if dx != 0 or dy != 0:
            self.direcao = normalizar_vetor(dx, dy)
        else:
            self.direcao = (1, 0)
        
        
        self.tempo_vida = 8000  
        self.tempo_criacao = pygame.time.get_ticks()

    def atualizar(self):
        """Atualiza posição e estado do projétil"""
        if not self.ativo:
            return
        
        
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_criacao > self.tempo_vida:
            self.ativo = False
            return
        
        
        self.pos[0] += self.direcao[0] * self.velocidade
        self.pos[1] += self.direcao[1] * self.velocidade
        
        
        if (self.pos[0] < -100 or self.pos[0] > LARGURA_MAPA + 100 or 
            self.pos[1] < -100 or self.pos[1] > ALTURA_MAPA + 100):
            self.ativo = False

    def colidir_com_jogador(self, jogador):
        """Verifica colisão com o jogador"""
        if not self.ativo:
            return False
        
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < self.raio + jogador.raio:
            self.ativo = False
            return jogador.receber_dano(self.dano)
        
        return False

    def desenhar(self, tela, camera):
        """Desenha o projétil na tela"""
        if not self.ativo:
            return
        
        
        pos_tela = (
            int(self.pos[0] - camera[0]),
            int(self.pos[1] - camera[1])
        )
        
        
        pygame.draw.circle(tela, self.cor, pos_tela, self.raio)

class IndicadorAtaque:
    """Indicador visual para ataques que caem do céu"""
    def __init__(self, x, y, tempo_criacao, tempo_queda):
        self.pos = [x, y]
        self.tempo_criacao = tempo_criacao
        self.tempo_queda = tempo_queda
        self.ativo = True
        self.raio = 30
        
    def atualizar(self):
        """Atualiza o indicador"""
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual >= self.tempo_queda:
            self.ativo = False
    
    def desenhar(self, tela, camera):
        """Desenha o indicador no chão"""
        if not self.ativo:
            return
        
        pos_tela = posicao_na_tela(self.pos, camera)
        if esta_na_tela(self.pos, camera):
            
            tempo_atual = pygame.time.get_ticks()
            tempo_restante = self.tempo_queda - tempo_atual
            intensidade = max(0, min(255, int(255 * (tempo_restante / 1500))))  
            
            cor = (intensidade, 0, 0, 255)  
            pygame.draw.circle(tela, (255, 0, 0), (int(pos_tela[0]), int(pos_tela[1])), self.raio, 3)
            pygame.draw.circle(tela, (255, 0, 0), (int(pos_tela[0]), int(pos_tela[1])), self.raio//2)

class Boss:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.raio = 38  
        self.hp_max = 375000
        self.hp = self.hp_max
        self.dano = 100  
        self.dano_projeteis = 75  
        self.ativo = True
        self.invulneravel = False
        self.tempo_ultimo_dano = 0
        self.cooldown_dano = 100
        self.fase = 1
        self.hp_fase2 = self.hp_max * 0.66
        self.hp_fase3 = self.hp_max * 0.33
        self.tipo = 'boss'  # Identificador para o campo gravitacional
        
        
        self.velocidade = 2.5
        self.direcao = [0, 0]
        self.tempo_mudanca_direcao = 0
        self.intervalo_mudanca_direcao = 2000
        self.ponto_destino = None  
        
        
        self.ataque_atual = None
        self.tempo_ultimo_ataque = 0
        self.tempo_pensamento = 0
        
        self.intervalo_pensamento_fase = [3000, 1700, 900]  
        self.duracao_descanso_fase = [1500, 700, 350]       
        self.max_ataques_antes_descanso_fase = [3, 5, 8]    
        self.contador_ataques = 0
        self.max_ataques_antes_descanso = self.max_ataques_antes_descanso_fase[0]
        self.tempo_descanso = 0
        self.duracao_descanso = self.duracao_descanso_fase[0]
        self.em_descanso = False
        
        
        self.ataques_fase1 = [
            "tiro_simples",
            "tiro_duplo",
            "tiro_triplo",
            "tiro_cruzado",
            "tiro_circular",
            "tiro_espiral_simples"  
        ]
        
        
        self.ataques_fase2 = [
            "tiro_espiral_duplo",    
            "tiro_alternado",        
            "chuva_projeteis",       
            "bullet_hell_1",
            "bullet_hell_2"
        ]
        
        
        self.ataques_fase3 = [
            "bullet_hell_caos",      
            "tempestade_projeteis",  
            "espiral_morte",         
            "dash_ataque",
            "tiros_queda"
        ]
        
        
        self.indicadores = []
        
        
        self.dash_ativo = False
        self.dash_direcao = [0, 0]
        self.dash_tempo = 0
        self.duracao_dash = 500

    def atualizar(self, jogador_pos):
        """Atualiza o estado do boss"""
        if not self.ativo:
            return []
        tempo_atual = pygame.time.get_ticks()
        self.atualizar_movimento(jogador_pos, tempo_atual)
        
        if self.hp <= self.hp_fase3:
            self.fase = 3
        elif self.hp <= self.hp_fase2:
            self.fase = 2
        else:
            self.fase = 1
        
        self.intervalo_pensamento = self.intervalo_pensamento_fase[self.fase-1]
        self.duracao_descanso = self.duracao_descanso_fase[self.fase-1]
        self.max_ataques_antes_descanso = self.max_ataques_antes_descanso_fase[self.fase-1]
        
        projeteis = []
        if self.em_descanso:
            if tempo_atual - self.tempo_descanso >= self.duracao_descanso:
                self.em_descanso = False
                self.contador_ataques = 0
                self.ataque_atual = None
                self.tempo_ultimo_ataque = tempo_atual  
        else:
            
            if self.ataque_atual is None:
                if tempo_atual - self.tempo_ultimo_ataque >= self.intervalo_pensamento:
                    self.escolher_proximo_ataque()
                    self.tempo_ultimo_ataque = tempo_atual
            
            if self.ataque_atual:
                novos_projeteis = self.executar_ataque(jogador_pos, tempo_atual)
                if novos_projeteis:
                    projeteis.extend(novos_projeteis)
                
                self.ataque_atual = None
        return projeteis

    def atualizar_movimento(self, jogador_pos, tempo_atual):
        """Atualiza o movimento do boss com padrões aleatórios"""
        if self.dash_ativo:
            return
        
        
        if self.ponto_destino is None or tempo_atual - self.tempo_mudanca_direcao > self.intervalo_mudanca_direcao:
            
            margem = 100
            self.ponto_destino = [
                random.randint(margem, LARGURA_MAPA - margem),
                random.randint(margem, ALTURA_MAPA - margem)
            ]
            self.tempo_mudanca_direcao = tempo_atual
        
        
        dx = self.ponto_destino[0] - self.pos[0]
        dy = self.ponto_destino[1] - self.pos[1]
        distancia = math.sqrt(dx * dx + dy * dy)
        
        if distancia > 5:  
            
            self.direcao = [dx / distancia, dy / distancia]
            
            
            velocidade_atual = self.velocidade * (1 + (self.fase - 1) * 0.3)
            
            
            self.pos[0] += self.direcao[0] * velocidade_atual
            self.pos[1] += self.direcao[1] * velocidade_atual
        else:
            
            self.ponto_destino = None
        
        
        self.pos[0] = max(self.raio, min(LARGURA_MAPA - self.raio, self.pos[0]))
        self.pos[1] = max(self.raio, min(ALTURA_MAPA - self.raio, self.pos[1]))

    def atualizar_dash(self, tempo_atual):
        """Atualiza o dash do boss"""
        if tempo_atual - self.dash_tempo > self.duracao_dash:
            self.dash_ativo = False
        else:
            
            self.pos[0] += self.dash_direcao[0] * self.velocidade * 3
            self.pos[1] += self.dash_direcao[1] * self.velocidade * 3
            
            
            self.pos[0] = max(self.raio, min(LARGURA_MAPA - self.raio, self.pos[0]))
            self.pos[1] = max(self.raio, min(ALTURA_MAPA - self.raio, self.pos[1]))

    def atualizar_indicadores(self):
        """Atualiza os indicadores de ataques"""
        for indicador in self.indicadores[:]:
            indicador.atualizar()
            if not indicador.ativo:
                self.indicadores.remove(indicador)

    def escolher_proximo_ataque(self):
        """Escolhe o próximo ataque baseado na fase atual"""
        if self.fase == 3:
            if random.random() < 0.6:
                self.ataque_atual = random.choice(self.ataques_fase3)
            elif random.random() < 0.5:
                self.ataque_atual = random.choice(self.ataques_fase2)
            else:
                self.ataque_atual = random.choice(self.ataques_fase1)
        elif self.fase == 2:
            if random.random() < 0.7:
                self.ataque_atual = random.choice(self.ataques_fase2)
            else:
                self.ataque_atual = random.choice(self.ataques_fase1)
        else:
            self.ataque_atual = random.choice(self.ataques_fase1)
        self.contador_ataques += 1
        if self.contador_ataques >= self.max_ataques_antes_descanso:
            self.em_descanso = True
            self.tempo_descanso = pygame.time.get_ticks()
        return self.ataque_atual

    def executar_ataque(self, jogador_pos, tempo_atual):
        """Executa o ataque atual"""
        projeteis = []
        
        if self.ataque_atual == "tiro_espiral_simples":
            projeteis.extend(self.ataque_tiro_espiral_simples())
        elif self.ataque_atual == "tiro_espiral_duplo":
            projeteis.extend(self.ataque_tiro_espiral_duplo())
        elif self.ataque_atual == "tiro_alternado":
            projeteis.extend(self.ataque_tiro_alternado(jogador_pos))
        elif self.ataque_atual == "chuva_projeteis":
            projeteis.extend(self.ataque_chuva_projeteis(jogador_pos))
        elif self.ataque_atual == "bullet_hell_caos":
            projeteis.extend(self.ataque_bullet_hell_caos())
        elif self.ataque_atual == "tempestade_projeteis":
            projeteis.extend(self.ataque_tempestade_projeteis(jogador_pos))
        elif self.ataque_atual == "espiral_morte":
            projeteis.extend(self.ataque_espiral_morte())
        else:
            
            if self.ataque_atual == "tiro_simples":
                projeteis.extend(self.ataque_tiro_simples(jogador_pos))
            elif self.ataque_atual == "tiro_duplo":
                projeteis.extend(self.ataque_tiro_duplo(jogador_pos))
            elif self.ataque_atual == "tiro_triplo":
                projeteis.extend(self.ataque_tiro_triplo(jogador_pos))
            elif self.ataque_atual == "tiro_cruzado":
                projeteis.extend(self.ataque_tiro_cruzado(jogador_pos))
            elif self.ataque_atual == "tiro_circular":
                projeteis.extend(self.ataque_tiro_circular())
            elif self.ataque_atual == "bullet_hell_1":
                projeteis.extend(self.ataque_bullet_hell_1(jogador_pos))
            elif self.ataque_atual == "bullet_hell_2":
                projeteis.extend(self.ataque_bullet_hell_2(jogador_pos))
            elif self.ataque_atual == "dash_ataque":
                self.ataque_dash(jogador_pos)
            elif self.ataque_atual == "tiros_queda":
                self.ataque_tiros_queda(jogador_pos, tempo_atual)
        
        return projeteis

    
    def ataque_tiro_espiral_simples(self):
        """Espiral simples de projéteis"""
        projeteis = []
        angulo_base = pygame.time.get_ticks() * 0.005
        for i in range(8):
            angulo = angulo_base + (i * math.pi / 4)
            alvo_x = self.pos[0] + math.cos(angulo) * 100
            alvo_y = self.pos[1] + math.sin(angulo) * 100
            projeteis.append(ProjetilBoss(self.pos[0], self.pos[1], 
                                         alvo_x, alvo_y, 
                                         self.dano_projeteis, 3, (255, 200, 0)))
        return projeteis

    def ataque_tiro_espiral_duplo(self):
        """Duas espirais de projéteis em direções opostas"""
        projeteis = []
        angulo_base = pygame.time.get_ticks() * 0.005
        for i in range(12):
            
            angulo1 = angulo_base + (i * math.pi / 6)
            alvo_x = self.pos[0] + math.cos(angulo1) * 100
            alvo_y = self.pos[1] + math.sin(angulo1) * 100
            projeteis.append(ProjetilBoss(self.pos[0], self.pos[1], 
                                        alvo_x, alvo_y, 
                                        self.dano_projeteis, 4, (255, 100, 0)))
            
            
            angulo2 = -angulo_base + (i * math.pi / 6)
            alvo_x = self.pos[0] + math.cos(angulo2) * 100
            alvo_y = self.pos[1] + math.sin(angulo2) * 100
            projeteis.append(ProjetilBoss(self.pos[0], self.pos[1], 
                                        alvo_x, alvo_y, 
                                        self.dano_projeteis, 4, (255, 100, 0)))
        return projeteis

    def ataque_tiro_alternado(self, jogador_pos):
        """Alternância entre tiros direcionados e tiros em círculo"""
        projeteis = []
        tempo = pygame.time.get_ticks()
        
        
        if (tempo // 500) % 2 == 0:  
            
            dx = jogador_pos[0] - self.pos[0]
            dy = jogador_pos[1] - self.pos[1]
            angulo_base = math.atan2(dy, dx)
            for i in range(3):
                angulo = angulo_base + (i - 1) * math.pi/6
                alvo_x = self.pos[0] + math.cos(angulo) * 100
                alvo_y = self.pos[1] + math.sin(angulo) * 100
                projeteis.append(ProjetilBoss(self.pos[0], self.pos[1], 
                                            alvo_x, alvo_y, 
                                            self.dano_projeteis, 4, (255, 150, 0)))
        else:
            
            for i in range(8):
                angulo = i * math.pi/4
                alvo_x = self.pos[0] + math.cos(angulo) * 100
                alvo_y = self.pos[1] + math.sin(angulo) * 100
                projeteis.append(ProjetilBoss(self.pos[0], self.pos[1], 
                                            alvo_x, alvo_y, 
                                            self.dano_projeteis, 3, (0, 150, 255)))
        return projeteis

    def ataque_chuva_projeteis(self, jogador_pos):
        """Chuva de projéteis que seguem o jogador"""
        projeteis = []
        num_projeteis = 12
        
        for i in range(num_projeteis):
            
            x_inicial = jogador_pos[0] + random.randint(-200, 200)
            y_inicial = jogador_pos[1] - 300 + random.randint(-50, 50)
            
            
            x_inicial = max(0, min(LARGURA_MAPA, x_inicial))
            y_inicial = max(0, min(ALTURA_MAPA, y_inicial))
            
            projeteis.append(ProjetilBoss(x_inicial, y_inicial,
                                        jogador_pos[0], jogador_pos[1],
                                        self.dano_projeteis, 5, (100, 100, 255)))
        return projeteis

    def ataque_bullet_hell_caos(self):
        """Padrão caótico de projéteis"""
        projeteis = []
        tempo = pygame.time.get_ticks() * 0.003
        num_projeteis = 16
        
        for i in range(num_projeteis):
            
            angulo = (i * math.pi * 2 / num_projeteis) + math.sin(tempo) + math.cos(tempo * 0.5)
            velocidade = 3 + math.sin(tempo + i) * 2
            
            alvo_x = self.pos[0] + math.cos(angulo) * 100
            alvo_y = self.pos[1] + math.sin(angulo) * 100
            
            cor = (
                255,
                int(128 + 127 * math.sin(tempo + i)),
                int(128 + 127 * math.cos(tempo + i))
            )
            
            projeteis.append(ProjetilBoss(self.pos[0], self.pos[1],
                                        alvo_x, alvo_y,
                                        self.dano_projeteis, velocidade, cor))
        return projeteis

    def ataque_tempestade_projeteis(self, jogador_pos):
        """Tempestade intensa de projéteis"""
        projeteis = []
        num_ondas = 3
        projeteis_por_onda = 12
        
        for onda in range(num_ondas):
            angulo_base = (pygame.time.get_ticks() * 0.002) + (onda * math.pi / num_ondas)
            
            for i in range(projeteis_por_onda):
                angulo = angulo_base + (i * 2 * math.pi / projeteis_por_onda)
                velocidade = 4 + onda * 0.5
                
                alvo_x = self.pos[0] + math.cos(angulo) * 100
                alvo_y = self.pos[1] + math.sin(angulo) * 100
                
                cor = (255, 50 + onda * 70, 50 + onda * 70)
                
                projeteis.append(ProjetilBoss(self.pos[0], self.pos[1],
                                            alvo_x, alvo_y,
                                            self.dano_projeteis, velocidade, cor))
        return projeteis

    def ataque_espiral_morte(self):
        """Espiral múltipla de projéteis mortais"""
        projeteis = []
        tempo = pygame.time.get_ticks() * 0.004
        num_bracos = 4
        projeteis_por_braco = 8
        
        for braco in range(num_bracos):
            angulo_base = tempo + (braco * 2 * math.pi / num_bracos)
            
            for i in range(projeteis_por_braco):
                distancia = 30 + i * 20
                angulo = angulo_base + (i * 0.2)
                
                alvo_x = self.pos[0] + math.cos(angulo) * distancia
                alvo_y = self.pos[1] + math.sin(angulo) * distancia
                
                cor = (255, int(255 * (i / projeteis_por_braco)), 0)
                
                projeteis.append(ProjetilBoss(self.pos[0], self.pos[1],
                                            alvo_x, alvo_y,
                                            self.dano_projeteis, 3, cor))
        return projeteis

    def ataque_tiro_simples(self, jogador_pos):
        """Tiro simples direto"""
        projeteis = []
        dx = jogador_pos[0] - self.pos[0]
        dy = jogador_pos[1] - self.pos[1]
        projeteis.append(ProjetilBoss(self.pos[0], self.pos[1], 
                                     jogador_pos[0], jogador_pos[1], 
                                     self.dano_projeteis, 5, (255, 0, 0)))
        return projeteis

    def ataque_tiro_duplo(self, jogador_pos):
        """Dois tiros com pequeno spread"""
        projeteis = []
        dx = jogador_pos[0] - self.pos[0]
        dy = jogador_pos[1] - self.pos[1]
        
        
        angulo_base = math.atan2(dy, dx)
        
        
        for i in [-1, 1]:
            angulo = angulo_base + i * math.pi/12  
            alvo_x = self.pos[0] + math.cos(angulo) * 100
            alvo_y = self.pos[1] + math.sin(angulo) * 100
            projeteis.append(ProjetilBoss(self.pos[0], self.pos[1], 
                                         alvo_x, alvo_y, 
                                         self.dano_projeteis, 4, (255, 100, 0)))
        return projeteis

    def ataque_tiro_triplo(self, jogador_pos):
        """Três tiros em spread"""
        projeteis = []
        dx = jogador_pos[0] - self.pos[0]
        dy = jogador_pos[1] - self.pos[1]
        
        angulo_base = math.atan2(dy, dx)
        
        
        for i in [-1, 0, 1]:
            angulo = angulo_base + i * math.pi/9  
            alvo_x = self.pos[0] + math.cos(angulo) * 100
            alvo_y = self.pos[1] + math.sin(angulo) * 100
            projeteis.append(ProjetilBoss(self.pos[0], self.pos[1], 
                                         alvo_x, alvo_y, 
                                         self.dano_projeteis, 4, (255, 150, 0)))
        return projeteis

    def ataque_tiro_cruzado(self, jogador_pos):
        """Quatro tiros em cruz"""
        projeteis = []
        angulos = [0, math.pi/2, math.pi, 3*math.pi/2]
        
        for angulo in angulos:
            alvo_x = self.pos[0] + math.cos(angulo) * 100
            alvo_y = self.pos[1] + math.sin(angulo) * 100
            projeteis.append(ProjetilBoss(self.pos[0], self.pos[1], 
                                         alvo_x, alvo_y, 
                                         self.dano_projeteis, 3, (255, 0, 255)))
        return projeteis

    def ataque_tiro_circular(self):
        """Oito tiros em círculo"""
        projeteis = []
        for i in range(8):
            angulo = i * math.pi/4
            alvo_x = self.pos[0] + math.cos(angulo) * 100
            alvo_y = self.pos[1] + math.sin(angulo) * 100
            projeteis.append(ProjetilBoss(self.pos[0], self.pos[1], 
                                         alvo_x, alvo_y, 
                                         self.dano_projeteis, 3, (255, 255, 0)))
        return projeteis

    def ataque_bullet_hell_1(self, jogador_pos):
        """Bullet hell estilo espiral"""
        projeteis = []
        for i in range(12):
            angulo = i * math.pi/6 + pygame.time.get_ticks() * 0.001
            alvo_x = self.pos[0] + math.cos(angulo) * 80
            alvo_y = self.pos[1] + math.sin(angulo) * 80
            projeteis.append(ProjetilBoss(self.pos[0], self.pos[1], 
                                         alvo_x, alvo_y, 
                                         self.dano_projeteis, 2, (0, 255, 255)))
        return projeteis

    def ataque_bullet_hell_2(self, jogador_pos):
        """Bullet hell estilo ondas"""
        projeteis = []
        tempo = pygame.time.get_ticks() * 0.002
        for i in range(16):
            angulo = i * math.pi/8 + math.sin(tempo) * 0.5
            alvo_x = self.pos[0] + math.cos(angulo) * 90
            alvo_y = self.pos[1] + math.sin(angulo) * 90
            projeteis.append(ProjetilBoss(self.pos[0], self.pos[1], 
                                         alvo_x, alvo_y, 
                                         self.dano_projeteis, 2.5, (255, 0, 255)))
        return projeteis

    def ataque_dash(self, jogador_pos):
        """Dash em direção ao jogador"""
        dx = jogador_pos[0] - self.pos[0]
        dy = jogador_pos[1] - self.pos[1]
        distancia = math.sqrt(dx*dx + dy*dy)
        
        if distancia > 0:
            self.dash_direcao = [dx/distancia, dy/distancia]
            self.dash_ativo = True
            self.dash_tempo = pygame.time.get_ticks()

    def ataque_tiros_queda(self, jogador_pos, tempo_atual):
        """Tiros que caem do céu com indicadores"""
        
        for _ in range(5):
            x = jogador_pos[0] + random.randint(-100, 100)
            y = jogador_pos[1] + random.randint(-100, 100)
            
            
            x = max(50, min(LARGURA_MAPA - 50, x))
            y = max(50, min(ALTURA_MAPA - 50, y))
            
            
            indicador = IndicadorAtaque(x, y, tempo_atual, tempo_atual + 1500)
            self.indicadores.append(indicador)

    def receber_dano(self, dano, fonte="normal"):
        """Processa dano recebido
        fonte: tipo de dano ('normal' para dano único, 'continuo' para dano ao longo do tempo)
        Retorna True se o boss morreu, False caso contrário"""
        if not self.invulneravel:
            tempo_atual = pygame.time.get_ticks()
            
            
            if fonte == "continuo":
                if tempo_atual - self.tempo_ultimo_dano < self.cooldown_dano:
                    return False
            
            self.hp -= dano
            self.tempo_ultimo_dano = tempo_atual
            
            if self.hp <= 0:
                self.ativo = False
                print("💀 BOSS DERROTADO! 💀")
                return True  
        
        return False  

    def colidir_com_jogador(self, jogador):
        """Processa colisão com o jogador"""
        if not self.ativo or self.invulneravel or self.dash_ativo:
            return False
        
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < self.raio + jogador.raio:
            return jogador.receber_dano(self.dano)
        return False

    def desenhar(self, tela, camera):
        """Desenha o boss e seus efeitos"""
        if not self.ativo:
            return
        
        
        pos_tela = [self.pos[0] - camera[0], self.pos[1] - camera[1]]
        
        
        if self.fase == 3:
            cor = (255, 0, 0)  
        elif self.fase == 2:
            cor = (255, 165, 0)  
        else:
            cor = (128, 0, 128)  
        
        
        if self.em_descanso:
            cor = (100, 100, 100)  
        
        
        if self.dash_ativo:
            cor = (255, 255, 0)  
        
        pygame.draw.circle(tela, cor, (int(pos_tela[0]), int(pos_tela[1])), self.raio)
        
        
        largura_barra = 80
        altura_barra = 8
        x_barra = pos_tela[0] - largura_barra // 2
        y_barra = pos_tela[1] - self.raio - 20
        
        
        pygame.draw.rect(tela, (100, 0, 0), 
                        (x_barra, y_barra, largura_barra, altura_barra))
        
        
        vida_largura = int(largura_barra * (self.hp / self.hp_max))
        if vida_largura > 0:
            pygame.draw.rect(tela, (0, 255, 0),
                           (x_barra, y_barra, vida_largura, altura_barra))
        
        
        for indicador in self.indicadores:
            indicador.desenhar(tela, camera) 