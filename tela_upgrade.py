import pygame
import math
from config import *
from utils import *
import os


class TelaUpgrade:
    def __init__(self, opcoes):
        self.opcoes = opcoes
        self.opcao_selecionada = 0
        self.tempo_criacao = pygame.time.get_ticks()
        self.cache_imagens = {}
        self.carregar_imagens_upgrades()

    def carregar_imagens_upgrades(self):
        mapeamento_imagens = {
            'vida': 'hearth-removebg-preview.png',
            'dano': 'dmg.png',
            'velocidade': 'speed.png',
            'alcance': 'range.png',
            'cadencia': 'fire-rate.png',
            'atravessar': 'piercing-shots.png',
            'projeteis': 'multi-shots.png',
            'espada': 'swords-around.png',
            'dash': 'dash.png',
            'bomba': 'bomb.png',
            'raios': 'lightning-upgrade.png',
            'coleta': 'magnet.png',
            'campo': 'black-hole.png',
            'vida_lendaria': 'legendary-hearth.png',
            'dano_lendaria': 'legendary-dmg.png',
            'velocidade_lendaria': 'legendary-speed.png',
            'alcance_lendaria': 'legendary-range.png',
            'cadencia_lendaria': 'fire-rate.png',
            'atravessar_lendaria': 'legendary-piercing-shots.png',
            'projeteis_lendaria': 'legendary-multi-shots.png',
            'espada_lendaria': 'legendary-swords-around.png',
            'dash_lendaria': 'legendary-dash.png',
            'bomba_lendaria': 'legendary-bomb.png',
            'raios_lendaria': 'legendary-lightning.png',
            'coleta_lendaria': 'legendary-magnet.png',
            'campo_lendaria': 'legendary-black-hole.png'
        }

        for tipo, nome_arquivo in mapeamento_imagens.items():
            caminho_imagem = os.path.join('assets', nome_arquivo)
            try:
                if os.path.exists(caminho_imagem):
                    imagem_original = pygame.image.load(caminho_imagem).convert_alpha()
                    imagem_redimensionada = pygame.transform.scale(imagem_original, (70, 70))
                    self.cache_imagens[tipo] = imagem_redimensionada
                else:
                    print(f"Imagem não encontrada: {caminho_imagem}")
                    self.cache_imagens[tipo] = None
            except pygame.error as e:
                print(f"Erro ao carregar imagem {nome_arquivo}: {e}")
                self.cache_imagens[tipo] = None

    def obter_imagem_upgrade(self, tipo):
        return self.cache_imagens.get(tipo, None)

    def desenhar(self, tela):
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 15))
        tela.blit(overlay, (0, 0))

        tempo_atual = pygame.time.get_ticks()
        pulsacao = 0.8 + 0.2 * math.sin((tempo_atual - self.tempo_criacao) * 0.005)
        titulo_cor = tuple(int(c * pulsacao) for c in (255, 215, 0))

        desenhar_texto(tela, "VOCE SUBIU DE NIVEL!", 
                      (LARGURA_TELA // 2, 60), titulo_cor, 52, 
                      centralizado=True, sombra=True)
        desenhar_texto(tela, "Escolha uma carta de upgrade:", 
                      (LARGURA_TELA // 2, 120), BRANCO, 28, 
                      centralizado=True, sombra=True)

        num_opcoes = len(self.opcoes)
        largura_carta = 220
        altura_carta = 300
        espacamento = 60
        largura_total = num_opcoes * largura_carta + (num_opcoes - 1) * espacamento
        x_inicial = (LARGURA_TELA - largura_total) // 2
        y_carta = 160

        for i, opcao in enumerate(self.opcoes):
            x_carta = x_inicial + i * (largura_carta + espacamento)
            self.desenhar_carta_upgrade(tela, opcao, x_carta, y_carta, 
                                      largura_carta, altura_carta, 
                                      i == self.opcao_selecionada)

        desenhar_texto(tela, "Navegacao: Setas ou Mouse  |  Selecionar: Enter/Espaco/Clique",
                      (LARGURA_TELA // 2, ALTURA_TELA - 40), BRANCO, 22, 
                      centralizado=True, sombra=True)

    def desenhar_carta_upgrade(self, tela, opcao, x, y, largura, altura, selecionada):
        eh_lendaria = opcao.get('raridade') == 'lendaria' or opcao.get('id', '').endswith('_lendaria')

        if selecionada:
            tempo = pygame.time.get_ticks()
            pulsacao = 1.0 + 0.05 * math.sin(tempo * 0.01)
            y_offset = -8
            largura_real = int(largura * pulsacao)
            altura_real = int(altura * pulsacao)
            x_real = x - (largura_real - largura) // 2
            y_real = y - (altura_real - altura) // 2 + y_offset
        else:
            largura_real = largura
            altura_real = altura
            x_real = x
            y_real = y

        if selecionada or eh_lendaria:
            sombra_offset = 8 if selecionada else 5
            sombra_surface = pygame.Surface((largura_real + sombra_offset, altura_real + sombra_offset))
            sombra_surface.set_alpha(100)
            sombra_surface.fill((0, 0, 0))
            self.desenhar_retangulo_arredondado(sombra_surface, (0, 0, 0), 
                                              (0, 0, largura_real + sombra_offset, altura_real + sombra_offset), 15)
            tela.blit(sombra_surface, (x_real + sombra_offset, y_real + sombra_offset))

        carta_surface = pygame.Surface((largura_real, altura_real))
        carta_surface.set_alpha(255)

        if eh_lendaria:
            cor_base = (40, 30, 10)
            cor_topo = (120, 90, 30)
        else:
            cor_base = (25, 35, 50)
            cor_topo = (45, 55, 80)

        for i in range(altura_real):
            alpha = i / altura_real
            cor_atual = tuple(int(cor_base[j] + (cor_topo[j] - cor_base[j]) * alpha) for j in range(3))
            pygame.draw.rect(carta_surface, cor_atual, (0, i, largura_real, 1))

        self.desenhar_retangulo_arredondado(carta_surface, cor_topo, 
                                          (0, 0, largura_real, altura_real), 15)

        if eh_lendaria:
            for offset in range(3, 0, -1):
                alpha = 60 - offset * 15
                brilho_surface = pygame.Surface((largura_real - offset*4, altura_real - offset*4))
                brilho_surface.set_alpha(alpha)
                brilho_surface.fill((255, 215, 0))
                self.desenhar_retangulo_arredondado(brilho_surface, (255, 215, 0),
                                                  (0, 0, largura_real - offset*4, altura_real - offset*4), 12)
                carta_surface.blit(brilho_surface, (offset*2, offset*2))

        tela.blit(carta_surface, (x_real, y_real))

        cor_borda = (255, 215, 0) if (selecionada or eh_lendaria) else (100, 150, 200)
        espessura_borda = 3 if (selecionada or eh_lendaria) else 2
        self.desenhar_borda_arredondada(tela, cor_borda, 
                                       (x_real, y_real, largura_real, altura_real), 
                                       15, espessura_borda)

        if eh_lendaria:
            self.desenhar_borda_arredondada(tela, (255, 255, 255), 
                                           (x_real + 4, y_real + 4, largura_real - 8, altura_real - 8), 
                                           12, 1)

        centro_x = x_real + largura_real // 2

        if eh_lendaria:
            y_raridade = y_real + 15
            y_nome = y_real + 35
            y_icone = y_real + altura_real // 2 - 30
            y_descricao = y_real + altura_real - 110
        else:
            y_nome = y_real + 25
            y_icone = y_real + altura_real // 2 - 30
            y_descricao = y_real + altura_real - 100

        if eh_lendaria:
            desenhar_texto(tela, "★ LENDARIA ★", 
                          (centro_x, y_raridade), 
                          (255, 255, 255), 12, centralizado=True, sombra=True)
            cor_nome = (255, 255, 255)
            tamanho_nome = 16
        else:
            cor_nome = (255, 215, 0) if selecionada else (255, 255, 255)
            tamanho_nome = 18

        nome = opcao['nome']
        if len(nome) > 15:
            palavras = nome.split()
            if len(palavras) > 1:
                meio = len(palavras) // 2
                linha1 = ' '.join(palavras[:meio])
                linha2 = ' '.join(palavras[meio:])
                desenhar_texto(tela, linha1, (centro_x, y_nome - 6), 
                              cor_nome, tamanho_nome - 2, centralizado=True, sombra=True)
                desenhar_texto(tela, linha2, (centro_x, y_nome + 8), 
                              cor_nome, tamanho_nome - 2, centralizado=True, sombra=True)
            else:
                desenhar_texto(tela, nome, (centro_x, y_nome), 
                              cor_nome, tamanho_nome - 4, centralizado=True, sombra=True)
        else:
            desenhar_texto(tela, nome, (centro_x, y_nome), 
                          cor_nome, tamanho_nome, centralizado=True, sombra=True)

        imagem_upgrade = self.obter_imagem_upgrade(opcao['tipo'])
        if imagem_upgrade:
            if eh_lendaria:
                img_size = 55
                imagem_redimensionada = pygame.transform.scale(imagem_upgrade, (img_size, img_size))
                raio_fundo = 35
            else:
                img_size = 65
                imagem_redimensionada = pygame.transform.scale(imagem_upgrade, (img_size, img_size))
                raio_fundo = 38

            img_x = centro_x - img_size // 2
            img_y = y_icone - img_size // 2

            if eh_lendaria:
                surf_fundo = pygame.Surface((raio_fundo * 2, raio_fundo * 2))
                surf_fundo.set_alpha(80)
                surf_fundo.fill((255, 215, 0))
                pygame.draw.circle(surf_fundo, (255, 215, 0), (raio_fundo, raio_fundo), raio_fundo)
                tela.blit(surf_fundo, (centro_x - raio_fundo, y_icone - raio_fundo))
                pygame.draw.circle(tela, (255, 215, 0), (centro_x, y_icone), raio_fundo, 2)
                pygame.draw.circle(tela, (255, 255, 255), (centro_x, y_icone), raio_fundo - 2, 1)
            else:
                surf_fundo = pygame.Surface((raio_fundo * 2, raio_fundo * 2))
                surf_fundo.set_alpha(60)
                surf_fundo.fill((100, 150, 200))
                pygame.draw.circle(surf_fundo, (100, 150, 200), (raio_fundo, raio_fundo), raio_fundo)
                tela.blit(surf_fundo, (centro_x - raio_fundo, y_icone - raio_fundo))
                pygame.draw.circle(tela, (100, 150, 200), (centro_x, y_icone), raio_fundo, 2)
                pygame.draw.circle(tela, (255, 255, 255), (centro_x, y_icone), raio_fundo - 2, 1)

            tela.blit(imagem_redimensionada, (img_x, img_y))

            if eh_lendaria:
                tempo = pygame.time.get_ticks()
                intensidade_brilho = 0.2 + 0.1 * math.sin(tempo * 0.005)
                surf_brilho = pygame.Surface((img_size, img_size))
                surf_brilho.set_alpha(int(intensidade_brilho * 80))
                surf_brilho.fill((255, 255, 255))
                tela.blit(surf_brilho, (img_x, img_y))
        else:
            icone = self.obter_icone_upgrade(opcao['tipo'])
            raio_icone = 30 if eh_lendaria else 35
            cor_fundo_icone = (255, 215, 0, 120) if eh_lendaria else (100, 150, 200, 120)
            icone_surface = pygame.Surface((raio_icone * 2, raio_icone * 2))
            icone_surface.set_alpha(120)
            icone_surface.fill(cor_fundo_icone[:3])
            pygame.draw.circle(icone_surface, cor_fundo_icone[:3], (raio_icone, raio_icone), raio_icone)
            tela.blit(icone_surface, (centro_x - raio_icone, y_icone - raio_icone))
            cor_icone = (255, 255, 255)
            tamanho_icone = 28 if eh_lendaria else 32
            desenhar_texto(tela, icone, (centro_x, y_icone), 
                          cor_icone, tamanho_icone, centralizado=True, sombra=True)

        altura_desc = 90 if eh_lendaria else 80
        desc_rect = pygame.Rect(x_real + 10, y_descricao - 10, largura_real - 20, altura_desc)
        desc_surface = pygame.Surface((desc_rect.width, desc_rect.height))
        desc_surface.set_alpha(80)
        desc_surface.fill((0, 0, 0))
        self.desenhar_retangulo_arredondado(desc_surface, (0, 0, 0), 
                                          (0, 0, desc_rect.width, desc_rect.height), 8)
        tela.blit(desc_surface, desc_rect.topleft)

        descricao = opcao.get('descricao', '')
        cor_descricao = (255, 255, 255) if eh_lendaria else (200, 220, 255)
        limite_chars = 20 if eh_lendaria else 25
        palavras = descricao.split()
        linhas = []
        linha_atual = ""

        for palavra in palavras:
            teste_linha = linha_atual + " " + palavra if linha_atual else palavra
            if len(teste_linha) <= limite_chars:
                linha_atual = teste_linha
            else:
                if linha_atual:
                    linhas.append(linha_atual)
                linha_atual = palavra

        if linha_atual:
            linhas.append(linha_atual)

        y_linha = y_descricao + 5
        tamanho_fonte_desc = 12 if eh_lendaria else 14
        espacamento_linha = 15 if eh_lendaria else 18
        max_linhas = 4 if eh_lendaria else 3

        for linha in linhas[:max_linhas]:
            desenhar_texto(tela, linha, (centro_x, y_linha), 
                          cor_descricao, tamanho_fonte_desc, centralizado=True, sombra=True)
            y_linha += espacamento_linha

        numero_carta = str(self.opcoes.index(opcao) + 1)
        desenhar_texto(tela, numero_carta, 
                      (x_real + largura_real - 20, y_real + altura_real - 20), 
                      cor_nome, 20, centralizado=False, sombra=True)

        if selecionada:
            pulso_color = tuple(int(255 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.01))) 
                              for _ in range(3))
            self.desenhar_borda_arredondada(tela, pulso_color, 
                                           (x_real - 2, y_real - 2, largura_real + 4, altura_real + 4), 
                                           17, 2)

    def desenhar_retangulo_arredondado(self, surface, cor, rect, raio):
        x, y, largura, altura = rect
        pygame.draw.rect(surface, cor, (x + raio, y, largura - 2*raio, altura))
        pygame.draw.rect(surface, cor, (x, y + raio, largura, altura - 2*raio))
        pygame.draw.circle(surface, cor, (x + raio, y + raio), raio)
        pygame.draw.circle(surface, cor, (x + largura - raio, y + raio), raio)
        pygame.draw.circle(surface, cor, (x + raio, y + altura - raio), raio)
        pygame.draw.circle(surface, cor, (x + largura - raio, y + altura - raio), raio)

    def desenhar_borda_arredondada(self, surface, cor, rect, raio, espessura):
        x, y, largura, altura = rect
        pygame.draw.rect(surface, cor, (x + raio, y, largura - 2*raio, espessura))
        pygame.draw.rect(surface, cor, (x + raio, y + altura - espessura, largura - 2*raio, espessura))
        pygame.draw.rect(surface, cor, (x, y + raio, espessura, altura - 2*raio))
        pygame.draw.rect(surface, cor, (x + largura - espessura, y + raio, espessura, altura - 2*raio))

        for i in range(espessura):
            pygame.draw.circle(surface, cor, (x + raio, y + raio), raio - i, 1)
            pygame.draw.circle(surface, cor, (x + largura - raio, y + raio), raio - i, 1)
            pygame.draw.circle(surface, cor, (x + raio, y + altura - raio), raio - i, 1)
            pygame.draw.circle(surface, cor, (x + largura - raio, y + altura - raio), raio - i, 1)

    def obter_icone_upgrade(self, tipo):
        icones_lendarios = {
            'vida_lendaria': 'LIFE',
            'dano_lendaria': 'RAGE',
            'velocidade_lendaria': 'WIND',
            'alcance_lendaria': 'SNIP',
            'cadencia_lendaria': 'MEGA',
            'atravessar_lendaria': 'PIER',
            'projeteis_lendaria': 'STAR',
            'coleta_lendaria': 'PULL',
            'espada_lendaria': 'SWRD',
            'dash_lendaria': 'WARP',
            'bomba_lendaria': 'NUKE',
            'raios_lendaria': 'BOLT',
            'campo_lendaria': 'VOID'
        }

        icones = {
            'vida': 'HP',
            'dano': 'ATK',
            'velocidade': 'SPD',
            'alcance': 'RNG',
            'cadencia': 'CDR',
            'atravessar': 'PEN',
            'projeteis': 'MLT',
            'espada': 'SWD',
            'dash': 'DSH',
            'bomba': 'BMB',
            'raios': 'ZAP',
            'coleta': 'MAG',
            'campo': 'FLD'
        }

        if tipo in icones_lendarios:
            return icones_lendarios[tipo]
        return icones.get(tipo, 'UPG')

    def processar_input(self, evento):
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
            if evento.button == 1:
                mouse_x, mouse_y = evento.pos
                num_opcoes = len(self.opcoes)
                largura_carta = 220
                altura_carta = 300
                espacamento = 60
                largura_total = num_opcoes * largura_carta + (num_opcoes - 1) * espacamento
                x_inicial = (LARGURA_TELA - largura_total) // 2
                y_carta = 160

                for i in range(num_opcoes):
                    x_carta = x_inicial + i * (largura_carta + espacamento)
                    if (x_carta <= mouse_x <= x_carta + largura_carta and
                        y_carta <= mouse_y <= y_carta + altura_carta):
                        return i
        elif evento.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = evento.pos
            num_opcoes = len(self.opcoes)
            largura_carta = 220
            altura_carta = 300
            espacamento = 60
            largura_total = num_opcoes * largura_carta + (num_opcoes - 1) * espacamento
            x_inicial = (LARGURA_TELA - largura_total) // 2
            y_carta = 160

            for i in range(num_opcoes):
                x_carta = x_inicial + i * (largura_carta + espacamento)
                if (x_carta <= mouse_x <= x_carta + largura_carta and
                    y_carta <= mouse_y <= y_carta + altura_carta):
                    self.opcao_selecionada = i
                    break

        return -1