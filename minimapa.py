import pygame
from config import *
from utils import *

class Minimapa:
    def __init__(self):
        self.tamanho = MINIMAPA_TAMANHO
        self.x = MINIMAPA_X
        self.y = MINIMAPA_Y
        self.escala_x = self.tamanho / LARGURA_MAPA
        self.escala_y = self.tamanho / ALTURA_MAPA
    
    def mundo_para_minimapa(self, pos_mundo):
        """Converte posição do mundo para posição no minimapa"""
        x = int(pos_mundo[0] * self.escala_x)
        y = int(pos_mundo[1] * self.escala_y)
        return (self.x + x, self.y + y)
    
    def desenhar(self, tela, jogador, inimigos, xps, itens):
        # Fundo do minimapa
        pygame.draw.rect(tela, PRETO, (self.x, self.y, self.tamanho, self.tamanho))
        pygame.draw.rect(tela, BRANCO, (self.x, self.y, self.tamanho, self.tamanho), 2)
        
        # Desenhar XPs (verde pequeno)
        for xp in xps:
            if xp.ativo:
                pos_mini = self.mundo_para_minimapa(xp.pos)
                if (self.x <= pos_mini[0] <= self.x + self.tamanho and 
                    self.y <= pos_mini[1] <= self.y + self.tamanho):
                    pygame.draw.circle(tela, VERDE, pos_mini, 1)
        
        # Desenhar inimigos (vermelho)
        for inimigo in inimigos:
            if inimigo.ativo:
                pos_mini = self.mundo_para_minimapa(inimigo.pos)
                if (self.x <= pos_mini[0] <= self.x + self.tamanho and 
                    self.y <= pos_mini[1] <= self.y + self.tamanho):
                    
                    # Cor baseada no tipo
                    if inimigo.tipo == "tanque":
                        cor = CINZA
                    elif inimigo.tipo == "rapido":
                        cor = LARANJA
                    else:
                        cor = VERMELHO
                    
                    pygame.draw.circle(tela, cor, pos_mini, 2)
        
        # Desenhar itens (amarelo)
        for item in itens:
            if item.ativo:
                pos_mini = self.mundo_para_minimapa(item.pos)
                if (self.x <= pos_mini[0] <= self.x + self.tamanho and 
                    self.y <= pos_mini[1] <= self.y + self.tamanho):
                    pygame.draw.circle(tela, AMARELO, pos_mini, 2)
        
        # Desenhar jogador (azul, maior)
        pos_mini = self.mundo_para_minimapa(jogador.pos)
        if (self.x <= pos_mini[0] <= self.x + self.tamanho and 
            self.y <= pos_mini[1] <= self.y + self.tamanho):
            pygame.draw.circle(tela, AZUL, pos_mini, 3)
            pygame.draw.circle(tela, BRANCO, pos_mini, 3, 1)
        
        # Label
        desenhar_texto(tela, "Mini", (self.x, self.y - 20), BRANCO, 16) 