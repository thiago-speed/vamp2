import pygame
import random
import math
from config import *
from utils import *

class UpgradeManager:
    def __init__(self):
        self.upgrades_basicos = [
            {"nome": "+1 Dano", "tipo": "dano", "descricao": "Aumenta dano em 1"},
            {"nome": "+10 Vida", "tipo": "vida", "descricao": "Aumenta vida máxima em 10"},
            {"nome": "Múltiplos Tiros", "tipo": "projeteis", "descricao": "Atira mais 1 projétil"},
            {"nome": "Tiro Atravessa", "tipo": "atravessar", "descricao": "Projétil atravessa +1 inimigo"},
            {"nome": "Velocidade Tiro", "tipo": "vel_tiro", "descricao": "Projéteis mais rápidos"},
            {"nome": "Alcance +1", "tipo": "alcance", "descricao": "Maior alcance de tiro"},
            {"nome": "Velocidade +1", "tipo": "velocidade", "descricao": "Movimento mais rápido"}
        ]
        
        self.upgrades_fisicos = [
            {"nome": "Espada", "tipo": "espada", "descricao": "Espada giratória", "max_nivel": 5},
            {"nome": "Raios", "tipo": "raios", "descricao": "Raios caem do céu", "max_nivel": 5},
            {"nome": "Dash", "tipo": "dash", "descricao": "Dash invulnerável", "max_nivel": 5},
            {"nome": "Bomba", "tipo": "bomba", "descricao": "Bomba área", "max_nivel": 5},
            {"nome": "Escudo", "tipo": "escudo", "descricao": "Escudo protetor", "max_nivel": 5},
            {"nome": "Campo", "tipo": "campo", "descricao": "Campo gravitacional", "max_nivel": 5},
            {"nome": "Coleta", "tipo": "coleta", "descricao": "Raio de coleta XP", "max_nivel": 5}
        ]
    
    def obter_opcoes_upgrade(self, jogador):
        """Retorna 3 opções de upgrade aleatórias"""
        opcoes = []
        
        # Combinar upgrades básicos e físicos disponíveis
        upgrades_disponiveis = []
        
        # Adicionar upgrades básicos (verificar limite de vida)
        for upgrade in self.upgrades_basicos:
            if upgrade['tipo'] == 'vida':
                # Verificar se já pegou 5 upgrades de vida
                vida_nivel = getattr(jogador, 'vida_upgrades', 0)
                if vida_nivel < 5:
                    upgrade_copia = upgrade.copy()
                    upgrade_copia['nivel_atual'] = str(vida_nivel)
                    upgrades_disponiveis.append(upgrade_copia)
            else:
                upgrades_disponiveis.append(upgrade)
        
        # Adicionar upgrades físicos que ainda não estão no nível máximo
        for upgrade in self.upgrades_fisicos:
            nivel_atual = getattr(jogador, f"{upgrade['tipo']}_nivel", 0)
            if nivel_atual < upgrade['max_nivel']:
                opcao = upgrade.copy()
                opcao['nivel_atual'] = nivel_atual
                upgrades_disponiveis.append(opcao)
        
        # Escolher 3 opções aleatórias
        if len(upgrades_disponiveis) >= 3:
            opcoes = random.sample(upgrades_disponiveis, 3)
        else:
            opcoes = upgrades_disponiveis
        
        return opcoes
    
    def aplicar_upgrade(self, jogador, upgrade):
        """Aplica um upgrade ao jogador"""
        tipo = upgrade['tipo']
        
        if tipo == "dano":
            jogador.dano += 1
        elif tipo == "vida":
            # Inicializar contador se não existir
            if not hasattr(jogador, 'vida_upgrades'):
                jogador.vida_upgrades = 0
            
            jogador.hp_max += 10
            jogador.hp += 10
            jogador.vida_upgrades += 1
        elif tipo == "projeteis":
            jogador.projeteis_simultaneos += 1
        elif tipo == "atravessar":
            jogador.atravessar_inimigos += 1
        elif tipo == "vel_tiro":
            jogador.velocidade_tiro += 1
        elif tipo == "alcance":
            jogador.alcance_tiro += 50
        elif tipo == "velocidade":
            jogador.velocidade += 0.5
        
        # Upgrades físicos
        elif tipo == "espada":
            jogador.espada_nivel += 1
        elif tipo == "raios":
            jogador.raios_nivel += 1
        elif tipo == "dash":
            jogador.dash_nivel += 1
        elif tipo == "bomba":
            jogador.bomba_nivel += 1
        elif tipo == "escudo":
            jogador.escudo_nivel += 1
        elif tipo == "campo":
            jogador.campo_nivel += 1
        elif tipo == "coleta":
            jogador.coleta_nivel += 1

