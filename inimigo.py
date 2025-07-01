import pygame
import math
import random
from config import *
from utils import *
from projetil import XP

class Inimigo:
    def __init__(self, x, y, tipo="normal"):
        self.pos = [x, y]
        self.tipo = tipo
        self.ativo = True
        self.ultimo_ataque = 0
        
        # Configurar estatísticas por tipo
        if tipo == "tanque":
            self.raio = INIMIGO_TANQUE_RAIO
            self.hp_max = 8
            self.velocidade = 1.5
            self.dano = 3
            self.cor = CINZA
            self.intervalo_ataque = 800
            self.xp_drop = 3
            self.pode_atirar = True
            self.alcance_tiro = 250
            self.intervalo_tiro = 2000  # 2 segundos
        elif tipo == "rapido":
            self.raio = INIMIGO_RAPIDO_RAIO
            self.hp_max = 2
            self.velocidade = 4
            self.dano = 1
            self.cor = LARANJA
            self.intervalo_ataque = 400
            self.xp_drop = 1
            self.pode_atirar = False  # Rápido é corpo a corpo
            self.alcance_tiro = 0
            self.intervalo_tiro = 0
        else:  # normal
            self.raio = INIMIGO_NORMAL_RAIO
            self.hp_max = 4
            self.velocidade = 2.5
            self.dano = 2
            self.cor = VERMELHO
            self.intervalo_ataque = 600
            self.xp_drop = 2
            self.pode_atirar = True
            self.alcance_tiro = 200
            self.intervalo_tiro = 1500  # 1.5 segundos
        
        self.hp = self.hp_max
        self.ultimo_tiro = 0
    
    def atualizar(self, jogador_pos):
        if not self.ativo:
            return []
        
        # Mover em direção ao jogador
        dx = jogador_pos[0] - self.pos[0]
        dy = jogador_pos[1] - self.pos[1]
        
        if dx != 0 or dy != 0:
            dir_x, dir_y = normalizar_vetor(dx, dy)
            self.pos[0] += dir_x * self.velocidade
            self.pos[1] += dir_y * self.velocidade
        
        # Limitar posição ao mapa
        self.pos = list(limitar_posicao(self.pos))
        
        # Verificar se pode atirar
        novos_projeteis = []
        if self.pode_atirar and self.pode_atirar_jogador(jogador_pos):
            projetil = self.atirar(jogador_pos)
            if projetil:
                novos_projeteis.append(projetil)
        
        return novos_projeteis
    
    def pode_atirar_jogador(self, jogador_pos):
        """Verifica se pode atirar no jogador"""
        if not self.pode_atirar:
            return False
        
        # Verificar cooldown
        if pygame.time.get_ticks() - self.ultimo_tiro < self.intervalo_tiro:
            return False
        
        # Verificar distância
        distancia = calcular_distancia(self.pos, jogador_pos)
        return distancia <= self.alcance_tiro
    
    def atirar(self, jogador_pos):
        """Cria um projétil direcionado ao jogador"""
        self.ultimo_tiro = pygame.time.get_ticks()
        return ProjetilInimigo(self.pos[0], self.pos[1], jogador_pos[0], jogador_pos[1], self.dano)
    
    def pode_atacar(self):
        return pygame.time.get_ticks() - self.ultimo_ataque > self.intervalo_ataque
    
    def atacar_jogador(self, jogador):
        if not self.pode_atacar():
            return False
        
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < self.raio + jogador.raio + 10:  # Alcance de ataque
            if jogador.receber_dano(self.dano):
                self.ultimo_ataque = pygame.time.get_ticks()
                return True
        
        return False
    
    def receber_dano(self, dano):
        self.hp -= dano
        if self.hp <= 0:
            self.morrer()
    
    def morrer(self):
        self.ativo = False
        return XP(self.pos[0], self.pos[1], self.xp_drop)
    
    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        
        pos_tela = posicao_na_tela(self.pos, camera)
        
        if esta_na_tela(self.pos, camera):
            pygame.draw.circle(tela, self.cor, (int(pos_tela[0]), int(pos_tela[1])), self.raio)
            
            # Desenhar borda mais escura
            pygame.draw.circle(tela, PRETO, (int(pos_tela[0]), int(pos_tela[1])), self.raio, 2)
            
            # Desenhar barra de vida se ferido
            if self.hp < self.hp_max:
                desenhar_barra_vida(tela, pos_tela, self.hp, self.hp_max)

