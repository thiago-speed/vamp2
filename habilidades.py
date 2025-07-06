import pygame
import random
import math
from config import *
from utils import *

class Raio:
    def __init__(self, x, y, dano):
        self.pos = [x, y]
        self.dano = dano
        self.ativo = True
        self.duracao = 40  
        self.animacao = 0
        self.raio_dano = 35
        self.pontos_raio = self.gerar_pontos_raio()
        self.brilho_particulas = []
        self.gerar_particulas_brilho()
        
    def gerar_particulas_brilho(self):
        """Gera partículas de brilho ao redor do raio"""
        for _ in range(8):
            angulo = random.uniform(0, 2 * math.pi)
            distancia = random.uniform(10, 25)
            self.brilho_particulas.append({
                'x': self.pos[0] + math.cos(angulo) * distancia,
                'y': self.pos[1] + math.sin(angulo) * distancia,
                'vida': random.randint(15, 25),
                'vida_max': 25
            })
        
    def gerar_pontos_raio(self):
        """Gera pontos para desenhar um raio ramificado mais suave"""
        pontos = []
        
        
        x_inicio = self.pos[0] + random.randint(-30, 30)
        y_inicio = self.pos[1] - 250
        
        
        x_fim = self.pos[0]
        y_fim = self.pos[1]
        
        
        num_segmentos = random.randint(8, 12)
        for i in range(num_segmentos + 1):
            progresso = i / num_segmentos
            
            x = x_inicio + (x_fim - x_inicio) * progresso
            y = y_inicio + (y_fim - y_inicio) * progresso
            
            
            if i > 0 and i < num_segmentos:
                variacao = math.sin(progresso * math.pi * 3) * 10
                x += variacao + random.randint(-8, 8)
                y += random.randint(-3, 3)
            
            pontos.append((x, y))
        
        
        ramificacoes = []
        for i in range(2, len(pontos) - 2):
            if random.random() < 0.4:  
                base_x, base_y = pontos[i]
                
                angulo = random.uniform(-math.pi/3, math.pi/3)
                comprimento = random.uniform(20, 50)
                ram_x = base_x + math.cos(angulo) * comprimento
                ram_y = base_y + math.sin(angulo) * comprimento
                ramificacoes.append([(base_x, base_y), (ram_x, ram_y)])
        
        return pontos, ramificacoes
    
    def atualizar(self):
        self.animacao += 1
        if self.animacao >= self.duracao:
            self.ativo = False
        
        
        for particula in self.brilho_particulas:
            particula['vida'] -= 1
    
    def colidir_com_inimigo(self, inimigo):
        if not self.ativo:
            return False
        
        distancia = calcular_distancia(self.pos, inimigo.pos)
        if distancia < self.raio_dano:
            inimigo.receber_dano(self.dano)
            return True
        
        return False
    
    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        
        if esta_na_tela(self.pos, camera):
            pontos_principais, ramificacoes = self.pontos_raio
            
            
            pontos_tela = []
            for x, y in pontos_principais:
                pos_tela = posicao_na_tela([x, y], camera)
                pontos_tela.append((int(pos_tela[0]), int(pos_tela[1])))
            
            
            progresso = self.animacao / self.duracao
            intensidade = 1.0 - (progresso * 0.3)  
            if (self.animacao // 2) % 3 == 0:  
                intensidade *= 1.2
            
            
            pos_tela_centro = posicao_na_tela(self.pos, camera)
            raio_aura = int(self.raio_dano * (1.5 - progresso))
            if raio_aura > 0:
                cor_aura = tuple(max(0, min(255, int(c * intensidade * 0.1))) for c in (200, 200, 255))
                pygame.draw.circle(tela, cor_aura, (int(pos_tela_centro[0]), int(pos_tela_centro[1])), raio_aura)
            
            
            cores = [
                (255, 255, 255),  
                (220, 220, 255),  
                (180, 180, 255),  
                (140, 140, 255),  
            ]
            
            for i, cor in enumerate(cores):
                cor_final = tuple(max(0, min(255, int(c * intensidade))) for c in cor)
                if len(pontos_tela) > 1:
                    for j in range(len(pontos_tela) - 1):
                        pygame.draw.line(tela, cor_final, pontos_tela[j], pontos_tela[j + 1], max(1, 5 - i))
            
            
            for ramificacao in ramificacoes:
                pontos_ram = []
                for x, y in ramificacao:
                    pos_tela = posicao_na_tela([x, y], camera)
                    pontos_ram.append((int(pos_tela[0]), int(pos_tela[1])))
                
                if len(pontos_ram) == 2:
                    cor_ram = tuple(max(0, min(255, int(c * intensidade * 0.8))) for c in (220, 220, 255))
                    pygame.draw.line(tela, cor_ram, pontos_ram[0], pontos_ram[1], 3)
                    
                    cor_ram_brilho = tuple(max(0, min(255, int(c * intensidade))) for c in (255, 255, 255))
                    pygame.draw.line(tela, cor_ram_brilho, pontos_ram[0], pontos_ram[1], 1)
            
            
            for particula in self.brilho_particulas:
                if particula['vida'] > 0:
                    vida_prop = particula['vida'] / particula['vida_max']
                    part_pos = posicao_na_tela([particula['x'], particula['y']], camera)
                    cor_part = tuple(max(0, min(255, int(c * vida_prop * intensidade))) for c in (255, 255, 200))
                    tamanho = max(1, int(3 * vida_prop))
                    pygame.draw.circle(tela, cor_part, (int(part_pos[0]), int(part_pos[1])), tamanho)
            
            
            raio_circulo = int(self.raio_dano * (1.2 - progresso))
            if raio_circulo > 0:
                for i in range(3):
                    raio_onda = raio_circulo - (i * 8)
                    if raio_onda > 0:
                        alpha = intensidade * (1 - i * 0.3)
                        cor_circulo = tuple(max(0, min(255, int(c * alpha))) for c in (255, 255, 150))
                        pygame.draw.circle(tela, cor_circulo, (int(pos_tela_centro[0]), int(pos_tela_centro[1])), raio_onda, 2)

class Bomba:
    def __init__(self, x, y, dano, raio, pos_inicial=None, tempo_voo=60):
        self.pos = [x, y]
        self.pos_final = [x, y]  
        self.pos_inicial = pos_inicial if pos_inicial else [x, y]
        self.dano = dano
        self.raio = raio
        self.ativo = True
        
        
        self.tempo_voo = tempo_voo
        self.tempo_atual = 0
        self.altura_maxima = 100  
        
        
        self.pos_atual = list(self.pos_inicial)
        
        self.tempo_vida = pygame.time.get_ticks() + (tempo_voo * 16)  
        self.animacao = 0
        self.inimigos_atingidos = []
        self.particulas = []
        self.ondas_choque = []
        
        
        self.voando = True
        self.explodindo = False
        
    def atualizar(self):
        if self.voando:
            self.atualizar_voo()
        elif self.explodindo:
            self.atualizar_explosao()
        
        if pygame.time.get_ticks() > self.tempo_vida:
            self.ativo = False
        
    def atualizar_voo(self):
        """Atualiza o movimento em arco da bomba"""
        self.tempo_atual += 1
        
        if self.tempo_atual >= self.tempo_voo:
            
            self.voando = False
            self.explodindo = True
            self.pos_atual = list(self.pos_final)
            self.gerar_particulas()
            self.gerar_ondas()
            self.tempo_vida = pygame.time.get_ticks() + 600  
            return
        
        
        progresso = self.tempo_atual / self.tempo_voo
        
        
        self.pos_atual[0] = self.pos_inicial[0] + (self.pos_final[0] - self.pos_inicial[0]) * progresso
        self.pos_atual[1] = self.pos_inicial[1] + (self.pos_final[1] - self.pos_inicial[1]) * progresso
        
        
        altura_arco = 4 * self.altura_maxima * progresso * (1 - progresso)
        self.pos_atual[1] -= altura_arco
    
    def atualizar_explosao(self):
        """Atualiza a animação da explosão"""
        self.animacao += 1
        
        
        for particula in self.particulas[:]:
            particula['x'] += particula['vx']
            particula['y'] += particula['vy']
            particula['vida'] -= 1
            particula['vx'] *= 0.96  
            particula['vy'] *= 0.96
            particula['rotacao'] += particula['vel_rotacao']
            
            
            particula['vy'] += 0.1
            
            if particula['vida'] <= 0:
                self.particulas.remove(particula)
    
    def gerar_ondas(self):
        """Gera ondas de choque em momentos diferentes"""
        for i in range(4):
            self.ondas_choque.append({
                'inicio': i * 8,  
                'raio_max': self.raio + (i * 15),
                'espessura': 4 - i,
                'cor': [(255, 120 - i*20, 0), (255, 180 - i*30, 50), (255, 220 - i*40, 100)][min(i, 2)]
            })
    
    def gerar_particulas(self):
        """Gera partículas mais detalhadas para a explosão"""
        for _ in range(30):  
            angulo = random.uniform(0, 2 * math.pi)
            velocidade = random.uniform(4, 15)
            vida = random.randint(30, 60)
            
            particula = {
                'x': self.pos_atual[0],
                'y': self.pos_atual[1],
                'vx': math.cos(angulo) * velocidade,
                'vy': math.sin(angulo) * velocidade,
                'vida': vida,
                'vida_max': vida,
                'tamanho': random.randint(4, 10),
                'rotacao': random.uniform(0, 2 * math.pi),
                'vel_rotacao': random.uniform(-0.3, 0.3)
            }
            self.particulas.append(particula)
    
    def colidir_com_inimigo(self, inimigo):
        if not self.explodindo:
            return False
        
        
        if hasattr(inimigo, 'fase'):  
            distancia = calcular_distancia(self.pos_atual, inimigo.pos)
            if distancia < self.raio + inimigo.raio:
                inimigo.receber_dano(self.dano, fonte="continuo")
                return True
        
        elif inimigo not in self.inimigos_atingidos:
            distancia = calcular_distancia(self.pos_atual, inimigo.pos)
            if distancia < self.raio + inimigo.raio:
                inimigo.receber_dano(self.dano)
                self.inimigos_atingidos.append(inimigo)
                return True
        return False
    
    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        
        if self.voando:
            self.desenhar_voo(tela, camera)
        elif self.explodindo:
            self.desenhar_explosao(tela, camera)
    
    def desenhar_voo(self, tela, camera):
        """Desenha a bomba durante o voo"""
        pos_tela = posicao_na_tela(self.pos_atual, camera)
        if esta_na_tela(self.pos_atual, camera):
            
            raio_bomba = 8 + int(2 * math.sin(self.tempo_atual * 0.3))
            
            
            pygame.draw.circle(tela, (50, 50, 50), 
                             (int(pos_tela[0] + 2), int(pos_tela[1] + 2)), raio_bomba)
            
            
            pygame.draw.circle(tela, (80, 80, 80), (int(pos_tela[0]), int(pos_tela[1])), raio_bomba)
            
            
            pygame.draw.circle(tela, (120, 120, 120), (int(pos_tela[0]), int(pos_tela[1])), raio_bomba - 2)
            
            
            pavio_x = pos_tela[0] + random.randint(-3, 3)
            pavio_y = pos_tela[1] - raio_bomba - 5 + random.randint(-2, 2)
            cor_pavio = random.choice([(255, 100, 0), (255, 150, 0), (255, 200, 0)])
            pygame.draw.circle(tela, cor_pavio, (int(pavio_x), int(pavio_y)), 3)
            
            
            for i in range(3):
                rastro_x = pos_tela[0] + random.randint(-8, 8)
                rastro_y = pos_tela[1] + random.randint(-8, 8)
                cor_rastro = (255, random.randint(80, 200), 0)
                tamanho_rastro = random.randint(1, 2)
                pygame.draw.circle(tela, cor_rastro, (int(rastro_x), int(rastro_y)), tamanho_rastro)
    
    def desenhar_explosao(self, tela, camera):
        """Desenha a explosão da bomba"""
        pos_tela = posicao_na_tela(self.pos_atual, camera)
        if esta_na_tela(self.pos_atual, camera):
            progresso = min(1.0, self.animacao / 36)  
            
            
            for onda in self.ondas_choque:
                if self.animacao >= onda['inicio']:
                    onda_progresso = min(1.0, (self.animacao - onda['inicio']) / 25)
                    raio_atual = int(onda['raio_max'] * onda_progresso)
                    alpha = max(0.0, 1.0 - onda_progresso)
                    
                    if raio_atual > 0 and alpha > 0:
                        
                        cor_original = onda['cor']
                        cor_final = tuple(max(0, min(255, int(c * alpha))) for c in cor_original)
                        if any(c > 0 for c in cor_final):  
                            pygame.draw.circle(tela, cor_final, (int(pos_tela[0]), int(pos_tela[1])), 
                                             raio_atual, max(1, int(onda['espessura'] * alpha)))
            
            
            if progresso < 0.3:
                raio_flash = int(25 * (1 - progresso * 3))
                if raio_flash > 0:
                    pygame.draw.circle(tela, (255, 255, 255), (int(pos_tela[0]), int(pos_tela[1])), raio_flash)
                    
                    pygame.draw.circle(tela, (255, 200, 100), (int(pos_tela[0]), int(pos_tela[1])), raio_flash + 8, 3)
            
            
            for particula in self.particulas:
                if esta_na_tela([particula['x'], particula['y']], camera):
                    part_pos = posicao_na_tela([particula['x'], particula['y']], camera)
                    vida_prop = particula['vida'] / particula['vida_max']
                    
                    
                    if vida_prop > 0.8:
                        cor_base = (255, 255, 255)  
                    elif vida_prop > 0.6:
                        cor_base = (255, 255, 150)  
                    elif vida_prop > 0.4:
                        cor_base = (255, 180, 0)    
                    elif vida_prop > 0.2:
                        cor_base = (255, 100, 0)    
                    else:
                        cor_base = (180, 50, 0)     
                    
                    
                    cor_part = tuple(max(0, min(255, int(c * vida_prop))) for c in cor_base)
                    
                    tamanho = max(1, int(particula['tamanho'] * vida_prop))
                    if tamanho > 0 and any(c > 0 for c in cor_part):
                        
                        pygame.draw.circle(tela, cor_part, (int(part_pos[0]), int(part_pos[1])), tamanho)
                        
                        if tamanho > 2:
                            cor_brilho = tuple(max(0, min(255, c + 50)) for c in cor_part)
                            pygame.draw.circle(tela, cor_brilho, (int(part_pos[0]), int(part_pos[1])), tamanho // 2)

class CampoGravitacional:
    def __init__(self, x, y, forca, raio, duracao):
        self.pos = [x, y]
        self.forca = forca
        self.raio = raio
        self.ativo = True
        self.tempo_vida = pygame.time.get_ticks() + duracao
        self.animacao = 0
    
    def atualizar(self):
        if pygame.time.get_ticks() > self.tempo_vida:
            self.ativo = False
        self.animacao += 1
    
    def afetar_inimigo(self, inimigo):
        if not self.ativo:
            return False
        
        # Não afeta o boss
        if hasattr(inimigo, 'tipo') and inimigo.tipo == 'boss':
            return False
        
        distancia = calcular_distancia(self.pos, inimigo.pos)
        if distancia < self.raio:
            
            tempo_atual = pygame.time.get_ticks()
            
            
            if not hasattr(inimigo, 'ultimo_dano_campo'):
                inimigo.ultimo_dano_campo = 0
                inimigo.intervalo_dano_campo = 500  
            
            if tempo_atual - inimigo.ultimo_dano_campo > inimigo.intervalo_dano_campo:
                
                dano_campo = self.forca * 2  
                inimigo.receber_dano(dano_campo)
                inimigo.ultimo_dano_campo = tempo_atual
                return True
        
        return False
    
    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        
        pos_tela = posicao_na_tela(self.pos, camera)
        if esta_na_tela(self.pos, camera):
            
            intensidade = int(128 + 127 * math.sin(self.animacao * 0.2))
            cor = (max(0, min(255, intensidade // 2)), 0, max(0, min(255, intensidade)))
            
            
            pygame.draw.circle(tela, cor, (int(pos_tela[0]), int(pos_tela[1])), self.raio, 2)
            
            pygame.draw.circle(tela, (255, 0, 255), (int(pos_tela[0]), int(pos_tela[1])), 8)

class CampoPermanente:
    def __init__(self, jogador):
        self.jogador = jogador
        self.animacao = 0
        self.ultimo_dano = 0
        self.intervalo_dano = 500  
    
    def atualizar(self):
        self.animacao += 1
    
    def afetar_inimigo(self, inimigo):
        campo_dados = self.jogador.obter_campo_ativo()
        if not campo_dados:
            return False
        
        # Não afeta o boss
        if hasattr(inimigo, 'tipo') and inimigo.tipo == 'boss':
            return False
        
        distancia = calcular_distancia(self.jogador.pos, inimigo.pos)
        if distancia < campo_dados['raio']:
            
            tempo_atual = pygame.time.get_ticks()
            
            
            if not hasattr(inimigo, 'ultimo_dano_campo_permanente'):
                inimigo.ultimo_dano_campo_permanente = 0
                inimigo.intervalo_dano_campo_permanente = 500  
            
            if tempo_atual - inimigo.ultimo_dano_campo_permanente > inimigo.intervalo_dano_campo_permanente:
                
                dano_campo = campo_dados['dano']
                if self.jogador.campo_nivel >= 5:
                    dano_campo *= 1.5  
                inimigo.receber_dano(dano_campo)
                inimigo.ultimo_dano_campo_permanente = tempo_atual
                return True
        
        return False
    
    def desenhar(self, tela, camera):
        campo_dados = self.jogador.obter_campo_ativo()
        if not campo_dados:
            return
        
        pos_tela = posicao_na_tela(self.jogador.pos, camera)
        if esta_na_tela(self.jogador.pos, camera):
            
            intensidade_base = 32 + 31 * math.sin(self.animacao * 0.08)
            
            
            for i in range(4):
                raio_circulo = campo_dados['raio'] - (i * 15)
                if raio_circulo > 0:
                    alpha = intensidade_base * (1 - i * 0.2)
                    if self.jogador.campo_nivel >= 5:
                        
                        cor = (max(0, min(255, int(alpha * 0.8))), 0, max(0, min(255, int(alpha * 1.5))))
                    else:
                        cor = (max(0, min(255, int(alpha * 0.3))), 0, max(0, min(255, int(alpha))))
                    
                    pygame.draw.circle(tela, cor, (int(pos_tela[0]), int(pos_tela[1])), raio_circulo, 1)
            
            
            raio_centro = 8 + int(4 * math.sin(self.animacao * 0.15))
            if self.jogador.campo_nivel >= 5:
                cor_centro = (150, 0, 255)  
            else:
                cor_centro = (80, 0, 160)   
            pygame.draw.circle(tela, cor_centro, (int(pos_tela[0]), int(pos_tela[1])), raio_centro) 