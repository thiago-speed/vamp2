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
            self.intervalo_tiro = 2000
        elif tipo == "rapido":
            self.raio = INIMIGO_RAPIDO_RAIO
            self.hp_max = 2
            self.velocidade = 4
            self.dano = 1
            self.cor = LARANJA
            self.intervalo_ataque = 400
            self.xp_drop = 1
            self.pode_atirar = False
            self.alcance_tiro = 0
            self.intervalo_tiro = 0
        else:
            self.raio = INIMIGO_NORMAL_RAIO
            self.hp_max = 4
            self.velocidade = 2.5
            self.dano = 2
            self.cor = VERMELHO
            self.intervalo_ataque = 600
            self.xp_drop = 2
            self.pode_atirar = True
            self.alcance_tiro = 200
            self.intervalo_tiro = 1500
            
        self.hp = self.hp_max
        self.ultimo_tiro = 0

    def atualizar(self, jogador_pos):
        if not self.ativo:
            return []
            
        dx = jogador_pos[0] - self.pos[0]
        dy = jogador_pos[1] - self.pos[1]
        
        if dx != 0 or dy != 0:
            dir_x, dir_y = normalizar_vetor(dx, dy)
            nova_x = self.pos[0] + dir_x * self.velocidade
            nova_y = self.pos[1] + dir_y * self.velocidade
            self.pos = [nova_x, nova_y]
            
        self.pos = list(limitar_posicao(self.pos))
        novos_projeteis = []
        
        if self.pode_atirar and self.pode_atirar_jogador(jogador_pos):
            projetil = self.atirar(jogador_pos)
            if projetil:
                novos_projeteis.append(projetil)
                
        return novos_projeteis

    def pode_atirar_jogador(self, jogador_pos):
        if not self.pode_atirar:
            return False
        if pygame.time.get_ticks() - self.ultimo_tiro < self.intervalo_tiro:
            return False
        distancia = calcular_distancia(self.pos, jogador_pos)
        return distancia <= self.alcance_tiro

    def atirar(self, jogador_pos):
        self.ultimo_tiro = pygame.time.get_ticks()
        return ProjetilInimigo(self.pos[0], self.pos[1], jogador_pos[0], jogador_pos[1], self.dano)

    def pode_atacar(self):
        return pygame.time.get_ticks() - self.ultimo_ataque > self.intervalo_ataque

    def atacar_jogador(self, jogador):
        if not self.pode_atacar():
            return False
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < self.raio + jogador.raio + 10:
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
            pygame.draw.circle(tela, PRETO, (int(pos_tela[0]), int(pos_tela[1])), self.raio, 2)
            if self.hp < self.hp_max:
                desenhar_barra_vida(tela, pos_tela, self.hp, self.hp_max)


