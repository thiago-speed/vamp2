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
        self.distancia = 60 + (jogador.espada_nivel * 8)  # Distância fixa
        self.tamanho = 20 + (jogador.espada_nivel * 3)     # Tamanho da espada
        self.dano = jogador.dano * (1 + jogador.espada_nivel * 0.8)
        
        # Alcance de ataque maior que o do jogador
        self.alcance_ataque = jogador.alcance_tiro + 50  # +50 pixels de alcance
        
        # Estados da estocada melhorados
        self.em_estocada = False
        self.tempo_estocada = 0
        self.alvo_estocada = None
        self.pos_inicial = [0, 0]
        self.pos_alvo = [0, 0]
        self.pos_atual = [0, 0]
        
        # Manter posição original para retorno
        self.angulo_original = self.angulo_base
        
        # Efeitos visuais
        self.trilha = []  # Trilha da espada
        self.particulas_corte = []
        self.brilho_intensidade = 1.0
        
    def atualizar(self, inimigos):
        if self.em_estocada:
            self.atualizar_estocada()
        else:
            self.atualizar_orbital()
            self.verificar_estocada(inimigos)
        
        # Atualizar trilha visual
        self.atualizar_trilha()
        self.atualizar_particulas()
        
    def atualizar_trilha(self):
        """Atualiza a trilha visual da espada"""
        self.trilha.append({
            'pos': self.pos_atual.copy(),
            'vida': 8,
            'vida_max': 8
        })
        
        # Limitar tamanho da trilha e atualizar
        if len(self.trilha) > 6:
            self.trilha.pop(0)
        
        for ponto in self.trilha:
            ponto['vida'] -= 1
        
        self.trilha = [p for p in self.trilha if p['vida'] > 0]
    
    def atualizar_particulas(self):
        """Atualiza partículas de corte"""
        for particula in self.particulas_corte[:]:
            particula['vida'] -= 1
            particula['x'] += particula['vx']
            particula['y'] += particula['vy']
            particula['vx'] *= 0.95
            particula['vy'] *= 0.95
            
            if particula['vida'] <= 0:
                self.particulas_corte.remove(particula)
        
    def gerar_particulas_corte(self, pos):
        """Gera partículas quando corta um inimigo"""
        for _ in range(4):
            angulo = random.uniform(0, 2 * math.pi)
            velocidade = random.uniform(2, 4)
            self.particulas_corte.append({
                'x': pos[0],
                'y': pos[1],
                'vx': math.cos(angulo) * velocidade,
                'vy': math.sin(angulo) * velocidade,
                'vida': random.randint(8, 15),
                'vida_max': 15
            })
        
    def atualizar_orbital(self):
        """Movimento orbital normal - mantém posição fixa"""
        velocidade_rotacao = 2.0 + (self.jogador.espada_nivel * 0.2)
        self.angulo_atual += velocidade_rotacao * 0.016  # ~60fps
        
        # Manter a posição original relativa
        self.pos_atual[0] = self.jogador.pos[0] + math.cos(self.angulo_atual) * self.distancia
        self.pos_atual[1] = self.jogador.pos[1] + math.sin(self.angulo_atual) * self.distancia
        
        # Atualizar brilho baseado na velocidade
        self.brilho_intensidade = 0.9 + 0.3 * math.sin(self.angulo_atual * 2)
        
    def verificar_estocada(self, inimigos):
        """Verifica se deve atacar um inimigo próximo - usa alcance maior"""
        if pygame.time.get_ticks() - self.jogador.ultimo_ataque_espada < self.jogador.cooldown_estocada:
            return
            
        # Procurar inimigo mais próximo dentro do alcance de ataque da espada
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
            self.jogador.ultimo_ataque_espada = pygame.time.get_ticks()
    
    def iniciar_estocada(self, alvo):
        """Inicia uma estocada em direção ao alvo"""
        self.em_estocada = True
        self.tempo_estocada = 0
        self.alvo_estocada = alvo
        self.pos_inicial = self.pos_atual.copy()
        self.pos_alvo = alvo.pos.copy()
        self.brilho_intensidade = 1.8  # Brilho intenso durante estocada
        
    def atualizar_estocada(self):
        """Atualiza movimento de estocada - retorna sempre para posição original"""
        self.tempo_estocada += 1
        duracao_total = 20  # frames para ida e volta (mais rápido)
        
        if self.tempo_estocada < duracao_total // 2:
            # Ida - movimento para o alvo com aceleração
            progresso = self.tempo_estocada / (duracao_total // 2)
            progresso_suave = progresso * progresso  # Aceleração quadrática
            self.pos_atual[0] = self.pos_inicial[0] + (self.pos_alvo[0] - self.pos_inicial[0]) * progresso_suave
            self.pos_atual[1] = self.pos_inicial[1] + (self.pos_alvo[1] - self.pos_inicial[1]) * progresso_suave
        elif self.tempo_estocada < duracao_total:
            # Volta - retorno à posição orbital original
            progresso = (self.tempo_estocada - duracao_total // 2) / (duracao_total // 2)
            progresso_suave = 1 - (1 - progresso) * (1 - progresso)  # Desaceleração quadrática
            
            # Calcular posição orbital original no momento atual
            pos_orbital_atual = [
                self.jogador.pos[0] + math.cos(self.angulo_atual) * self.distancia,
                self.jogador.pos[1] + math.sin(self.angulo_atual) * self.distancia
            ]
            
            self.pos_atual[0] = self.pos_alvo[0] + (pos_orbital_atual[0] - self.pos_alvo[0]) * progresso_suave
            self.pos_atual[1] = self.pos_alvo[1] + (pos_orbital_atual[1] - self.pos_alvo[1]) * progresso_suave
        else:
            # Finalizar estocada
            self.em_estocada = False
            self.alvo_estocada = None
            self.brilho_intensidade = 1.0
            self.atualizar_orbital()  # Retomar posição orbital
    
    def colidir_com_inimigo(self, inimigo):
        """Verifica colisão com inimigo"""
        if not inimigo.ativo:
            return False
            
        distancia = calcular_distancia(self.pos_atual, inimigo.pos)
        if distancia < self.tamanho + inimigo.raio:
            inimigo.receber_dano(self.dano)
            # Gerar partículas de corte
            self.gerar_particulas_corte(inimigo.pos)
            return True
        return False
    
    def desenhar(self, tela, camera):
        """Desenha a espada com visual realista melhorado"""
        pos_tela = posicao_na_tela(self.pos_atual, camera)
        
        if esta_na_tela(self.pos_atual, camera):
            # Desenhar trilha da espada mais sutil
            for i, ponto in enumerate(self.trilha):
                vida_prop = ponto['vida'] / ponto['vida_max']
                pos_trilha = posicao_na_tela(ponto['pos'], camera)
                alpha = vida_prop * 0.3
                tamanho_trilha = int(self.tamanho * vida_prop * 0.4)
                
                if tamanho_trilha > 0:
                    cor_trilha = tuple(max(0, min(255, int(c * alpha))) for c in (180, 180, 220))
                    pygame.draw.circle(tela, cor_trilha, (int(pos_trilha[0]), int(pos_trilha[1])), tamanho_trilha)
            
            # Calcular ângulo da espada baseado no movimento
            if self.em_estocada:
                # Durante estocada, apontar para o alvo
                dx = self.pos_alvo[0] - self.pos_atual[0]
                dy = self.pos_alvo[1] - self.pos_atual[1]
                angulo_espada = math.atan2(dy, dx)
                cor_base_raw = tuple(c * self.brilho_intensidade for c in (255, 215, 0))  # Dourado brilhante
            else:
                # Durante órbita, apontar para fora do centro
                dx = self.pos_atual[0] - self.jogador.pos[0]
                dy = self.pos_atual[1] - self.jogador.pos[1]
                angulo_espada = math.atan2(dy, dx)
                cor_base_raw = tuple(c * self.brilho_intensidade for c in (192, 192, 192))  # Prata
            
            # Validar cor para evitar erros
            cor_base = tuple(max(0, min(255, int(c))) for c in cor_base_raw)
            
            # Dimensões da espada realista
            comprimento = self.tamanho * 3.5  # Lâmina longa
            largura_base = self.tamanho // 3   # Base da lâmina
            comprimento_cabo = self.tamanho // 2  # Cabo
            
            # Desenhar sombra da espada
            offset_sombra = 2
            ponta_x = pos_tela[0] + math.cos(angulo_espada) * comprimento + offset_sombra
            ponta_y = pos_tela[1] + math.sin(angulo_espada) * comprimento + offset_sombra
            
            base_x = pos_tela[0] - math.cos(angulo_espada) * comprimento_cabo + offset_sombra
            base_y = pos_tela[1] - math.sin(angulo_espada) * comprimento_cabo + offset_sombra
            
            # Lados da lâmina
            lado1_x = pos_tela[0] + math.cos(angulo_espada + math.pi/2) * largura_base + offset_sombra
            lado1_y = pos_tela[1] + math.sin(angulo_espada + math.pi/2) * largura_base + offset_sombra
            
            lado2_x = pos_tela[0] + math.cos(angulo_espada - math.pi/2) * largura_base + offset_sombra
            lado2_y = pos_tela[1] + math.sin(angulo_espada - math.pi/2) * largura_base + offset_sombra
            
            # Desenhar sombra
            pontos_sombra = [
                (int(ponta_x), int(ponta_y)),
                (int(lado1_x), int(lado1_y)),
                (int(base_x), int(base_y)),
                (int(lado2_x), int(lado2_y))
            ]
            pygame.draw.polygon(tela, (0, 0, 0), pontos_sombra)
            
            # Recalcular para lâmina principal
            ponta_x = pos_tela[0] + math.cos(angulo_espada) * comprimento
            ponta_y = pos_tela[1] + math.sin(angulo_espada) * comprimento
            
            base_x = pos_tela[0] - math.cos(angulo_espada) * comprimento_cabo
            base_y = pos_tela[1] - math.sin(angulo_espada) * comprimento_cabo
            
            lado1_x = pos_tela[0] + math.cos(angulo_espada + math.pi/2) * largura_base
            lado1_y = pos_tela[1] + math.sin(angulo_espada + math.pi/2) * largura_base
            
            lado2_x = pos_tela[0] + math.cos(angulo_espada - math.pi/2) * largura_base
            lado2_y = pos_tela[1] + math.sin(angulo_espada - math.pi/2) * largura_base
            
            # Desenhar lâmina principal
            pontos_lamina = [
                (int(ponta_x), int(ponta_y)),
                (int(lado1_x), int(lado1_y)),
                (int(base_x), int(base_y)),
                (int(lado2_x), int(lado2_y))
            ]
            pygame.draw.polygon(tela, cor_base, pontos_lamina)
            
            # Desenhar reflexo central na lâmina
            meio_x = (ponta_x + base_x) / 2
            meio_y = (ponta_y + base_y) / 2
            cor_reflexo_raw = tuple(min(255, c + 60) for c in cor_base)
            cor_reflexo = tuple(max(0, min(255, int(c))) for c in cor_reflexo_raw)
            
            # Linha central brilhante
            pygame.draw.line(tela, cor_reflexo, 
                           (int(ponta_x), int(ponta_y)), 
                           (int(base_x), int(base_y)), 2)
            
            # Desenhar cabo detalhado
            cabo_x = pos_tela[0] - math.cos(angulo_espada) * (comprimento_cabo + 8)
            cabo_y = pos_tela[1] - math.sin(angulo_espada) * (comprimento_cabo + 8)
            
            # Cabo marrom
            pygame.draw.line(tela, (101, 67, 33), 
                           (int(base_x), int(base_y)), 
                           (int(cabo_x), int(cabo_y)), 8)
            
            # Guarda da espada (crossguard)
            guarda_tamanho = largura_base * 2
            guarda1_x = pos_tela[0] + math.cos(angulo_espada + math.pi/2) * guarda_tamanho
            guarda1_y = pos_tela[1] + math.sin(angulo_espada + math.pi/2) * guarda_tamanho
            guarda2_x = pos_tela[0] + math.cos(angulo_espada - math.pi/2) * guarda_tamanho
            guarda2_y = pos_tela[1] + math.sin(angulo_espada - math.pi/2) * guarda_tamanho
            
            pygame.draw.line(tela, cor_base, 
                           (int(guarda1_x), int(guarda1_y)), 
                           (int(guarda2_x), int(guarda2_y)), 4)
            
            # Pomo da espada
            pygame.draw.circle(tela, (101, 67, 33), (int(cabo_x), int(cabo_y)), 4)
            
            # Desenhar partículas de corte
            for particula in self.particulas_corte:
                vida_prop = particula['vida'] / particula['vida_max']
                part_pos = posicao_na_tela([particula['x'], particula['y']], camera)
                cor_part = tuple(max(0, min(255, int(c * vida_prop))) for c in (255, 255, 150))
                tamanho_part = max(1, int(2 * vida_prop))
                pygame.draw.circle(tela, cor_part, (int(part_pos[0]), int(part_pos[1])), tamanho_part)
            
            # Efeito de brilho para estocada
            if self.em_estocada:
                brilho_raio = int(self.tamanho * 2)
                cor_brilho = tuple(max(0, min(255, int(c * 0.5))) for c in (255, 255, 255))
                pygame.draw.circle(tela, cor_brilho, (int(pos_tela[0]), int(pos_tela[1])), brilho_raio, 2)

class Jogador:
    def __init__(self, x, y):
        # Posição e movimento
        self.pos = [x, y]
        self.velocidade = JOGADOR_VELOCIDADE
        self.raio = JOGADOR_RAIO
        
        # Vida e combate
        self.hp = JOGADOR_HP_INICIAL
        self.hp_max = JOGADOR_HP_INICIAL
        self.dano = JOGADOR_DANO_INICIAL
        self.invulneravel = False
        self.tempo_invulneravel = 0
        
        # Progressão
        self.level = 1
        self.xp = 0
        self.xp_para_proximo = calcular_xp_para_level(1)  # Usar sistema progressivo
        
        # Upgrades básicos - agora com níveis explícitos
        self.vida_nivel = 0        # Contador de upgrades de vida
        self.dano_nivel = 0        # Contador de upgrades de dano  
        self.velocidade_nivel = 0  # Contador de upgrades de velocidade
        self.alcance_nivel = 0     # Contador de upgrades de alcance
        self.cadencia_nivel = 0    # Contador de upgrades de cadência
        self.atravessar_nivel = 0  # Contador de upgrades de atravessar
        self.projeteis_nivel = 0   # Contador de upgrades de projéteis
        self.coleta_nivel = 0      # Contador de upgrades de coleta
        
        # Tiro
        self.ultimo_tiro = 0
        self.cooldown_tiro = 500  # ms
        self.alcance_tiro = PROJETIL_ALCANCE
        self.velocidade_tiro = PROJETIL_VELOCIDADE
        self.atravessar_inimigos = 0
        self.projeteis_simultaneos = 1
        
        # Coleta de XP
        self.raio_coleta = 30
        
        # Habilidades especiais
        self.espada_nivel = 0
        self.dash_nivel = 0
        self.bomba_nivel = 0
        self.raios_nivel = 0
        self.campo_nivel = 0
        
        # Estados das habilidades
        self.dash_ativo = False
        self.dash_cooldown = 0
        self.escudo_ativo = False
        self.escudo_nivel = 0
        self.escudo_cooldown = 0
        self.bomba_cooldown = 0
        self.raios_cooldown = 0
        self.espada_cooldown = 0
        self.campo_cooldown = 0
        
        # Espadas orbitais
        self.espadas = []
        self.ultimo_ataque_espada = 0
        self.cooldown_estocada = 800  # Cooldown entre ataques de espada
        
        # Bombas automáticas
        self.ultimo_bomba_auto = 0
        
        # Raios automáticos  
        self.ultimo_raios_auto = 0
        
    def mover(self, keys):
        dx, dy = 0, 0
        
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        
        # Atualizar direção do movimento
        if dx != 0 or dy != 0:
            self.direcao_movimento = [dx, dy]
            self.ultima_direcao_valida = [dx, dy]
            
            # Normalizar movimento diagonal
            if dx != 0 and dy != 0:
                dx *= 0.707
                dy *= 0.707
        
        # Aplicar movimento
        self.pos[0] += dx * self.velocidade
        self.pos[1] += dy * self.velocidade
        
        # Limitar aos bordos do mapa
        self.pos = list(limitar_posicao(self.pos))
    
    def pode_atirar(self):
        return pygame.time.get_ticks() - self.ultimo_tiro > self.cooldown_tiro
    
    def atirar(self):
        self.ultimo_tiro = pygame.time.get_ticks()
    
    def receber_dano(self, dano):
        if self.invulneravel:
            return False
        
        # Verificar se o escudo está ativo
        if self.escudo_ativo:
            return False  # Escudo bloqueia todo o dano
        
        self.hp -= dano
        self.invulneravel = True
        self.tempo_invulneravel = pygame.time.get_ticks() + 500  # 0.5s invulnerável
        return True
    
    def ganhar_xp(self, quantidade):
        """Ganha XP e verifica se subiu de nível - sistema progressivo"""
        self.xp += quantidade
        
        # Verificar se tem XP suficiente para subir de nível
        if self.xp >= self.xp_para_proximo:
            # Calcular XP restante após o level up
            xp_restante = self.xp - self.xp_para_proximo
            
            # Subir de nível
            self.level += 1
            
            # Definir XP necessário para o próximo nível - progressivo
            self.xp_para_proximo = calcular_xp_para_level(self.level)
            
            # Definir XP atual como o restante
            self.xp = xp_restante
            
            # Retornar True para indicar level up
            return True
        
        return False
    
    def curar(self, quantidade):
        self.hp = min(self.hp_max, self.hp + quantidade)
    
    def atualizar(self):
        # Atualizar invulnerabilidade
        if self.invulneravel and pygame.time.get_ticks() > self.tempo_invulneravel:
            self.invulneravel = False
        
        # Atualizar dash contínuo
        if self.dash_ativo:
            if hasattr(self, 'dash_frames_restantes') and self.dash_frames_restantes > 0:
                # Aplicar movimento do dash
                nova_x = self.pos[0] + self.dash_dx
                nova_y = self.pos[1] + self.dash_dy
                self.pos = list(limitar_posicao([nova_x, nova_y]))
                
                self.dash_frames_restantes -= 1
                
                if self.dash_frames_restantes <= 0:
                    self.dash_ativo = False
            else:
                self.dash_ativo = False
        
        # Reduzir cooldowns
        tempo_atual = pygame.time.get_ticks()
        if self.dash_cooldown > 0:
            self.dash_cooldown = max(0, self.dash_cooldown - 16)  # ~60 FPS
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
        
        # Atualizar raio de coleta
        self.atualizar_raio_coleta()
        
        # Atualizar habilidades especiais
        self.atualizar_habilidades()
    
    def desenhar(self, tela, camera):
        pos_tela = posicao_na_tela(self.pos, camera)
        
        # Desenhar raio de coleta se tiver upgrade
        if self.coleta_nivel > 0:
            cor_coleta = (0, 255, 0, 50)  # Verde transparente
            pygame.draw.circle(tela, (0, 100, 0), (int(pos_tela[0]), int(pos_tela[1])), self.raio_coleta, 1)
        
        # Desenhar escudo se ativo
        if self.escudo_ativo:
            raio_escudo = self.raio + 15 + (self.escudo_nivel * 3)
            pygame.draw.circle(tela, (0, 255, 255), (int(pos_tela[0]), int(pos_tela[1])), raio_escudo, 3)
        
        # Piscar quando invulnerável
        if self.invulneravel and (pygame.time.get_ticks() // 100) % 2:
            cor = CINZA
        elif self.dash_ativo:
            cor = (255, 255, 0)  # Amarelo durante dash
        else:
            cor = AZUL
        
        pygame.draw.circle(tela, cor, (int(pos_tela[0]), int(pos_tela[1])), self.raio)
        
        # Desenhar espadas orbitais
        for espada in self.espadas:
            espada.desenhar(tela, camera)
        
        # Desenhar barra de vida
        desenhar_barra_vida(tela, pos_tela, self.hp, self.hp_max)
    
    def esta_vivo(self):
        return self.hp > 0
    
    def usar_dash(self, direcao_x, direcao_y):
        """Ativa o dash como movimento suave para frente com invulnerabilidade"""
        if self.dash_nivel > 0 and self.dash_cooldown <= 0:
            # Cooldown baseado no nível (menor = melhor)
            cooldown_dash = max(3000 - (self.dash_nivel * 400), 1000)  # 3s até 1s
            self.dash_cooldown = cooldown_dash
            
            # Dash como movimento contínuo
            distancia_dash = 120 + (self.dash_nivel * 30)  # Distância maior
            velocidade_dash = 15  # Velocidade do dash
            frames_dash = int(distancia_dash / velocidade_dash)  # Calcular duração
            
            # Aplicar movimento gradual por alguns frames
            self.dash_ativo = True
            self.dash_frames_restantes = frames_dash
            self.dash_dx = direcao_x * velocidade_dash
            self.dash_dy = direcao_y * velocidade_dash
            
            # Invulnerabilidade durante todo o dash
            self.invulneravel = True
            self.tempo_invulneravel = pygame.time.get_ticks() + (frames_dash * 16)  # 16ms por frame
            return True
        return False
    
    def usar_bomba(self):
        """Retorna dados da bomba se disponível"""
        if self.bomba_nivel > 0 and self.bomba_cooldown <= 0:
            # Cooldown baseado no nível
            cooldown_bomba = max(5000 - (self.bomba_nivel * 500), 2000)  # 5s até 2s
            self.bomba_cooldown = cooldown_bomba
            
            # Dados da bomba
            dano_bomba = self.dano * (1 + self.bomba_nivel)
            raio_bomba = 80 + (self.bomba_nivel * 20)
            
            return {
                'pos': self.pos.copy(),
                'dano': dano_bomba,
                'raio': raio_bomba
            }
        return None
    
    def ativar_escudo(self):
        """Ativa o escudo se disponível"""
        if self.escudo_nivel > 0 and self.escudo_cooldown <= 0:
            # Cooldown e duração baseados no nível
            cooldown_escudo = max(8000 - (self.escudo_nivel * 800), 3000)  # 8s até 3s
            duracao_escudo = 2000 + (self.escudo_nivel * 500)  # 2s até 4.5s
            
            self.escudo_cooldown = cooldown_escudo
            self.escudo_ativo = True
            self.escudo_duracao = pygame.time.get_ticks() + duracao_escudo
            return True
        return False
    
    def obter_raios(self):
        """Retorna dados dos raios se disponível"""
        if self.raios_nivel > 0 and self.raios_cooldown <= 0:
            # Cooldown baseado no nível
            cooldown_raios = max(4000 - (self.raios_nivel * 400), 1500)  # 4s até 1.5s
            self.raios_cooldown = cooldown_raios
            
            # Quantidade e dano baseados no nível
            quantidade_raios = self.raios_nivel + 1  # 2 até 6 raios
            dano_raios = self.dano * (1 + self.raios_nivel * 0.5)
            
            return {
                'quantidade': quantidade_raios,
                'dano': dano_raios
            }
        return None
    
    def obter_campo_gravitacional(self):
        """Retorna dados do campo gravitacional se disponível"""
        if self.campo_nivel > 0 and self.campo_cooldown <= 0:
            # Cooldown baseado no nível
            cooldown_campo = max(6000 - (self.campo_nivel * 600), 2000)  # 6s até 2s
            self.campo_cooldown = cooldown_campo
            
            # Força e raio baseados no nível
            forca_campo = 2 + (self.campo_nivel * 0.5)
            raio_campo = 100 + (self.campo_nivel * 25)
            
            return {
                'pos': self.pos.copy(),
                'forca': forca_campo,
                'raio': raio_campo,
                'duracao': 3000 + (self.campo_nivel * 500)  # 3s até 5.5s
            }
        return None
    
    def atualizar_habilidades(self):
        """Atualiza estados das habilidades especiais"""
        tempo_atual = pygame.time.get_ticks()
        
        # Atualizar dash
        if self.dash_ativo and tempo_atual > self.dash_duracao:
            self.dash_ativo = False
        
        # Atualizar escudo
        if self.escudo_ativo and tempo_atual > self.escudo_duracao:
            self.escudo_ativo = False
        
        # Atualizar espadas orbitais
        self.atualizar_espadas()
    
    def atualizar_espadas(self):
        """Atualiza o sistema de espadas orbitais"""
        # Verificar se precisa criar/atualizar espadas
        num_espadas_desejado = self.espada_nivel
        
        if len(self.espadas) != num_espadas_desejado:
            # Recriar espadas com novo número
            self.espadas = []
            for i in range(num_espadas_desejado):
                espada = EspadaOrbital(self, i, num_espadas_desejado)
                self.espadas.append(espada)
        
        # Atualizar cada espada
        for espada in self.espadas:
            espada.atualizar([])  # Passaremos inimigos no main.py
    
    def obter_espadas(self):
        """Retorna lista de espadas orbitais"""
        return self.espadas
    
    def obter_posicao_espada(self):
        """Método compatibilidade - não usado mais"""
        return None
    
    def verificar_bomba_automatica(self):
        """Verifica se deve ativar bomba automaticamente - lança para longe em arco"""
        if self.bomba_nivel > 0:
            tempo_atual = pygame.time.get_ticks()
            intervalo_bomba = max(8000 - (self.bomba_nivel * 1000), 3000)  # 8s até 3s
            
            if tempo_atual - self.ultimo_bomba_auto > intervalo_bomba:
                self.ultimo_bomba_auto = tempo_atual
                
                # Calcular posição bem à frente do jogador (lançamento longo)
                distancia_bomba = 150 + (self.bomba_nivel * 25)  # Distância muito maior
                dir_x, dir_y = self.ultima_direcao_valida
                
                # Normalizar direção se necessário
                if dir_x != 0 or dir_y != 0:
                    magnitude = math.sqrt(dir_x*dir_x + dir_y*dir_y)
                    dir_x /= magnitude
                    dir_y /= magnitude
                
                pos_bomba = [
                    self.pos[0] + dir_x * distancia_bomba,
                    self.pos[1] + dir_y * distancia_bomba
                ]
                
                # Garantir que a bomba está dentro do mapa
                pos_bomba = list(limitar_posicao(pos_bomba))
                
                # Dados da bomba melhorados
                dano_bomba = 12 + (self.bomba_nivel * 6)  # Dano maior
                raio_bomba = 90 + (self.bomba_nivel * 22)  # Raio maior
                
                return {
                    'pos': pos_bomba,
                    'pos_inicial': self.pos.copy(),  # Para animação de arco
                    'dano': dano_bomba,
                    'raio': raio_bomba,
                    'tempo_voo': 60  # 1 segundo de voo
                }
        return None
    
    def verificar_raios_automaticos(self):
        """Verifica se deve ativar raios automaticamente"""
        if self.raios_nivel > 0:
            tempo_atual = pygame.time.get_ticks()
            intervalo_raios = max(6000 - (self.raios_nivel * 800), 2000)  # 6s até 2s
            
            if tempo_atual - self.ultimo_raios_auto > intervalo_raios:
                self.ultimo_raios_auto = tempo_atual
                
                # Quantidade e dano baseados no nível
                quantidade_raios = min(self.raios_nivel + 1, 6)  # 2 até 6 raios
                dano_raios = 3 + (self.raios_nivel * 2)  # Dano baixo inicial
                
                return {
                    'quantidade': quantidade_raios,
                    'dano': dano_raios
                }
        return None
    
    def obter_campo_ativo(self):
        """Retorna dados do campo gravitacional sempre ativo"""
        if self.campo_nivel > 0:
            # Campo sempre ativo com dano baixo
            dano_campo = 1 + (self.campo_nivel * 0.5)  # Dano muito baixo
            forca_campo = 1 + (self.campo_nivel * 0.3)
            raio_campo = 80 + (self.campo_nivel * 20)  # Raio cresce
            
            return {
                'pos': self.pos.copy(),
                'dano': dano_campo,
                'forca': forca_campo,
                'raio': raio_campo
            }
        return None
    
    def atualizar_raio_coleta(self):
        """Atualiza o raio de coleta baseado no nível do upgrade"""
        # Raio base é 30, mais 30 por nível de coleta
        raio_base = 30
        self.raio_coleta = raio_base + (self.coleta_nivel * 30)  # +30 pixels por nível 