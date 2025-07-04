# Boss fight implementation will go here 

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
        self.velocidade = velocidade * 0.7  # Reduzir velocidade geral em 30%
        self.cor = cor
        self.tipo = tipo
        self.ativo = True
        self.raio = 8 if tipo in ["basico", "laser"] else 12
        
        # Calcular direção
        dx = alvo_x - x
        dy = alvo_y - y
        if dx != 0 or dy != 0:
            self.direcao = normalizar_vetor(dx, dy)
        else:
            self.direcao = (1, 0)
        
        # Tempo de vida (alguns projéteis desaparecem com o tempo)
        self.tempo_vida = 8000  # 8 segundos padrão
        self.tempo_criacao = pygame.time.get_ticks()

    def atualizar(self):
        """Atualiza posição e estado do projétil"""
        if not self.ativo:
            return
        
        # Verificar tempo de vida
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_criacao > self.tempo_vida:
            self.ativo = False
            return
        
        # Movimento normal
        self.pos[0] += self.direcao[0] * self.velocidade
        self.pos[1] += self.direcao[1] * self.velocidade
        
        # Verificar limites do mapa - projéteis do boss podem sair um pouco do mapa
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
        
        # Posição na tela (considerando a câmera)
        pos_tela = (
            int(self.pos[0] - camera[0]),
            int(self.pos[1] - camera[1])
        )
        
        # Desenho padrão
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
            # Círculo pulsante vermelho
            tempo_atual = pygame.time.get_ticks()
            tempo_restante = self.tempo_queda - tempo_atual
            intensidade = int(255 * (tempo_restante / 1500))  # 1.5 segundos
            
            cor = (intensidade, 0, 0)
            pygame.draw.circle(tela, cor, (int(pos_tela[0]), int(pos_tela[1])), self.raio, 3)
            pygame.draw.circle(tela, (255, 0, 0), (int(pos_tela[0]), int(pos_tela[1])), self.raio//2)

class Boss:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.raio = 30
        self.hp_max = 375000  # Reduzido em 25% (era 500000)
        self.hp = self.hp_max
        self.dano = 15
        self.ativo = True
        self.invulneravel = False
        self.fase = 1
        self.hp_fase2 = self.hp_max * 0.66  # 66% do HP
        self.hp_fase3 = self.hp_max * 0.33  # 33% do HP
        
        # Movimento
        self.velocidade = 2.5  # Velocidade base do boss
        self.direcao = [0, 0]  # Direção atual
        self.tempo_mudanca_direcao = 0
        self.intervalo_mudanca_direcao = 2000  # Muda direção a cada 2 segundos
        self.distancia_minima_jogador = 200  # Distância mínima que o boss mantém do jogador
        
        # Sistema de ataques
        self.ataque_atual = None
        self.tempo_ultimo_ataque = 0
        self.tempo_pensamento = 0
        self.intervalo_pensamento = 3000  # 3 segundos
        self.contador_ataques = 0
        self.max_ataques_antes_descanso = 4
        self.tempo_descanso = 0
        self.duracao_descanso = 1500  # 1.5 segundos
        self.em_descanso = False
        
        # Ataques da fase 1
        self.ataques_fase1 = ["tiro_simples", "tiro_duplo", "tiro_triplo", "tiro_cruzado", "tiro_circular"]
        
        # Ataques da fase 2
        self.ataques_fase2 = self.ataques_fase1 + ["bullet_hell_1", "bullet_hell_2"]
        
        # Ataques da fase 3
        self.ataques_fase3 = self.ataques_fase2 + ["dash_ataque", "tiros_queda"]
        
        # Indicadores de ataques
        self.indicadores = []
        
        # Estado do dash
        self.dash_ativo = False
        self.dash_direcao = [0, 0]
        self.dash_tempo = 0
        self.duracao_dash = 500  # 0.5 segundos

    def atualizar(self, jogador_pos):
        """Atualiza estado do boss"""
        if not self.ativo:
            return []
        
        tempo_atual = pygame.time.get_ticks()
        
        # Verificar mudança de fase
        self.verificar_mudanca_fase()
        
        # Atualizar movimento
        if not self.dash_ativo:
            self.atualizar_movimento(jogador_pos, tempo_atual)
        
        # Atualizar dash se ativo
        if self.dash_ativo:
            self.atualizar_dash(tempo_atual)
        
        # Atualizar indicadores
        self.atualizar_indicadores()
        
        # Sistema de ataques
        projeteis = self.atualizar_ataques(jogador_pos, tempo_atual)
        
        return projeteis

    def verificar_mudanca_fase(self):
        """Verifica se deve mudar de fase"""
        if self.hp <= self.hp_fase3 and self.fase < 3:
            self.fase = 3
            print("BOSS: Fase 3 ativada!")
        elif self.hp <= self.hp_fase2 and self.fase < 2:
            self.fase = 2
            print("BOSS: Fase 2 ativada!")

    def atualizar_movimento(self, jogador_pos, tempo_atual):
        """Atualiza o movimento do boss"""
        # Calcular distância até o jogador
        dx = jogador_pos[0] - self.pos[0]
        dy = jogador_pos[1] - self.pos[1]
        distancia = math.sqrt(dx * dx + dy * dy)
        
        # Mudar direção periodicamente ou quando muito perto do jogador
        if (tempo_atual - self.tempo_mudanca_direcao > self.intervalo_mudanca_direcao or 
            distancia < self.distancia_minima_jogador):
            
            if distancia < self.distancia_minima_jogador:
                # Se muito perto do jogador, mover-se para longe
                self.direcao = [-dx/distancia, -dy/distancia]
            else:
                # Movimento semi-aleatório, mas tendendo a se aproximar do jogador
                angulo_base = math.atan2(dy, dx)
                angulo_variacao = random.uniform(-math.pi/4, math.pi/4)  # ±45 graus
                angulo_final = angulo_base + angulo_variacao
                
                self.direcao = [
                    math.cos(angulo_final),
                    math.sin(angulo_final)
                ]
            
            self.tempo_mudanca_direcao = tempo_atual
        
        # Aplicar movimento
        self.pos[0] += self.direcao[0] * self.velocidade
        self.pos[1] += self.direcao[1] * self.velocidade
        
        # Manter dentro dos limites do mapa
        self.pos[0] = max(self.raio, min(LARGURA_MAPA - self.raio, self.pos[0]))
        self.pos[1] = max(self.raio, min(ALTURA_MAPA - self.raio, self.pos[1]))

    def atualizar_dash(self, tempo_atual):
        """Atualiza o dash do boss"""
        if tempo_atual - self.dash_tempo > self.duracao_dash:
            self.dash_ativo = False
        else:
            # Aplicar movimento do dash
            self.pos[0] += self.dash_direcao[0] * self.velocidade * 3
            self.pos[1] += self.dash_direcao[1] * self.velocidade * 3
            
            # Manter dentro dos limites
            self.pos[0] = max(self.raio, min(LARGURA_MAPA - self.raio, self.pos[0]))
            self.pos[1] = max(self.raio, min(ALTURA_MAPA - self.raio, self.pos[1]))

    def atualizar_indicadores(self):
        """Atualiza os indicadores de ataques"""
        for indicador in self.indicadores[:]:
            indicador.atualizar()
            if not indicador.ativo:
                self.indicadores.remove(indicador)

    def atualizar_ataques(self, jogador_pos, tempo_atual):
        """Atualiza o sistema de ataques do boss"""
        projeteis = []
        
        # Se está em descanso
        if self.em_descanso:
            if tempo_atual - self.tempo_descanso > self.duracao_descanso:
                self.em_descanso = False
                self.contador_ataques = 0
            return projeteis
        
        # Se não há ataque atual, pensar no próximo
        if not self.ataque_atual:
            if tempo_atual - self.tempo_pensamento > self.intervalo_pensamento:
                self.escolher_proximo_ataque()
                self.tempo_pensamento = tempo_atual
            return projeteis
        
        # Executar ataque atual
        projeteis = self.executar_ataque(jogador_pos, tempo_atual)
        
        return projeteis

    def escolher_proximo_ataque(self):
        """Escolhe o próximo ataque baseado na fase"""
        if self.fase == 1:
            ataques_disponiveis = self.ataques_fase1
        elif self.fase == 2:
            ataques_disponiveis = self.ataques_fase2
        else:
            ataques_disponiveis = self.ataques_fase3
        
        # Escolher 1 ou 2 ataques simultâneos
        num_ataques = random.choice([1, 2])
        self.ataque_atual = random.sample(ataques_disponiveis, min(num_ataques, len(ataques_disponiveis)))

    def executar_ataque(self, jogador_pos, tempo_atual):
        """Executa o ataque atual"""
        projeteis = []
        
        if self.ataque_atual is None:
            return projeteis
        
        for ataque in self.ataque_atual:
            if ataque == "tiro_simples":
                projeteis.extend(self.ataque_tiro_simples(jogador_pos))
            elif ataque == "tiro_duplo":
                projeteis.extend(self.ataque_tiro_duplo(jogador_pos))
            elif ataque == "tiro_triplo":
                projeteis.extend(self.ataque_tiro_triplo(jogador_pos))
            elif ataque == "tiro_cruzado":
                projeteis.extend(self.ataque_tiro_cruzado(jogador_pos))
            elif ataque == "tiro_circular":
                projeteis.extend(self.ataque_tiro_circular())
            elif ataque == "bullet_hell_1":
                projeteis.extend(self.ataque_bullet_hell_1(jogador_pos))
            elif ataque == "bullet_hell_2":
                projeteis.extend(self.ataque_bullet_hell_2(jogador_pos))
            elif ataque == "dash_ataque":
                self.ataque_dash(jogador_pos)
            elif ataque == "tiros_queda":
                self.ataque_tiros_queda(jogador_pos, tempo_atual)
        
        # Finalizar ataque
        self.contador_ataques += 1
        if self.contador_ataques >= self.max_ataques_antes_descanso:
            self.em_descanso = True
            self.tempo_descanso = tempo_atual
        
        self.ataque_atual = None
        return projeteis

    def ataque_tiro_simples(self, jogador_pos):
        """Tiro simples direto"""
        projeteis = []
        dx = jogador_pos[0] - self.pos[0]
        dy = jogador_pos[1] - self.pos[1]
        projeteis.append(ProjetilBoss(self.pos[0], self.pos[1], 
                                     jogador_pos[0], jogador_pos[1], 
                                     10, 5, (255, 0, 0)))
        return projeteis

    def ataque_tiro_duplo(self, jogador_pos):
        """Dois tiros com pequeno spread"""
        projeteis = []
        dx = jogador_pos[0] - self.pos[0]
        dy = jogador_pos[1] - self.pos[1]
        
        # Calcular ângulo base
        angulo_base = math.atan2(dy, dx)
        
        # Dois tiros com spread de 15 graus
        for i in [-1, 1]:
            angulo = angulo_base + i * math.pi/12  # 15 graus
            alvo_x = self.pos[0] + math.cos(angulo) * 100
            alvo_y = self.pos[1] + math.sin(angulo) * 100
            projeteis.append(ProjetilBoss(self.pos[0], self.pos[1], 
                                         alvo_x, alvo_y, 
                                         8, 4, (255, 100, 0)))
        return projeteis

    def ataque_tiro_triplo(self, jogador_pos):
        """Três tiros em spread"""
        projeteis = []
        dx = jogador_pos[0] - self.pos[0]
        dy = jogador_pos[1] - self.pos[1]
        
        angulo_base = math.atan2(dy, dx)
        
        # Três tiros com spread de 20 graus
        for i in [-1, 0, 1]:
            angulo = angulo_base + i * math.pi/9  # 20 graus
            alvo_x = self.pos[0] + math.cos(angulo) * 100
            alvo_y = self.pos[1] + math.sin(angulo) * 100
            projeteis.append(ProjetilBoss(self.pos[0], self.pos[1], 
                                         alvo_x, alvo_y, 
                                         6, 4, (255, 150, 0)))
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
                                         7, 3, (255, 0, 255)))
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
                                         5, 3, (255, 255, 0)))
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
                                         4, 2, (0, 255, 255)))
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
                                         3, 2.5, (255, 0, 255)))
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
        # Criar 5 indicadores aleatórios
        for _ in range(5):
            x = jogador_pos[0] + random.randint(-100, 100)
            y = jogador_pos[1] + random.randint(-100, 100)
            
            # Limitar ao mapa
            x = max(50, min(LARGURA_MAPA - 50, x))
            y = max(50, min(ALTURA_MAPA - 50, y))
            
            # Criar indicador que dura 1.5 segundos
            indicador = IndicadorAtaque(x, y, tempo_atual, tempo_atual + 1500)
            self.indicadores.append(indicador)

    def receber_dano(self, dano):
        """Processa dano recebido"""
        if not self.invulneravel:
            self.hp -= dano
            if self.hp <= 0:
                self.ativo = False

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
        
        # Posição na tela
        pos_tela = [self.pos[0] - camera[0], self.pos[1] - camera[1]]
        
        # Cor baseada na fase
        if self.fase == 3:
            cor = (255, 0, 0)  # Vermelho
        elif self.fase == 2:
            cor = (255, 165, 0)  # Amarelo
        else:
            cor = (128, 0, 128)  # Roxo
        
        # Efeito de descanso
        if self.em_descanso:
            cor = (100, 100, 100)  # Cinza
        
        # Efeito de dash
        if self.dash_ativo:
            cor = (255, 255, 0)  # Amarelo brilhante
        
        pygame.draw.circle(tela, cor, (int(pos_tela[0]), int(pos_tela[1])), self.raio)
        
        # Barra de vida
        largura_barra = 80
        altura_barra = 8
        x_barra = pos_tela[0] - largura_barra // 2
        y_barra = pos_tela[1] - self.raio - 20
        
        # Fundo da barra
        pygame.draw.rect(tela, (100, 0, 0), 
                        (x_barra, y_barra, largura_barra, altura_barra))
        
        # Vida atual
        vida_largura = int(largura_barra * (self.hp / self.hp_max))
        if vida_largura > 0:
            pygame.draw.rect(tela, (0, 255, 0),
                           (x_barra, y_barra, vida_largura, altura_barra))
        
        # Desenhar indicadores
        for indicador in self.indicadores:
            indicador.desenhar(tela, camera) 