def gerar_inimigo_aleatorio(jogador_pos, tempo_jogo):
    mult_hp = 1 + (tempo_jogo / 180)
    mult_dano = 1 + (tempo_jogo / 240)
    mult_xp = 1 + (tempo_jogo / 150)
    mult_velocidade = 1 + (tempo_jogo / 300)
    
    if tempo_jogo < 120:
        tipos_disponiveis = ["basico"]
        pesos = [1.0]
    elif tempo_jogo < 240:
        tipos_disponiveis = ["basico", "voador"]
        pesos = [0.7, 0.3]
    elif tempo_jogo < 360:
        tipos_disponiveis = ["basico", "voador", "tanque"]
        pesos = [0.5, 0.3, 0.2]
    elif tempo_jogo < 480:
        tipos_disponiveis = ["basico", "voador", "tanque", "veloz"]
        pesos = [0.4, 0.25, 0.2, 0.15]
    elif tempo_jogo < 600:
        tipos_disponiveis = ["basico", "voador", "tanque", "veloz"]
        pesos = [0.3, 0.25, 0.3, 0.15]
    else:
        tipos_disponiveis = ["basico", "voador", "tanque", "veloz"]
        pesos = [0.25, 0.25, 0.25, 0.25]
        
    tipo = random.choices(tipos_disponiveis, weights=pesos)[0]
    angulo = random.uniform(0, 2 * math.pi)
    distancia = random.uniform(300, 500)
    x = jogador_pos[0] + math.cos(angulo) * distancia
    y = jogador_pos[1] + math.sin(angulo) * distancia
    x = max(50, min(LARGURA_MAPA - 50, x))
    y = max(50, min(ALTURA_MAPA - 50, y))
    
    if tipo == "voador":
        inimigo = InimigoVoador(x, y)
    elif tipo == "tanque":
        inimigo = InimigoTanque(x, y)
    elif tipo == "veloz":
        inimigo = InimigoVeloz(x, y)
    else:
        inimigo = Inimigo(x, y)
        
    inimigo.hp = int(inimigo.hp * mult_hp)
    inimigo.hp_max = int(inimigo.hp_max * mult_hp)
    inimigo.dano = int(inimigo.dano * mult_dano)
    inimigo.xp_drop = int(inimigo.xp_drop * mult_xp)
    
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
        dx = alvo_x - x
        dy = alvo_y - y
        self.direcao_x, self.direcao_y = normalizar_vetor(dx, dy)
        self.ativo = True

    def atualizar(self):
        if not self.ativo:
            return
        nova_x = self.pos[0] + self.direcao_x * self.velocidade
        nova_y = self.pos[1] + self.direcao_y * self.velocidade
        self.pos = [nova_x, nova_y]
        distancia_percorrida = calcular_distancia(self.pos, self.pos_inicial)
        if distancia_percorrida > self.alcance:
            self.ativo = False
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
        self.tempo_ultimo_tiro = 0
        self.cooldown_tiro = 2500
        self.distancia_ataque = 180
        self.altura_voo = random.uniform(0.7, 1.2)
        self.animacao = random.randint(0, 100)
        self.ultimo_ataque = 0
        self.intervalo_ataque = 1000

    def atualizar(self, jogador_pos):
        if not self.ativo:
            return None
            
        self.animacao += 1
        dx = self.pos[0] - jogador_pos[0]
        dy = self.pos[1] - jogador_pos[1]
        distancia = math.sqrt(dx*dx + dy*dy)
        
        if distancia < self.distancia_ataque - 30:
            if distancia > 0:
                nova_x = self.pos[0] + (dx / distancia) * self.velocidade * 1.5
                nova_y = self.pos[1] + (dy / distancia) * self.velocidade * 1.5
                self.pos = [nova_x, nova_y]
        elif distancia > self.distancia_ataque + 30:
            if distancia > 0:
                nova_x = self.pos[0] - (dx / distancia) * self.velocidade
                nova_y = self.pos[1] - (dy / distancia) * self.velocidade
                self.pos = [nova_x, nova_y]
        else:
            angulo = math.atan2(dy, dx) + 0.02
            nova_x = jogador_pos[0] + math.cos(angulo) * self.distancia_ataque
            nova_y = jogador_pos[1] + math.sin(angulo) * self.distancia_ataque
            self.pos = [nova_x, nova_y]
            
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
        if pygame.time.get_ticks() - self.ultimo_ataque < self.intervalo_ataque:
            return False
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < self.raio + jogador.raio + 15:
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
        self.ativo = False
        return XP(self.pos[0], self.pos[1], self.xp_drop)

    def desenhar_barra_vida(self, tela, pos):
        if self.hp < self.hp_max:
            largura = 30
            altura = 4
            x = pos[0] - largura // 2
            y = pos[1] - self.raio - 8
            pygame.draw.rect(tela, (100, 0, 0), (x, y, largura, altura))
            vida_largura = int((self.hp / self.hp_max) * largura)
            if vida_largura > 0:
                pygame.draw.rect(tela, (0, 255, 0), (x, y, vida_largura, altura))

    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        pos_tela = posicao_na_tela(self.pos, camera)
        if esta_na_tela(self.pos, camera):
            offset_y = math.sin(self.animacao * 0.1) * 3 * self.altura_voo
            pos_sombra = (int(pos_tela[0]), int(pos_tela[1] + offset_y + 5))
            pos_corpo = (int(pos_tela[0]), int(pos_tela[1] + offset_y))
            
            pygame.draw.ellipse(tela, (50, 50, 50), 
                              (pos_sombra[0] - 8, pos_sombra[1] - 3, 16, 6))
            pygame.draw.circle(tela, (0, 50, 150), pos_corpo, self.raio)
            pygame.draw.circle(tela, (0, 100, 200), pos_corpo, self.raio - 3)
            
            asa_offset = math.sin(self.animacao * 0.3) * 8
            pygame.draw.ellipse(tela, (100, 150, 255),
                              (pos_corpo[0] - 20, pos_corpo[1] - 8 + asa_offset, 15, 8))
            pygame.draw.ellipse(tela, (100, 150, 255),
                              (pos_corpo[0] + 5, pos_corpo[1] - 8 - asa_offset, 15, 8))
            self.desenhar_barra_vida(tela, pos_corpo)