def gerar_inimigo_aleatorio(jogador_pos, tempo_jogo):
    """Gera um inimigo aleatório - sistema melhorado com novos tipos"""
    # Calcular multiplicadores baseados no tempo - mais equilibrados
    mult_hp = 1 + (tempo_jogo / 180)  # +100% HP a cada 3 minutos (era 2)
    mult_dano = 1 + (tempo_jogo / 240)  # +100% dano a cada 4 minutos (era 3)
    mult_xp = 1 + (tempo_jogo / 150)    # +100% XP a cada 2.5 minutos (era 1)
    mult_velocidade = 1 + (tempo_jogo / 300)  # +100% velocidade a cada 5 minutos
    
    # Probabilidades dos tipos baseadas no tempo
    if tempo_jogo < 120:  # Primeiros 2 minutos - só básicos
        tipos_disponiveis = ["basico"]
        pesos = [1.0]
    elif tempo_jogo < 240:  # 2-4 minutos - adicionar voadores
        tipos_disponiveis = ["basico", "voador"]
        pesos = [0.7, 0.3]
    elif tempo_jogo < 360:  # 4-6 minutos - adicionar tanques
        tipos_disponiveis = ["basico", "voador", "tanque"]
        pesos = [0.5, 0.3, 0.2]
    elif tempo_jogo < 480:  # 6-8 minutos - adicionar velozes
        tipos_disponiveis = ["basico", "voador", "tanque", "veloz"]
        pesos = [0.4, 0.25, 0.2, 0.15]
    elif tempo_jogo < 600:  # 8-10 minutos - mais tanques
        tipos_disponiveis = ["basico", "voador", "tanque", "veloz"]
        pesos = [0.3, 0.25, 0.3, 0.15]
    else:  # 10+ minutos - distribuição equilibrada
        tipos_disponiveis = ["basico", "voador", "tanque", "veloz"]
        pesos = [0.25, 0.25, 0.25, 0.25]
    
    # Selecionar tipo
    tipo = random.choices(tipos_disponiveis, weights=pesos)[0]
    
    # Posição de spawn
    angulo = random.uniform(0, 2 * math.pi)
    distancia = random.uniform(300, 500)
    x = jogador_pos[0] + math.cos(angulo) * distancia
    y = jogador_pos[1] + math.sin(angulo) * distancia
    
    # Garantir que está dentro dos limites do mapa
    x = max(50, min(LARGURA_MAPA - 50, x))
    y = max(50, min(ALTURA_MAPA - 50, y))
    
    # Criar inimigo baseado no tipo
    if tipo == "voador":
        inimigo = InimigoVoador(x, y)
    elif tipo == "tanque":
        inimigo = InimigoTanque(x, y)
    elif tipo == "veloz":
        inimigo = InimigoVeloz(x, y)
    else:  # básico
        inimigo = Inimigo(x, y)
    
    # Aplicar multiplicadores
    inimigo.hp = int(inimigo.hp * mult_hp)
    inimigo.hp_max = int(inimigo.hp_max * mult_hp)
    inimigo.dano = int(inimigo.dano * mult_dano)
    inimigo.xp_drop = int(inimigo.xp_drop * mult_xp)
    
    # Velocidade apenas para alguns tipos
    if hasattr(inimigo, 'velocidade') and tipo in ["basico", "veloz"]:
        inimigo.velocidade *= mult_velocidade
    
    return inimigo

class ProjetilInimigo:
    def __init__(self, x, y, alvo_x, alvo_y, dano, velocidade=4):
        self.pos = [x, y]
        self.pos_inicial = [x, y]
        self.raio = 4
        self.dano = dano
        self.velocidade = velocidade
        self.alcance = 400
        
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
    
    def colidir_com_jogador(self, jogador):
        if not self.ativo:
            return False
        
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < self.raio + jogador.raio:
            jogador.receber_dano(self.dano)
            self.ativo = False
            return True
        
        return False
    
    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        
        pos_tela = posicao_na_tela(self.pos, camera)
        
        if esta_na_tela(self.pos, camera):
            pygame.draw.circle(tela, ROXO, (int(pos_tela[0]), int(pos_tela[1])), self.raio)