class TelaUpgrade:
    def __init__(self, opcoes):
        self.opcoes = opcoes
        self.selecionado = 0
        self.ativo = True
        
        # Definir área das cartas para clique (ajustado para 3 cartas)
        self.largura_carta = 250  # Reduzido de 300 para 250
        self.altura_carta = 180   # Reduzido de 200 para 180
        self.espacamento = 40     # Reduzido de 50 para 40
        
        # Calcular posições das cartas
        self.areas_cartas = []
        largura_total = len(self.opcoes) * self.largura_carta + (len(self.opcoes) - 1) * self.espacamento
        x_inicial = (LARGURA_TELA - largura_total) // 2
        y_carta = 250
        
        for i in range(len(self.opcoes)):
            x = x_inicial + i * (self.largura_carta + self.espacamento)
            area = pygame.Rect(x, y_carta, self.largura_carta, self.altura_carta)
            self.areas_cartas.append(area)
    
    def processar_input(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_1 and len(self.opcoes) >= 1:
                self.ativo = False
                return 0
            elif evento.key == pygame.K_2 and len(self.opcoes) >= 2:
                self.ativo = False
                return 1
            elif evento.key == pygame.K_3 and len(self.opcoes) >= 3:
                self.ativo = False
                return 2
            elif evento.key == pygame.K_LEFT and self.selecionado > 0:
                self.selecionado -= 1
            elif evento.key == pygame.K_RIGHT and self.selecionado < len(self.opcoes) - 1:
                self.selecionado += 1
            elif evento.key == pygame.K_RETURN or evento.key == pygame.K_SPACE:
                self.ativo = False
                return self.selecionado
        
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1:  # Clique esquerdo
                pos_mouse = pygame.mouse.get_pos()
                
                # Verificar se clicou em alguma carta
                for i, area in enumerate(self.areas_cartas):
                    if area.collidepoint(pos_mouse):
                        self.ativo = False
                        return i
        
        elif evento.type == pygame.MOUSEMOTION:
            # Atualizar seleção baseada na posição do mouse
            pos_mouse = pygame.mouse.get_pos()
            for i, area in enumerate(self.areas_cartas):
                if area.collidepoint(pos_mouse):
                    self.selecionado = i
        
        return -1
    
    def desenhar(self, tela):
        # Fundo semi-transparente com gradiente
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        overlay.set_alpha(180)
        overlay.fill((10, 10, 30))  # Azul escuro
        tela.blit(overlay, (0, 0))
        
        # Título principal
        desenhar_texto(tela, "VOCE SUBIU DE NIVEL! Escolha um upgrade",
                      (LARGURA_TELA // 2, 80), DOURADO, 48, 
                      centralizado=True, sombra=True)
        
        # Desenhar cartas com efeitos melhorados
        for i, opcao in enumerate(self.opcoes):
            area = self.areas_cartas[i]
            
            # Animação de pulso para carta selecionada
            pulso = 1.0
            if i == self.selecionado:
                pulso = 1.0 + 0.1 * math.sin(pygame.time.get_ticks() * 0.01)
            
            # Calcular dimensões com pulso
            largura_atual = int(area.width * pulso)
            altura_atual = int(area.height * pulso)
            x_atual = area.centerx - largura_atual // 2
            y_atual = area.centery - altura_atual // 2
            
            area_atual = pygame.Rect(x_atual, y_atual, largura_atual, altura_atual)
            
            # Cores baseadas na seleção e tipo
            if i == self.selecionado:
                cor_borda = DOURADO
                cor_fundo = (60, 40, 20)  # Marrom dourado
                cor_sombra = (255, 255, 100)
                espessura_borda = 4
            else:
                cor_borda = BRANCO
                cor_fundo = (25, 25, 35)  # Azul escuro
                cor_sombra = (100, 100, 150)
                espessura_borda = 2
            
            # Desenhar sombra
            sombra = pygame.Rect(area_atual.x + 5, area_atual.y + 5, area_atual.width, area_atual.height)
            pygame.draw.rect(tela, (0, 0, 0), sombra)
            
            # Desenhar fundo da carta com gradiente simulado
            for j in range(area_atual.height // 4):
                alpha = 1 - (j / (area_atual.height // 4))
                cor_grad = tuple(int(c * alpha) for c in cor_fundo)
                linha_rect = pygame.Rect(area_atual.x, area_atual.y + j * 4, area_atual.width, 4)
                pygame.draw.rect(tela, cor_grad, linha_rect)
            
            # Borda principal
            pygame.draw.rect(tela, cor_borda, area_atual, espessura_borda)
            
            # Efeito de brilho se selecionado
            if i == self.selecionado:
                brilho_rect = pygame.Rect(area_atual.x + 4, area_atual.y + 4, 
                                        area_atual.width - 8, area_atual.height - 8)
                pygame.draw.rect(tela, cor_sombra, brilho_rect, 1)
            
            # Ícone do upgrade (baseado no tipo)
            icone_x = area_atual.x + 15
            icone_y = area_atual.y + 15
            
            if opcao.get('tipo') == 'vida':
                # Ícone de coração
                pygame.draw.circle(tela, (255, 100, 100), (icone_x, icone_y), 8)
                pygame.draw.circle(tela, (255, 150, 150), (icone_x - 3, icone_y - 2), 4)
                pygame.draw.circle(tela, (255, 150, 150), (icone_x + 3, icone_y - 2), 4)
            elif opcao.get('tipo') == 'espada':
                # Ícone de espada
                pygame.draw.line(tela, (200, 200, 255), (icone_x - 5, icone_y + 5), (icone_x + 5, icone_y - 5), 3)
                pygame.draw.circle(tela, (139, 69, 19), (icone_x, icone_y + 5), 3)
            elif opcao.get('tipo') == 'raios':
                # Ícone de raio
                pontos = [(icone_x - 3, icone_y - 6), (icone_x + 2, icone_y), 
                         (icone_x - 2, icone_y), (icone_x + 3, icone_y + 6)]
                pygame.draw.lines(tela, (255, 255, 150), False, pontos, 2)
            elif opcao.get('tipo') == 'bomba':
                # Ícone de bomba
                pygame.draw.circle(tela, (255, 100, 0), (icone_x, icone_y), 6)
                pygame.draw.line(tela, (255, 200, 0), (icone_x - 3, icone_y - 6), (icone_x - 1, icone_y - 4), 2)
            else:
                # Ícone genérico
                pygame.draw.circle(tela, cor_borda, (icone_x, icone_y), 6, 2)
            
            # Nome do upgrade
            nome = opcao['nome']
            if opcao.get('nivel_atual', -1) >= 0:
                nivel = opcao.get('nivel_atual', 0) + 1
                if nivel == 5:
                    nome += " MAX"
                    cor_nome = DOURADO
                else:
                    nome += f" [{nivel}]"
                    cor_nome = BRANCO
            else:
                cor_nome = BRANCO
            
            # Centralizar texto na carta
            texto_x = area_atual.centerx - 80
            texto_y = area_atual.centery - 25
            
            # Sombra do texto
            desenhar_texto(tela, nome, (texto_x + 1, texto_y + 1), PRETO, 20)
            desenhar_texto(tela, nome, (texto_x, texto_y), cor_nome, 20)
            
            # Descrição
            desenhar_texto(tela, opcao['descricao'], (texto_x + 1, texto_y + 26), PRETO, 14)
            desenhar_texto(tela, opcao['descricao'], (texto_x, texto_y + 25), CINZA, 14)
            
            # Número da carta com efeito
            num_x, num_y = area_atual.x + 8, area_atual.y + 8
            for offset in [(0, 0), (-1, -1)]:
                cor = cor_borda if offset == (0, 0) else PRETO
                desenhar_texto(tela, str(i + 1), (num_x + offset[0], num_y + offset[1]), cor, 28)
        
        # Instruções com efeito
        instrucoes_y = ALTURA_TELA - 80
        for offset in [(0, 0), (-1, -1)]:
            cor = BRANCO if offset == (0, 0) else PRETO
            desenhar_texto(tela, "Clique na carta ou pressione 1/2/3", 
                          (LARGURA_TELA // 2 - 200 + offset[0], instrucoes_y + offset[1]), cor, 18) 