class InimigoTanque:
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
        self.armor = 2
        self.ultimo_ataque = 0
        self.intervalo_ataque = 1500

    def atualizar(self, jogador_pos):
        if not self.ativo:
            return None
            
        dx = jogador_pos[0] - self.pos[0]
        dy = jogador_pos[1] - self.pos[1]
        
        if dx != 0 or dy != 0:
            dir_x, dir_y = normalizar_vetor(dx, dy)
            nova_x = self.pos[0] + dir_x * self.velocidade
            nova_y = self.pos[1] + dir_y * self.velocidade
            self.pos = [nova_x, nova_y]
            
        self.pos = list(limitar_posicao(self.pos))
        return None

    def atacar_jogador(self, jogador):
        if pygame.time.get_ticks() - self.ultimo_ataque < self.intervalo_ataque:
            return False
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < self.raio + jogador.raio + 10:
            if jogador.receber_dano(self.dano):
                self.ultimo_ataque = pygame.time.get_ticks()
                return True
        return False

    def receber_dano(self, dano):
        dano_final = max(1, dano - self.armor)
        self.hp -= dano_final
        if self.hp <= 0:
            self.ativo = False
            return True
        return False

    def morrer(self):
        self.ativo = False
        return XP(self.pos[0], self.pos[1], self.xp_drop)

    def desenhar_barra_vida(self, tela, pos):
        if self.hp < self.hp_max:
            largura = 40
            altura = 6
            x = pos[0] - largura // 2
            y = pos[1] - self.raio - 10
            pygame.draw.rect(tela, (100, 0, 0), (x, y, largura, altura))
            vida_largura = int((self.hp / self.hp_max) * largura)
            if vida_largura > 0:
                if self.hp > self.hp_max * 0.5:
                    cor = (0, 255, 0)
                elif self.hp > self.hp_max * 0.25:
                    cor = (255, 255, 0)
                else:
                    cor = (255, 0, 0)
                pygame.draw.rect(tela, cor, (x, y, vida_largura, altura))

    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        pos_tela = posicao_na_tela(self.pos, camera)
        if esta_na_tela(self.pos, camera):
            pygame.draw.circle(tela, (60, 60, 60), (int(pos_tela[0]), int(pos_tela[1])), self.raio)
            pygame.draw.circle(tela, (80, 80, 80), (int(pos_tela[0]), int(pos_tela[1])), self.raio - 4)
            pygame.draw.circle(tela, (100, 100, 100), (int(pos_tela[0]), int(pos_tela[1])), self.raio - 8)
            
            for i in range(4):
                angulo = i * math.pi / 2
                x_det = int(pos_tela[0] + math.cos(angulo) * (self.raio - 6))
                y_det = int(pos_tela[1] + math.sin(angulo) * (self.raio - 6))
                pygame.draw.circle(tela, (120, 120, 120), (x_det, y_det), 3)
                
            pygame.draw.circle(tela, (30, 30, 30), (int(pos_tela[0]), int(pos_tela[1])), self.raio, 3)
            self.desenhar_barra_vida(tela, pos_tela)


