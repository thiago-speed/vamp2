import pygame
import sys
import random
import math
from config import *
from utils import *
from jogador import Jogador
from inimigo import Inimigo
from projetil import Projetil, XP, ProjetilInimigo
from tela_upgrade import TelaUpgrade
from upgrade_manager import UpgradeManager
from habilidades import Raio, Bomba, CampoGravitacional, CampoPermanente
from minimapa import Minimapa
from itens import Item
from inimigo import gerar_inimigo_aleatorio
from itens import gerar_item_aleatorio, usar_item_xp_magnetico, usar_item_bomba_tela, usar_item_coracao
import os

class Boss:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.raio = 30
        self.velocidade = 1.0
        self.hp_max = 500000
        self.hp = self.hp_max
        self.hp_fase2 = self.hp_max * 0.6  # 60% do HP
        self.hp_fase3 = self.hp_max * 0.3  # 30% do HP
        self.fase = 1
        self.ativo = True
        self.cor = VERMELHO
        self.projeteis = []
        self.indicadores = []
        self.ataque_atual = None
        self.tempo_ultimo_ataque = 0
        self.intervalo_ataque = 8000  # 8 segundos na fase 1
        self.bullet_hell_ativo = False
        self.bullet_hell_tempo = 0
        self.bullet_hell_duracao = 8000  # 8 segundos de bullet hell
        self.bullet_hell_padrao = 0
        self.bullet_hell_ultimo_tiro = 0
        self.bullet_hell_intervalo = 150  # Aumentado de 100 para 150ms entre tiros
        self.ultimo_ataque_usado = None
        self.ataques_consecutivos = 0
        self.dano = 15  # Reduzido de 20 para 15
        self.invulneravel = False
        
        # Controle de ataques
        self.tempo_execucao = 0
        self.tempo_aviso = 0
        self.indicadores_area = []
        
        # Controle do bullet hell
        self.bullet_hell_intervalo = 100  # 0.1 segundo entre padrões
        
        # Controle de movimento
        self.destino = None
        self.tempo_movimento = 0
        self.duracao_movimento = 0
        self.pos_inicial_movimento = None
        
        # Controle de ataques especiais
        self.ataque_rajada_laser = self._ataque_rajada_laser
        self.ataque_meteoros = self._ataque_meteoros
        self.ataque_espinhos = self._ataque_espinhos
        self.ataque_laser_varredor = self._ataque_laser_varredor
        self.ataque_explosao_infernal = self._ataque_explosao_infernal
        self.ataque_teleporte = self._ataque_teleporte
        self.ataque_apocalipse = self._ataque_apocalipse
        self.ataque_vortice = self._ataque_vortice
        self.ataque_furia = self._ataque_furia
    
    def determinar_fase(self):
        """Determina a fase atual do boss baseado no HP"""
        fase_anterior = self.fase
        
        if self.hp <= self.hp_fase3:
            if not self.bullet_hell_ativo and self.fase < 3:
                # Iniciar bullet hell ao entrar na fase 3
                self.bullet_hell_ativo = True
                self.bullet_hell_tempo = pygame.time.get_ticks()
                self.bullet_hell_padrao = 0
                print("Boss entrando na Fase 3!")
            return 3
        elif self.hp <= self.hp_fase2:
            if self.fase < 2:
                print("Boss entrando na Fase 2!")
            return 2
        
        if self.fase > 1:
            print("Boss voltando para Fase 1!")
        return 1
    
    def obter_ataques_disponiveis(self):
        """Retorna lista de ataques disponíveis baseado na fase com suas probabilidades"""
        ataques = []
        
        # Fase 1 - Ataques mais simples
        if self.fase == 1:
            ataques.extend([
                # Ataques básicos (60% chance total)
                {"nome": "basico", "chance": 15},
                {"nome": "tiro_duplo", "chance": 15},
                {"nome": "tiro_triplo", "chance": 15},
                {"nome": "tiro_angular", "chance": 15},
                
                # Ataques fortes (30% chance total)
                {"nome": "espiral_simples", "chance": 15},
                {"nome": "onda_circular", "chance": 15},
                
                # Ataque devastador (10% chance)
                {"nome": "explosao_anel", "chance": 10}
            ])
        
        # Fase 2 - Ataques médios
        elif self.fase == 2:
            ataques.extend([
                # Ataques básicos (50% chance total)
                {"nome": "tiro_rapido", "chance": 15},
                {"nome": "tiro_perseguidor", "chance": 10},
                {"nome": "tiro_espalhado", "chance": 15},
                {"nome": "rajada_laser", "chance": 10},
                
                # Ataques fortes (35% chance total)
                {"nome": "meteoros", "chance": 20},
                {"nome": "laser_varredor", "chance": 15},
                
                # Ataque devastador (15% chance)
                {"nome": "explosao_infernal", "chance": 15}
            ])
        
        # Fase 3 - Ataques mais fortes
        else:
            ataques.extend([
                # Ataques básicos (50% chance total)
                {"nome": "tiro_rapido", "chance": 15},
                {"nome": "tiro_perseguidor", "chance": 15},
                {"nome": "tiro_ricochete", "chance": 10},
                {"nome": "tiro_espalhado", "chance": 10},
                
                # Ataques fortes (35% chance total)
                {"nome": "vortice", "chance": 20},
                {"nome": "meteoros", "chance": 15},
                
                # Ataque devastador (15% chance)
                {"nome": "furia", "chance": 15}
            ])
        
        return ataques
    
    def atualizar(self, jogador_pos):
        """Atualiza estado do boss"""
        if not self.ativo:
            return
        
        # Atualizar fase e intervalo de ataque
        nova_fase = self.determinar_fase()
        if nova_fase != self.fase:
            self.fase = nova_fase
            # Ajustar intervalo de ataque baseado na fase
            if self.fase == 1:
                self.intervalo_ataque = 8000  # 8 segundos
            elif self.fase == 2:
                self.intervalo_ataque = 5000  # 5 segundos
            else:
                self.intervalo_ataque = 4000  # 4 segundos
            self.tempo_ultimo_ataque = 0
            print(f"Boss mudou para Fase {self.fase}! HP: {self.hp}/{self.hp_max}")
        
        tempo_atual = pygame.time.get_ticks()
        
        # Atualizar bullet hell se ativo
        if self.bullet_hell_ativo:
            if tempo_atual - self.bullet_hell_tempo >= self.bullet_hell_duracao:
                self.bullet_hell_ativo = False
                print("Bullet Hell terminou!")
            else:
                return self.atualizar_bullet_hell(jogador_pos)
        
        # Processar ataque atual
        if self.ataque_atual:
            self.tempo_execucao = tempo_atual - self.tempo_ultimo_ataque
            if self.tempo_execucao >= min(2000, self.intervalo_ataque * 0.5):  # Máximo de 2 segundos ou metade do intervalo
                self.ataque_atual = None
                print("Ataque finalizado")
            else:
                return self.executar_ataque(jogador_pos)
        
        # Iniciar novo ataque
        if tempo_atual - self.tempo_ultimo_ataque > self.intervalo_ataque:
            print("\nIniciando novo ataque...")
            return self.iniciar_ataque(jogador_pos)
        
        return []
    
    def atualizar_bullet_hell(self, jogador_pos):
        """Atualiza o padrão bullet hell"""
        tempo_atual = pygame.time.get_ticks()
        novos_projeteis = []
        
        if tempo_atual - self.bullet_hell_ultimo_tiro >= self.bullet_hell_intervalo:
            self.bullet_hell_ultimo_tiro = tempo_atual
            self.bullet_hell_padrao = (self.bullet_hell_padrao + 1) % 4
            
            # Diferentes padrões de tiro
            if self.bullet_hell_padrao == 0:
                # Espiral
                for i in range(8):
                    angulo = (tempo_atual / 500.0) + (i * math.pi / 4)
                    dx = math.cos(angulo)
                    dy = math.sin(angulo)
                    novos_projeteis.append(
                        ProjetilBoss(self.pos[0], self.pos[1], 
                                   self.pos[0] + dx, self.pos[1] + dy,
                                   15, 3, (255, 0, 0))
                    )
            
            elif self.bullet_hell_padrao == 1:
                # Grade
                for x in range(-2, 3):
                    for y in range(-2, 3):
                        if x == 0 and y == 0:
                            continue
                        novos_projeteis.append(
                            ProjetilBoss(self.pos[0], self.pos[1],
                                       self.pos[0] + x * 100, self.pos[1] + y * 100,
                                       15, 2, (0, 255, 255))
                        )
            
            elif self.bullet_hell_padrao == 2:
                # Círculo expansivo
                num_projeteis = 16
                for i in range(num_projeteis):
                    angulo = (i * 2 * math.pi / num_projeteis)
                    dx = math.cos(angulo)
                    dy = math.sin(angulo)
                    novos_projeteis.append(
                        ProjetilBoss(self.pos[0], self.pos[1],
                                   self.pos[0] + dx, self.pos[1] + dy,
                                   15, 4, (255, 255, 0))
                    )
            
            else:
                # Chuva de projéteis
                for _ in range(10):
                    x_alvo = random.randint(0, LARGURA_MAPA)
                    novos_projeteis.append(
                        ProjetilBoss(self.pos[0], self.pos[1],
                                   x_alvo, ALTURA_MAPA,
                                   15, 5, (255, 0, 255))
                    )
        
        return novos_projeteis

    def ataque_basico(self, jogador_pos):
        """Ataque básico melhorado com mais projéteis"""
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_ultimo_ataque < 300:  # Intervalo entre rajadas
            return []
        
        self.tempo_ultimo_ataque = tempo_atual
        novos_projeteis = []
        
        # Aumentar número de projéteis baseado na fase
        num_projeteis = 3 if self.fase == 1 else (5 if self.fase == 2 else 7)
        angulo_base = math.atan2(jogador_pos[1] - self.pos[1], jogador_pos[0] - self.pos[0])
        
        for i in range(num_projeteis):
            # Distribuir os tiros em leque
            offset = (i - (num_projeteis - 1) / 2) * 0.2
            angulo = angulo_base + offset
            
            dx = math.cos(angulo)
            dy = math.sin(angulo)
            
            novos_projeteis.append(
                ProjetilBoss(self.pos[0], self.pos[1],
                           self.pos[0] + dx, self.pos[1] + dy,
                           self.dano, 4, (255, 0, 0))
            )
        
        return novos_projeteis

    def iniciar_ataque(self, jogador_pos):
        """Inicia um novo ataque baseado nas probabilidades"""
        ataques = self.obter_ataques_disponiveis()
        
        # Ajustar probabilidades para evitar repetição
        if self.ultimo_ataque_usado:
            for ataque in ataques:
                if ataque["nome"] == self.ultimo_ataque_usado:
                    # Reduz a chance do último ataque usado
                    ataque["chance"] *= 0.5
                    if self.ataques_consecutivos > 0:
                        # Reduz ainda mais se já foi usado múltiplas vezes
                        ataque["chance"] *= (0.5 ** self.ataques_consecutivos)
        
        # Escolher ataque baseado nas probabilidades
        numero_aleatorio = random.random() * 100  # Número entre 0 e 100
        soma_probabilidade = 0
        ataque_escolhido = None
        
        # Debug: imprimir probabilidades
        print(f"\nFase atual: {self.fase}")
        print(f"Último ataque: {self.ultimo_ataque_usado} (usado {self.ataques_consecutivos} vezes)")
        print(f"Número aleatório: {numero_aleatorio}")
        
        for ataque in ataques:
            soma_probabilidade += ataque["chance"]
            print(f"Testando {ataque['nome']} (chance: {ataque['chance']:.1f}%, soma: {soma_probabilidade:.1f}%)")
            if numero_aleatorio <= soma_probabilidade and ataque_escolhido is None:
                ataque_escolhido = ataque["nome"]
                print(f"Escolhido: {ataque_escolhido}")
                break
        
        # Fallback para ataque básico se algo der errado
        if ataque_escolhido is None:
            print("Fallback para ataque básico")
            ataque_escolhido = "basico"
        
        # Atualizar contadores de repetição
        if ataque_escolhido == self.ultimo_ataque_usado:
            self.ataques_consecutivos += 1
        else:
            self.ataques_consecutivos = 0
        
        self.ultimo_ataque_usado = ataque_escolhido
        self.ataque_atual = ataque_escolhido
        self.tempo_ultimo_ataque = pygame.time.get_ticks()
        self.tempo_execucao = 0
        
        # Criar indicadores de área se necessário
        if self.ataque_atual != "basico":
            self.criar_indicadores_area(jogador_pos, self.ataque_atual)
    
    def criar_indicadores_area(self, jogador_pos, tipo_ataque):
        """Cria indicadores visuais para o ataque"""
        self.indicadores_area = []
        
        if tipo_ataque in ["rajada_laser", "laser_varredor"]:
            # Linha indicando direção do laser
            self.indicadores_area.append({
                "tipo": "linha",
                "inicio": self.pos,
                "fim": jogador_pos,
                "cor": (255, 0, 0)
            })
        
        elif tipo_ataque in ["meteoros", "apocalipse"]:
            # Círculos indicando área de impacto
            for _ in range(5):
                x = random.randint(0, LARGURA_MAPA)
                y = random.randint(0, ALTURA_MAPA)
                self.indicadores_area.append({
                    "tipo": "circulo",
                    "pos": [x, y],
                    "raio": 100,
                    "cor": (255, 165, 0)
                })
        
        elif tipo_ataque == "espinhos":
            # Padrão circular ao redor do boss
            self.indicadores_area.append({
                "tipo": "circulo",
                "pos": self.pos,
                "raio": 200,
                "cor": (255, 0, 255)
            })
    
    def executar_ataque(self, jogador_pos):
        """Executa o ataque atual"""
        if not self.ataque_atual:
            return []
        
        # Ataques básicos
        if self.ataque_atual == "basico":
            return self.ataque_basico(jogador_pos)
        elif self.ataque_atual == "tiro_duplo":
            return self._ataque_tiro_duplo(jogador_pos)
        elif self.ataque_atual == "tiro_triplo":
            return self._ataque_tiro_triplo(jogador_pos)
        elif self.ataque_atual == "tiro_angular":
            return self._ataque_tiro_angular(jogador_pos)
        elif self.ataque_atual == "tiro_espalhado":
            return self._ataque_tiro_espalhado(jogador_pos)
        elif self.ataque_atual == "tiro_perseguidor":
            return self._ataque_tiro_perseguidor(jogador_pos)
        elif self.ataque_atual == "tiro_ricochete":
            return self._ataque_tiro_ricochete(jogador_pos)
        elif self.ataque_atual == "tiro_rapido":
            return self._ataque_tiro_rapido(jogador_pos)
        elif self.ataque_atual == "rajada_laser":
            return self._ataque_rajada_laser(jogador_pos)
        elif self.ataque_atual == "teleporte":
            return self._ataque_teleporte(jogador_pos)
        
        # Ataques fortes
        elif self.ataque_atual == "espiral_simples":
            return self._ataque_espiral_simples(jogador_pos)
        elif self.ataque_atual == "onda_circular":
            return self._ataque_onda_circular(jogador_pos)
        elif self.ataque_atual == "meteoros":
            return self._ataque_meteoros(jogador_pos)
        elif self.ataque_atual == "laser_varredor":
            return self._ataque_laser_varredor(jogador_pos)
        elif self.ataque_atual == "vortice":
            return self._ataque_vortice(jogador_pos)
        elif self.ataque_atual == "furia":
            return self._ataque_furia(jogador_pos)
        
        # Ataques devastadores
        elif self.ataque_atual == "explosao_anel":
            return self._ataque_explosao_anel(jogador_pos)
        elif self.ataque_atual == "explosao_infernal":
            return self._ataque_explosao_infernal(jogador_pos)
        elif self.ataque_atual == "apocalipse":
            return self._ataque_apocalipse(jogador_pos)
        
        # Bullet hell por fase
        elif self.ataque_atual == "bullet_hell_fase1":
            return self._bullet_hell_fase1(jogador_pos)
        elif self.ataque_atual == "bullet_hell_fase2":
            return self._bullet_hell_fase2(jogador_pos)
        elif self.ataque_atual == "bullet_hell_fase3":
            return self._bullet_hell_fase3(jogador_pos)
        
        print(f"Aviso: Ataque desconhecido '{self.ataque_atual}'")
        return []
    
    def receber_dano(self, dano):
        """Processa dano recebido"""
        if not self.invulneravel:
            self.hp -= dano
            if self.hp <= 0:
                self.ativo = False
    
    def colidir_com_jogador(self, jogador):
        """Processa colisão com o jogador"""
        if not self.ativo or self.invulneravel:
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
        
        # Desenhar boss
        cor = (255, 0, 0) if self.fase == 3 else ((255, 165, 0) if self.fase == 2 else (128, 0, 128))
        pygame.draw.circle(tela, cor, (int(pos_tela[0]), int(pos_tela[1])), self.raio)
        
        # Desenhar indicadores de ataque
        self.desenhar_indicadores(tela, camera)
        
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
    
    def desenhar_indicadores(self, tela, camera):
        """Desenha os indicadores de área de ataque"""
        for indicador in self.indicadores_area:
            if indicador["tipo"] == "linha":
                inicio = [indicador["inicio"][0] - camera[0],
                         indicador["inicio"][1] - camera[1]]
                fim = [indicador["fim"][0] - camera[0],
                      indicador["fim"][1] - camera[1]]
                pygame.draw.line(tela, indicador["cor"], inicio, fim, 2)
            
            elif indicador["tipo"] == "circulo":
                pos = [indicador["pos"][0] - camera[0],
                      indicador["pos"][1] - camera[1]]
                pygame.draw.circle(tela, indicador["cor"], 
                                 (int(pos[0]), int(pos[1])),
                                 indicador["raio"], 2)

    def _ataque_rajada_laser(self, jogador_pos):
        """Ataque de rajada de laser"""
        novos_projeteis = []
        
        for i in range(5):  # 5 lasers em leque
            angulo = math.atan2(jogador_pos[1] - self.pos[1], jogador_pos[0] - self.pos[0])
            offset = (i - 2) * 0.3  # Distribuir em leque
            angulo_final = angulo + offset
            
            dx = math.cos(angulo_final)
            dy = math.sin(angulo_final)
            
            novos_projeteis.append(
                ProjetilBoss(self.pos[0], self.pos[1],
                           self.pos[0] + dx, self.pos[1] + dy,
                           15, 5, (0, 255, 255))
            )
        
        return novos_projeteis
    
    def _ataque_meteoros(self, jogador_pos):
        """Cria uma chuva de meteoros com zonas seguras nas laterais"""
        projeteis = []
        
        # Definir área segura nas laterais
        area_segura_lateral = 200  # 200 pixels de cada lado da tela
        
        # Calcular área jogável para os meteoros
        area_jogavel_min = jogador_pos[0] - 800 + area_segura_lateral
        area_jogavel_max = jogador_pos[0] + 800 - area_segura_lateral
        
        # Criar 5-7 meteoros em posições aleatórias, mas garantindo espaços seguros
        num_meteoros = random.randint(5, 7)
        area_segura_entre = 100  # Espaço mínimo entre meteoros
        
        # Primeiro meteoro sempre mira próximo ao jogador (mas não diretamente)
        offset_jogador = random.randint(-100, 100)
        pos_x = max(min(jogador_pos[0] + offset_jogador, area_jogavel_max), area_jogavel_min)
        pos_y = jogador_pos[1] - 400  # Começa acima da tela
        
        # Criar primeiro meteoro
        vel_y = 4 + random.random() * 2
        projetil = ProjetilBoss(pos_x, pos_y,
                              pos_x, pos_y + 800,
                              self.dano * 2, vel_y, (200, 100, 0))
        projeteis.append(projetil)
        
        # Criar indicadores visuais nas áreas seguras
        self.indicadores_area = [
            {
                "tipo": "retangulo",
                "pos": [jogador_pos[0] - 800, jogador_pos[1] - 400],
                "largura": area_segura_lateral,
                "altura": 800,
                "cor": (0, 255, 0, 50),  # Verde transparente
                "duracao": 2000
            },
            {
                "tipo": "retangulo",
                "pos": [jogador_pos[0] + 800 - area_segura_lateral, jogador_pos[1] - 400],
                "largura": area_segura_lateral,
                "altura": 800,
                "cor": (0, 255, 0, 50),  # Verde transparente
                "duracao": 2000
            }
        ]
        
        # Criar meteoros adicionais
        for i in range(1, num_meteoros):
            tentativas = 0
            pos_valido = False
            
            while tentativas < 10 and not pos_valido:
                # Gerar posição dentro da área jogável
                pos_x = random.randint(int(area_jogavel_min), int(area_jogavel_max))
                pos_y = jogador_pos[1] - 400 - random.randint(0, 200)
                
                # Verificar se está longe o suficiente dos outros meteoros
                muito_perto = False
                for proj in projeteis:
                    dist = math.sqrt((pos_x - proj.pos[0])**2)  # Só verifica distância horizontal
                    if dist < area_segura_entre:
                        muito_perto = True
                        break
                
                if not muito_perto:
                    pos_valido = True
                tentativas += 1
            
            if pos_valido:
                vel_y = 4 + random.random() * 2
                projetil = ProjetilBoss(pos_x, pos_y,
                                      pos_x, pos_y + 800,
                                      self.dano * 2, vel_y, (200, 100, 0))
                projeteis.append(projetil)
        
        return projeteis
    
    def _ataque_espinhos(self, jogador_pos):
        """Ataque de espinhos em espiral"""
        novos_projeteis = []
        tempo = self.tempo_execucao / 1000.0  # Converter para segundos
        
        num_espinhos = 8
        for i in range(num_espinhos):
            angulo = tempo * 2 + (i * 2 * math.pi / num_espinhos)
            dx = math.cos(angulo)
            dy = math.sin(angulo)
            
            novos_projeteis.append(
                ProjetilBoss(self.pos[0], self.pos[1],
                           self.pos[0] + dx * 300, self.pos[1] + dy * 300,
                           15, 4, (255, 0, 255))
            )
        
        return novos_projeteis
    
    def _ataque_laser_varredor(self, jogador_pos):
        """Cria um laser que varre a área, mas com tempo suficiente para dodge"""
        projeteis = []
        
        # Tempo total do ataque: 2 segundos
        # Primeiro segundo: aviso visual
        # Segundo segundo: laser ativo
        if self.tempo_execucao < 1000:  # Primeiro segundo: apenas aviso
            self.criar_indicadores_area(jogador_pos, "laser_varredor")
            return []
        
        # Ângulo do laser baseado no tempo
        progresso = (self.tempo_execucao - 1000) / 1000  # 0 a 1 no segundo segundo
        angulo_base = math.pi * 2 * progresso  # Varre 360 graus
        
        # Criar vários projéteis em linha para formar o laser
        comprimento_laser = 800
        num_segmentos = 20
        for i in range(num_segmentos):
            dist = (i / num_segmentos) * comprimento_laser
            pos_x = self.pos[0] + math.cos(angulo_base) * dist
            pos_y = self.pos[1] + math.sin(angulo_base) * dist
            
            projetil = ProjetilBoss(pos_x, pos_y,
                                  pos_x, pos_y,  # Não se move
                                  self.dano, 0, AZUL)
            projeteis.append(projetil)
        
        return projeteis
    
    def _ataque_explosao_infernal(self, jogador_pos):
        """Ataque de explosão em área"""
        novos_projeteis = []
        
        # Criar círculo de projéteis
        num_projeteis = 16
        for i in range(num_projeteis):
            angulo = (i * 2 * math.pi / num_projeteis)
            dx = math.cos(angulo)
            dy = math.sin(angulo)
            
            novos_projeteis.append(
                ProjetilBoss(self.pos[0], self.pos[1],
                           self.pos[0] + dx * 200, self.pos[1] + dy * 200,
                           20, 3, (255, 100, 0))
            )
        
        return novos_projeteis
    
    def _ataque_teleporte(self, jogador_pos):
        """Ataque com teleporte"""
        if not hasattr(self, 'teleporte_pos'):
            # Escolher posição aleatória próxima ao jogador
            angulo = random.uniform(0, 2 * math.pi)
            dist = random.uniform(100, 300)
            self.teleporte_pos = [
                jogador_pos[0] + math.cos(angulo) * dist,
                jogador_pos[1] + math.sin(angulo) * dist
            ]
            self.pos = self.teleporte_pos
            return []
        
        # Após teleporte, atirar em todas as direções
        novos_projeteis = []
        num_projeteis = 16
        for i in range(num_projeteis):
            angulo = (i * 2 * math.pi / num_projeteis)
            dx = math.cos(angulo)
            dy = math.sin(angulo)
            
            novos_projeteis.append(
                ProjetilBoss(self.pos[0], self.pos[1],
                           self.pos[0] + dx * 300, self.pos[1] + dy * 300,
                           20, 4, (128, 0, 255))
            )
        
        delattr(self, 'teleporte_pos')
        return novos_projeteis
    
    def _ataque_apocalipse(self, jogador_pos):
        """Versão nerfada do ataque apocalipse"""
        projeteis = []
        
        # Reduzido de 8 para 6 lasers
        num_lasers = 6
        angulo_base = (self.tempo_execucao / 1000) * math.pi  # Rotação mais lenta
        
        for i in range(num_lasers):
            angulo = angulo_base + (i * 2 * math.pi / num_lasers)
            dist = 400  # Reduzido alcance
            
            pos_x = self.pos[0] + math.cos(angulo) * dist
            pos_y = self.pos[1] + math.sin(angulo) * dist
            
            # Criar laser com dano reduzido
            projetil = ProjetilBoss(self.pos[0], self.pos[1],
                                  pos_x, pos_y,
                                  self.dano * 1.5, 6, VERMELHO)  # Dano reduzido
            projeteis.append(projetil)
        
        return projeteis
    
    def _ataque_vortice(self, jogador_pos):
        """Versão mais fácil do vórtice"""
        projeteis = []
        tempo = self.tempo_execucao / 1000.0
        
        # Reduzido número de projéteis e velocidade
        num_projeteis = 4  # Era 6
        raio = 200 + math.sin(tempo * 2) * 50
        
        for i in range(num_projeteis):
            angulo = tempo * 3 + (i * 2 * math.pi / num_projeteis)
            pos_x = self.pos[0] + math.cos(angulo) * raio
            pos_y = self.pos[1] + math.sin(angulo) * raio
            
            projetil = ProjetilBoss(pos_x, pos_y,
                                  pos_x + math.cos(angulo) * 100,
                                  pos_y + math.sin(angulo) * 100,
                                  self.dano, 4, AZUL)  # Velocidade reduzida
            projeteis.append(projetil)
        
        return projeteis
    
    def _ataque_furia(self, jogador_pos):
        """Versão mais fácil da fúria"""
        projeteis = []
        
        # Reduzido ainda mais o número de projéteis
        num_ondas = 2
        num_projeteis_por_onda = 4  # Era 6
        
        for onda in range(num_ondas):
            angulo_base = (self.tempo_execucao / 600) * math.pi + (onda * math.pi / num_ondas)
            
            for i in range(num_projeteis_por_onda):
                angulo = angulo_base + (i * 2 * math.pi / num_projeteis_por_onda)
                dist = 250 + onda * 100  # Distância reduzida
                
                pos_x = self.pos[0] + math.cos(angulo) * dist
                pos_y = self.pos[1] + math.sin(angulo) * dist
                
                projetil = ProjetilBoss(pos_x, pos_y,
                                      pos_x + math.cos(angulo) * 100,
                                      pos_y + math.sin(angulo) * 100,
                                      self.dano, 4, VERMELHO)  # Velocidade reduzida
                projeteis.append(projetil)
        
        return projeteis

    # Novos ataques da Fase 1
    def _ataque_tiro_triplo(self, jogador_pos):
        """Ataque básico que dispara 3 projéteis em linha"""
        novos_projeteis = []
        angulo_base = math.atan2(jogador_pos[1] - self.pos[1], jogador_pos[0] - self.pos[0])
        
        for i in range(3):
            dx = math.cos(angulo_base)
            dy = math.sin(angulo_base)
            velocidade = 3 + i  # Cada projétil é um pouco mais rápido
            
            novos_projeteis.append(
                ProjetilBoss(self.pos[0], self.pos[1],
                           self.pos[0] + dx, self.pos[1] + dy,
                           10, velocidade, (255, 100, 100))
            )
        
        return novos_projeteis

    def _ataque_espiral_simples(self, jogador_pos):
        """Ataque forte que cria uma espiral simples de projéteis"""
        novos_projeteis = []
        tempo = self.tempo_execucao / 1000.0
        
        for i in range(4):  # 4 projéteis por vez
            angulo = tempo * 3 + (i * math.pi / 2)
            dx = math.cos(angulo) * 200
            dy = math.sin(angulo) * 200
            
            novos_projeteis.append(
                ProjetilBoss(self.pos[0], self.pos[1],
                           self.pos[0] + dx, self.pos[1] + dy,
                           15, 3, (100, 200, 255))
            )
        
        return novos_projeteis

    def _ataque_onda_circular(self, jogador_pos):
        """Ataque forte que cria uma onda circular de projéteis"""
        novos_projeteis = []
        num_projeteis = 8
        
        for i in range(num_projeteis):
            angulo = (i * 2 * math.pi / num_projeteis)
            dx = math.cos(angulo) * 150
            dy = math.sin(angulo) * 150
            
            novos_projeteis.append(
                ProjetilBoss(self.pos[0], self.pos[1],
                           self.pos[0] + dx, self.pos[1] + dy,
                           12, 2.5, (150, 150, 255))
            )
        
        return novos_projeteis

    def _ataque_explosao_anel(self, jogador_pos):
        """Ataque devastador que cria um anel explosivo"""
        novos_projeteis = []
        num_projeteis = 16
        
        for i in range(num_projeteis):
            angulo = (i * 2 * math.pi / num_projeteis)
            dx = math.cos(angulo) * 300
            dy = math.sin(angulo) * 300
            
            novos_projeteis.append(
                ProjetilBoss(self.pos[0], self.pos[1],
                           self.pos[0] + dx, self.pos[1] + dy,
                           20, 6, (255, 50, 50))
            )
        
        return novos_projeteis

    # Bullet Hell por fase
    def _bullet_hell_fase1(self, jogador_pos):
        """Bullet hell mais simples - padrão em espiral"""
        novos_projeteis = []
        tempo = pygame.time.get_ticks() / 1000.0
        
        for i in range(4):
            angulo = tempo * 2 + (i * math.pi / 2)
            dx = math.cos(angulo) * 200
            dy = math.sin(angulo) * 200
            
            novos_projeteis.append(
                ProjetilBoss(self.pos[0], self.pos[1],
                           self.pos[0] + dx, self.pos[1] + dy,
                           10, 3, (255, 200, 200))
            )
        
        return novos_projeteis

    def _bullet_hell_fase2(self, jogador_pos):
        """Bullet hell médio - padrão em grade"""
        novos_projeteis = []
        tempo = pygame.time.get_ticks() / 1000.0
        
        # Grade 3x3 de projéteis
        for x in range(-1, 2):
            for y in range(-1, 2):
                if x == 0 and y == 0:
                    continue
                
                dx = x * math.cos(tempo) - y * math.sin(tempo)
                dy = x * math.sin(tempo) + y * math.cos(tempo)
                
                novos_projeteis.append(
                    ProjetilBoss(self.pos[0], self.pos[1],
                               self.pos[0] + dx * 150, self.pos[1] + dy * 150,
                               15, 4, (255, 150, 50))
                )
        
        return novos_projeteis

    def _bullet_hell_fase3(self, jogador_pos):
        """Bullet hell difícil - múltiplos padrões"""
        novos_projeteis = []
        tempo = pygame.time.get_ticks() / 1000.0
        
        # Padrão 1: Espiral
        for i in range(8):
            angulo = tempo * 3 + (i * math.pi / 4)
            dx = math.cos(angulo) * 250
            dy = math.sin(angulo) * 250
            novos_projeteis.append(
                ProjetilBoss(self.pos[0], self.pos[1],
                           self.pos[0] + dx, self.pos[1] + dy,
                           15, 5, (255, 50, 50))
            )
        
        # Padrão 2: Círculos concêntricos
        if int(tempo * 2) % 2 == 0:
            for r in range(100, 301, 100):
                for i in range(6):
                    angulo = (i * 2 * math.pi / 6) + tempo
                    dx = math.cos(angulo) * r
                    dy = math.sin(angulo) * r
                    novos_projeteis.append(
                        ProjetilBoss(self.pos[0], self.pos[1],
                                   self.pos[0] + dx, self.pos[1] + dy,
                                   15, 4, (255, 0, 255))
                    )
        
        return novos_projeteis

    def _ataque_tiro_duplo(self, jogador_pos):
        """Atira dois projéteis em direção ao jogador com um pequeno ângulo entre eles"""
        projeteis = []
        angulo_base = math.atan2(jogador_pos[1] - self.pos[1], jogador_pos[0] - self.pos[0])
        
        # Ângulo entre os tiros
        angulo_separacao = math.pi / 12  # 15 graus
        
        for i in range(2):
            angulo = angulo_base + (angulo_separacao * (i - 0.5))
            vel_x = math.cos(angulo) * 5
            vel_y = math.sin(angulo) * 5
            
            projetil = ProjetilBoss(self.pos[0], self.pos[1], 
                                  self.pos[0] + vel_x, self.pos[1] + vel_y,
                                  self.dano, 5, VERMELHO)
            projeteis.append(projetil)
        
        return projeteis

    def _ataque_tiro_angular(self, jogador_pos):
        """Atira três projéteis em ângulos fixos, deixando espaços para dodge"""
        projeteis = []
        angulo_base = math.atan2(jogador_pos[1] - self.pos[1], jogador_pos[0] - self.pos[0])
        
        # Três tiros com espaços de 45 graus entre eles
        angulos = [-math.pi/4, 0, math.pi/4]  # -45°, 0°, 45°
        
        for angulo_offset in angulos:
            angulo = angulo_base + angulo_offset
            vel_x = math.cos(angulo) * 5
            vel_y = math.sin(angulo) * 5
            
            projetil = ProjetilBoss(self.pos[0], self.pos[1], 
                                  self.pos[0] + vel_x, self.pos[1] + vel_y,
                                  self.dano, 5, VERMELHO)
            projeteis.append(projetil)
        
        return projeteis

    def _ataque_tiro_espalhado(self, jogador_pos):
        """Atira vários projéteis em leque"""
        projeteis = []
        angulo_base = math.atan2(jogador_pos[1] - self.pos[1], jogador_pos[0] - self.pos[0])
        
        # 5 tiros em leque, cobrindo 60 graus
        num_tiros = 5
        angulo_total = math.pi / 3  # 60 graus
        
        for i in range(num_tiros):
            angulo = angulo_base + (angulo_total * (i / (num_tiros - 1) - 0.5))
            vel_x = math.cos(angulo) * 6
            vel_y = math.sin(angulo) * 6
            
            projetil = ProjetilBoss(self.pos[0], self.pos[1], 
                                  self.pos[0] + vel_x, self.pos[1] + vel_y,
                                  self.dano, 6, VERMELHO)
            projeteis.append(projetil)
        
        return projeteis

    def _ataque_tiro_perseguidor(self, jogador_pos):
        """Atira projéteis que perseguem o jogador"""
        projeteis = []
        angulo_base = math.atan2(jogador_pos[1] - self.pos[1], jogador_pos[0] - self.pos[0])
        
        # Cria um projétil que persegue o jogador
        projetil = ProjetilBoss(self.pos[0], self.pos[1], 
                              jogador_pos[0], jogador_pos[1],
                              self.dano, 3.5, VERMELHO, tipo="perseguidor")  # Velocidade reduzida
        projeteis.append(projetil)
        
        return projeteis

    def _ataque_tiro_ricochete(self, jogador_pos):
        """Atira projéteis que ricocheteiam nas paredes"""
        projeteis = []
        angulo_base = math.atan2(jogador_pos[1] - self.pos[1], jogador_pos[0] - self.pos[0])
        
        # 3 tiros que ricocheteiam
        for i in range(3):
            angulo = angulo_base + (math.pi / 6) * (i - 1)  # -30°, 0°, 30°
            vel_x = math.cos(angulo) * 7
            vel_y = math.sin(angulo) * 7
            
            projetil = ProjetilBoss(self.pos[0], self.pos[1], 
                                  self.pos[0] + vel_x, self.pos[1] + vel_y,
                                  self.dano, 7, LARANJA, tipo="ricochete")
            projeteis.append(projetil)
        
        return projeteis

    def _ataque_tiro_rapido(self, jogador_pos):
        """Atira uma rajada rápida de projéteis"""
        projeteis = []
        angulo_base = math.atan2(jogador_pos[1] - self.pos[1], jogador_pos[0] - self.pos[0])
        
        # 3 tiros rápidos em sequência
        for i in range(3):
            offset = (i - 1) * 30  # Aumentado offset para mais espaço entre tiros
            vel_x = math.cos(angulo_base) * 7  # Velocidade reduzida
            vel_y = math.sin(angulo_base) * 7
            
            projetil = ProjetilBoss(self.pos[0] + math.cos(angulo_base) * offset, 
                                  self.pos[1] + math.sin(angulo_base) * offset,
                                  self.pos[0] + vel_x, self.pos[1] + vel_y,
                                  self.dano, 7, VERMELHO)
            projeteis.append(projetil)
        
        return projeteis

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
        
        # Efeitos especiais baseados no tipo
        if tipo == "meteoro":
            self.trail = []  # Rastro do meteoro
            self.raio = 15
        elif tipo in ["laser", "laser_varredor"]:
            self.raio = 6  # Lasers mais finos
        elif tipo == "explosao":
            self.raio = 20  # Explosões maiores mas mais lentas
        
        # Tempo de vida (alguns projéteis desaparecem com o tempo)
        self.tempo_vida = 8000  # 8 segundos
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
        
        # Movimento
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
        
        pos_tela = (int(self.pos[0] - camera[0]), int(self.pos[1] - camera[1]))
        
        # Verificar se está na tela
        if (pos_tela[0] < -50 or pos_tela[0] > LARGURA_TELA + 50 or
            pos_tela[1] < -50 or pos_tela[1] > ALTURA_TELA + 50):
            return
        
        # Desenho baseado no tipo
        if self.tipo == "meteoro":
            # Rastro de fogo
            for i in range(3):
                rastro_x = int(self.pos[0] - self.direcao[0] * i * 10 - camera[0])
                rastro_y = int(self.pos[1] - self.direcao[1] * i * 10 - camera[1])
                alpha = 100 - i * 30
                if alpha > 0:
                    cor_rastro = (255, alpha, alpha // 2)
                    pygame.draw.circle(tela, cor_rastro, (rastro_x, rastro_y), self.raio - i * 2)
            
            # Meteoro principal
            pygame.draw.circle(tela, self.cor, pos_tela, self.raio)
            pygame.draw.circle(tela, (255, 255, 150), pos_tela, max(2, self.raio - 4))
            
        elif self.tipo in ["laser", "laser_varredor"]:
            # Laser com brilho
            pygame.draw.circle(tela, (255, 255, 255), pos_tela, self.raio + 2)
            pygame.draw.circle(tela, self.cor, pos_tela, self.raio)
            
        elif self.tipo == "explosao":
            # Projétil de explosão pulsante
            pulso = 1 + 0.3 * math.sin(pygame.time.get_ticks() * 0.01)
            raio_atual = int(self.raio * pulso)
            pygame.draw.circle(tela, (255, 100, 0), pos_tela, raio_atual)
            pygame.draw.circle(tela, self.cor, pos_tela, max(2, raio_atual - 4))
            
        else:
            # Projétil básico com pequeno brilho
            pygame.draw.circle(tela, (255, 255, 255), pos_tela, self.raio + 1)
            pygame.draw.circle(tela, self.cor, pos_tela, self.raio)

class Jogo:
    def __init__(self):
        pygame.init()
        
        # Configurações de janela
        self.tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
        pygame.display.set_caption("Vampire Survivors")
        
        # Carregar imagem do volume
        self.imagem_volume = pygame.image.load("assets/volume.png")
        self.imagem_volume = pygame.transform.scale(self.imagem_volume, (32, 32))
        
        # Configurações de volume
        self.volume = 0.15  # Volume inicial (15%)
        self.arrastando_volume = False
        self.barra_volume_rect = pygame.Rect(60, ALTURA_TELA - 40, 100, 10)
        self.mostrar_controle_volume = False
        self.tempo_ultimo_mouse_volume = 0
        
        # Relógio e tempo
        self.relogio = pygame.time.Clock()
        self.inicio_jogo = pygame.time.get_ticks()
        self.tempo_pausado = 0  # Tempo total em que o jogo ficou pausado
        self.momento_pausa = 0  # Momento em que a última pausa começou
        
        # Estado do jogo
        self.rodando = True
        self.estado = "jogando"  # jogando, upgrade, game_over, vitoria
        self.pausado = False
        
        # Modo Desenvolvedor
        self.modo_dev = False  # Começa desativado
        self.dev_menu_aberto = False
        
        # Inicializar sistema de áudio
        pygame.mixer.init()
        
        # Controle de volume
        self.mostrar_controle_volume = False
        self.tempo_ultimo_mouse_volume = 0
        self.arrastando_volume = False
        
        # Carregar sons
        try:
            self.som_boss_spawn = pygame.mixer.Sound("assets/boss-spawn.mp3")
            self.som_boss_spawn.set_volume(self.volume)  # Definir volume inicial
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o som boss-spawn.mp3: {e}")
            self.som_boss_spawn = None
        
        # Carregar música inicial
        try:
            self.caminho_musica_inicial = "assets/ost1.mp3"
            pygame.mixer.music.load(self.caminho_musica_inicial)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(-1)  # -1 faz tocar em loop infinito
            print("Música inicial iniciada em loop!")
        except Exception as e:
            print(f"Aviso: Não foi possível carregar a música inicial: {e}")
            self.caminho_musica_inicial = None
        
        # Carregar música do boss
        try:
            self.caminho_musica_boss = "assets/boss-theme.mp3"
            self.musica_boss_carregada = False
        except Exception as e:
            print(f"Aviso: Não foi possível carregar a música do boss: {e}")
            self.caminho_musica_boss = None
        
        # Inicialização do cenário espacial
        self.cenario = CenarioEspacial()
        
        # Objetos do jogo
        self.jogador = Jogador(LARGURA_MAPA // 2, ALTURA_MAPA // 2)
        self.inimigos = []
        self.projeteis = []
        self.projeteis_inimigos = []  # Projéteis dos inimigos
        self.projeteis_boss = []
        self.xps = []
        self.itens = []
        self.boss = None
        
        # Habilidades especiais
        self.raios = []
        self.bombas = []
        self.campos = []
        self.campo_permanente = CampoPermanente(self.jogador)
        
        # Sistemas
        self.upgrade_manager = UpgradeManager()
        self.tela_upgrade = None
        self.minimapa = Minimapa()
        
        # Spawning
        self.ultimo_spawn_inimigo = 0
        self.intervalo_spawn = 2000  # 2 segundos inicialmente
        self.ultimo_spawn_item = 0
        self.intervalo_spawn_item = 30000  # 30 segundos
        
        # Sistema de spawn de itens raros
        self.ultimo_coracao = 0
        self.intervalo_coracao = 30000  # 30 segundos mínimo entre corações (muito mais raro)
        
        # Controle de ondas
        self.onda_atual = 1
        self.inimigos_por_onda = 5
        self.max_inimigos_tela = 15
        
        # Mensagem de upgrades máximos
        self.mostrando_mensagem_maximos = False
        self.tempo_mensagem_maximos = 0
        
        # Câmera
        self.camera = [0, 0]
    
    def obter_tempo_jogo(self):
        """Retorna o tempo de jogo em segundos"""
        return (pygame.time.get_ticks() - self.inicio_jogo) / 1000.0
    
    def obter_tempo_restante(self):
        """Retorna o tempo restante em segundos (contagem regressiva)"""
        tempo_jogado = self.obter_tempo_jogo()
        tempo_restante = DURACAO_MAXIMA - tempo_jogado
        return max(0, tempo_restante)  # Não deixar negativo
    
    def atualizar_camera(self):
        """Atualiza a posição da câmera para seguir o jogador"""
        self.camera[0] = self.jogador.pos[0] - LARGURA_TELA // 2
        self.camera[1] = self.jogador.pos[1] - ALTURA_TELA // 2
        
        # Limitar câmera aos bordos do mapa
        self.camera[0] = max(0, min(LARGURA_MAPA - LARGURA_TELA, self.camera[0]))
        self.camera[1] = max(0, min(ALTURA_MAPA - ALTURA_TELA, self.camera[1]))
    
    def spawnar_inimigos(self):
        """Sistema de spawn melhorado com dificuldade progressiva"""
        tempo_atual = pygame.time.get_ticks()
        tempo_jogo = self.obter_tempo_jogo()
        
        # Boss aparece em 10 minutos (600 segundos)
        if tempo_jogo >= 600 and not self.boss:
            self.boss = Boss(
                LARGURA_MAPA // 2 + random.randint(-200, 200),
                ALTURA_MAPA // 2 + random.randint(-200, 200)
            )
            
            # Tocar som de spawn do boss
            if self.som_boss_spawn:
                self.som_boss_spawn.play()
            
            # Tocar música do boss
            self.tocar_musica_boss()
            
            # Limpar inimigos existentes para dar foco ao boss
            self.inimigos.clear()
            # Remover todo XP do chão
            self.xps.clear()
            return
        
        # Não spawnar inimigos se o boss estiver ativo
        if self.boss and self.boss.ativo:
            return
        
        # Ajustar intervalo de spawn baseado no tempo - mais agressivo
        if tempo_jogo < 60:
            self.intervalo_spawn = 1800  # 1.8s
        elif tempo_jogo < 180:
            self.intervalo_spawn = 1200  # 1.2s
        elif tempo_jogo < 300:
            self.intervalo_spawn = 800   # 0.8s
        elif tempo_jogo < 480:
            self.intervalo_spawn = 600   # 0.6s
        elif tempo_jogo < 660:
            self.intervalo_spawn = 400   # 0.4s
        else:
            self.intervalo_spawn = 300   # 0.3s - muito intenso
        
        if tempo_atual - self.ultimo_spawn_inimigo > self.intervalo_spawn:
            # Determinar quantos inimigos spawnar - progressão mais intensa
            quantidade = 1
            if tempo_jogo > 60:   # 1 minuto
                quantidade = 2
            if tempo_jogo > 180:  # 3 minutos
                quantidade = 3
            if tempo_jogo > 300:  # 5 minutos
                quantidade = 4
            if tempo_jogo > 480:  # 8 minutos
                quantidade = 5
            if tempo_jogo > 660:  # 11 minutos
                quantidade = 6
            
            for _ in range(quantidade):
                if len(self.inimigos) < 80:  # Limite maior de inimigos
                    inimigo = gerar_inimigo_aleatorio(self.jogador.pos, tempo_jogo)
                    self.inimigos.append(inimigo)
            
            self.ultimo_spawn_inimigo = tempo_atual
    
    def spawnar_itens(self):
        """Gera itens especiais ocasionalmente"""
        tempo_atual = pygame.time.get_ticks()
        
        # Spawn de itens especiais normais
        if tempo_atual - self.ultimo_spawn_item > self.intervalo_spawn_item:
            if len(self.itens) < 3:  # Limite de itens
                item = gerar_item_aleatorio(self.jogador.pos)
                self.itens.append(item)
            
            self.ultimo_spawn_item = tempo_atual
        
        # Spawn de coração (muito raro)
        if tempo_atual - self.ultimo_coracao > self.intervalo_coracao:
            if random.random() < 0.05:  # 5% chance a cada 10 segundos = muito raro
                pos_x = self.jogador.pos[0] + random.randint(-200, 200)
                pos_y = self.jogador.pos[1] + random.randint(-200, 200)
                
                # Garantir que está dentro dos limites do mapa
                pos_x = max(50, min(LARGURA_MAPA - 50, pos_x))
                pos_y = max(50, min(ALTURA_MAPA - 50, pos_y))
                
                coracao = Item(pos_x, pos_y, "coracao")
                self.itens.append(coracao)
                self.ultimo_coracao = tempo_atual
    
    def atirar(self):
        """Sistema de tiro automático do jogador"""
        if not self.jogador.pode_atirar():
            return
        
        # Encontrar inimigo mais próximo
        alvos = []
        if self.boss and self.boss.ativo:
            alvos.append(self.boss)
        alvos.extend([i for i in self.inimigos if i.ativo])
        
        if not alvos:
            return
        
        alvo = None
        menor_distancia = float('inf')
        
        for possivel_alvo in alvos:
            distancia = calcular_distancia(self.jogador.pos, possivel_alvo.pos)
            if distancia < self.jogador.alcance_tiro and distancia < menor_distancia:
                menor_distancia = distancia
                alvo = possivel_alvo
        
        if alvo:
            self.jogador.atirar()
            
            # Criar múltiplos projéteis se necessário
            for i in range(self.jogador.projeteis_simultaneos):
                angulo_offset = (i - self.jogador.projeteis_simultaneos // 2) * 0.2
                
                dx = alvo.pos[0] - self.jogador.pos[0]
                dy = alvo.pos[1] - self.jogador.pos[1]
                
                # Aplicar offset angular
                cos_offset = math.cos(angulo_offset)
                sin_offset = math.sin(angulo_offset)
                
                dx_rotacionado = dx * cos_offset - dy * sin_offset
                dy_rotacionado = dx * sin_offset + dy * cos_offset
                
                alvo_x = self.jogador.pos[0] + dx_rotacionado
                alvo_y = self.jogador.pos[1] + dy_rotacionado
                
                projetil = Projetil(
                    self.jogador.pos[0], self.jogador.pos[1],
                    alvo_x, alvo_y,
                    self.jogador.dano, self.jogador.velocidade_tiro, 
                    self.jogador.alcance_tiro, self.jogador.atravessar_inimigos
                )
                self.projeteis.append(projetil)
    
    def processar_colisoes(self):
        """Processa todas as colisões do jogo"""
        # Projéteis vs Inimigos
        for projetil in self.projeteis[:]:
            if not projetil.ativo:
                continue
            
            for inimigo in self.inimigos[:]:
                if projetil.colidir_com_inimigo(inimigo):
                    if not inimigo.ativo:
                        xp = inimigo.morrer()
                        if xp:
                            self.xps.append(xp)
                        self.inimigos.remove(inimigo)
        
        # Projéteis vs Boss
        if self.boss and self.boss.ativo:
            for projetil in self.projeteis[:]:
                if not projetil.ativo:
                    continue
                
                distancia = calcular_distancia(projetil.pos, self.boss.pos)
                if distancia < projetil.raio + self.boss.raio:
                    self.boss.receber_dano(projetil.dano)
                    projetil.ativo = False
        
        # Inimigos vs Jogador
        for inimigo in self.inimigos:
            inimigo.atacar_jogador(self.jogador)
        
        # Boss vs Jogador
        if self.boss and self.boss.ativo:
            self.boss.colidir_com_jogador(self.jogador)
        
        # Projéteis do Boss vs Jogador
        for proj_boss in self.projeteis_boss[:]:
            if proj_boss.colidir_com_jogador(self.jogador):
                pass  # Dano já aplicado
        
        # Projéteis dos Inimigos vs Jogador
        for proj_inimigo in self.projeteis_inimigos[:]:
            if proj_inimigo.colidir_com_jogador(self.jogador):
                pass  # Dano já aplicado
        
        # XP vs Jogador
        for xp in self.xps[:]:
            if xp.colidir_com_jogador(self.jogador):
                # Jogador ganha XP
                subiu_nivel = self.jogador.ganhar_xp(xp.valor)
                
                # Se subiu de nível, pausar jogo e mostrar opções
                if subiu_nivel:
                    opcoes = self.upgrade_manager.obter_opcoes_upgrade(self.jogador)
                    if opcoes == "todos_maximos":
                        # Todos os upgrades estão no máximo - mostrar mensagem
                        self.mostrar_mensagem_maximos()
                    else:
                        self.tela_upgrade = TelaUpgrade(opcoes)
                        self.estado = "upgrade"
                
                # Remover XP coletado
                self.xps.remove(xp)
        
        # Itens vs Jogador
        for item in self.itens[:]:
            if item.colidir_com_jogador(self.jogador):
                if item.tipo == "xp_magnetico":
                    usar_item_xp_magnetico(self.xps)
                elif item.tipo == "bomba_tela":
                    novos_xps = usar_item_bomba_tela(self.inimigos, self.jogador.pos, self.camera)
                    self.xps.extend(novos_xps)
                elif item.tipo == "coracao":
                    usar_item_coracao(self.jogador)
                
                self.itens.remove(item)
    
    def atualizar(self):
        """Atualiza o estado do jogo"""
        # Não atualizar se estiver em upgrade
        if self.estado == "upgrade":
            return
            
        # Não atualizar se estiver em game over ou vitória
        if self.estado != "jogando":
            return
            
        if self.pausado or self.estado == "upgrade":
            # Se pausado ou na tela de upgrade, não atualizar o tempo
            if self.momento_pausa == 0:
                self.momento_pausa = pygame.time.get_ticks()
            return
        elif self.momento_pausa > 0:
            # Ao despausar, ajustar o tempo total pausado
            self.tempo_pausado += pygame.time.get_ticks() - self.momento_pausa
            self.momento_pausa = 0
        
        # Atualizar cenário
        self.cenario.atualizar()
        
        keys = pygame.key.get_pressed()
        
        # Atualizar jogador
        self.jogador.mover(keys)
        self.jogador.atualizar()
        
        # Atualizar espadas orbitais com lista de inimigos e boss
        alvos_espadas = list(self.inimigos)  # Começar com inimigos
        if self.boss and self.boss.ativo:
            alvos_espadas.append(self.boss)  # Adicionar boss se ativo
            
        for espada in self.jogador.obter_espadas():
            espada.atualizar(alvos_espadas)
        
        # Verificar se o jogador morreu
        if not self.jogador.esta_vivo():
            self.estado = "game_over"
            return
        
        # Verificar se boss foi derrotado
        if self.boss and self.boss.hp <= 0:
            # Parar música do boss quando ele morrer
            self.parar_musica_boss()
            
            self.boss = None
            self.estado = "vitoria"
            return
        
        # Atualizar câmera
        self.atualizar_camera()
        
        # Spawning
        self.spawnar_inimigos()
        self.spawnar_itens()
        
        # Atirar
        self.atirar()
        
        # Atualizar inimigos
        self.atualizar_inimigos()
        
        # Atualizar boss se existir
        if self.boss and self.boss.ativo:
            projéteis_boss = self.boss.atualizar(self.jogador.pos)
            if projéteis_boss:
                self.projeteis_boss.extend(projéteis_boss)
            
            if self.boss.hp <= 0:
                self.boss.ativo = False
                # Parar música do boss quando ele morrer
                self.parar_musica_boss()
                self.estado = "vitoria"
        
        # Atualizar projéteis
        for projetil in self.projeteis[:]:
            projetil.atualizar()
            if not projetil.ativo:
                self.projeteis.remove(projetil)
        
        # Atualizar projéteis do boss
        for proj_boss in self.projeteis_boss[:]:
            proj_boss.atualizar()
            if not proj_boss.ativo:
                self.projeteis_boss.remove(proj_boss)
        
        # Atualizar projéteis dos inimigos
        for proj_inimigo in self.projeteis_inimigos[:]:
            proj_inimigo.atualizar()
            if not proj_inimigo.ativo:
                self.projeteis_inimigos.remove(proj_inimigo)
        
        # Atualizar XPs
        for xp in self.xps[:]:
            xp.atualizar(self.jogador.pos)
            if not xp.ativo:
                self.xps.remove(xp)
        
        # Atualizar itens
        for item in self.itens[:]:
            item.atualizar()
            if not item.ativo:
                self.itens.remove(item)
        
        # Atualizar habilidades
        self.atualizar_habilidades()
        
        # Atualizar mensagem de upgrades máximos
        if self.mostrando_mensagem_maximos:
            if pygame.time.get_ticks() > self.tempo_mensagem_maximos:
                self.mostrando_mensagem_maximos = False
        
        # Processar colisões
        self.processar_colisoes()
        
        # Atualizar controle de volume (esconder após 3 segundos)
        if self.mostrar_controle_volume:
            tempo_atual = pygame.time.get_ticks()
            if tempo_atual - self.tempo_ultimo_mouse_volume > 3000:  # 3 segundos
                self.mostrar_controle_volume = False
    
    def desenhar(self):
        """Desenha todos os elementos do jogo"""
        # Limpar tela com cor de fundo mais escura
        self.tela.fill((5, 5, 10))  # Azul muito escuro para o espaço
        
        # Desenhar cenário de fundo primeiro
        self.cenario.desenhar(self.tela, self.camera)
        
        # Desenhar objetos do jogo
        for xp in self.xps:
            xp.desenhar(self.tela, self.camera)
        
        for item in self.itens:
            item.desenhar(self.tela, self.camera)
        
        for proj in self.projeteis:
            proj.desenhar(self.tela, self.camera)
        
        for inimigo in self.inimigos:
            inimigo.desenhar(self.tela, self.camera)
        
        for proj_inimigo in self.projeteis_inimigos:
            proj_inimigo.desenhar(self.tela, self.camera)
        
        # Desenhar projéteis do boss
        for proj_boss in self.projeteis_boss:
            proj_boss.desenhar(self.tela, self.camera)
        
        self.jogador.desenhar(self.tela, self.camera)
        
        # Desenhar boss se ativo
        if self.boss and self.boss.ativo:
            self.boss.desenhar(self.tela, self.camera)
        
        # Desenhar habilidades
        for raio in self.raios:
            raio.desenhar(self.tela, self.camera)
        
        for bomba in self.bombas:
            bomba.desenhar(self.tela, self.camera)
        
        for campo in self.campos:
            campo.desenhar(self.tela, self.camera)
        
        # Desenhar campo permanente
        self.campo_permanente.desenhar(self.tela, self.camera)
        
        # UI
        self.desenhar_ui()
        
        # Minimapa
        self.minimapa.desenhar(self.tela, self.jogador, self.inimigos, self.xps, self.itens)
        
        # Tela de upgrade
        if self.estado == "upgrade" and self.tela_upgrade:
            self.tela_upgrade.desenhar(self.tela)
        
        # Mensagem de todos upgrades coletados
        if self.mostrando_mensagem_maximos:
            self.desenhar_mensagem_maximos()
        
        # Telas finais
        elif self.estado == "game_over":
            self.desenhar_game_over()
        elif self.estado == "vitoria":
            self.desenhar_vitoria()
        
        # Menu Desenvolvedor
        if self.modo_dev:
            self.desenhar_menu_dev()
        
        # Desenhar controle de volume
        self.desenhar_controle_volume()
        
        pygame.display.flip()
    
    def desenhar_ui(self):
        """Desenha a interface do usuário com design melhorado"""
        
        # === PAINEL PRINCIPAL (Canto superior esquerdo) ===
        largura_painel = 320
        altura_painel = 160
        
        # Fundo do painel principal com bordas arredondadas
        painel_surf = pygame.Surface((largura_painel, altura_painel))
        painel_surf.set_alpha(140)
        painel_surf.fill((15, 20, 35))
        self.tela.blit(painel_surf, (10, 10))
        
        # Borda dourada sutil
        pygame.draw.rect(self.tela, (255, 215, 0), (10, 10, largura_painel, altura_painel), 2)
        
        # === VIDA ===
        y_offset = 25
        # Texto HP
        desenhar_texto(self.tela, "HP", (30, y_offset - 8), BRANCO, 24, sombra=True)
        
        # Barra de vida visual
        barra_largura = 200
        barra_altura = 8
        x_barra = 80
        y_barra = y_offset - 4
        
        # Fundo da barra
        pygame.draw.rect(self.tela, (50, 20, 20), (x_barra, y_barra, barra_largura, barra_altura))
        
        # Barra atual
        proporcao_vida = self.jogador.hp / self.jogador.hp_max
        largura_vida = int(barra_largura * proporcao_vida)
        cor_vida = VERDE if proporcao_vida > 0.6 else (255, 165, 0) if proporcao_vida > 0.3 else VERMELHO
        pygame.draw.rect(self.tela, cor_vida, (x_barra, y_barra, largura_vida, barra_altura))
        
        # === XP ===
        y_offset += 35
        # Texto XP
        desenhar_texto(self.tela, "XP", (30, y_offset - 8), BRANCO, 24, sombra=True)
        
        # Barra de XP
        y_barra_xp = y_offset - 4
        pygame.draw.rect(self.tela, (20, 30, 50), (x_barra, y_barra_xp, barra_largura, barra_altura))
        proporcao_xp = self.jogador.xp / self.jogador.xp_para_proximo
        largura_xp = int(barra_largura * proporcao_xp)
        pygame.draw.rect(self.tela, AZUL_CLARO, (x_barra, y_barra_xp, largura_xp, barra_altura))
        
        # === TEMPO RESTANTE ===
        y_offset += 45
        tempo_restante = self.obter_tempo_restante()
        minutos = int(tempo_restante // 60)
        segundos = int(tempo_restante % 60)
        
        # Determinar cor baseada no tempo restante
        if tempo_restante <= 60:  # Último minuto
            cor_tempo = VERMELHO
            tempo_texto = f"{minutos:02d}:{segundos:02d}"
        elif tempo_restante <= 180:  # Últimos 3 minutos
            cor_tempo = (255, 165, 0)  # Laranja
            tempo_texto = f"{minutos:02d}:{segundos:02d}"
        else:
            cor_tempo = BRANCO
            tempo_texto = f"{minutos:02d}:{segundos:02d}"
        
        desenhar_texto(self.tela, tempo_texto, (25, y_offset - 8), cor_tempo, 26, sombra=True)
        
        # === HABILIDADES (Canto inferior direito) ===
        x_habilidades = LARGURA_TELA - 300
        y_base = ALTURA_TELA - 240  # Movido para baixo
        
        # Painel de habilidades
        largura_hab = 285
        altura_hab = 220
        hab_surf = pygame.Surface((largura_hab, altura_hab))
        hab_surf.set_alpha(140)
        hab_surf.fill((15, 25, 15))
        self.tela.blit(hab_surf, (x_habilidades, y_base))
        
        # Borda verde para habilidades
        pygame.draw.rect(self.tela, (100, 255, 100), (x_habilidades, y_base, largura_hab, altura_hab), 2)
        
        # Título das habilidades
        desenhar_texto(self.tela, "HABILIDADES", (x_habilidades + 20, y_base + 15), 
                      (100, 255, 100), 18, sombra=True)
        y_hab = y_base + 45
        
        # Dash
        if self.jogador.dash_nivel > 0:
            if self.jogador.dash_cooldown > 0:
                texto = f"Dash: {self.jogador.dash_cooldown//1000 + 1}s"
                cor = (255, 100, 100)
            else:
                texto = "Dash: PRONTO"
                cor = (100, 255, 100)
            desenhar_texto(self.tela, texto, (x_habilidades + 20, y_hab), cor, 16, sombra=True)
            y_hab += 22
        
        # Espada orbital
        if self.jogador.espada_nivel > 0:
            texto = f"Espadas Orbitais Nv.{self.jogador.espada_nivel}"
            desenhar_texto(self.tela, texto, (x_habilidades + 20, y_hab), BRANCO, 16, sombra=True)
            y_hab += 22
        
        # Raios
        if self.jogador.raios_nivel > 0:
            if self.jogador.raios_cooldown > 0:
                texto = f"Raios: {self.jogador.raios_cooldown//1000 + 1}s"
                cor = (255, 100, 100)
            else:
                texto = "Raios: PRONTO"
                cor = (100, 255, 100)
            desenhar_texto(self.tela, texto, (x_habilidades + 20, y_hab), cor, 16, sombra=True)
            y_hab += 22
        
        # Bomba
        if self.jogador.bomba_nivel > 0:
            if self.jogador.bomba_cooldown > 0:
                texto = f"Bomba: {self.jogador.bomba_cooldown//1000 + 1}s"
                cor = (255, 100, 100)
            else:
                texto = "Bomba: PRONTO"
                cor = (100, 255, 100)
            desenhar_texto(self.tela, texto, (x_habilidades + 20, y_hab), cor, 16, sombra=True)
            y_hab += 22
        
        # Escudo
        if self.jogador.escudo_nivel > 0:
            if self.jogador.escudo_cooldown > 0:
                texto = f"Escudo: {self.jogador.escudo_cooldown//1000 + 1}s"
                cor = (255, 100, 100)
            else:
                texto = "Escudo: PRONTO"
                cor = (100, 255, 100)
            desenhar_texto(self.tela, texto, (x_habilidades + 20, y_hab), cor, 16, sombra=True)
            y_hab += 22
        
        # Campo gravitacional
        if self.jogador.campo_nivel > 0:
            texto = f"Campo Gravitacional Nv.{self.jogador.campo_nivel}"
            desenhar_texto(self.tela, texto, (x_habilidades + 20, y_hab), BRANCO, 16, sombra=True)
            y_hab += 22
        
        # === BARRA DO BOSS (se ativo) ===
        if self.boss and self.boss.ativo:
            self.desenhar_barra_boss()
        
        # === CONTROLE DE VOLUME ===
        self.desenhar_controle_volume()
    
    def desenhar_game_over(self):
        """Desenha a tela de game over"""
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        overlay.set_alpha(200)
        overlay.fill(PRETO)
        self.tela.blit(overlay, (0, 0))
        
        desenhar_texto(self.tela, "GAME OVER!", 
                      (LARGURA_TELA // 2 - 80, ALTURA_TELA // 2 - 50), VERMELHO, 48)
        desenhar_texto(self.tela, "Pressione ESC para sair", 
                      (LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 20), BRANCO, 24)
    
    def desenhar_vitoria(self):
        """Desenha a tela de vitória"""
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        overlay.set_alpha(200)
        overlay.fill(PRETO)
        self.tela.blit(overlay, (0, 0))
        
        desenhar_texto(self.tela, "VITÓRIA!", 
                      (LARGURA_TELA // 2 - 60, ALTURA_TELA // 2 - 80), DOURADO, 48)
        desenhar_texto(self.tela, "Obrigado por jogar a demo!", 
                      (LARGURA_TELA // 2 - 150, ALTURA_TELA // 2 - 30), BRANCO, 32)
        desenhar_texto(self.tela, "Pressione ESC para sair", 
                      (LARGURA_TELA // 2 - 100, ALTURA_TELA // 2 + 20), BRANCO, 24)
    
    def processar_eventos(self):
        """Processa eventos do pygame"""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.rodando = False
            
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    if self.estado == "jogando":
                        self.pausado = not self.pausado
                        if self.pausado:
                            self.momento_pausa = pygame.time.get_ticks()
                        else:
                            self.tempo_pausado += pygame.time.get_ticks() - self.momento_pausa
                    elif self.estado == "game_over" or self.estado == "vitoria":
                        self.rodando = False
                
                # Ativar modo dev com F10
                elif evento.key == pygame.K_F10:
                    self.modo_dev = not self.modo_dev
                    if not self.modo_dev:
                        self.dev_menu_aberto = False
                
                # Habilidades especiais (apenas durante o jogo)
                elif self.estado == "jogando":
                    # Dash com ESPAÇO - ÚNICA habilidade manual
                    if evento.key == pygame.K_SPACE:
                        keys = pygame.key.get_pressed()
                        dx, dy = 0, 0
                        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                            dx = -1
                        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                            dx = 1
                        if keys[pygame.K_w] or keys[pygame.K_UP]:
                            dy = -1
                        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                            dy = 1
                        
                        # Se não há direção, dash para frente
                        if dx == 0 and dy == 0:
                            dy = -1
                        
                        # Normalizar direção
                        if dx != 0 and dy != 0:
                            dx *= 0.707
                            dy *= 0.707
                        
                        self.jogador.usar_dash(dx, dy)
                    
                    # Modo Desenvolvedor - teclas de atalho
                    elif self.modo_dev:
                        if evento.key == pygame.K_F1:
                            # Subir de nível instantaneamente
                            self.jogador.xp = self.jogador.xp_para_proximo
                            opcoes = self.upgrade_manager.obter_opcoes_upgrade(self.jogador)
                            if opcoes == "todos_maximos":
                                self.mostrar_mensagem_maximos()
                            else:
                                self.tela_upgrade = TelaUpgrade(opcoes)
                                self.estado = "upgrade"
                        
                        elif evento.key == pygame.K_F2:
                            # Avançar 1 minuto no tempo de jogo
                            self.inicio_jogo -= 60000  # 60 segundos em ms
                        
                        elif evento.key == pygame.K_F3:
                            # Dar todos os upgrades básicos level 1
                            for upgrade_tipo in ['vida', 'dano', 'velocidade', 'alcance', 'cadencia']:
                                if getattr(self.jogador, f"{upgrade_tipo}_nivel") == 0:
                                    fake_upgrade = {
                                        'id': upgrade_tipo,
                                        'nome': f'Dev {upgrade_tipo}',
                                        'descricao': f'Dev upgrade {upgrade_tipo}',
                                        'tipo': upgrade_tipo
                                    }
                                    self.upgrade_manager.aplicar_upgrade(self.jogador, fake_upgrade)
                        
                        elif evento.key == pygame.K_F4:
                            # Dar uma habilidade especial aleatória
                            habilidades = ['espada', 'dash', 'bomba', 'raios', 'campo']
                            for habilidade in habilidades:
                                if getattr(self.jogador, f"{habilidade}_nivel") == 0:
                                    fake_upgrade = {
                                        'id': habilidade,
                                        'nome': f'Dev {habilidade}',
                                        'descricao': f'Dev habilidade {habilidade}',
                                        'tipo': habilidade
                                    }
                                    self.upgrade_manager.aplicar_upgrade(self.jogador, fake_upgrade)
                                    break
                        
                        elif evento.key == pygame.K_F5:
                            # Spawnar boss instantaneamente
                            if not self.boss:
                                self.boss = Boss(
                                    LARGURA_MAPA // 2 + random.randint(-200, 200),
                                    ALTURA_MAPA // 2 + random.randint(-200, 200)
                                )
                                
                                # Tocar som de spawn do boss
                                if self.som_boss_spawn:
                                    self.som_boss_spawn.play()
                                
                                # Tocar música do boss
                                self.tocar_musica_boss()
                        
                        elif evento.key == pygame.K_F6:
                            # Curar completamente
                            self.jogador.hp = self.jogador.hp_max
                        
                        elif evento.key == pygame.K_F7:
                            # Toggle menu dev visual
                            self.dev_menu_aberto = not self.dev_menu_aberto
                        
                        elif evento.key == pygame.K_F8:
                            # Toggle vida infinita
                            self.jogador.vida_infinita = not self.jogador.vida_infinita
            
            # Processar eventos de upgrade (teclado e mouse)
            if self.estado == "upgrade" and self.tela_upgrade:
                escolha = self.tela_upgrade.processar_input(evento)
                if escolha >= 0:
                    upgrade_escolhido = self.tela_upgrade.opcoes[escolha]
                    self.upgrade_manager.aplicar_upgrade(self.jogador, upgrade_escolhido)
                    self.tela_upgrade = None
                    self.estado = "jogando"
            
            # Processar eventos do controle de volume
            if self.estado == "jogando":
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if evento.button == 1:  # Botão esquerdo
                        mouse_x, mouse_y = evento.pos
                        x_barra, y_barra, largura_barra = self.obter_posicao_barra_volume()
                        
                        # Área de clique da barra (um pouco maior para facilitar)
                        area_barra = pygame.Rect(x_barra - 5, y_barra - 5, largura_barra + 10, 18)
                        
                        if area_barra.collidepoint(mouse_x, mouse_y):
                            self.arrastando_volume = True
                            # Calcular novo volume baseado na posição do clique
                            proporcao = (mouse_x - x_barra) / largura_barra
                            proporcao = max(0, min(1, proporcao))  # Limitar entre 0 e 1
                            self.atualizar_volume(proporcao)
                
                elif evento.type == pygame.MOUSEBUTTONUP:
                    if evento.button == 1:  # Botão esquerdo
                        self.arrastando_volume = False
                
                elif evento.type == pygame.MOUSEMOTION:
                    mouse_x, mouse_y = evento.pos
                    x_icone, y_icone = self.obter_posicao_icone_volume()
                    x_barra, y_barra, largura_barra = self.obter_posicao_barra_volume()
                    
                    # Área do ícone e barra de volume
                    area_icone = pygame.Rect(x_icone, y_icone, 32, 32)
                    area_barra = pygame.Rect(x_barra - 5, y_barra - 5, largura_barra + 10, 18)
                    
                    # Mostrar controle se mouse sobre ícone ou barra
                    if area_icone.collidepoint(mouse_x, mouse_y) or area_barra.collidepoint(mouse_x, mouse_y):
                        self.mostrar_controle_volume = True
                        self.tempo_ultimo_mouse_volume = pygame.time.get_ticks()
                    
                    # Atualizar volume se estiver arrastando
                    if self.arrastando_volume:
                        proporcao = (mouse_x - x_barra) / largura_barra
                        proporcao = max(0, min(1, proporcao))  # Limitar entre 0 e 1
                        self.atualizar_volume(proporcao)
        
        return True
    
    def executar(self):
        """Loop principal do jogo"""
        while self.rodando:
            self.processar_eventos()
            
            self.atualizar()
            self.desenhar()
            
            self.relogio.tick(FPS)
        
        pygame.quit()
        sys.exit()

    def atualizar_habilidades(self):
        """Atualiza todas as habilidades especiais"""
        # Verificar e ativar bombas automaticamente
        bomba_dados = self.jogador.verificar_bomba_automatica()
        if bomba_dados:
            bomba = Bomba(bomba_dados['pos'][0], bomba_dados['pos'][1], 
                         bomba_dados['dano'], bomba_dados['raio'],
                         bomba_dados['pos_inicial'], bomba_dados['tempo_voo'])
            self.bombas.append(bomba)
        
        # Verificar e ativar raios automaticamente
        raios_dados = self.jogador.verificar_raios_automaticos()
        if raios_dados:
            # Criar raios aleatórios ao redor do jogador
            for _ in range(raios_dados['quantidade']):
                # Posição aleatória próxima ao jogador
                angulo = random.uniform(0, 2 * math.pi)
                distancia = random.uniform(50, 150)
                x = self.jogador.pos[0] + math.cos(angulo) * distancia
                y = self.jogador.pos[1] + math.sin(angulo) * distancia
                
                raio = Raio(x, y, raios_dados['dano'])
                self.raios.append(raio)
        
        # Atualizar raios
        for raio in self.raios[:]:
            raio.atualizar()
            if not raio.ativo:
                self.raios.remove(raio)
        
        # Atualizar bombas
        for bomba in self.bombas[:]:
            bomba.atualizar()
            if not bomba.ativo:
                self.bombas.remove(bomba)
        
        # Atualizar campos gravitacionais temporários
        for campo in self.campos[:]:
            campo.atualizar()
            if not campo.ativo:
                self.campos.remove(campo)
        
        # Atualizar campo permanente
        self.campo_permanente.atualizar()
        
        # Aplicar efeitos das habilidades nos inimigos
        self.processar_colisoes_habilidades()
    
    def processar_colisoes_habilidades(self):
        """Processa colisões das habilidades especiais"""
        # Espadas orbitais vs Inimigos
        for espada in self.jogador.obter_espadas():
            for inimigo in self.inimigos[:]:
                if espada.colidir_com_inimigo(inimigo):
                    if not inimigo.ativo:
                        xp = inimigo.morrer()
                        if xp:
                            self.xps.append(xp)
                        self.inimigos.remove(inimigo)
            
            # Espadas orbitais vs Boss
            if self.boss and self.boss.ativo:
                if espada.colidir_com_inimigo(self.boss):
                    # Boss recebe dano mas não morre como inimigo normal
                    pass  # Dano já aplicado no método colidir_com_inimigo
        
        # Raios vs Inimigos
        for raio in self.raios:
            for inimigo in self.inimigos[:]:
                if raio.colidir_com_inimigo(inimigo):
                    if not inimigo.ativo:
                        xp = inimigo.morrer()
                        if xp:
                            self.xps.append(xp)
                        self.inimigos.remove(inimigo)
        
        # Bombas vs Inimigos
        for bomba in self.bombas:
            for inimigo in self.inimigos[:]:
                if bomba.colidir_com_inimigo(inimigo):
                    if not inimigo.ativo:
                        xp = inimigo.morrer()
                        if xp:
                            self.xps.append(xp)
                        self.inimigos.remove(inimigo)
        
        # Campo permanente vs Inimigos
        for inimigo in self.inimigos[:]:
            campo_matou = self.campo_permanente.afetar_inimigo(inimigo)
            if campo_matou and not inimigo.ativo:
                xp = inimigo.morrer()
                if xp:
                    self.xps.append(xp)
                self.inimigos.remove(inimigo)
        
        # Campos gravitacionais temporários vs Inimigos
        for campo in self.campos:
            for inimigo in self.inimigos:
                campo.afetar_inimigo(inimigo)
    
    def desenhar_barra_boss(self):
        """Desenha a barra de vida do boss na parte inferior da tela"""
        if not self.boss or not self.boss.ativo:
            return
        
        # Dimensões da barra
        largura_barra = LARGURA_TELA - 100
        altura_barra = 30
        x_barra = 50
        y_barra = ALTURA_TELA - 60
        
        # Fundo da barra
        pygame.draw.rect(self.tela, (50, 0, 0), (x_barra - 2, y_barra - 2, largura_barra + 4, altura_barra + 4))
        pygame.draw.rect(self.tela, (0, 0, 0), (x_barra, y_barra, largura_barra, altura_barra))
        
        # Barra de vida atual
        proporcao_vida = self.boss.hp / self.boss.hp_max
        largura_vida = int(largura_barra * proporcao_vida)
        
        # Cor da barra baseada na vida
        if proporcao_vida > 0.6:
            cor_vida = (255, 0, 0)  # Vermelho
        elif proporcao_vida > 0.3:
            cor_vida = (255, 100, 0)  # Laranja
        else:
            cor_vida = (255, 200, 0)  # Amarelo
        
        if largura_vida > 0:
            pygame.draw.rect(self.tela, cor_vida, (x_barra, y_barra, largura_vida, altura_barra))
        
        # Texto do boss (sem números de HP)
        texto_boss = "BOSS"
        desenhar_texto(self.tela, texto_boss, (x_barra + largura_barra // 2 - 50, y_barra - 30), 
                      VERMELHO, 24, sombra=True)

    def atualizar_inimigos(self):
        """Atualiza todos os inimigos e processa projéteis"""
        for inimigo in self.inimigos[:]:
            if not inimigo.ativo:
                self.inimigos.remove(inimigo)
                continue
            
            # Atualizar inimigo e verificar se criou projétil
            resultado = inimigo.atualizar(self.jogador.pos)
            
            # Verificar se resultado é um projétil (não uma lista)
            if resultado and hasattr(resultado, 'atualizar'):
                self.projeteis_inimigos.append(resultado)
            elif resultado and isinstance(resultado, list):
                # Se por acaso retornou uma lista, adicionar todos
                self.projeteis_inimigos.extend(resultado)
            
            # Verificar colisão com jogador (apenas para inimigos corpo a corpo)
            if hasattr(inimigo, 'alcance_ataque') and hasattr(inimigo, 'tempo_ultimo_ataque'):
                # Inimigos tanque podem atacar corpo a corpo
                if inimigo.tipo == "tanque":
                    distancia = calcular_distancia(inimigo.pos, self.jogador.pos)
                    if distancia < inimigo.alcance_ataque:
                        tempo_atual = pygame.time.get_ticks()
                        if tempo_atual - inimigo.tempo_ultimo_ataque > inimigo.cooldown_ataque:
                            if self.jogador.receber_dano(inimigo.dano):
                                inimigo.tempo_ultimo_ataque = tempo_atual
            else:
                # Inimigos tradicionais (básicos e velozes)
                distancia = calcular_distancia(inimigo.pos, self.jogador.pos)
                if distancia < inimigo.raio + self.jogador.raio:
                    self.jogador.receber_dano(inimigo.dano)

    def mostrar_mensagem_maximos(self):
        """Ativa a mensagem de todos upgrades coletados"""
        self.mostrando_mensagem_maximos = True
        self.tempo_mensagem_maximos = pygame.time.get_ticks() + 1000  # 1 segundo

    def desenhar_mensagem_maximos(self):
        """Desenha a mensagem de todos upgrades coletados"""
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        overlay.set_alpha(150)
        overlay.fill(PRETO)
        self.tela.blit(overlay, (0, 0))
        
        # Fundo da mensagem
        largura_msg = 600
        altura_msg = 200
        x_msg = LARGURA_TELA // 2 - largura_msg // 2
        y_msg = ALTURA_TELA // 2 - altura_msg // 2
        
        pygame.draw.rect(self.tela, (50, 50, 50), (x_msg, y_msg, largura_msg, altura_msg))
        pygame.draw.rect(self.tela, DOURADO, (x_msg, y_msg, largura_msg, altura_msg), 3)
        
        desenhar_texto(self.tela, "TODOS OS UPGRADES COLETADOS!", 
                      (LARGURA_TELA // 2 - 200, ALTURA_TELA // 2 - 50), DOURADO, 36, sombra=True)
        desenhar_texto(self.tela, "Você é imbatível!", 
                      (LARGURA_TELA // 2 - 80, ALTURA_TELA // 2), VERDE, 24, sombra=True)
        desenhar_texto(self.tela, "Continue jogando para enfrentar o BOSS!", 
                      (LARGURA_TELA // 2 - 160, ALTURA_TELA // 2 + 30), BRANCO, 20, sombra=True)

    def desenhar_menu_dev(self):
        """Desenha o menu de desenvolvedor"""
        if not self.dev_menu_aberto:
            # Apenas mostrar indicador no canto
            desenhar_texto(self.tela, "DEV MODE (F7)", (10, 10), AMARELO, 16)
            desenhar_texto(self.tela, "F1:Level F2:+1min F3:Stats F4:Skill F5:Boss F6:Heal F8:God", 
                          (10, 30), BRANCO, 14)
            # Mostrar status de vida infinita
            if self.jogador.vida_infinita:
                desenhar_texto(self.tela, "VIDA INFINITA ATIVA", (10, 50), VERDE, 16)
            return
            
        # Menu completo
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        overlay.set_alpha(180)
        overlay.fill(PRETO)
        self.tela.blit(overlay, (0, 0))
        
        # Fundo do menu
        largura_menu = 500
        altura_menu = 450
        x_menu = LARGURA_TELA // 2 - largura_menu // 2
        y_menu = ALTURA_TELA // 2 - altura_menu // 2
        
        pygame.draw.rect(self.tela, (40, 40, 40), (x_menu, y_menu, largura_menu, altura_menu))
        pygame.draw.rect(self.tela, DOURADO, (x_menu, y_menu, largura_menu, altura_menu), 3)
        
        # Título
        desenhar_texto(self.tela, "MENU DESENVOLVEDOR", 
                      (x_menu + largura_menu // 2 - 140, y_menu + 20), DOURADO, 24)
        
        y_atual = y_menu + 60
        espaco = 35
        
        # Lista de comandos
        comandos = [
            ("F1", "Subir de nível instantaneamente", VERDE),
            ("F2", "Avançar 1 minuto no tempo", AZUL_CLARO),  
            ("F3", "Dar upgrades básicos (level 1)", AMARELO),
            ("F4", "Dar habilidade especial aleatória", ROXO),
            ("F5", "Spawnar boss instantaneamente", VERMELHO),
            ("F6", "Curar jogador completamente", VERDE),
            ("F7", "Fechar este menu", BRANCO),
            ("F8", f"Vida Infinita: {'ON' if self.jogador.vida_infinita else 'OFF'}", 
             VERDE if self.jogador.vida_infinita else VERMELHO)
        ]
        
        for tecla, descricao, cor in comandos:
            # Desenhar tecla
            pygame.draw.rect(self.tela, cor, (x_menu + 20, y_atual - 2, 30, 25))
            desenhar_texto(self.tela, tecla, (x_menu + 25, y_atual), PRETO, 16)
            
            # Desenhar descrição
            desenhar_texto(self.tela, descricao, (x_menu + 65, y_atual), BRANCO, 18)
            y_atual += espaco
        
        # Info atual do jogador
        y_atual += 20
        desenhar_texto(self.tela, f"Nível: {self.jogador.level} | XP: {self.jogador.xp}/{self.jogador.xp_para_proximo}", 
                      (x_menu + 20, y_atual), BRANCO, 16)
        y_atual += 20
        desenhar_texto(self.tela, f"Tempo: {self.obter_tempo_jogo():.1f}s | HP: {self.jogador.hp}/{self.jogador.hp_max}", 
                      (x_menu + 20, y_atual), BRANCO, 16)
        y_atual += 20
        desenhar_texto(self.tela, f"Boss: {'Ativo' if self.boss and self.boss.ativo else 'Inativo'} | Inimigos: {len(self.inimigos)}", 
                      (x_menu + 20, y_atual), BRANCO, 16)

    def tocar_musica_boss(self):
        """Inicia a música do boss"""
        if self.caminho_musica_boss:
            try:
                pygame.mixer.music.stop()  # Parar música atual antes
                pygame.mixer.music.load(self.caminho_musica_boss)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play(-1)  # Tocar em loop
                self.musica_boss_carregada = True
                print("Música do boss iniciada!")
            except Exception as e:
                print(f"Aviso: Erro ao tocar música do boss: {e}")
                self.musica_boss_carregada = False
    
    def parar_musica_boss(self):
        """Para a música do boss e volta para a música normal"""
        if self.caminho_musica_inicial:
            try:
                pygame.mixer.music.load(self.caminho_musica_inicial)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play(-1)  # Voltar a tocar em loop
                self.musica_boss_carregada = False
                print("Voltando para música inicial!")
            except Exception as e:
                print(f"Aviso: Erro ao voltar para música inicial: {e}")

    def atualizar_volume(self, novo_volume):
        """Atualiza o volume de todos os sons do jogo"""
        self.volume = novo_volume
        pygame.mixer.music.set_volume(novo_volume)  # Música de fundo
        # Se houver outros sons, atualizar aqui também

    def obter_posicao_icone_volume(self):
        """Retorna a posição do ícone de volume"""
        return (20, ALTURA_TELA - 40)  # Ajustado para alinhar melhor
    
    def obter_posicao_barra_volume(self):
        """Retorna a posição e tamanho da barra de volume"""
        x_icone, y_icone = self.obter_posicao_icone_volume()
        x_barra = x_icone + 35   # Ajustado para melhor espaçamento
        y_barra = y_icone + 10   # Centralizado com o ícone
        largura_barra = 100      # Barra mais larga para melhor controle
        return x_barra, y_barra, largura_barra
    
    def desenhar_controle_volume(self):
        """Desenha o controle de volume no canto inferior esquerdo"""
        # Desenhar ícone
        x_icone, y_icone = self.obter_posicao_icone_volume()
        self.tela.blit(self.imagem_volume, (x_icone, y_icone))
        
        # Obter posição da barra
        x_barra, y_barra, largura_barra = self.obter_posicao_barra_volume()
        
        # Desenhar barra de volume
        barra_rect = pygame.Rect(x_barra, y_barra, largura_barra, 8)
        pygame.draw.rect(self.tela, (50, 50, 50), barra_rect)  # Fundo
        
        # Desenhar volume atual
        largura_atual = int(largura_barra * self.volume)
        if largura_atual > 0:
            pygame.draw.rect(self.tela, (100, 255, 100), 
                           (x_barra, y_barra, largura_atual, 8))
        
        # Borda da barra
        pygame.draw.rect(self.tela, BRANCO, barra_rect, 1)

if __name__ == "__main__":
    jogo = Jogo()
    jogo.executar() 