class InimigoVoador:
    """Inimigo voador que ataca de longe"""
    def __init__(self, x, y):
        self.pos = [x, y]
        self.hp = 20
        self.hp_max = 20
        self.dano = 1
        self.velocidade = 1.8
        self.raio = 15
        self.xp_drop = 8
        self.tipo = "voador"
        self.ativo = True
        
        # Comportamento específico
        self.tempo_ultimo_tiro = 0
        self.cooldown_tiro = 2500  # 2.5 segundos
        self.distancia_ataque = 180
        self.altura_voo = random.uniform(0.7, 1.2)
        self.animacao = random.randint(0, 100)
        
        # Ataque corpo a corpo
        self.ultimo_ataque = 0
        self.intervalo_ataque = 1000  # 1 segundo
        
    def atualizar(self, jogador_pos):
        if not self.ativo:
            return None
        
        self.animacao += 1
        
        # Movimento circular ao redor do jogador mantendo distância
        dx = self.pos[0] - jogador_pos[0]
        dy = self.pos[1] - jogador_pos[1]
        distancia = math.sqrt(dx*dx + dy*dy)
        
        if distancia < self.distancia_ataque - 30:
            # Muito próximo, afastar-se
            if distancia > 0:
                self.pos[0] += (dx / distancia) * self.velocidade * 1.5
                self.pos[1] += (dy / distancia) * self.velocidade * 1.5
        elif distancia > self.distancia_ataque + 30:
            # Muito longe, aproximar-se
            if distancia > 0:
                self.pos[0] -= (dx / distancia) * self.velocidade
                self.pos[1] -= (dy / distancia) * self.velocidade
        else:
            # Movimento orbital
            angulo = math.atan2(dy, dx) + 0.02
            self.pos[0] = jogador_pos[0] + math.cos(angulo) * self.distancia_ataque
            self.pos[1] = jogador_pos[1] + math.sin(angulo) * self.distancia_ataque
        
        # Atirar se possível
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_ultimo_tiro > self.cooldown_tiro:
            if distancia < self.distancia_ataque + 50:
                self.tempo_ultimo_tiro = tempo_atual
                return self.criar_projetil(jogador_pos)
        
        return None
    
    def criar_projetil(self, jogador_pos):
        from projetil import ProjetilInimigo
        return ProjetilInimigo(self.pos[0], self.pos[1], jogador_pos[0], jogador_pos[1], self.dano, 4)
    
    def atacar_jogador(self, jogador):
        """Ataque corpo a corpo quando muito próximo"""
        if pygame.time.get_ticks() - self.ultimo_ataque < self.intervalo_ataque:
            return False
        
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < self.raio + jogador.raio + 15:  # Alcance de ataque
            if jogador.receber_dano(self.dano):
                self.ultimo_ataque = pygame.time.get_ticks()
                return True
        
        return False
    
    def receber_dano(self, dano):
        self.hp -= dano
        if self.hp <= 0:
            self.ativo = False
            return True
        return False
    
    def morrer(self):
        """Retorna XP quando morre"""
        self.ativo = False
        return XP(self.pos[0], self.pos[1], self.xp_drop)
    
    def desenhar_barra_vida(self, tela, pos):
        if self.hp < self.hp_max:
            largura = 30
            altura = 4
            x = pos[0] - largura // 2
            y = pos[1] - self.raio - 8
            
            # Fundo da barra
            pygame.draw.rect(tela, (100, 0, 0), (x, y, largura, altura))
            
            # Barra de vida atual
            vida_largura = int((self.hp / self.hp_max) * largura)
            if vida_largura > 0:
                pygame.draw.rect(tela, (0, 255, 0), (x, y, vida_largura, altura))
    
    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        
        pos_tela = posicao_na_tela(self.pos, camera)
        if esta_na_tela(self.pos, camera):
            # Efeito de voo (altura variável)
            offset_y = math.sin(self.animacao * 0.1) * 3 * self.altura_voo
            pos_sombra = (int(pos_tela[0]), int(pos_tela[1] + offset_y + 5))
            pos_corpo = (int(pos_tela[0]), int(pos_tela[1] + offset_y))
            
            # Sombra
            pygame.draw.ellipse(tela, (50, 50, 50), 
                              (pos_sombra[0] - 8, pos_sombra[1] - 3, 16, 6))
            
            # Corpo (azul escuro)
            pygame.draw.circle(tela, (0, 50, 150), pos_corpo, self.raio)
            pygame.draw.circle(tela, (0, 100, 200), pos_corpo, self.raio - 3)
            
            # Asas (animadas)
            asa_offset = math.sin(self.animacao * 0.3) * 8
            # Asa esquerda
            pygame.draw.ellipse(tela, (100, 150, 255),
                              (pos_corpo[0] - 20, pos_corpo[1] - 8 + asa_offset, 15, 8))
            # Asa direita  
            pygame.draw.ellipse(tela, (100, 150, 255),
                              (pos_corpo[0] + 5, pos_corpo[1] - 8 - asa_offset, 15, 8))
            
            # Barra de vida
            self.desenhar_barra_vida(tela, pos_corpo)