class InimigoVeloz:
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
        self.tempo_mudanca = 0
        self.direcao_atual = random.uniform(0, 2 * math.pi)
        self.contador_zigzag = 0
        self.ultimo_ataque = 0
        self.intervalo_ataque = 800

    def atualizar(self, jogador_pos):
        if not self.ativo:
            return None
            
        self.contador_zigzag += 1
        dx_jogador = jogador_pos[0] - self.pos[0]
        dy_jogador = jogador_pos[1] - self.pos[1]
        
        if dx_jogador != 0 or dy_jogador != 0:
            dist_jogador = math.sqrt(dx_jogador*dx_jogador + dy_jogador*dy_jogador)
            dir_jogador_x = dx_jogador / dist_jogador
            dir_jogador_y = dy_jogador / dist_jogador
        else:
            dir_jogador_x, dir_jogador_y = 0, 0
            
        if self.contador_zigzag % 30 == 0:
            self.direcao_atual += random.uniform(-math.pi/3, math.pi/3)
            
        zigzag_x = math.cos(self.direcao_atual) * 0.3
        zigzag_y = math.sin(self.direcao_atual) * 0.3
        movimento_x = (dir_jogador_x * 0.7 + zigzag_x)
        movimento_y = (dir_jogador_y * 0.7 + zigzag_y)
        
        nova_x = self.pos[0] + movimento_x * self.velocidade
        nova_y = self.pos[1] + movimento_y * self.velocidade
        self.pos = [nova_x, nova_y]
        self.pos = list(limitar_posicao(self.pos))
        return None

    def atacar_jogador(self, jogador):
        if pygame.time.get_ticks() - self.ultimo_ataque < self.intervalo_ataque:
            return False
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < self.raio + jogador.raio + 8:
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
        self.ativo = False
        return XP(self.pos[0], self.pos[1], self.xp_drop)

    def desenhar_barra_vida(self, tela, pos):
        if self.hp < self.hp_max:
            largura = 25
            altura = 3
            x = pos[0] - largura // 2
            y = pos[1] - self.raio - 6
            pygame.draw.rect(tela, (100, 0, 0), (x, y, largura, altura))
            vida_largura = int((self.hp / self.hp_max) * largura)
            if vida_largura > 0:
                pygame.draw.rect(tela, (0, 255, 0), (x, y, vida_largura, altura))

    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        pos_tela = posicao_na_tela(self.pos, camera)
        if esta_na_tela(self.pos, camera):
            for i in range(3):
                alpha = 0.3 - (i * 0.1)
                offset = i * 4
                rastro_x = int(pos_tela[0] - math.cos(self.direcao_atual) * offset)
                rastro_y = int(pos_tela[1] - math.sin(self.direcao_atual) * offset)
                rastro_raio = max(1, self.raio - i * 3)
                cor_rastro = tuple(max(0, int(c * alpha)) for c in (255, 255, 100))
                if sum(cor_rastro) > 0:
                    pygame.draw.circle(tela, cor_rastro, (rastro_x, rastro_y), rastro_raio)
                    
            pygame.draw.circle(tela, (255, 255, 0), (int(pos_tela[0]), int(pos_tela[1])), self.raio)
            pygame.draw.circle(tela, (255, 255, 150), (int(pos_tela[0]), int(pos_tela[1])), self.raio - 3)
            pygame.draw.circle(tela, (200, 200, 0), (int(pos_tela[0]), int(pos_tela[1])), self.raio, 2)
            self.desenhar_barra_vida(tela, pos_tela) 