import pygame
import math
from config import *
from utils import *

class TelaUpgrade:
    def __init__(self, opcoes):
        self.opcoes = opcoes
        self.opcao_selecionada = 0
        self.tempo_criacao = pygame.time.get_ticks()
        
    def desenhar(self, tela):
        """Desenha a tela de upgrade com design premium"""
        # Overlay escuro com transparência
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 20))
        tela.blit(overlay, (0, 0))
        
        # Título principal com glow
        tempo_atual = pygame.time.get_ticks()
        pulsacao = 0.8 + 0.2 * math.sin((tempo_atual - self.tempo_criacao) * 0.005)
        
        titulo_cor = tuple(int(c * pulsacao) for c in (255, 215, 0))  # Dourado pulsante
        desenhar_texto(tela, "🌟 LEVEL UP! 🌟", 
                      (LARGURA_TELA // 2, 80), titulo_cor, 48, 
                      centralizado=True, sombra=True)
        
        desenhar_texto(tela, "Escolha um upgrade:", 
                      (LARGURA_TELA // 2, 130), BRANCO, 24, 
                      centralizado=True, sombra=True)
        
        # Calcular posicionamento das cartas
        num_opcoes = len(self.opcoes)
        largura_carta = 280
        altura_carta = 160
        espacamento = 40
        largura_total = num_opcoes * largura_carta + (num_opcoes - 1) * espacamento
        x_inicial = (LARGURA_TELA - largura_total) // 2
        y_carta = 200
        
        # Desenhar cartas de upgrade
        for i, opcao in enumerate(self.opcoes):
            x_carta = x_inicial + i * (largura_carta + espacamento)
            self.desenhar_carta_upgrade(tela, opcao, x_carta, y_carta, 
                                      largura_carta, altura_carta, 
                                      i == self.opcao_selecionada)
        
        # Instruções na parte inferior
        y_instrucoes = ALTURA_TELA - 80
        desenhar_texto(tela, "⌨️ Setas: Navegar  |  ⏎ Enter/Espaço: Selecionar  |  🖱️ Mouse: Clicar", 
                      (LARGURA_TELA // 2, y_instrucoes), AZUL_CLARO, 20, 
                      centralizado=True, sombra=True)
    
    def desenhar_carta_upgrade(self, tela, opcao, x, y, largura, altura, selecionada):
        """Desenha uma carta de upgrade individual com efeitos visuais"""
        # Efeito de pulsação para carta selecionada
        if selecionada:
            tempo = pygame.time.get_ticks()
            pulsacao = 1.0 + 0.1 * math.sin(tempo * 0.01)
            largura_real = int(largura * pulsacao)
            altura_real = int(altura * pulsacao)
            x_real = x - (largura_real - largura) // 2
            y_real = y - (altura_real - altura) // 2
        else:
            largura_real = largura
            altura_real = altura
            x_real = x
            y_real = y
        
        # Fundo da carta com gradiente
        carta_surface = pygame.Surface((largura_real, altura_real))
        carta_surface.set_alpha(220)
        
        if selecionada:
            # Gradiente dourado para carta selecionada
            for i in range(altura_real):
                alpha = i / altura_real
                cor = (
                    int(60 + alpha * 40),    # R: 60->100
                    int(40 + alpha * 30),    # G: 40->70  
                    int(0 + alpha * 20)      # B: 0->20
                )
                pygame.draw.rect(carta_surface, cor, (0, i, largura_real, 1))
        else:
            # Gradiente azul escuro para cartas não selecionadas
            for i in range(altura_real):
                alpha = i / altura_real
                cor = (
                    int(20 + alpha * 20),    # R: 20->40
                    int(20 + alpha * 30),    # G: 20->50
                    int(40 + alpha * 40)     # B: 40->80
                )
                pygame.draw.rect(carta_surface, cor, (0, i, largura_real, 1))
        
        tela.blit(carta_surface, (x_real, y_real))
        
        # Borda da carta
        cor_borda = (255, 215, 0) if selecionada else (100, 150, 200)
        espessura_borda = 3 if selecionada else 2
        pygame.draw.rect(tela, cor_borda, (x_real, y_real, largura_real, altura_real), espessura_borda)
        
        # Sombra (efeito drop shadow)
        if selecionada:
            sombra_surface = pygame.Surface((largura_real, altura_real))
            sombra_surface.set_alpha(100)
            sombra_surface.fill((255, 215, 0))
            tela.blit(sombra_surface, (x_real + 4, y_real + 4))
        
        # Ícone do upgrade
        icone = self.obter_icone_upgrade(opcao['tipo'])
        desenhar_texto(tela, icone, (x_real + largura_real // 2, y_real + 25), 
                      (255, 255, 255), 36, centralizado=True, sombra=True)
        
        # Nome do upgrade
        cor_nome = (255, 215, 0) if selecionada else BRANCO
        tamanho_nome = 22 if selecionada else 20
        desenhar_texto(tela, opcao['nome'], 
                      (x_real + largura_real // 2, y_real + 70), 
                      cor_nome, tamanho_nome, centralizado=True, sombra=True)
        
        # Descrição do upgrade
        descricao = opcao.get('descricao', '')
        if len(descricao) > 30:
            # Quebrar texto em duas linhas
            meio = len(descricao) // 2
            quebra = descricao.rfind(' ', 0, meio + 10)
            if quebra == -1:
                quebra = meio
            linha1 = descricao[:quebra]
            linha2 = descricao[quebra:].strip()
            
            desenhar_texto(tela, linha1, 
                          (x_real + largura_real // 2, y_real + 100), 
                          AZUL_CLARO, 14, centralizado=True, sombra=True)
            desenhar_texto(tela, linha2, 
                          (x_real + largura_real // 2, y_real + 115), 
                          AZUL_CLARO, 14, centralizado=True, sombra=True)
        else:
            desenhar_texto(tela, descricao, 
                          (x_real + largura_real // 2, y_real + 105), 
                          AZUL_CLARO, 16, centralizado=True, sombra=True)
        
        # Nível atual/máximo
        if 'nivel_atual' in opcao and 'nivel_max' in opcao:
            if opcao['nivel_atual'] >= opcao['nivel_max']:
                nivel_texto = "⭐ MAX"
                cor_nivel = (255, 215, 0)
            else:
                nivel_texto = f"Nível {opcao['nivel_atual'] + 1}/{opcao['nivel_max']}"
                cor_nivel = VERDE
            
            desenhar_texto(tela, nivel_texto, 
                          (x_real + largura_real // 2, y_real + altura_real - 25), 
                          cor_nivel, 14, centralizado=True, sombra=True)
    
    def obter_icone_upgrade(self, tipo):
        """Retorna o ícone emoji para cada tipo de upgrade"""
        icones = {
            'vida': '❤️',
            'dano': '⚔️',
            'velocidade': '💨',
            'alcance': '🎯',
            'cadencia': '⚡',
            'atravessar': '🌟',
            'projeteis': '🔥',
            'espada': '🗡️',
            'dash': '💫',
            'bomba': '💥',
            'raios': '⚡',
            'coleta': '🔮',
            'campo': '🌀'
        }
        return icones.get(tipo, '⭐')
    
    def processar_input(self, evento):
        """Processa entrada do usuário e retorna a opção selecionada (-1 se nenhuma)"""
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_LEFT or evento.key == pygame.K_a:
                self.opcao_selecionada = (self.opcao_selecionada - 1) % len(self.opcoes)
            elif evento.key == pygame.K_RIGHT or evento.key == pygame.K_d:
                self.opcao_selecionada = (self.opcao_selecionada + 1) % len(self.opcoes)
            elif evento.key == pygame.K_RETURN or evento.key == pygame.K_SPACE:
                return self.opcao_selecionada
            elif evento.key >= pygame.K_1 and evento.key <= pygame.K_9:
                numero = evento.key - pygame.K_1
                if numero < len(self.opcoes):
                    return numero
        
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1:  # Clique esquerdo
                mouse_x, mouse_y = evento.pos
                
                # Calcular posicionamento das cartas (mesmo código do desenhar)
                num_opcoes = len(self.opcoes)
                largura_carta = 280
                altura_carta = 160
                espacamento = 40
                largura_total = num_opcoes * largura_carta + (num_opcoes - 1) * espacamento
                x_inicial = (LARGURA_TELA - largura_total) // 2
                y_carta = 200
                
                # Verificar clique em cada carta
                for i in range(num_opcoes):
                    x_carta = x_inicial + i * (largura_carta + espacamento)
                    
                    if (x_carta <= mouse_x <= x_carta + largura_carta and
                        y_carta <= mouse_y <= y_carta + altura_carta):
                        return i
        
        elif evento.type == pygame.MOUSEMOTION:
            # Atualizar seleção baseada na posição do mouse
            mouse_x, mouse_y = evento.pos
            
            num_opcoes = len(self.opcoes)
            largura_carta = 280
            altura_carta = 160
            espacamento = 40
            largura_total = num_opcoes * largura_carta + (num_opcoes - 1) * espacamento
            x_inicial = (LARGURA_TELA - largura_total) // 2
            y_carta = 200
            
            for i in range(num_opcoes):
                x_carta = x_inicial + i * (largura_carta + espacamento)
                
                if (x_carta <= mouse_x <= x_carta + largura_carta and
                    y_carta <= mouse_y <= y_carta + altura_carta):
                    self.opcao_selecionada = i
                    break
        
        return -1  # Nenhuma seleção feita 