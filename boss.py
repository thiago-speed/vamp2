import pygame
import math
import random
from config import *
from utils import *

class Boss:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.raio = 60  # Boss é grande
        self.hp_max = 3000  # Vida alta para ser desafiador
        self.hp = self.hp_max
        self.velocidade = 1.5
        self.dano = 30
        self.ativo = True
        self.cor = ROXO
        
        # Sistema de fases baseado na vida
        self.fase_atual = 1  # Fases 1, 2, 3
        self.cores_fase = [(128, 0, 128), (255, 0, 0), (255, 100, 0)]  # Roxo, Vermelho, Laranja
        
        # Sistema de ataques
        self.ultimo_ataque = 0
        self.intervalo_ataque = 2000  # 2 segundos entre ataques
        self.ultimo_ataque_basico = 0
        self.intervalo_ataque_basico = 800  # 0.8 segundos para ataque básico
        self.executando_ataque = False
        self.executando_ataque_basico = False
        self.tipo_ataque_atual = 0
        self.tempo_ataque = 0
        self.tempo_ataque_basico = 0
        
        # Lista de ataques por fase
        self.ataques_fase1 = ["Rajada Laser", "Meteoros", "Espinhos Rotativos"]
        self.ataques_fase2 = ["Laser Varredor", "Explosao Infernal", "Teleporte Ataque"]
        self.ataques_fase3 = ["Apocalipse", "Vortice Mortal", "Furia Final"]
        
        # Efeitos visuais
        self.particulas = []
        self.aura_intensidade = 0
        self.shake_intensidade = 0  # Garantir que começa como inteiro
        self.tremor_tela = 0
        self.brilho_ataque = 0
        
        # Estados especiais
        self.teleportando = False
        self.tempo_teleporte = 0
        self.pos_teleporte = None
        self.invulneravel = False
        self.tempo_invulneravel = 0
        
        # Counters para ataques especiais
        self.meteoros_restantes = 0
        self.angulo_varredor = 0
        self.espinhos_angulo = 0
        
        # Efeitos de câmera
        self.flash_tela = 0
        
        # Sistema de indicadores de ataque
        self.indicadores = []  # Lista de dicionários com pos, tempo, tipo
        self.tempo_aviso = 1000  # 1 segundo de aviso

    def determinar_fase(self):
        """Determina a fase atual baseada na vida"""
        porcentagem_vida = self.hp / self.hp_max
        if porcentagem_vida > 0.66:
            return 1
        elif porcentagem_vida > 0.33:
            return 2
        else:
            return 3

    def obter_ataques_disponiveis(self):
        """Retorna lista de ataques baseada na fase"""
        fase = self.determinar_fase()
        if fase == 1:
            return self.ataques_fase1
        elif fase == 2:
            return self.ataques_fase2
        else:
            return self.ataques_fase3
    
    def atualizar(self, jogador_pos):
        if not self.ativo:
            return []
        
        projéteis_criados = []
        tempo_atual = pygame.time.get_ticks()
        
        # Atualizar fase
        fase_anterior = self.fase_atual
        self.fase_atual = self.determinar_fase()
        
        # Transição de fase - ficar invulnerável momentaneamente
        if fase_anterior != self.fase_atual:
            self.invulneravel = True
            self.tempo_invulneravel = tempo_atual + 2000  # 2 segundos
            self.shake_intensidade = 20
            self.flash_tela = 255
            # Limpar ataques em andamento
            self.executando_ataque = False
            self.executando_ataque_basico = False
            
        # Atualizar invulnerabilidade
        if self.invulneravel and tempo_atual > self.tempo_invulneravel:
            self.invulneravel = False
        
        # Atualizar efeitos visuais
        self.atualizar_efeitos()
        
        # Teleporte
        if self.teleportando:
            if tempo_atual > self.tempo_teleporte:
                if self.pos_teleporte:
                    self.pos = list(self.pos_teleporte)
                    self.pos_teleporte = None
                self.teleportando = False
                self.shake_intensidade = 10
                # Garantir que o boss ataque logo após teleportar
                self.ultimo_ataque = tempo_atual - self.intervalo_ataque
        
        # Lógica de movimento (quando não atacando e não teleportando)
        if not self.executando_ataque and not self.teleportando:
            # Movimento mais agressivo nas fases avançadas
            velocidade_atual = self.velocidade * (1 + self.fase_atual * 0.5)
            
            dx = jogador_pos[0] - self.pos[0]
            dy = jogador_pos[1] - self.pos[1]
            
            if dx != 0 or dy != 0:
                dir_x, dir_y = normalizar_vetor(dx, dy)
                self.pos[0] += dir_x * velocidade_atual
                self.pos[1] += dir_y * velocidade_atual
        
        # Sistema de ataques melhorado
        # 1. Ataque básico (sempre ativo quando não invulnerável)
        if not self.invulneravel and tempo_atual - self.ultimo_ataque_basico > self.intervalo_ataque_basico:
            projéteis_básicos = self.ataque_basico(jogador_pos)
            if projéteis_básicos:
                projéteis_criados.extend(projéteis_básicos)
                self.ultimo_ataque_basico = tempo_atual
                self.brilho_ataque = 50  # Brilho menor para ataques básicos
        
        # 2. Ataques especiais
        if not self.executando_ataque and not self.teleportando and not self.invulneravel:
            # Intervalo menor conforme a fase avança
            intervalo_atual = max(2000, self.intervalo_ataque - (self.fase_atual * 500))
            if tempo_atual - self.ultimo_ataque > intervalo_atual:
                self.iniciar_ataque(jogador_pos)
        
        # Executar ataque especial atual
        if self.executando_ataque:
            projéteis_especiais = self.executar_ataque(jogador_pos)
            if projéteis_especiais:
                projéteis_criados.extend(projéteis_especiais)
                self.brilho_ataque = 150  # Brilho intenso para ataques especiais
        
        # Limitar posição ao mapa
        self.pos = list(limitar_posicao(self.pos))
        
        return projéteis_criados
    
    def atualizar_efeitos(self):
        """Atualiza efeitos visuais"""
        # Aura pulsante baseada na fase
        tempo_atual = pygame.time.get_ticks()
        self.aura_intensidade = 50 + 30 * self.fase_atual + 20 * math.sin(tempo_atual * 0.005)
        
        # Diminuir shake e flash
        if self.shake_intensidade > 0:
            self.shake_intensidade = max(0, int(self.shake_intensidade - 0.5))  # Converter para inteiro
        if self.flash_tela > 0:
            self.flash_tela = max(0, self.flash_tela - 15)
        if self.brilho_ataque > 0:
            self.brilho_ataque = max(0, self.brilho_ataque - 8)
        
        # Atualizar partículas existentes
        for particula in self.particulas[:]:
            particula['vida'] -= 1
            
            # Movimento mais complexo
            if 'velocidade_x' in particula:
                particula['pos'][0] += particula['velocidade_x']
                particula['pos'][1] += particula['velocidade_y']
                # Desaceleração
                particula['velocidade_x'] *= 0.95
                particula['velocidade_y'] *= 0.95
            else:
                # Movimento padrão para partículas antigas
                particula['pos'][1] -= particula['velocidade']
            
            # Efeito de rotação na aura
            if random.random() < 0.1:
                angulo = random.uniform(0, 2 * math.pi)
                dist = random.uniform(5, 15)
                particula['pos'][0] += math.cos(angulo) * dist
                particula['pos'][1] += math.sin(angulo) * dist
            
            if particula['vida'] <= 0:
                self.particulas.remove(particula)
        
        # Gerar novas partículas da aura
        num_particulas_base = 20 + self.fase_atual * 5
        if len(self.particulas) < num_particulas_base:
            # Partículas em volta do boss
            angulo = random.uniform(0, 2 * math.pi)
            raio = random.uniform(self.raio, self.raio + 40)
            
            # Chance de criar partícula especial
            if random.random() < 0.3:  # 30% de chance
                velocidade = random.uniform(3, 6)
                self.particulas.append({
                    'pos': [
                        self.pos[0] + math.cos(angulo) * raio,
                        self.pos[1] + math.sin(angulo) * raio
                    ],
                    'velocidade_x': math.cos(angulo) * velocidade,
                    'velocidade_y': math.sin(angulo) * velocidade,
                    'vida': random.randint(40, 80),
                    'cor': self.cores_fase[self.fase_atual - 1]
                })
            else:
                # Partícula normal
                self.particulas.append({
                    'pos': [
                        self.pos[0] + math.cos(angulo) * raio,
                        self.pos[1] + math.sin(angulo) * raio
                    ],
                    'velocidade': random.uniform(0.5, 2),
                    'vida': random.randint(30, 60),
                    'cor': self.cores_fase[self.fase_atual - 1]
                })
            
        # Efeitos especiais durante ataques
        if self.executando_ataque:
            # Partículas extras durante ataques
            if random.random() < 0.3:  # 30% de chance por frame
                angulo = random.uniform(0, 2 * math.pi)
                dist = self.raio + 20
                velocidade = random.uniform(4, 8)
                self.particulas.append({
                    'pos': [
                        self.pos[0] + math.cos(angulo) * dist,
                        self.pos[1] + math.sin(angulo) * dist
                    ],
                    'velocidade_x': math.cos(angulo) * velocidade,
                    'velocidade_y': math.sin(angulo) * velocidade,
                    'vida': random.randint(20, 40),
                    'cor': self.cores_fase[self.fase_atual - 1]
                })

    def iniciar_ataque(self, jogador_pos):
        """Inicia um ataque baseado na fase atual"""
        if self.invulneravel:
            return
            
        self.executando_ataque = True
        self.tempo_ataque = pygame.time.get_ticks()
        self.ultimo_ataque = pygame.time.get_ticks()
        
        ataques_disponiveis = self.obter_ataques_disponiveis()
        self.tipo_ataque_atual = random.randint(0, len(ataques_disponiveis) - 1)
        ataque_nome = ataques_disponiveis[self.tipo_ataque_atual]
        
        # Preparações específicas por ataque
        if ataque_nome == "Meteoros":
            self.meteoros_restantes = 8 + self.fase_atual * 2
            self.shake_intensidade = 15  # Shake forte para meteoros
            self.flash_tela = 200  # Flash intenso
            # Pré-calcular posições dos meteoros e adicionar indicadores
            self.pre_calcular_posicoes_meteoros(jogador_pos)
        elif ataque_nome == "Laser Varredor":
            self.angulo_varredor = 0
            self.shake_intensidade = 10
            self.flash_tela = 150
        elif ataque_nome == "Espinhos Rotativos":
            self.espinhos_angulo = 0
            self.shake_intensidade = 8
            self.flash_tela = 100
        elif ataque_nome == "Teleporte Ataque":
            self.iniciar_teleporte(jogador_pos)
            self.shake_intensidade = 20
            self.flash_tela = 255
        elif ataque_nome == "Apocalipse":
            self.shake_intensidade = 25  # Shake muito forte
            self.flash_tela = 255  # Flash máximo
            # Pré-calcular posições do apocalipse
            self.pre_calcular_posicoes_apocalipse()
        elif ataque_nome == "Vortice Mortal":
            self.shake_intensidade = 15
            self.flash_tela = 180
        elif ataque_nome == "Furia Final":
            self.shake_intensidade = 30  # Shake extremo
            self.flash_tela = 255  # Flash máximo
            # Pré-calcular posições da fúria final
            self.pre_calcular_posicoes_furia_final(jogador_pos)
        else:  # Ataques padrão
            self.shake_intensidade = 10
            self.flash_tela = 150
        
        # Efeitos visuais ao iniciar ataque
        self.brilho_ataque = 255  # Brilho máximo ao iniciar qualquer ataque
        
        # Gerar partículas extras para o início do ataque
        num_particulas = 20 + self.fase_atual * 10
        for _ in range(num_particulas):
            angulo = random.uniform(0, 2 * math.pi)
            velocidade = random.uniform(2, 5)
            self.particulas.append({
                'pos': list(self.pos),
                'velocidade_x': math.cos(angulo) * velocidade,
                'velocidade_y': math.sin(angulo) * velocidade,
                'vida': random.randint(30, 60),
                'cor': self.cores_fase[self.fase_atual - 1]
            })

    def iniciar_teleporte(self, jogador_pos):
        """Inicia sequência de teleporte"""
        self.teleportando = True
        self.tempo_teleporte = pygame.time.get_ticks() + 1000  # 1 segundo
        
        # Teleportar para posição estratégica
        angulo = random.uniform(0, 2 * math.pi)
        distancia = 200 + random.randint(-50, 50)
        self.pos_teleporte = [
            jogador_pos[0] + math.cos(angulo) * distancia,
            jogador_pos[1] + math.sin(angulo) * distancia
        ]
        
        # Garantir que está dentro do mapa
        self.pos_teleporte = list(limitar_posicao(self.pos_teleporte))
        
    def executar_ataque(self, jogador_pos):
        """Executa o ataque atual com base na fase"""
        tempo_atual = pygame.time.get_ticks()
        tempo_decorrido = tempo_atual - self.tempo_ataque
        ataques_disponiveis = self.obter_ataques_disponiveis()
        
        # Verificação de segurança
        if self.tipo_ataque_atual >= len(ataques_disponiveis):
            self.tipo_ataque_atual = 0
            
        ataque = ataques_disponiveis[self.tipo_ataque_atual]
        projéteis = []
        
        # Executar ataque específico
        try:
            if ataque == "Rajada Laser":
                projéteis = self.ataque_rajada_laser(jogador_pos, tempo_decorrido)
            elif ataque == "Meteoros":
                projéteis = self.ataque_meteoros(jogador_pos, tempo_decorrido)
            elif ataque == "Espinhos Rotativos":
                projéteis = self.ataque_espinhos_rotativos(tempo_decorrido)
            elif ataque == "Laser Varredor":
                projéteis = self.ataque_laser_varredor(tempo_decorrido)
            elif ataque == "Explosao Infernal":
                projéteis = self.ataque_explosao_infernal(jogador_pos, tempo_decorrido)
            elif ataque == "Teleporte Ataque":
                projéteis = self.ataque_teleporte(jogador_pos, tempo_decorrido)
            elif ataque == "Apocalipse":
                projéteis = self.ataque_apocalipse(jogador_pos, tempo_decorrido)
            elif ataque == "Vortice Mortal":
                projéteis = self.ataque_vortice_mortal(tempo_decorrido)
            elif ataque == "Furia Final":
                projéteis = self.ataque_furia_final(jogador_pos, tempo_decorrido)
            
            # Efeitos visuais durante o ataque
            if projéteis:
                self.brilho_ataque = max(50, self.brilho_ataque)
                if len(projéteis) > 3:  # Ataques grandes
                    self.shake_intensidade = max(5, self.shake_intensidade)
                
                # Flash na tela para ataques grandes
                if ataque in ["Apocalipse", "Furia Final", "Meteoros"]:
                    self.flash_tela = max(100, self.flash_tela)
                
        except Exception as e:
            print(f"Erro no ataque {ataque}: {e}")
            self.executando_ataque = False
            return []
        
        # Verificar se o ataque terminou
        duracao_base = 3000  # 3 segundos base
        duracao_por_fase = 1000  # +1 segundo por fase
        duracao_ataque = duracao_base + (self.fase_atual * duracao_por_fase)
        
        # Alguns ataques duram mais
        if ataque in ["Apocalipse", "Furia Final"]:
            duracao_ataque *= 1.5
        
        if tempo_decorrido > duracao_ataque:
            self.executando_ataque = False
            self.meteoros_restantes = 0
            self.angulo_varredor = 0
            self.espinhos_angulo = 0
            # Garantir que o próximo ataque não demore muito
            self.ultimo_ataque = tempo_atual - (self.intervalo_ataque // 2)
        
        return projéteis if projéteis else []

    def ataque_basico(self, jogador_pos):
        """Ataque básico que o boss sempre executa - agora com múltiplos projéteis em padrão"""
        projéteis = []
        
        # Padrão em espiral
        num_projeteis = 3 + self.fase_atual  # Mais projéteis por fase
        angulo_base = math.atan2(jogador_pos[1] - self.pos[1], jogador_pos[0] - self.pos[0])
        
        for i in range(num_projeteis):
            angulo = angulo_base + (i * 2 * math.pi / num_projeteis)
            dir_x = math.cos(angulo)
            dir_y = math.sin(angulo)
            
            # Posição inicial ligeiramente à frente do boss
            origem_x = self.pos[0] + dir_x * (self.raio + 10)
            origem_y = self.pos[1] + dir_y * (self.raio + 10)
            
            # Alvo com padrão em espiral
            alvo_x = origem_x + dir_x * 400
            alvo_y = origem_y + dir_y * 400
            
            projéteis.append(ProjetilBoss(
                origem_x, origem_y, alvo_x, alvo_y,
                self.dano // 2, 10, 500, "basico"  # Mais rápido e maior alcance
            ))
        
        return projéteis

    def ataque_rajada_laser(self, jogador_pos, tempo):
        """Múltiplos lasers em padrões complexos"""
        projéteis = []
        if tempo % 150 == 0 and tempo < 3000:  # Mais frequente
            # Padrão em leque duplo
            num_lasers = 5  # Número de lasers por leque
            angulo_base = math.atan2(jogador_pos[1] - self.pos[1], jogador_pos[0] - self.pos[0])
            
            for espelho in [-1, 1]:  # Dois leques simétricos
                for i in range(num_lasers):
                    angulo_offset = espelho * (i - num_lasers/2) * 0.2
                    angulo = angulo_base + angulo_offset
                    
                    alvo_x = self.pos[0] + math.cos(angulo) * 500
                    alvo_y = self.pos[1] + math.sin(angulo) * 500
                    
                    projéteis.append(ProjetilBoss(
                        self.pos[0], self.pos[1], alvo_x, alvo_y,
                        self.dano, 15, 600, "laser_rapido"  # Mais rápido
                    ))
            
            # Adicionar lasers giratórios
            if tempo % 450 == 0:  # A cada 450ms
                for i in range(8):
                    angulo_rot = (2 * math.pi * i / 8) + (tempo * 0.001)
                    alvo_x = self.pos[0] + math.cos(angulo_rot) * 400
                    alvo_y = self.pos[1] + math.sin(angulo_rot) * 400
                    
                    projéteis.append(ProjetilBoss(
                        self.pos[0], self.pos[1], alvo_x, alvo_y,
                        self.dano, 12, 500, "laser_rapido"
                    ))
        
        return projéteis

    def ataque_meteoros(self, jogador_pos, tempo):
        """Meteoros em padrões mais complexos"""
        projéteis = []
        if tempo % 200 == 0 and self.meteoros_restantes > 0:  # Mais rápido
            self.meteoros_restantes -= 1
            
            # Padrão em grade menor (2x2 em vez de 3x3)
            grid_size = 2
            spacing = 120
            
            for i in range(grid_size):
                for j in range(grid_size):
                    # Posição alvo em grade
                    alvo_x = jogador_pos[0] + (i - grid_size/2) * spacing
                    alvo_y = jogador_pos[1] + (j - grid_size/2) * spacing
                    
                    # Adicionar indicador
                    self.adicionar_indicador((alvo_x, alvo_y), "Meteoro")
                    
                    # Origem aleatória acima da tela
                    origem_x = alvo_x + random.randint(-50, 50)
                    origem_y = alvo_y - 400
                    
                    projéteis.append(ProjetilBoss(
                        origem_x, origem_y, alvo_x, alvo_y,
                        self.dano + 8, 8, 600, "meteoro"  # Velocidade reduzida
                    ))
            
            # Meteoros extras em círculo (reduzido de 8 para 6)
            if tempo % 600 == 0:
                num_extras = 6
                raio = 200
                for i in range(num_extras):
                    angulo = (2 * math.pi * i / num_extras)
                    alvo_x = jogador_pos[0] + math.cos(angulo) * raio
                    alvo_y = jogador_pos[1] + math.sin(angulo) * raio
                    
                    self.adicionar_indicador((alvo_x, alvo_y), "Meteoro")
                    
                    origem_x = alvo_x
                    origem_y = alvo_y - 400
                    
                    projéteis.append(ProjetilBoss(
                        origem_x, origem_y, alvo_x, alvo_y,
                        self.dano + 10, 10, 600, "meteoro"
                    ))
        
        return projéteis

    def ataque_espinhos_rotativos(self, tempo):
        """Espinhos em padrões mais complexos e densos"""
        projéteis = []
        if tempo % 100 == 0 and tempo < 3000:  # Mais frequente
            # Múltiplas camadas de espinhos
            num_camadas = 3
            espinhos_por_camada = 12
            
            for camada in range(num_camadas):
                raio_base = 100 + camada * 50
                velocidade_base = 8 - camada  # Camadas externas mais lentas
                
                # Rotação alternada por camada
                rotacao = self.espinhos_angulo * (-1 if camada % 2 == 0 else 1)
                
                for i in range(espinhos_por_camada):
                    angulo = (2 * math.pi * i / espinhos_por_camada) + rotacao
                    
                    # Posição inicial
                    x = self.pos[0] + math.cos(angulo) * raio_base
                    y = self.pos[1] + math.sin(angulo) * raio_base
                    
                    # Direção do movimento
                    alvo_x = x + math.cos(angulo) * 300
                    alvo_y = y + math.sin(angulo) * 300
                    
                    projéteis.append(ProjetilBoss(
                        x, y, alvo_x, alvo_y,
                        self.dano, velocidade_base, 400, "espinho_rotativo"
                    ))
            
            self.espinhos_angulo += 0.8  # Rotação mais rápida
        
        return projéteis

    def ataque_laser_varredor(self, tempo):
        """Laser que varre a área em múltiplos padrões"""
        projéteis = []
        if tempo % 100 == 0 and tempo < 4000:  # Mais frequente
            # Padrão em cruz giratória
            self.angulo_varredor += 0.3  # Giro mais rápido
            
            # Cruz principal
            for i in range(4):
                angulo_base = self.angulo_varredor + (i * math.pi / 2)
                
                # Cada braço da cruz tem 3 lasers
                for j in range(3):
                    offset = (j - 1) * 0.2
                    angulo = angulo_base + offset
                    
                    alvo_x = self.pos[0] + math.cos(angulo) * 500
                    alvo_y = self.pos[1] + math.sin(angulo) * 500
                    
                    projéteis.append(ProjetilBoss(
                        self.pos[0], self.pos[1], alvo_x, alvo_y,
                        self.dano + 5, 18, 600, "laser_varredor"
                    ))
            
            # Padrão em espiral adicional
            if tempo % 300 == 0:  # A cada 300ms
                num_espiral = 8
                for i in range(num_espiral):
                    angulo = self.angulo_varredor + (i * 2 * math.pi / num_espiral)
                    alvo_x = self.pos[0] + math.cos(angulo) * 400
                    alvo_y = self.pos[1] + math.sin(angulo) * 400
                    
                    projéteis.append(ProjetilBoss(
                        self.pos[0], self.pos[1], alvo_x, alvo_y,
                        self.dano + 3, 15, 500, "laser_varredor"
                    ))
        
        return projéteis
    
    def ataque_explosao_infernal(self, jogador_pos, tempo):
        """Múltiplas explosões em padrões complexos"""
        projéteis = []
        if tempo % 300 == 0 and tempo < 3000:
            # Padrão em onda expansiva (reduzido de 8 para 6 por anel)
            num_aneis = 3
            explosoes_por_anel = 6
            
            for anel in range(num_aneis):
                raio = 100 + anel * 80
                offset_angulo = tempo * 0.001 + anel * (math.pi / num_aneis)
                
                for i in range(explosoes_por_anel):
                    angulo = offset_angulo + (i * 2 * math.pi / explosoes_por_anel)
                    x = self.pos[0] + math.cos(angulo) * raio
                    y = self.pos[1] + math.sin(angulo) * raio
                    
                    self.adicionar_indicador((x, y), "Explosao Infernal")
                    
                    projéteis.append(ProjetilBoss(
                        x, y, x, y,
                        self.dano + 10, 0, 100, "explosao"
                    ))
            
            # Explosões perseguidoras (reduzido de 4 para 3)
            if tempo % 900 == 0:
                num_perseguidoras = 3
                for _ in range(num_perseguidoras):
                    dx = jogador_pos[0] - self.pos[0]
                    dy = jogador_pos[1] - self.pos[1]
                    dist = math.sqrt(dx*dx + dy*dy)
                    
                    if dist > 0:
                        for j in range(3):
                            fator = (j + 1) / 4
                            x = self.pos[0] + dx * fator
                            y = self.pos[1] + dy * fator
                            
                            self.adicionar_indicador((x, y), "Explosao Infernal")
                            
                            projéteis.append(ProjetilBoss(
                                x, y, x, y,
                                self.dano + 15, 0, 120, "explosao"
                            ))
        
        return projéteis

    def ataque_teleporte(self, jogador_pos, tempo):
        """Ataque após teleporte com padrões mais complexos"""
        if not self.teleportando and tempo > 1500 and tempo < 1800:
            projéteis = []
            
            # Ondas concêntricas
            num_ondas = 3
            projeteis_por_onda = 16
            
            for onda in range(num_ondas):
                velocidade = 12 - onda * 2  # Ondas mais externas são mais lentas
                for i in range(projeteis_por_onda):
                    angulo = (2 * math.pi * i / projeteis_por_onda) + (onda * math.pi / num_ondas)
                    
                    # Posição inicial em espiral
                    raio_inicial = 50 + onda * 30
                    x = self.pos[0] + math.cos(angulo) * raio_inicial
                    y = self.pos[1] + math.sin(angulo) * raio_inicial
                    
                    # Alvo em espiral expandindo
                    raio_alvo = 200 + onda * 50
                    alvo_x = self.pos[0] + math.cos(angulo) * raio_alvo
                    alvo_y = self.pos[1] + math.sin(angulo) * raio_alvo
                    
                    projéteis.append(ProjetilBoss(
                        x, y, alvo_x, alvo_y,
                        self.dano + 8, velocidade, 400, "onda_teleporte"
                    ))
            
            # Projéteis direcionados ao jogador
            num_direcionados = 5
            for i in range(num_direcionados):
                offset = (i - num_direcionados/2) * 0.2
                dx = jogador_pos[0] - self.pos[0]
                dy = jogador_pos[1] - self.pos[1]
                angulo = math.atan2(dy, dx) + offset
                
                alvo_x = self.pos[0] + math.cos(angulo) * 300
                alvo_y = self.pos[1] + math.sin(angulo) * 300
                
                projéteis.append(ProjetilBoss(
                    self.pos[0], self.pos[1], alvo_x, alvo_y,
                    self.dano + 10, 15, 400, "onda_teleporte"
                ))
            
            return projéteis
        return []
    
    def ataque_apocalipse(self, jogador_pos, tempo):
        """Ataque devastador em toda a área com múltiplos padrões sobrepostos"""
        projéteis = []
        if tempo % 150 == 0 and tempo < 5000:
            # Ondas concêntricas expansivas (reduzido de 16 para 12 projéteis)
            num_ondas = 3
            projeteis_por_onda = 12
            
            for onda in range(num_ondas):
                raio = 100 + onda * 60 + (tempo * 0.1)
                offset_angulo = tempo * 0.002 + onda * (math.pi / num_ondas)
                
                for i in range(projeteis_por_onda):
                    angulo = offset_angulo + (i * 2 * math.pi / projeteis_por_onda)
                    x = self.pos[0] + math.cos(angulo) * raio
                    y = self.pos[1] + math.sin(angulo) * raio
                    
                    self.adicionar_indicador((x, y), "Apocalipse")
                    
                    projéteis.append(ProjetilBoss(
                        x, y, x, y,
                        self.dano + 12, 0, 120, "apocalipse"
                    ))
            
            # Padrão em grade (reduzido de 5x5 para 3x3)
            if tempo % 450 == 0:
                grid_size = 3
                spacing = 150
                for i in range(-grid_size//2, grid_size//2 + 1):
                    for j in range(-grid_size//2, grid_size//2 + 1):
                        x = self.pos[0] + i * spacing
                        y = self.pos[1] + j * spacing
                        
                        self.adicionar_indicador((x, y), "Apocalipse")
                        
                        projéteis.append(ProjetilBoss(
                            x, y, x, y,
                            self.dano + 15, 0, 150, "apocalipse"
                        ))
        
        return projéteis

    def ataque_vortice_mortal(self, tempo):
        """Vórtice com múltiplos padrões de projéteis"""
        projéteis = []
        if tempo % 80 == 0 and tempo < 4000:  # Mais frequente
            # Espiral principal
            num_bracos = 4
            projeteis_por_braco = 6
            
            for braco in range(num_bracos):
                angulo_base = (tempo * 0.003) + (braco * 2 * math.pi / num_bracos)
                
                for i in range(projeteis_por_braco):
                    distancia = 50 + i * 40
                    angulo = angulo_base + (i * 0.2)
                    
                    x = self.pos[0] + math.cos(angulo) * distancia
                    y = self.pos[1] + math.sin(angulo) * distancia
                    
                    # Calcular posição final estimada
                    angulo_final = angulo + math.pi  # Meio giro
                    pos_final_x = x + math.cos(angulo_final) * 200
                    pos_final_y = y + math.sin(angulo_final) * 200
                    
                    # Adicionar indicador na posição final estimada
                    if tempo % 1000 == 0:  # Mostrar indicador a cada segundo
                        self.adicionar_indicador((pos_final_x, pos_final_y), "Vortice Mortal", 1000)
                    
                    # Movimento em espiral
                    vel_x = -math.cos(angulo + math.pi/2) * 4
                    vel_y = -math.sin(angulo + math.pi/2) * 4
                    
                    projéteis.append(ProjetilBoss(
                        x, y, x + vel_x * 50, y + vel_y * 50,
                        self.dano + 8, 5, 400, "vortice"
                    ))
            
            # Anéis que se contraem
            if tempo % 240 == 0:  # A cada 240ms
                num_aneis = 2
                projeteis_por_anel = 12
                
                for anel in range(num_aneis):
                    raio = 300 - anel * 100
                    for i in range(projeteis_por_anel):
                        angulo = (2 * math.pi * i / projeteis_por_anel) + (tempo * 0.001)
                        x = self.pos[0] + math.cos(angulo) * raio
                        y = self.pos[1] + math.sin(angulo) * raio
                        
                        # Indicador no centro, onde os projéteis vão convergir
                        if tempo % 1000 == 0:  # Mostrar indicador a cada segundo
                            self.adicionar_indicador(self.pos, "Vortice Mortal", 1000)
                        
                        projéteis.append(ProjetilBoss(
                            x, y, self.pos[0], self.pos[1],
                            self.dano + 6, 6, 400, "vortice"
                        ))
        
        return projéteis

    def ataque_furia_final(self, jogador_pos, tempo):
        """Ataque final absolutamente devastador"""
        projéteis = []
        if tempo % 50 == 0 and tempo < 6000:
            # Padrão em estrela giratória (reduzido de 3 para 2 lasers por ponta)
            num_pontas = 5
            lasers_por_ponta = 2
            
            for i in range(num_pontas):
                angulo_base = (tempo * 0.002) + (i * 2 * math.pi / num_pontas)
                
                for j in range(lasers_por_ponta):
                    offset = (j - lasers_por_ponta/2) * 0.15
                    angulo = angulo_base + offset
                    
                    alvo_x = self.pos[0] + math.cos(angulo) * 600
                    alvo_y = self.pos[1] + math.sin(angulo) * 600
                    
                    self.adicionar_indicador((alvo_x, alvo_y), "Furia Final")
                    
                    projéteis.append(ProjetilBoss(
                        self.pos[0], self.pos[1], alvo_x, alvo_y,
                        self.dano + 15, 20, 700, "furia_laser"  # Velocidade reduzida
                    ))
            
            # Explosões em onda (reduzido de 12 para 8)
            if tempo % 300 == 0:
                num_explosoes = 8
                raio = 150 + math.sin(tempo * 0.001) * 50
                
                for i in range(num_explosoes):
                    angulo = (2 * math.pi * i / num_explosoes) + (tempo * 0.002)
                    x = self.pos[0] + math.cos(angulo) * raio
                    y = self.pos[1] + math.sin(angulo) * raio
                    
                    self.adicionar_indicador((x, y), "Furia Final")
                    
                    projéteis.append(ProjetilBoss(
                        x, y, x, y,
                        self.dano + 12, 0, 100, "furia_explosao"
                    ))
            
            # Ondas de choque (reduzido de 24 para 16 projéteis por onda)
            if tempo % 800 == 0:
                num_ondas = 3
                projeteis_por_onda = 16
                
                for onda in range(num_ondas):
                    raio = 50 + onda * 80
                    for i in range(projeteis_por_onda):
                        angulo = (2 * math.pi * i / projeteis_por_onda)
                        x = self.pos[0] + math.cos(angulo) * raio
                        y = self.pos[1] + math.sin(angulo) * raio
                        
                        # Expandindo para fora
                        alvo_x = self.pos[0] + math.cos(angulo) * (raio + 200)
                        alvo_y = self.pos[1] + math.sin(angulo) * (raio + 200)
                        
                        self.adicionar_indicador((x, y), "Furia Final")
                        
                        projéteis.append(ProjetilBoss(
                            x, y, alvo_x, alvo_y,
                            self.dano + 8, 12, 300, "furia_explosao"  # Velocidade reduzida
                        ))
        
        return projéteis
    
    def receber_dano(self, dano):
        if self.invulneravel:
            return
            
        self.hp -= dano
        
        # Efeitos visuais ao receber dano
        self.shake_intensidade = max(self.shake_intensidade, 3)
        self.brilho_ataque = 50
        
        if self.hp <= 0:
            self.ativo = False
            # Explosão final épica
            self.shake_intensidade = 30
            self.flash_tela = 255
    
    def colidir_com_jogador(self, jogador):
        """Verifica colisão direta com o jogador"""
        if not self.ativo or self.teleportando:
            return False
        
        distancia = calcular_distancia(self.pos, jogador.pos)
        if distancia < self.raio + jogador.raio:
            # Dano baseado na fase
            dano_colisao = self.dano + (self.fase_atual * 5)
            return jogador.receber_dano(dano_colisao)
        
        return False
    
    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        
        # Atualizar e desenhar indicadores primeiro
        self.atualizar_indicadores(pygame.time.get_ticks())
        self.desenhar_indicadores(tela, camera)
        
        pos_tela = posicao_na_tela(self.pos, camera)
        
        if esta_na_tela(self.pos, camera):
            # Aplicar shake da câmera se necessário
            offset_x = random.randint(-self.shake_intensidade, self.shake_intensidade) if self.shake_intensidade > 0 else 0
            offset_y = random.randint(-self.shake_intensidade, self.shake_intensidade) if self.shake_intensidade > 0 else 0
            
            pos_final = (int(pos_tela[0] + offset_x), int(pos_tela[1] + offset_y))
            
            # Desenhar aura baseada na fase
            cor_aura = self.cores_fase[self.fase_atual - 1]
            
            # Aura externa pulsante
            for i in range(4):
                raio_aura = self.raio + 30 + i * 15 + int(self.aura_intensidade * 0.5)
                alpha = max(20 - i * 5, 5)
                
                surf_aura = pygame.Surface((raio_aura * 2, raio_aura * 2))
                surf_aura.set_alpha(alpha)
                surf_aura.fill(cor_aura)
                tela.blit(surf_aura, (pos_final[0] - raio_aura, pos_final[1] - raio_aura))
            
            # Aura interna mais brilhante
            raio_interno = self.raio + 10
            surf_interna = pygame.Surface((raio_interno * 2, raio_interno * 2))
            surf_interna.set_alpha(60)
            surf_interna.fill(cor_aura)
            tela.blit(surf_interna, (pos_final[0] - raio_interno, pos_final[1] - raio_interno))
            
            # Desenhar partículas da aura com efeito de fade
            for particula in self.particulas:
                if esta_na_tela(particula['pos'], camera):
                    pos_part = posicao_na_tela(particula['pos'], camera)
                    vida_prop = particula['vida'] / 60
                    tamanho = int(4 * vida_prop)
                    if tamanho > 0:
                        alpha = int(vida_prop * 255)
                        cor_part = particula['cor']
                        
                        # Partícula principal
                        surf_part = pygame.Surface((tamanho * 2, tamanho * 2))
                        surf_part.set_alpha(alpha)
                        surf_part.fill(cor_part)
                        tela.blit(surf_part, (pos_part[0] - tamanho, pos_part[1] - tamanho))
                        
                        # Brilho central
                        if tamanho > 1:
                            pygame.draw.circle(tela, BRANCO, (int(pos_part[0]), int(pos_part[1])), tamanho // 2)
            
            # Corpo principal do boss
            if self.teleportando:
                # Efeito de teleporte - semi-transparente com distorção
                num_copias = 3
                for i in range(num_copias):
                    offset = int(10 * math.sin(pygame.time.get_ticks() * 0.01 + i * 2))
                    pos_distorcido = (pos_final[0] + offset, pos_final[1] + offset)
                    
                    surf_boss = pygame.Surface((self.raio * 2, self.raio * 2))
                    surf_boss.set_alpha(50)
                    surf_boss.fill(cor_aura)
                    tela.blit(surf_boss, (pos_distorcido[0] - self.raio, pos_distorcido[1] - self.raio))
            else:
                # Boss normal com efeitos
                cor_principal = cor_aura
                if self.brilho_ataque > 0:
                    # Brilho especial durante ataques
                    intensidade = self.brilho_ataque / 255
                    cor_principal = (
                        min(255, cor_aura[0] + int(intensidade * 150)),
                        min(255, cor_aura[1] + int(intensidade * 150)),
                        min(255, cor_aura[2] + int(intensidade * 150))
                    )
                
                # Corpo principal com gradiente
                for i in range(3):
                    raio_atual = self.raio - i * 3
                    cor_atual = (
                        min(255, cor_principal[0] + i * 30),
                        min(255, cor_principal[1] + i * 30),
                        min(255, cor_principal[2] + i * 30)
                    )
                    pygame.draw.circle(tela, cor_atual, pos_final, raio_atual)
                
                # Bordas múltiplas para efeito épico
                for i in range(4):
                    espessura = 3 - i
                    if espessura > 0:
                        cor_borda = (255 - i * 40, 255 - i * 40, 255 - i * 40)
                        pygame.draw.circle(tela, cor_borda, pos_final, self.raio - i * 2, espessura)
                
                # Desenhar símbolo da fase no centro com efeito de brilho
                simbolos = ["Ⅰ", "Ⅱ", "☠"]  # Símbolos romanos para fases 1, 2 e símbolo de morte para fase 3
                simbolo = simbolos[self.fase_atual - 1]
                
                # Sombra do símbolo
                desenhar_texto(tela, simbolo, (pos_final[0] - 12, pos_final[1] - 17), 
                             PRETO, 34, sombra=True)
                # Símbolo principal
                desenhar_texto(tela, simbolo, (pos_final[0] - 10, pos_final[1] - 15), 
                             BRANCO, 30, sombra=True)
            
            # Barra de vida épica
            self.desenhar_barra_vida_epica(tela, pos_tela)
            
            # Indicador de ataque com nome épico
            if self.executando_ataque:
                ataques_disponiveis = self.obter_ataques_disponiveis()
                ataque_nome = ataques_disponiveis[self.tipo_ataque_atual].upper().replace("_", " ")
                
                # Fundo do nome do ataque
                largura_texto = len(ataque_nome) * 12
                altura_texto = 30
                x_texto = pos_final[0] - largura_texto // 2
                y_texto = pos_final[1] - 90
                
                # Fundo semi-transparente
                surf_fundo = pygame.Surface((largura_texto + 20, altura_texto))
                surf_fundo.set_alpha(150)
                surf_fundo.fill(PRETO)
                tela.blit(surf_fundo, (x_texto - 10, y_texto - 5))
                
                # Texto com efeito pulsante
                escala = 1 + 0.1 * math.sin(pygame.time.get_ticks() * 0.01)
                tamanho_fonte = int(22 * escala)
                desenhar_texto(tela, f"💀 {ataque_nome} 💀", 
                             (x_texto, y_texto), 
                             cor_aura, tamanho_fonte, sombra=True)
            
            # Indicador de fase
            fase_texto = f"FASE {self.fase_atual}"
            if self.fase_atual == 3:
                fase_texto += " - FÚRIA FINAL"
            desenhar_texto(tela, fase_texto, (pos_final[0] - 60, pos_final[1] + 70), 
                         cor_aura, 18, sombra=True)
            
            # Flash de tela se necessário
            if self.flash_tela > 0:
                flash_surf = pygame.Surface((tela.get_width(), tela.get_height()))
                flash_surf.set_alpha(self.flash_tela)
                flash_surf.fill(BRANCO)
                tela.blit(flash_surf, (0, 0))

    def desenhar_barra_vida_epica(self, tela, pos_tela):
        """Desenha barra de vida com efeitos épicos"""
        largura_barra = 120
        altura_barra = 12
        x_barra = pos_tela[0] - largura_barra // 2
        y_barra = pos_tela[1] - self.raio - 25
        
        # Fundo da barra com borda épica
        pygame.draw.rect(tela, PRETO, (x_barra - 2, y_barra - 2, largura_barra + 4, altura_barra + 4))
        pygame.draw.rect(tela, DOURADO, (x_barra - 3, y_barra - 3, largura_barra + 6, altura_barra + 6), 2)
        
        # Barra de vida com gradiente baseado na fase
        proporcao_vida = self.hp / self.hp_max
        largura_vida = int(largura_barra * proporcao_vida)
        
        if largura_vida > 0:
            cor_vida = self.cores_fase[self.fase_atual - 1]
            pygame.draw.rect(tela, cor_vida, (x_barra, y_barra, largura_vida, altura_barra))
            
            # Efeito de brilho na barra
            if self.brilho_ataque > 0:
                surf_brilho = pygame.Surface((largura_vida, altura_barra))
                surf_brilho.set_alpha(self.brilho_ataque)
                surf_brilho.fill(BRANCO)
                tela.blit(surf_brilho, (x_barra, y_barra))
        
        # Texto da vida
        texto_vida = f"{self.hp}/{self.hp_max}"
        desenhar_texto(tela, texto_vida, (x_barra + largura_barra // 2 - 30, y_barra - 20), 
                      BRANCO, 16, sombra=True)

    def atualizar_indicadores(self, tempo_atual):
        """Atualiza os indicadores de ataque"""
        # Remover indicadores expirados
        self.indicadores = [ind for ind in self.indicadores if tempo_atual < ind['tempo_fim']]
        
    def adicionar_indicador(self, pos, tipo, duracao=1000):
        """Adiciona um novo indicador de ataque"""
        tempo_atual = pygame.time.get_ticks()
        self.indicadores.append({
            'pos': pos,
            'tipo': tipo,
            'tempo_inicio': tempo_atual,
            'tempo_fim': tempo_atual + duracao,
            'raio': 30  # Raio inicial do indicador
        })
    
    def desenhar_indicadores(self, tela, camera):
        """Desenha os indicadores de ataque"""
        tempo_atual = pygame.time.get_ticks()
        
        for ind in self.indicadores:
            pos_tela = posicao_na_tela(ind['pos'], camera)
            tempo_passado = tempo_atual - ind['tempo_inicio']
            tempo_total = ind['tempo_fim'] - ind['tempo_inicio']
            
            # Efeito de pulso
            progresso = tempo_passado / tempo_total
            raio_base = ind['raio']
            raio_atual = raio_base + 10 * math.sin(progresso * 6 * math.pi)
            
            # Cor baseada no tipo
            if "explosao" in ind['tipo'].lower() or "apocalipse" in ind['tipo'].lower():
                cor = (255, 50, 0)  # Vermelho para explosões
            elif "laser" in ind['tipo'].lower():
                cor = (255, 0, 255)  # Magenta para lasers
            else:
                cor = (255, 255, 0)  # Amarelo para outros
            
            # Desenhar círculo pulsante
            alpha = int(255 * (1 - progresso))
            surf_indicador = pygame.Surface((raio_atual * 2, raio_atual * 2))
            surf_indicador.set_alpha(alpha)
            surf_indicador.fill(cor)
            tela.blit(surf_indicador, (pos_tela[0] - raio_atual, pos_tela[1] - raio_atual))
            
            # Desenhar símbolo de alerta
            texto = "!"
            tamanho_fonte = int(20 + 5 * math.sin(progresso * 8 * math.pi))
            desenhar_texto(tela, texto, 
                         (pos_tela[0] - 5, pos_tela[1] - tamanho_fonte//2),
                         BRANCO, tamanho_fonte, sombra=True)

    def pre_calcular_posicoes_meteoros(self, jogador_pos):
        """Pré-calcula as posições dos meteoros e adiciona indicadores"""
        # Grade 2x2
        grid_size = 2
        spacing = 120
        
        for i in range(grid_size):
            for j in range(grid_size):
                alvo_x = jogador_pos[0] + (i - grid_size/2) * spacing
                alvo_y = jogador_pos[1] + (j - grid_size/2) * spacing
                self.adicionar_indicador((alvo_x, alvo_y), "Meteoros", 1000)
        
        # Círculo extra
        if random.random() < 0.5:  # 50% de chance
            num_extras = 6
            raio = 200
            for i in range(num_extras):
                angulo = (2 * math.pi * i / num_extras)
                alvo_x = jogador_pos[0] + math.cos(angulo) * raio
                alvo_y = jogador_pos[1] + math.sin(angulo) * raio
                self.adicionar_indicador((alvo_x, alvo_y), "Meteoros", 1000)

    def pre_calcular_posicoes_apocalipse(self):
        """Pré-calcula as posições do apocalipse e adiciona indicadores"""
        # Grade 3x3
        grid_size = 3
        spacing = 150
        for i in range(-grid_size//2, grid_size//2 + 1):
            for j in range(-grid_size//2, grid_size//2 + 1):
                x = self.pos[0] + i * spacing
                y = self.pos[1] + j * spacing
                self.adicionar_indicador((x, y), "Apocalipse", 1000)

    def pre_calcular_posicoes_furia_final(self, jogador_pos):
        """Pré-calcula as posições da fúria final e adiciona indicadores"""
        # Estrela
        num_pontas = 5
        for i in range(num_pontas):
            angulo = (2 * math.pi * i / num_pontas)
            x = self.pos[0] + math.cos(angulo) * 300
            y = self.pos[1] + math.sin(angulo) * 300
            self.adicionar_indicador((x, y), "Furia Final", 1000)
        
        # Círculo de explosões
        num_explosoes = 8
        raio = 150
        for i in range(num_explosoes):
            angulo = (2 * math.pi * i / num_explosoes)
            x = self.pos[0] + math.cos(angulo) * raio
            y = self.pos[1] + math.sin(angulo) * raio
            self.adicionar_indicador((x, y), "Furia Final", 1000)

class ProjetilBoss:
    def __init__(self, x, y, alvo_x, alvo_y, dano, velocidade, alcance, tipo):
        self.pos = [x, y]
        self.pos_inicial = [x, y]
        self.dano = dano
        self.velocidade = velocidade
        self.alcance = alcance
        self.tipo = tipo
        self.ativo = True
        self.tempo_criacao = pygame.time.get_ticks()
        
        # Configurações por tipo
        self.configurar_tipo()
        
        # Calcular direção se necessário
        if velocidade > 0 and (alvo_x != x or alvo_y != y):
            dx = alvo_x - x
            dy = alvo_y - y
            if dx != 0 or dy != 0:
            self.direcao_x, self.direcao_y = normalizar_vetor(dx, dy)
            else:
                self.direcao_x, self.direcao_y = 0, 0
        else:
            self.direcao_x, self.direcao_y = 0, 0
        
        # Efeitos visuais
        self.particulas_rastro = []
        self.brilho = 0

    def configurar_tipo(self):
        """Configura propriedades específicas baseadas no tipo"""
        if self.tipo == "basico":
            self.cor = (255, 100, 100)  # Vermelho claro
            self.raio = 8
            self.rastro_cor = (255, 50, 50, 100)
        elif self.tipo == "laser_rapido":
            self.cor = (255, 0, 255)  # Magenta
            self.raio = 6
            self.rastro_cor = (255, 0, 255, 150)
        elif self.tipo == "meteoro":
            self.cor = (255, 100, 0)  # Amarelo
            self.raio = 12
            self.rastro_cor = (255, 100, 0, 100)
        elif self.tipo == "espinho_rotativo":
            self.cor = (0, 255, 0)  # Verde
            self.raio = 6
            self.rastro_cor = (0, 255, 0, 100)
        elif self.tipo == "laser_varredor":
            self.cor = (255, 0, 0)  # Vermelho
            self.raio = 8
            self.rastro_cor = (255, 0, 0, 120)
        elif self.tipo == "explosao":
            self.cor = (255, 150, 0)  # Laranja
            self.raio = 60
            self.rastro_cor = (255, 150, 0, 150)
        elif self.tipo == "onda_teleporte":
            self.cor = (200, 0, 200)  # Roxo
            self.raio = 8
            self.rastro_cor = (200, 0, 200, 100)
        elif self.tipo == "apocalipse":
            self.cor = (255, 50, 50)  # Vermelho
            self.raio = 80
            self.rastro_cor = (255, 50, 50, 200)
        elif self.tipo == "vortice":
            self.cor = (150, 0, 255)  # Roxo
            self.raio = 6
            self.rastro_cor = (150, 0, 255, 100)
        elif self.tipo == "furia_laser":
            self.cor = (255, 255, 0)  # Amarelo
            self.raio = 10
            self.rastro_cor = (255, 255, 0, 150)
        elif self.tipo == "furia_explosao":
            self.cor = (255, 0, 0)  # Vermelho
            self.raio = 70
            self.rastro_cor = (255, 0, 0, 180)
    
    def atualizar(self):
        if not self.ativo:
            return
        
        tempo_atual = pygame.time.get_ticks()
        tempo_vida = tempo_atual - self.tempo_criacao
        
        # Movimento
        if self.velocidade > 0:
            self.pos[0] += self.direcao_x * self.velocidade
            self.pos[1] += self.direcao_y * self.velocidade
        
        # Verificar alcance
        distancia_percorrida = calcular_distancia(self.pos, self.pos_inicial)
        if distancia_percorrida > self.alcance:
            self.ativo = False
            return
        
        # Comportamentos especiais por tipo
        if self.tipo in ["explosao", "apocalipse", "furia_explosao"]:
            # Projéteis de área desaparecem rapidamente
            if tempo_vida > 800:
                self.ativo = False
        elif self.tipo == "meteoro":
            # Meteoros aceleram conforme caem
            self.velocidade += 0.1
        elif self.tipo == "vortice":
            # Projéteis do vórtice fazem curva e somem após um tempo
            if tempo_vida > 2000:  # Somem após 2 segundos
                self.ativo = False
            else:
                # Curva mais suave
                angulo_atual = math.atan2(self.direcao_y, self.direcao_x)
                angulo_atual += 0.03  # Reduzido de 0.05 para 0.03
                self.direcao_x = math.cos(angulo_atual)
                self.direcao_y = math.sin(angulo_atual)
        
        # Gerar partículas de rastro para alguns tipos
        if self.tipo in ["laser_rapido", "laser_varredor", "furia_laser", "meteoro"]:
            if len(self.particulas_rastro) < 5:
                self.particulas_rastro.append({
                    'pos': list(self.pos),
                    'vida': 20,
                    'cor': self.cor
                })
        
        # Atualizar partículas
        for particula in self.particulas_rastro[:]:
            particula['vida'] -= 1
            if particula['vida'] <= 0:
                self.particulas_rastro.remove(particula)
    
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
            # Desenhar partículas de rastro primeiro
            for particula in self.particulas_rastro:
                if esta_na_tela(particula['pos'], camera):
                    pos_part = posicao_na_tela(particula['pos'], camera)
                    alpha = int((particula['vida'] / 20) * 100)
                    surf_part = pygame.Surface((3, 3))
                    surf_part.set_alpha(alpha)
                    surf_part.fill(particula['cor'])
                    tela.blit(surf_part, (pos_part[0] - 1, pos_part[1] - 1))
            
            # Projéteis de área com efeito especial
            if self.tipo in ["explosao", "apocalipse", "furia_explosao"]:
                # Múltiplos círculos concêntricos
                for i in range(3):
                    raio_atual = self.raio - i * 15
                    if raio_atual > 0:
                        alpha = 150 - i * 40
                        surf = pygame.Surface((raio_atual * 2, raio_atual * 2))
                        surf.set_alpha(alpha)
                surf.fill(self.cor)
                        tela.blit(surf, (pos_tela[0] - raio_atual, pos_tela[1] - raio_atual))
                
                # Círculo central sólido
                pygame.draw.circle(tela, BRANCO, (int(pos_tela[0]), int(pos_tela[1])), 5)
            
            else:
                # Projéteis normais com aura
                # Aura brilhante
                surf_aura = pygame.Surface((self.raio * 3, self.raio * 3))
                surf_aura.set_alpha(50)
                surf_aura.fill(self.cor)
                tela.blit(surf_aura, (pos_tela[0] - self.raio * 1.5, pos_tela[1] - self.raio * 1.5))
                
                # Projétil principal
                pygame.draw.circle(tela, self.cor, (int(pos_tela[0]), int(pos_tela[1])), self.raio) 
                
                # Borda brilhante
                pygame.draw.circle(tela, BRANCO, (int(pos_tela[0]), int(pos_tela[1])), self.raio, 2)
                
                # Centro ultra-brilhante
                pygame.draw.circle(tela, (255, 255, 255), (int(pos_tela[0]), int(pos_tela[1])), max(1, self.raio // 3)) 