class InimigoTanque:
    """Inimigo tanque com muita vida e movimento lento"""
    def __init__(self, x, y):
        self.pos = [x, y]
        self.hp = 80
        self.hp_max = 80
        self.dano = 4
        self.velocidade = 0.8
        self.raio = 25
        self.xp_drop = 15
        self.tipo = "tanque"
        self.ativo = True
        self.armor = 2  # Reduz dano recebido
        
        # Ataque corpo a corpo
        self.ultimo_ataque = 0
        self.intervalo_ataque = 1500  # 1.5 segundos
        
    def atualizar(self, jogador_pos):
        if not self.ativo:
            return None
        
        # Movimento lento mas determinado em direção ao jogador
        dx = jogador_pos[0] - self.pos[0]
        dy = jogador_pos[1] - self.pos[1]
        
        if dx != 0 or dy != 0:
            dir_x, dir_y = normalizar_vetor(dx, dy)
            self.pos[0] += dir_x * self.velocidade
            self.pos[1] += dir_y * self.velocidade
        
        # Limitar posição ao mapa
        self.pos = list(limitar_posicao(self.pos))
        
        return None  # Tanque não atira
    
    def atacar_jogador(self, jogador):
        """Ataque corpo a corpo poderoso"""
        if pygame.time.get_ticks() - self.ultimo_ataque < self.intervalo_ataque:
            return False
        
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < self.raio + jogador.raio + 10:  # Alcance de ataque
            if jogador.receber_dano(self.dano):
                self.ultimo_ataque = pygame.time.get_ticks()
                return True
        
        return False
    
    def receber_dano(self, dano):
        # Aplicar armor
        dano_final = max(1, dano - self.armor)
        self.hp -= dano_final
        if self.hp <= 0:
            self.ativo = False
            return True
        return False
    
    def morrer(self):
        """Retorna XP quando morre"""
        self.ativo = False
        return XP(self.pos[0], self.pos[1], self.xp_drop)
    
    def desenhar_barra_vida(self, tela, pos):
        if self.hp < self.hp_max:
            largura = 40
            altura = 6
            x = pos[0] - largura // 2
            y = pos[1] - self.raio - 10
            
            # Fundo da barra
            pygame.draw.rect(tela, (100, 0, 0), (x, y, largura, altura))
            
            # Barra de vida atual
            vida_largura = int((self.hp / self.hp_max) * largura)
            if vida_largura > 0:
                if self.hp > self.hp_max * 0.5:
                    cor = (0, 255, 0)  # Verde
                elif self.hp > self.hp_max * 0.25:
                    cor = (255, 255, 0)  # Amarelo
                else:
                    cor = (255, 0, 0)  # Vermelho
                pygame.draw.rect(tela, cor, (x, y, vida_largura, altura))
    
    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        
        pos_tela = posicao_na_tela(self.pos, camera)
        if esta_na_tela(self.pos, camera):
            # Corpo principal (cinza metálico escuro)
            pygame.draw.circle(tela, (60, 60, 60), (int(pos_tela[0]), int(pos_tela[1])), self.raio)
            pygame.draw.circle(tela, (80, 80, 80), (int(pos_tela[0]), int(pos_tela[1])), self.raio - 4)
            pygame.draw.circle(tela, (100, 100, 100), (int(pos_tela[0]), int(pos_tela[1])), self.raio - 8)
            
            # Detalhes metálicos
            for i in range(4):
                angulo = i * math.pi / 2
                x_det = int(pos_tela[0] + math.cos(angulo) * (self.raio - 6))
                y_det = int(pos_tela[1] + math.sin(angulo) * (self.raio - 6))
                pygame.draw.circle(tela, (120, 120, 120), (x_det, y_det), 3)
            
            # Borda escura
            pygame.draw.circle(tela, (30, 30, 30), (int(pos_tela[0]), int(pos_tela[1])), self.raio, 3)
            
            # Barra de vida
            self.desenhar_barra_vida(tela, pos_tela)

