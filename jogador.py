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
        self.distancia = 50 + (jogador.espada_nivel * 5)  # Menor distância
        self.tamanho = 12 + (jogador.espada_nivel * 2)     # Menor tamanho
        self.dano = jogador.dano * (1 + jogador.espada_nivel * 0.8)
        
        # Cada espada tem seu próprio cooldown
        self.ultimo_ataque = 0
        self.cooldown_ataque = 1000 - (jogador.espada_nivel * 100)  # Cooldown individual
        
        # Alcance de ataque
        self.alcance_ataque = jogador.alcance_tiro + 40
        
        # Posição fixa orbital - nunca muda
        self.posicao_orbital_fixa = self.angulo_base
        self.velocidade_rotacao = 1.5 + (jogador.espada_nivel * 0.15)  # Rotação independente
        
        # Estados da estocada simplificados
        self.em_estocada = False
        self.tempo_estocada = 0
        self.alvo_estocada = None
        self.pos_inicial = [0, 0]
        self.pos_alvo = [0, 0]
        self.pos_atual = [0, 0]
        
        # Efeitos visuais reduzidos
        self.trilha = []
        self.particulas_corte = []
        self.brilho_intensidade = 1.0
        
    def atualizar(self, inimigos):
        if self.em_estocada:
            self.atualizar_estocada()
        else:
            self.atualizar_orbital()
            self.verificar_estocada(inimigos)
        
        # Atualizar trilha visual mais sutil
        self.atualizar_trilha()
        self.atualizar_particulas()
        
    def atualizar_trilha(self):
        """Trilha mais sutil"""
        self.trilha.append({
            'pos': list(self.pos_atual),
            'vida': 4,  # Trilha mais curta
            'vida_max': 4
        })
        
        if len(self.trilha) > 3:  # Trilha menor
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
        """Menos partículas"""
        for _ in range(2):  # Apenas 2 partículas
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
        """Movimento orbital independente - sempre retorna à posição fixa"""
        # Cada espada rota independentemente
        self.angulo_atual += self.velocidade_rotacao * 0.016
        
        # Manter a posição fixa orbital
        self.pos_atual[0] = self.jogador.pos[0] + math.cos(self.angulo_atual) * self.distancia
        self.pos_atual[1] = self.jogador.pos[1] + math.sin(self.angulo_atual) * self.distancia
        
        # Brilho sutil
        self.brilho_intensidade = 0.8 + 0.2 * math.sin(self.angulo_atual * 2)
        
    def verificar_estocada(self, inimigos):
        """Verifica se deve atacar - cada espada tem seu próprio cooldown"""
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.ultimo_ataque < self.cooldown_ataque:
            return
            
        # Procurar inimigo mais próximo
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
        """Inicia estocada mas lembra posição orbital original"""
        self.em_estocada = True
        self.tempo_estocada = 0
        self.alvo_estocada = alvo
        self.pos_inicial = list(self.pos_atual)
        self.pos_alvo = list(alvo.pos)
        self.brilho_intensidade = 1.5
        
        # Salvar posição orbital para retorno
        self.angulo_retorno = self.angulo_atual
        
    def atualizar_estocada(self):
        """Estocada rápida e sempre retorna à posição orbital original"""
        self.tempo_estocada += 1
        duracao_total = 15  # Mais rápido
        
        if self.tempo_estocada < duracao_total // 2:
            # Ida para o alvo
            progresso = self.tempo_estocada / (duracao_total // 2)
            self.pos_atual[0] = self.pos_inicial[0] + (self.pos_alvo[0] - self.pos_inicial[0]) * progresso
            self.pos_atual[1] = self.pos_inicial[1] + (self.pos_alvo[1] - self.pos_inicial[1]) * progresso
        elif self.tempo_estocada < duracao_total:
            # Volta para a posição orbital EXATA
            progresso = (self.tempo_estocada - duracao_total // 2) / (duracao_total // 2)
            
            # Posição orbital exata de onde saiu
            pos_orbital_original = [
                self.jogador.pos[0] + math.cos(self.angulo_retorno) * self.distancia,
                self.jogador.pos[1] + math.sin(self.angulo_retorno) * self.distancia
            ]
            
            self.pos_atual[0] = self.pos_alvo[0] + (pos_orbital_original[0] - self.pos_alvo[0]) * progresso
            self.pos_atual[1] = self.pos_alvo[1] + (pos_orbital_original[1] - self.pos_alvo[1]) * progresso
        else:
            # Finalizar estocada - retomar rotação normal
            self.em_estocada = False
            self.alvo_estocada = None
            self.brilho_intensidade = 1.0
            # Continuar rotação de onde parou
            self.angulo_atual = self.angulo_retorno
    
    def colidir_com_inimigo(self, inimigo):
        """Verifica colisão com inimigo"""
        if not inimigo.ativo:
            return False
            
        distancia = calcular_distancia(self.pos_atual, inimigo.pos)
        if distancia < self.tamanho + inimigo.raio:
            inimigo.receber_dano(self.dano)
            self.gerar_particulas_corte(inimigo.pos)
            return True
        return False
    
    def desenhar(self, tela, camera):
        """Desenha espada menor e mais simples"""
        pos_tela = posicao_na_tela(self.pos_atual, camera)
        
        if esta_na_tela(self.pos_atual, camera):
            # Trilha mais sutil
            for i, ponto in enumerate(self.trilha):
                vida_prop = ponto['vida'] / ponto['vida_max']
                pos_trilha = posicao_na_tela(ponto['pos'], camera)
                alpha = vida_prop * 0.2
                tamanho_trilha = int(self.tamanho * vida_prop * 0.3)
                
                if tamanho_trilha > 0:
                    cor_trilha = tuple(max(0, min(255, int(c * alpha))) for c in (150, 150, 180))
                    pygame.draw.circle(tela, cor_trilha, (int(pos_trilha[0]), int(pos_trilha[1])), tamanho_trilha)
            
            # Espada menor e mais simples
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
            
            # Espada menor
            comprimento = self.tamanho * 2.5  # Menor
            largura_base = self.tamanho // 4
            comprimento_cabo = self.tamanho // 3
            
            # Desenhar espada simples
            ponta_x = pos_tela[0] + math.cos(angulo_espada) * comprimento
            ponta_y = pos_tela[1] + math.sin(angulo_espada) * comprimento
            
            base_x = pos_tela[0] - math.cos(angulo_espada) * comprimento_cabo
            base_y = pos_tela[1] - math.sin(angulo_espada) * comprimento_cabo
            
            # Linha principal da espada
            pygame.draw.line(tela, cor_base, (int(pos_tela[0]), int(pos_tela[1])), 
                           (int(ponta_x), int(ponta_y)), 3)
            
            # Cabo
            pygame.draw.line(tela, (101, 67, 33), (int(pos_tela[0]), int(pos_tela[1])), 
                           (int(base_x), int(base_y)), 5)
            
            # Partículas pequenas
            for particula in self.particulas_corte:
                vida_prop = particula['vida'] / particula['vida_max']
                part_pos = posicao_na_tela([particula['x'], particula['y']], camera)
                cor_part = tuple(max(0, min(255, int(c * vida_prop))) for c in (255, 255, 150))
                tamanho_part = max(1, int(1.5 * vida_prop))
                pygame.draw.circle(tela, cor_part, (int(part_pos[0]), int(part_pos[1])), tamanho_part)

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
        
        # Direção do movimento
        self.direcao_movimento = [0, -1]  # Padrão: para cima
        self.ultima_direcao_valida = [0, -1]  # Última direção válida para bombas
        
        # Estados visuais e animação
        self.cor = AZUL_CLARO
        
        # Stats base
        self.vida_infinita = False  # Cheat de vida infinita
        
    def mover(self, keys):
        dx, dy = 0, 0
        
        # Capturar direção do teclado
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1
        
        # Normalizar movimento diagonal
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707
        
        # Atualizar direção do movimento
        if dx != 0 or dy != 0:
            self.direcao_movimento = [dx, dy]
            self.ultima_direcao_valida = [dx, dy]
        
        # Aplicar movimento
        nova_pos = [
            self.pos[0] + dx * self.velocidade,
            self.pos[1] + dy * self.velocidade
        ]
        
        # Limitar aos bordos do mapa
        self.pos = limitar_posicao(nova_pos)
    
    def pode_atirar(self):
        return pygame.time.get_ticks() - self.ultimo_tiro > self.cooldown_tiro
    
    def atirar(self):
        self.ultimo_tiro = pygame.time.get_ticks()
    
    def receber_dano(self, dano):
        """Aplica dano ao jogador, considerando vida infinita"""
        if self.vida_infinita:
            return False  # Não recebe dano se vida infinita está ativa
        
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
        """Desenha o jogador na tela"""
        # Posição na tela (considerando a câmera)
        pos_tela = [self.pos[0] - camera[0], self.pos[1] - camera[1]]
        
        # Desenhar raio de coleta se tiver upgrade
        if self.coleta_nivel > 0:
            cor_coleta = (0, 255, 0, 50)  # Verde transparente
            pygame.draw.circle(tela, (0, 100, 0), (int(pos_tela[0]), int(pos_tela[1])), self.raio_coleta, 1)
        
        # Desenhar escudo se ativo
        if self.escudo_ativo:
            raio_escudo = self.raio + 15 + (self.escudo_nivel * 3)
            pygame.draw.circle(tela, (0, 255, 255), (int(pos_tela[0]), int(pos_tela[1])), raio_escudo, 3)
        
        # Desenhar quadrado do jogador com cor baseada no estado
        if self.invulneravel and (pygame.time.get_ticks() // 100) % 2:
            cor = CINZA
        elif self.dash_ativo:
            cor = (255, 255, 0)  # Amarelo durante dash
        else:
            cor = BRANCO
        
        pygame.draw.rect(tela, cor, 
                        (pos_tela[0] - self.raio, pos_tela[1] - self.raio, 
                         self.raio * 2, self.raio * 2))
        
        # Se invulnerável, desenhar efeito de brilho
        if self.invulneravel:
            # Brilho pulsante
            alpha = int(128 + 128 * math.sin(pygame.time.get_ticks() * 0.01))
            brilho = pygame.Surface((self.raio * 2 + 4, self.raio * 2 + 4))
            brilho.set_alpha(alpha)
            brilho.fill(DOURADO)
            tela.blit(brilho, (pos_tela[0] - self.raio - 2, pos_tela[1] - self.raio - 2))
        
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
                'pos': list(self.pos),
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
                'pos': list(self.pos),
                'forca': forca_campo,
                'raio': raio_campo,
                'duracao': 3000 + (self.campo_nivel * 500)  # 3s até 5.5s
            }
        return None
    
    def atualizar_habilidades(self):
        """Atualiza estados das habilidades especiais"""
        tempo_atual = pygame.time.get_ticks()
        
        # Atualizar escudo
        if self.escudo_ativo and tempo_atual > self.escudo_duracao:
            self.escudo_ativo = False
    
    def atualizar_espadas(self, inimigos):
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
            espada.atualizar(inimigos)
    
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
                    'pos_inicial': list(self.pos),  # Para animação de arco
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
            # Campo sempre ativo
            if self.campo_nivel >= 5:
                # Nível lendário: mais dano e área maior
                dano_campo = 3  # Dano base maior
                forca_campo = 2  # Força de atração maior
                raio_campo = 150  # Área maior
            else:
                # Níveis normais: apenas atração
                dano_campo = 1 + (self.campo_nivel * 0.3)  # Dano menor
                forca_campo = 1 + (self.campo_nivel * 0.2)  # Força de atração moderada
                raio_campo = 80 + (self.campo_nivel * 15)  # Raio cresce moderadamente
            
            return {
                'pos': list(self.pos),
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