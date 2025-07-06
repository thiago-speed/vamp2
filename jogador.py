import pygame
import math
import random
from config import *
from utils import *


class EspadaOrbital:
    def __init__(self, jogador, indice, total_espadas):
        self.jogador = jogador
        self.indice = indice
        self.total_espadas = total_espadas
        self.angulo_base = (2 * math.pi / total_espadas) * indice
        self.angulo_atual = self.angulo_base
        self.distancia = 50 + (jogador.espada_nivel * 5)
        self.tamanho = 12 + (jogador.espada_nivel * 2)
        self.dano = jogador.dano * (1 + jogador.espada_nivel * 0.8)
        self.ultimo_ataque = 0
        self.cooldown_ataque = 1000 - (jogador.espada_nivel * 100)
        self.alcance_ataque = jogador.alcance_tiro + 40
        self.posicao_orbital_fixa = self.angulo_base
        self.velocidade_rotacao = 1.5 + (jogador.espada_nivel * 0.15)
        self.em_estocada = False
        self.tempo_estocada = 0
        self.alvo_estocada = None
        self.pos_inicial = [0, 0]
        self.pos_alvo = [0, 0]
        self.pos_atual = [0, 0]
        self.trilha = []
        self.particulas_corte = []
        self.brilho_intensidade = 1.0

    def atualizar(self, inimigos):
        if self.em_estocada:
            self.atualizar_estocada()
        else:
            self.atualizar_orbital()
            self.verificar_estocada(inimigos)
        self.atualizar_trilha()
        self.atualizar_particulas()

    def atualizar_trilha(self):
        self.trilha.append({
            'pos': list(self.pos_atual),
            'vida': 4,
            'vida_max': 4
        })
        if len(self.trilha) > 3:
            self.trilha.pop(0)
        for ponto in self.trilha:
            ponto['vida'] -= 1
        self.trilha = [p for p in self.trilha if p['vida'] > 0]

    def atualizar_particulas(self):
        for particula in self.particulas_corte[:]:
            particula['vida'] -= 1
            particula['x'] += particula['vx']
            particula['y'] += particula['vy']
            particula['vx'] *= 0.95
            particula['vy'] *= 0.95
            if particula['vida'] <= 0:
                self.particulas_corte.remove(particula)

    def gerar_particulas_corte(self, pos):
        for _ in range(2):
            angulo = random.uniform(0, 2 * math.pi)
            velocidade = random.uniform(1, 2)
            self.particulas_corte.append({
                'x': pos[0],
                'y': pos[1],
                'vx': math.cos(angulo) * velocidade,
                'vy': math.sin(angulo) * velocidade,
                'vida': random.randint(5, 8),
                'vida_max': 8
            })

    def atualizar_orbital(self):
        self.angulo_atual += self.velocidade_rotacao * 0.016
        nova_x = self.jogador.pos[0] + math.cos(self.angulo_atual) * self.distancia
        nova_y = self.jogador.pos[1] + math.sin(self.angulo_atual) * self.distancia
        self.pos_atual = [nova_x, nova_y]
        self.brilho_intensidade = 0.8 + 0.2 * math.sin(self.angulo_atual * 2)

    def verificar_estocada(self, inimigos):
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.ultimo_ataque < self.cooldown_ataque:
            return
        inimigo_mais_proximo = None
        menor_distancia = self.alcance_ataque
        for inimigo in inimigos:
            if not inimigo.ativo:
                continue
            distancia = calcular_distancia(self.jogador.pos, inimigo.pos)
            if distancia < menor_distancia:
                menor_distancia = distancia
                inimigo_mais_proximo = inimigo
        if inimigo_mais_proximo:
            self.iniciar_estocada(inimigo_mais_proximo)
            self.ultimo_ataque = tempo_atual

    def iniciar_estocada(self, alvo):
        self.em_estocada = True
        self.tempo_estocada = 0
        self.alvo_estocada = alvo
        self.pos_inicial = list(self.pos_atual)
        self.pos_alvo = list(alvo.pos)
        self.brilho_intensidade = 1.5
        self.angulo_retorno = self.angulo_atual

    def atualizar_estocada(self):
        self.tempo_estocada += 1
        duracao_total = 15
        if self.tempo_estocada < duracao_total // 2:
            progresso = self.tempo_estocada / (duracao_total // 2)
            nova_x = self.pos_inicial[0] + (self.pos_alvo[0] - self.pos_inicial[0]) * progresso
            nova_y = self.pos_inicial[1] + (self.pos_alvo[1] - self.pos_inicial[1]) * progresso
            self.pos_atual = [nova_x, nova_y]
            if self.alvo_estocada and self.alvo_estocada.ativo:
                distancia = calcular_distancia(self.pos_atual, self.alvo_estocada.pos)
                if distancia < self.tamanho + self.alvo_estocada.raio:
                    if hasattr(self.alvo_estocada, 'fase'):
                        self.alvo_estocada.receber_dano(self.dano * 2, fonte="continuo")
                    else:
                        self.alvo_estocada.receber_dano(self.dano * 2)
                    self.gerar_particulas_corte(self.alvo_estocada.pos)
        elif self.tempo_estocada < duracao_total:
            progresso = (self.tempo_estocada - duracao_total // 2) / (duracao_total // 2)
            pos_orbital_original = [
                self.jogador.pos[0] + math.cos(self.angulo_retorno) * self.distancia,
                self.jogador.pos[1] + math.sin(self.angulo_retorno) * self.distancia
            ]
            nova_x = self.pos_alvo[0] + (pos_orbital_original[0] - self.pos_alvo[0]) * progresso
            nova_y = self.pos_alvo[1] + (pos_orbital_original[1] - self.pos_alvo[1]) * progresso
            self.pos_atual = [nova_x, nova_y]
        else:
            self.em_estocada = False
            self.alvo_estocada = None
            self.brilho_intensidade = 1.0
            self.angulo_atual = self.angulo_retorno

    def colidir_com_inimigo(self, inimigo):
        if not inimigo.ativo:
            return False
        distancia = calcular_distancia(self.pos_atual, inimigo.pos)
        if distancia < self.tamanho + inimigo.raio:
            if hasattr(inimigo, 'fase'):
                inimigo.receber_dano(self.dano, fonte="continuo")
            else:
                inimigo.receber_dano(self.dano)
            self.gerar_particulas_corte(inimigo.pos)
            return True
        return False

    def desenhar(self, tela, camera):
        pos_tela = posicao_na_tela(self.pos_atual, camera)
        if esta_na_tela(self.pos_atual, camera):
            for i, ponto in enumerate(self.trilha):
                vida_prop = ponto['vida'] / ponto['vida_max']
                pos_trilha = posicao_na_tela(ponto['pos'], camera)
                alpha = vida_prop * 0.2
                tamanho_trilha = int(self.tamanho * vida_prop * 0.3)
                if tamanho_trilha > 0:
                    cor_trilha = tuple(max(0, min(255, int(c * alpha))) for c in (150, 150, 180))
                    pygame.draw.circle(tela, cor_trilha, (int(pos_trilha[0]), int(pos_trilha[1])), tamanho_trilha)
            
            if self.em_estocada:
                dx = self.pos_alvo[0] - self.pos_atual[0]
                dy = self.pos_alvo[1] - self.pos_atual[1]
                angulo_espada = math.atan2(dy, dx)
                cor_base_raw = tuple(c * self.brilho_intensidade for c in (255, 215, 0))
            else:
                dx = self.pos_atual[0] - self.jogador.pos[0]
                dy = self.pos_atual[1] - self.jogador.pos[1]
                angulo_espada = math.atan2(dy, dx)
                cor_base_raw = tuple(c * self.brilho_intensidade for c in (192, 192, 192))
            
            cor_base = tuple(max(0, min(255, int(c))) for c in cor_base_raw)
            comprimento = self.tamanho * 2.5
            largura_base = self.tamanho // 4
            comprimento_cabo = self.tamanho // 3
            ponta_x = pos_tela[0] + math.cos(angulo_espada) * comprimento
            ponta_y = pos_tela[1] + math.sin(angulo_espada) * comprimento
            base_x = pos_tela[0] - math.cos(angulo_espada) * comprimento_cabo
            base_y = pos_tela[1] - math.sin(angulo_espada) * comprimento_cabo
            
            pygame.draw.line(tela, cor_base, (int(pos_tela[0]), int(pos_tela[1])), 
                           (int(ponta_x), int(ponta_y)), 3)
            pygame.draw.line(tela, (101, 67, 33), (int(pos_tela[0]), int(pos_tela[1])), 
                           (int(base_x), int(base_y)), 5)
            
            for particula in self.particulas_corte:
                vida_prop = particula['vida'] / particula['vida_max']
                part_pos = posicao_na_tela([particula['x'], particula['y']], camera)
                cor_part = tuple(max(0, min(255, int(c * vida_prop))) for c in (255, 255, 150))
                tamanho_part = max(1, int(1.5 * vida_prop))
                pygame.draw.circle(tela, cor_part, (int(part_pos[0]), int(part_pos[1])), tamanho_part)


class Jogador:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.velocidade = JOGADOR_VELOCIDADE
        self.raio = JOGADOR_RAIO
        self.hp = JOGADOR_HP_INICIAL
        self.hp_max = JOGADOR_HP_INICIAL
        self.dano = JOGADOR_DANO_INICIAL
        self.invulneravel = False
        self.tempo_invulneravel = 0
        self.level = 1
        self.xp = 0
        self.xp_para_proximo = calcular_xp_para_level(1)
        self.vida_nivel = 0
        self.dano_nivel = 0
        self.velocidade_nivel = 0
        self.alcance_nivel = 0
        self.cadencia_nivel = 0
        self.atravessar_nivel = 0
        self.projeteis_nivel = 0
        self.coleta_nivel = 0
        self.ultimo_tiro = 0
        self.cooldown_tiro = 500
        self.alcance_tiro = PROJETIL_ALCANCE
        self.velocidade_tiro = PROJETIL_VELOCIDADE
        self.atravessar_inimigos = 0
        self.projeteis_simultaneos = 1
        self.raio_coleta = 30
        self.espada_nivel = 0
        self.dash_nivel = 0
        self.bomba_nivel = 0
        self.raios_nivel = 0
        self.campo_nivel = 0
        self.dash_ativo = False
        self.dash_cooldown = 0
        self.escudo_ativo = False
        self.escudo_nivel = 0
        self.escudo_cooldown = 0
        self.bomba_cooldown = 0
        self.raios_cooldown = 0
        self.espada_cooldown = 0
        self.campo_cooldown = 0
        self.espadas = []
        self.ultimo_ataque_espada = 0
        self.cooldown_estocada = 800
        self.ultimo_bomba_auto = 0
        self.ultimo_raios_auto = 0
        self.direcao_movimento = [0, -1]
        self.ultima_direcao_valida = [0, -1]
        self.cor = AZUL_CLARO
        self.vida_infinita = False

    def mover(self, keys):
        dx, dy = 0, 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707
        if dx != 0 or dy != 0:
            self.direcao_movimento = [dx, dy]
            self.ultima_direcao_valida = [dx, dy]
        nova_pos = [
            self.pos[0] + dx * self.velocidade,
            self.pos[1] + dy * self.velocidade
        ]
        self.pos = limitar_posicao(nova_pos)

    def pode_atirar(self):
        return pygame.time.get_ticks() - self.ultimo_tiro > self.cooldown_tiro

    def atirar(self):
        self.ultimo_tiro = pygame.time.get_ticks()

    def receber_dano(self, dano):
        if self.vida_infinita:
            return False
        if self.invulneravel:
            return False
        if self.escudo_ativo:
            return False
        self.hp -= dano
        self.invulneravel = True
        self.tempo_invulneravel = pygame.time.get_ticks() + 500
        return True

    def ganhar_xp(self, quantidade):
        self.xp += quantidade
        if self.xp >= self.xp_para_proximo:
            xp_restante = self.xp - self.xp_para_proximo
            self.level += 1
            self.xp_para_proximo = calcular_xp_para_level(self.level)
            self.xp = xp_restante
            return True
        return False

    def curar(self, quantidade):
        self.hp = min(self.hp_max, self.hp + quantidade)

    def atualizar(self):
        if self.invulneravel and pygame.time.get_ticks() > self.tempo_invulneravel:
            self.invulneravel = False
        if self.dash_ativo:
            if hasattr(self, 'dash_frames_restantes') and self.dash_frames_restantes > 0:
                nova_x = self.pos[0] + self.dash_dx
                nova_y = self.pos[1] + self.dash_dy
                self.pos = list(limitar_posicao([nova_x, nova_y]))
                self.dash_frames_restantes -= 1
                if self.dash_frames_restantes <= 0:
                    self.dash_ativo = False
            else:
                self.dash_ativo = False
        tempo_atual = pygame.time.get_ticks()
        if self.dash_cooldown > 0:
            self.dash_cooldown = max(0, self.dash_cooldown - 16)
        if self.bomba_cooldown > 0:
            self.bomba_cooldown = max(0, self.bomba_cooldown - 16)
        if self.escudo_cooldown > 0:
            self.escudo_cooldown = max(0, self.escudo_cooldown - 16)
        if self.raios_cooldown > 0:
            self.raios_cooldown = max(0, self.raios_cooldown - 16)
        if self.espada_cooldown > 0:
            self.espada_cooldown = max(0, self.espada_cooldown - 16)
        if self.campo_cooldown > 0:
            self.campo_cooldown = max(0, self.campo_cooldown - 16)
        self.atualizar_raio_coleta()
        self.atualizar_habilidades()

    def desenhar(self, tela, camera):
        pos_tela = [self.pos[0] - camera[0], self.pos[1] - camera[1]]
        if self.coleta_nivel > 0:
            cor_coleta = (0, 255, 0, 50)
            pygame.draw.circle(tela, (0, 100, 0), (int(pos_tela[0]), int(pos_tela[1])), self.raio_coleta, 1)
        if self.escudo_ativo:
            raio_escudo = self.raio + 15 + (self.escudo_nivel * 3)
            pygame.draw.circle(tela, (0, 255, 255), (int(pos_tela[0]), int(pos_tela[1])), raio_escudo, 3)
        if self.invulneravel and (pygame.time.get_ticks() // 100) % 2:
            cor = CINZA
        elif self.dash_ativo:
            cor = (255, 255, 0)
        else:
            cor = BRANCO
        pygame.draw.rect(tela, cor, 
                        (pos_tela[0] - self.raio, pos_tela[1] - self.raio, 
                         self.raio * 2, self.raio * 2))
        if self.invulneravel:
            alpha = int(128 + 128 * math.sin(pygame.time.get_ticks() * 0.01))
            brilho = pygame.Surface((self.raio * 2 + 4, self.raio * 2 + 4))
            brilho.set_alpha(alpha)
            brilho.fill(DOURADO)
            tela.blit(brilho, (pos_tela[0] - self.raio - 2, pos_tela[1] - self.raio - 2))
        for espada in self.espadas:
            espada.desenhar(tela, camera)
        desenhar_barra_vida(tela, pos_tela, self.hp, self.hp_max)

    def esta_vivo(self):
        return self.hp > 0

    def usar_dash(self, direcao_x, direcao_y):
        if self.dash_nivel > 0 and self.dash_cooldown <= 0:
            cooldown_dash = max(3000 - (self.dash_nivel * 400), 1000)
            self.dash_cooldown = cooldown_dash
            distancia_dash = 120 + (self.dash_nivel * 30)
            velocidade_dash = 15
            frames_dash = int(distancia_dash / velocidade_dash)
            self.dash_ativo = True
            self.dash_frames_restantes = frames_dash
            self.dash_dx = direcao_x * velocidade_dash
            self.dash_dy = direcao_y * velocidade_dash
            self.invulneravel = True
            self.tempo_invulneravel = pygame.time.get_ticks() + (frames_dash * 16)
            return True
        return False

    def usar_bomba(self):
        if self.bomba_nivel > 0 and self.bomba_cooldown <= 0:
            cooldown_bomba = max(5000 - (self.bomba_nivel * 500), 2000)
            self.bomba_cooldown = cooldown_bomba
            dano_bomba = self.dano * (1 + self.bomba_nivel)
            raio_bomba = 80 + (self.bomba_nivel * 20)
            return {
                'pos': list(self.pos),
                'dano': dano_bomba,
                'raio': raio_bomba
            }
        return None

    def ativar_escudo(self):
        if self.escudo_nivel > 0 and self.escudo_cooldown <= 0:
            cooldown_escudo = max(8000 - (self.escudo_nivel * 800), 3000)
            duracao_escudo = 2000 + (self.escudo_nivel * 500)
            self.escudo_cooldown = cooldown_escudo
            self.escudo_ativo = True
            self.escudo_duracao = pygame.time.get_ticks() + duracao_escudo
            return True
        return False

    def obter_raios(self):
        if self.raios_nivel > 0 and self.raios_cooldown <= 0:
            cooldown_raios = max(4000 - (self.raios_nivel * 400), 1500)
            self.raios_cooldown = cooldown_raios
            quantidade_raios = self.raios_nivel + 1
            dano_raios = self.dano * (1 + self.raios_nivel * 0.5)
            return {
                'quantidade': quantidade_raios,
                'dano': dano_raios
            }
        return None

    def obter_campo_gravitacional(self):
        if self.campo_nivel > 0 and self.campo_cooldown <= 0:
            cooldown_campo = max(6000 - (self.campo_nivel * 600), 2000)
            self.campo_cooldown = cooldown_campo
            forca_campo = 2 + (self.campo_nivel * 0.5)
            raio_campo = 100 + (self.campo_nivel * 25)
            return {
                'pos': list(self.pos),
                'forca': forca_campo,
                'raio': raio_campo,
                'duracao': 3000 + (self.campo_nivel * 500)
            }
        return None

    def atualizar_habilidades(self):
        tempo_atual = pygame.time.get_ticks()
        if self.escudo_ativo and tempo_atual > self.escudo_duracao:
            self.escudo_ativo = False

    def atualizar_espadas(self, inimigos):
        num_espadas_desejado = self.espada_nivel
        if len(self.espadas) != num_espadas_desejado:
            self.espadas = []
            for i in range(num_espadas_desejado):
                espada = EspadaOrbital(self, i, num_espadas_desejado)
                self.espadas.append(espada)
        for espada in self.espadas:
            espada.atualizar(inimigos)

    def obter_espadas(self):
        return self.espadas

    def obter_posicao_espada(self):
        return None

    def verificar_bomba_automatica(self):
        if self.bomba_nivel > 0:
            tempo_atual = pygame.time.get_ticks()
            intervalo_bomba = max(8000 - (self.bomba_nivel * 1000), 3000)
            if tempo_atual - self.ultimo_bomba_auto > intervalo_bomba:
                self.ultimo_bomba_auto = tempo_atual
                distancia_bomba = 150 + (self.bomba_nivel * 25)
                dir_x, dir_y = self.ultima_direcao_valida
                if dir_x != 0 or dir_y != 0:
                    magnitude = math.sqrt(dir_x*dir_x + dir_y*dir_y)
                    dir_x /= magnitude
                    dir_y /= magnitude
                pos_bomba = [
                    self.pos[0] + dir_x * distancia_bomba,
                    self.pos[1] + dir_y * distancia_bomba
                ]
                pos_bomba = list(limitar_posicao(pos_bomba))
                dano_bomba = 12 + (self.bomba_nivel * 6)
                raio_bomba = 90 + (self.bomba_nivel * 22)
                return {
                    'pos': pos_bomba,
                    'pos_inicial': list(self.pos),
                    'dano': dano_bomba,
                    'raio': raio_bomba,
                    'tempo_voo': 60
                }
        return None

    def verificar_raios_automaticos(self):
        if self.raios_nivel > 0:
            tempo_atual = pygame.time.get_ticks()
            intervalo_raios = max(6000 - (self.raios_nivel * 800), 2000)
            if tempo_atual - self.ultimo_raios_auto > intervalo_raios:
                self.ultimo_raios_auto = tempo_atual
                quantidade_raios = min(self.raios_nivel + 1, 6)
                dano_raios = 3 + (self.raios_nivel * 2)
                return {
                    'quantidade': quantidade_raios,
                    'dano': dano_raios
                }
        return None

    def obter_campo_ativo(self):
        if self.campo_nivel > 0:
            if self.campo_nivel >= 5:
                dano_campo = 3
                forca_campo = 2
                raio_campo = 150
            else:
                dano_campo = 1 + (self.campo_nivel * 0.3)
                forca_campo = 1 + (self.campo_nivel * 0.2)
                raio_campo = 80 + (self.campo_nivel * 15)
            return {
                'pos': list(self.pos),
                'dano': dano_campo,
                'forca': forca_campo,
                'raio': raio_campo
            }
        return None

    def atualizar_raio_coleta(self):
        raio_base = 30
        self.raio_coleta = raio_base + (self.coleta_nivel * 30)