class InimigoVeloz:
    """Inimigo rápido com movimento errático"""
    def __init__(self, x, y):
        self.pos = [x, y]
        self.hp = 8
        self.hp_max = 8
        self.dano = 2
        self.velocidade = 4.5
        self.raio = 12
        self.xp_drop = 4
        self.tipo = "veloz"
        self.ativo = True
        
        # Movimento em zigzag
        self.tempo_mudanca = 0
        self.direcao_atual = random.uniform(0, 2 * math.pi)
        self.contador_zigzag = 0
        
        # Ataque corpo a corpo
        self.ultimo_ataque = 0
        self.intervalo_ataque = 800  # 0.8 segundos
        
    def atualizar(self, jogador_pos):
        if not self.ativo:
            return None
        
        self.contador_zigzag += 1
        
        # Movimento em zigzag em direção ao jogador
        dx_jogador = jogador_pos[0] - self.pos[0]
        dy_jogador = jogador_pos[1] - self.pos[1]
        
        # Normalizar direção ao jogador
        if dx_jogador != 0 or dy_jogador != 0:
            dist_jogador = math.sqrt(dx_jogador*dx_jogador + dy_jogador*dy_jogador)
            dir_jogador_x = dx_jogador / dist_jogador
            dir_jogador_y = dy_jogador / dist_jogador
        else:
            dir_jogador_x, dir_jogador_y = 0, 0
        
        # Aplicar movimento em zigzag
        if self.contador_zigzag % 30 == 0:  # Mudar direção a cada 0.5s
            self.direcao_atual += random.uniform(-math.pi/3, math.pi/3)
        
        # Combinar direção ao jogador com zigzag
        zigzag_x = math.cos(self.direcao_atual) * 0.3
        zigzag_y = math.sin(self.direcao_atual) * 0.3
        
        movimento_x = (dir_jogador_x * 0.7 + zigzag_x)
        movimento_y = (dir_jogador_y * 0.7 + zigzag_y)
        
        self.pos[0] += movimento_x * self.velocidade
        self.pos[1] += movimento_y * self.velocidade
        
        # Limitar posição ao mapa
        self.pos = list(limitar_posicao(self.pos))
        
        return None  # Veloz não atira
    
    def atacar_jogador(self, jogador):
        """Ataque corpo a corpo rápido"""
        if pygame.time.get_ticks() - self.ultimo_ataque < self.intervalo_ataque:
            return False
        
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < self.raio + jogador.raio + 8:  # Alcance de ataque
            if jogador.receber_dano(self.dano):
                self.ultimo_ataque = pygame.time.get_ticks()
                return True
        
        return False
    
    def receber_dano(self, dano):
        self.hp -= dano
        if self.hp <= 0:
            self.ativo = False
            return True
        return False
    
    def morrer(self):
        """Retorna XP quando morre"""
        self.ativo = False
        return XP(self.pos[0], self.pos[1], self.xp_drop)
    
    def desenhar_barra_vida(self, tela, pos):
        if self.hp < self.hp_max:
            largura = 25
            altura = 3
            x = pos[0] - largura // 2
            y = pos[1] - self.raio - 6
            
            # Fundo da barra
            pygame.draw.rect(tela, (100, 0, 0), (x, y, largura, altura))
            
            # Barra de vida atual
            vida_largura = int((self.hp / self.hp_max) * largura)
            if vida_largura > 0:
                pygame.draw.rect(tela, (0, 255, 0), (x, y, vida_largura, altura))
    
    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        
        pos_tela = posicao_na_tela(self.pos, camera)
        if esta_na_tela(self.pos, camera):
            # Rastro de velocidade
            for i in range(3):
                alpha = 0.3 - (i * 0.1)
                offset = i * 4
                rastro_x = int(pos_tela[0] - math.cos(self.direcao_atual) * offset)
                rastro_y = int(pos_tela[1] - math.sin(self.direcao_atual) * offset)
                rastro_raio = max(1, self.raio - i * 3)
                
                # Cor do rastro (amarelo desbotado)
                cor_rastro = tuple(max(0, int(c * alpha)) for c in (255, 255, 100))
                if sum(cor_rastro) > 0:
                    pygame.draw.circle(tela, cor_rastro, (rastro_x, rastro_y), rastro_raio)
            
            # Corpo principal (amarelo brilhante)
            pygame.draw.circle(tela, (255, 255, 0), (int(pos_tela[0]), int(pos_tela[1])), self.raio)
            pygame.draw.circle(tela, (255, 255, 150), (int(pos_tela[0]), int(pos_tela[1])), self.raio - 3)
            
            # Borda escura
            pygame.draw.circle(tela, (200, 200, 0), (int(pos_tela[0]), int(pos_tela[1])), self.raio, 2)
            
            # Barra de vida
            self.desenhar_barra_vida(tela, pos_tela) 