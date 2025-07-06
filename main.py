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
from boss import Boss
import os

def get_asset_path(relative_path):
    # Para executáveis empacotados com PyInstaller
    try:
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    except:
        base_path = os.path.abspath(".")
    
    # Primeiro tenta o caminho normal
    caminho = os.path.join(base_path, relative_path)
    if os.path.exists(caminho):
        return caminho
    
    # Se não encontrar, tenta procurar na pasta dist
    dist_path = os.path.join(os.path.dirname(base_path), "dist", relative_path)
    if os.path.exists(dist_path):
        return dist_path
    
    # Se ainda não encontrar, tenta o diretório atual
    current_path = os.path.join(os.getcwd(), relative_path)
    if os.path.exists(current_path):
        return current_path
    
    # Última tentativa: procura recursivamente
    for root, dirs, files in os.walk(os.getcwd()):
        if relative_path.split('/')[-1] in files:
            return os.path.join(root, relative_path.split('/')[-1])
    
    return caminho  # Retorna o caminho original mesmo se não existir

class Jogo:
    def __init__(self):
        pygame.init()
        
        
        self.tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
        pygame.display.set_caption("SQUARE VS CIRCLES")
        
        
        try:
            self.imagem_volume = pygame.image.load(get_asset_path("assets/volume.png"))
            self.imagem_volume = pygame.transform.scale(self.imagem_volume, (32, 32))
        except Exception as e:
            print(f"Erro ao carregar imagem do volume: {e}")
            sys.exit(1)
        
        self.volume = 0.15  
        self.arrastando_volume = False
        self.barra_volume_rect = pygame.Rect(60, ALTURA_TELA - 40, 100, 10)
        self.mostrar_controle_volume = False
        self.tempo_ultimo_mouse_volume = 0
        
        self.relogio = pygame.time.Clock()
        self.inicio_jogo = pygame.time.get_ticks()
        self.tempo_pausado = 0  
        self.momento_pausa = 0  
        
    
        self.rodando = True
        self.estado = "jogando"  
        self.pausado = False
        
        
        self.tempo_vitoria = 0
        self.duracao_vitoria = 10000  
        
        
        self.modo_dev = False  
        self.dev_menu_aberto = False
        
        
        pygame.mixer.init()
        
        
        self.mostrar_controle_volume = False
        self.tempo_ultimo_mouse_volume = 0
        self.arrastando_volume = False
        
        
        try:
            self.som_boss_spawn = pygame.mixer.Sound(get_asset_path("assets/boss-spawn.mp3"))
            self.som_boss_spawn.set_volume(self.volume)  
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o som boss-spawn.mp3: {e}")
            self.som_boss_spawn = None
        
        
        try:
            self.caminho_musica_inicial = get_asset_path("assets/ost1.mp3")
            pygame.mixer.music.load(self.caminho_musica_inicial)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(-1)  
            print("Música inicial iniciada em loop!")
        except Exception as e:
            print(f"Aviso: Não foi possível carregar a música inicial: {e}")
            self.caminho_musica_inicial = None
        
        
        try:
            self.caminho_musica_boss = get_asset_path("assets/boss-theme.mp3")
            self.musica_boss_carregada = False
        except Exception as e:
            print(f"Aviso: Não foi possível carregar a música do boss: {e}")
            self.caminho_musica_boss = None
        
        
        self.cenario = CenarioEspacial()
        
        
        self.jogador = Jogador(LARGURA_MAPA // 2, ALTURA_MAPA // 2)
        self.inimigos = []
        self.projeteis = []
        self.projeteis_inimigos = []
        self.projeteis_boss = []
        self.xps = []
        self.itens = []
        self.boss = None
        
        
        self.raios = []
        self.bombas = []
        self.campos = []
        self.campo_permanente = CampoPermanente(self.jogador)
        
        
        self.upgrade_manager = UpgradeManager()
        self.tela_upgrade = None
        self.minimapa = Minimapa()
        
        
        self.ultimo_spawn_inimigo = 0
        self.intervalo_spawn = 1800  
        self.ultimo_spawn_item = 0
        self.intervalo_spawn_item = 15000  
        self.ultimo_coracao = 0
        self.intervalo_coracao = 30000  
        
        
        self.camera = [0, 0]
    
    def obter_tempo_jogo(self):
        """Retorna o tempo de jogo em segundos"""
        tempo_total = pygame.time.get_ticks() - self.inicio_jogo - self.tempo_pausado
        return tempo_total / 1000.0
    
    def obter_tempo_restante(self):
        """Retorna o tempo restante em segundos (contagem regressiva)"""
        tempo_jogado = self.obter_tempo_jogo()
        tempo_restante = DURACAO_MAXIMA - tempo_jogado
        return max(0, tempo_restante)  
    
    def atualizar_camera(self):
        """Atualiza a posição da câmera para seguir o jogador"""
        self.camera[0] = self.jogador.pos[0] - LARGURA_TELA // 2
        self.camera[1] = self.jogador.pos[1] - ALTURA_TELA // 2
        
        
        self.camera[0] = max(0, min(LARGURA_MAPA - LARGURA_TELA, self.camera[0]))
        self.camera[1] = max(0, min(ALTURA_MAPA - ALTURA_TELA, self.camera[1]))
    
    def spawnar_inimigos(self):
        """Sistema de spawn melhorado com dificuldade progressiva"""
        tempo_atual = pygame.time.get_ticks()
        tempo_jogo = self.obter_tempo_jogo()
        
        
        if self.boss and self.boss.ativo:
            return
        
        
        if tempo_jogo < 60:
            self.intervalo_spawn = 1800  
        elif tempo_jogo < 180:
            self.intervalo_spawn = 1200  
        elif tempo_jogo < 300:
            self.intervalo_spawn = 800   
        elif tempo_jogo < 480:
            self.intervalo_spawn = 600   
        elif tempo_jogo < 660:
            self.intervalo_spawn = 400   
        else:
            self.intervalo_spawn = 300   
        
        if tempo_atual - self.ultimo_spawn_inimigo > self.intervalo_spawn:
            
            quantidade = 1
            if tempo_jogo > 60:   
                quantidade = 2
            if tempo_jogo > 180:  
                quantidade = 3
            if tempo_jogo > 300:  
                quantidade = 4
            if tempo_jogo > 480:  
                quantidade = 5
            if tempo_jogo > 660:  
                quantidade = 6
            
            for _ in range(quantidade):
                if len(self.inimigos) < 80:  
                    inimigo = gerar_inimigo_aleatorio(self.jogador.pos, tempo_jogo)
                    self.inimigos.append(inimigo)
            
            self.ultimo_spawn_inimigo = tempo_atual
    
    def spawnar_itens(self):
        """Gera itens especiais ocasionalmente"""
        tempo_atual = pygame.time.get_ticks()
        
        
        if tempo_atual - self.ultimo_spawn_item > self.intervalo_spawn_item:
            if len(self.itens) < 3:  
                item = gerar_item_aleatorio(self.jogador.pos)
                self.itens.append(item)
            
            self.ultimo_spawn_item = tempo_atual
        
        
        if tempo_atual - self.ultimo_coracao > self.intervalo_coracao:
            if random.random() < 0.05:  
                pos_x = self.jogador.pos[0] + random.randint(-200, 200)
                pos_y = self.jogador.pos[1] + random.randint(-200, 200)
                
                
                pos_x = max(50, min(LARGURA_MAPA - 50, pos_x))
                pos_y = max(50, min(ALTURA_MAPA - 50, pos_y))
                
                coracao = Item(pos_x, pos_y, "coracao")
                self.itens.append(coracao)
                self.ultimo_coracao = tempo_atual
    
    def atirar(self):
        """Sistema de tiro automático do jogador"""
        if not self.jogador.pode_atirar():
            return
        
        
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
            
            
            for i in range(self.jogador.projeteis_simultaneos):
                angulo_offset = (i - self.jogador.projeteis_simultaneos // 2) * 0.2
                
                dx = alvo.pos[0] - self.jogador.pos[0]
                dy = alvo.pos[1] - self.jogador.pos[1]
                
                
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
        
        
        if self.boss and self.boss.ativo:
            for projetil in self.projeteis[:]:
                if not projetil.ativo:
                    continue
                
                distancia = calcular_distancia(projetil.pos, self.boss.pos)
                if distancia < projetil.raio + self.boss.raio:
                    self.boss.receber_dano(projetil.dano)
                    projetil.ativo = False
        
        
        for inimigo in self.inimigos:
            inimigo.atacar_jogador(self.jogador)
        
        
        if self.boss and self.boss.ativo:
            self.boss.colidir_com_jogador(self.jogador)
        
        
        for proj_boss in self.projeteis_boss[:]:
            if proj_boss.colidir_com_jogador(self.jogador):
                pass  
        
        
        for proj_inimigo in self.projeteis_inimigos[:]:
            if proj_inimigo.colidir_com_jogador(self.jogador):
                pass  
        
        
        for xp in self.xps[:]:
            if xp.colidir_com_jogador(self.jogador):
                
                subiu_nivel = self.jogador.ganhar_xp(xp.valor)
                
                
                if subiu_nivel:
                    opcoes = self.upgrade_manager.obter_opcoes_upgrade(self.jogador)
                    if opcoes != "todos_maximos":  
                        self.tela_upgrade = TelaUpgrade(opcoes)
                        self.estado = "upgrade"
                
                
                self.xps.remove(xp)
        
        
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
        if self.pausado or self.estado == "vitoria":
            return
        
        
        keys = pygame.key.get_pressed()  
        self.jogador.mover(keys)  
        self.jogador.atualizar()
        
        
        alvos_espadas = self.inimigos.copy()
        if self.boss and self.boss.ativo:
            alvos_espadas.append(self.boss)
        self.jogador.atualizar_espadas(alvos_espadas)
        
        
        self.atualizar_camera()
        
        
        tempo_jogo = self.obter_tempo_jogo()
        if tempo_jogo >= 600 and not self.boss and self.estado != "vitoria":  
            self.spawnar_boss()
        
        
        self.atualizar_boss()
        
        
        if self.boss and not self.boss.ativo:
            print("🔍 DEBUG: Boss inativo detectado globalmente!")
            self.processar_vitoria_boss()
            return
        
        
        if (not self.boss or not self.boss.ativo) and self.estado != "vitoria":
            self.spawnar_inimigos()
        
        
        if self.estado != "vitoria":
            self.spawnar_itens()
        
        
        self.atirar()
        
        
        self.atualizar_inimigos()
        
        
        self.atualizar_projeteis()
        
        
        self.atualizar_itens()
        
        
        self.atualizar_xps()
        
        
        self.atualizar_habilidades()
        
        
        self.processar_colisoes()
        self.processar_colisoes_boss()
        
        
        if self.jogador.hp <= 0:
            self.estado = "game_over"
            self.parar_musica_boss()
    
    def desenhar(self):
        """Desenha todos os elementos do jogo"""
        
        self.tela.fill((5, 5, 10))  
        
        
        self.cenario.desenhar(self.tela, self.camera)
        
        
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
        
        
        for proj_boss in self.projeteis_boss:
            proj_boss.desenhar(self.tela, self.camera)
        
        self.jogador.desenhar(self.tela, self.camera)
        
        
        if self.boss and self.boss.ativo:
            self.boss.desenhar(self.tela, self.camera)
        
        
        for raio in self.raios:
            raio.desenhar(self.tela, self.camera)
        
        for bomba in self.bombas:
            bomba.desenhar(self.tela, self.camera)
        
        for campo in self.campos:
            campo.desenhar(self.tela, self.camera)
        
        
        self.campo_permanente.desenhar(self.tela, self.camera)
        
        
        self.desenhar_ui()
        
        
        self.minimapa.desenhar(self.tela, self.jogador, self.inimigos, self.xps, self.itens)
        
        
        if self.estado == "game_over":
            self.desenhar_game_over()
        elif self.estado == "vitoria":
            self.desenhar_tela_vitoria()
        
        
        if self.modo_dev:
            self.desenhar_menu_dev()
        
        
        if self.mostrar_controle_volume:
            self.desenhar_controle_volume()
        
        
        if self.estado == "upgrade" and self.tela_upgrade:
            self.tela_upgrade.desenhar(self.tela)
        
        pygame.display.flip()
    
    def desenhar_ui(self):
        """Desenha a interface do usuário com design melhorado"""
        
        
        largura_painel = 320
        altura_painel = 160
        
        
        painel_surf = pygame.Surface((largura_painel, altura_painel))
        painel_surf.set_alpha(140)
        painel_surf.fill((15, 20, 35))
        self.tela.blit(painel_surf, (10, 10))
        
        
        pygame.draw.rect(self.tela, (255, 215, 0), (10, 10, largura_painel, altura_painel), 2)
        
        
        y_offset = 25
        
        desenhar_texto(self.tela, "HP", (30, y_offset - 8), BRANCO, 24, sombra=True)
        
        
        barra_largura = 200
        barra_altura = 8
        x_barra = 80
        y_barra = y_offset - 4
        
        
        pygame.draw.rect(self.tela, (50, 20, 20), (x_barra, y_barra, barra_largura, barra_altura))
        
        
        proporcao_vida = self.jogador.hp / self.jogador.hp_max
        largura_vida = int(barra_largura * proporcao_vida)
        cor_vida = VERDE if proporcao_vida > 0.6 else (255, 165, 0) if proporcao_vida > 0.3 else VERMELHO
        pygame.draw.rect(self.tela, cor_vida, (x_barra, y_barra, largura_vida, barra_altura))
        
        
        y_offset += 35
        
        desenhar_texto(self.tela, "XP", (30, y_offset - 8), BRANCO, 24, sombra=True)
        
        
        y_barra_xp = y_offset - 4
        pygame.draw.rect(self.tela, (20, 30, 50), (x_barra, y_barra_xp, barra_largura, barra_altura))
        proporcao_xp = self.jogador.xp / self.jogador.xp_para_proximo
        largura_xp = int(barra_largura * proporcao_xp)
        pygame.draw.rect(self.tela, AZUL_CLARO, (x_barra, y_barra_xp, largura_xp, barra_altura))
        
        
        y_offset += 45
        tempo_restante = self.obter_tempo_restante()
        minutos = int(tempo_restante // 60)
        segundos = int(tempo_restante % 60)
        
        
        if tempo_restante <= 60:  
            cor_tempo = VERMELHO
            tempo_texto = f"{minutos:02d}:{segundos:02d}"
        elif tempo_restante <= 180:  
            cor_tempo = (255, 165, 0)  
            tempo_texto = f"{minutos:02d}:{segundos:02d}"
        else:
            cor_tempo = BRANCO
            tempo_texto = f"{minutos:02d}:{segundos:02d}"
        
        desenhar_texto(self.tela, tempo_texto, (25, y_offset - 8), cor_tempo, 26, sombra=True)
        
        
        x_habilidades = LARGURA_TELA - 300
        y_base = ALTURA_TELA - 240  
        
        
        largura_hab = 285
        altura_hab = 220
        hab_surf = pygame.Surface((largura_hab, altura_hab))
        hab_surf.set_alpha(140)
        hab_surf.fill((15, 25, 15))
        self.tela.blit(hab_surf, (x_habilidades, y_base))
        
        
        pygame.draw.rect(self.tela, (100, 255, 100), (x_habilidades, y_base, largura_hab, altura_hab), 2)
        
        
        desenhar_texto(self.tela, "HABILIDADES", (x_habilidades + 20, y_base + 15), 
                      (100, 255, 100), 18, sombra=True)
        y_hab = y_base + 45
        
        
        if self.jogador.dash_nivel > 0:
            if self.jogador.dash_cooldown > 0:
                texto = f"Dash: {self.jogador.dash_cooldown//1000 + 1}s"
                cor = (255, 100, 100)
            else:
                texto = "Dash: PRONTO"
                cor = (100, 255, 100)
            desenhar_texto(self.tela, texto, (x_habilidades + 20, y_hab), cor, 16, sombra=True)
            y_hab += 22
        
        
        if self.jogador.espada_nivel > 0:
            texto = f"Espadas Orbitais Nv.{self.jogador.espada_nivel}"
            desenhar_texto(self.tela, texto, (x_habilidades + 20, y_hab), BRANCO, 16, sombra=True)
            y_hab += 22
        
        
        if self.jogador.raios_nivel > 0:
            if self.jogador.raios_cooldown > 0:
                texto = f"Raios: {self.jogador.raios_cooldown//1000 + 1}s"
                cor = (255, 100, 100)
            else:
                texto = "Raios: PRONTO"
                cor = (100, 255, 100)
            desenhar_texto(self.tela, texto, (x_habilidades + 20, y_hab), cor, 16, sombra=True)
            y_hab += 22
        
        
        if self.jogador.bomba_nivel > 0:
            if self.jogador.bomba_cooldown > 0:
                texto = f"Bomba: {self.jogador.bomba_cooldown//1000 + 1}s"
                cor = (255, 100, 100)
            else:
                texto = "Bomba: PRONTO"
                cor = (100, 255, 100)
            desenhar_texto(self.tela, texto, (x_habilidades + 20, y_hab), cor, 16, sombra=True)
            y_hab += 22
        
        
        if self.jogador.escudo_nivel > 0:
            if self.jogador.escudo_cooldown > 0:
                texto = f"Escudo: {self.jogador.escudo_cooldown//1000 + 1}s"
                cor = (255, 100, 100)
            else:
                texto = "Escudo: PRONTO"
                cor = (100, 255, 100)
            desenhar_texto(self.tela, texto, (x_habilidades + 20, y_hab), cor, 16, sombra=True)
            y_hab += 22
        
        
        if self.jogador.campo_nivel > 0:
            texto = f"Campo Gravitacional Nv.{self.jogador.campo_nivel}"
            desenhar_texto(self.tela, texto, (x_habilidades + 20, y_hab), BRANCO, 16, sombra=True)
            y_hab += 22
        
        
        if self.boss and self.boss.ativo:
            self.desenhar_barra_boss()
        
        
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
    
    def desenhar_tela_vitoria(self):
        """Desenha a tela de vitória"""
        
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        overlay.set_alpha(200)
        overlay.fill(PRETO)
        self.tela.blit(overlay, (0, 0))
        
        
        largura_msg = 600
        altura_msg = 350  
        x_msg = LARGURA_TELA // 2 - largura_msg // 2
        y_msg = ALTURA_TELA // 2 - altura_msg // 2
        
        
        tempo = pygame.time.get_ticks()
        intensidade = 0.5 + 0.5 * math.sin(tempo * 0.003)
        cor_borda = tuple(int(c * intensidade) for c in DOURADO)
        
        pygame.draw.rect(self.tela, (30, 30, 40), (x_msg, y_msg, largura_msg, altura_msg))
        pygame.draw.rect(self.tela, cor_borda, (x_msg, y_msg, largura_msg, altura_msg), 3)
        
        
        desenhar_texto(self.tela, "FASE 1 COMPLETA!",
                      (LARGURA_TELA // 2, ALTURA_TELA // 2 - 120),
                      DOURADO, 48, True)
        
        
        desenhar_texto(self.tela, "Obrigado por jogar a demo!",
                      (LARGURA_TELA // 2, ALTURA_TELA // 2 - 20),
                      BRANCO, 36, True)
        
        
        if self.tempo_vitoria > 0:
            tempo_atual = pygame.time.get_ticks()
            tempo_restante = self.duracao_vitoria - (tempo_atual - self.tempo_vitoria)
            segundos_restantes = max(0, int(tempo_restante / 1000)) + 1
            
            
            if segundos_restantes <= 3:
                cor_timer = VERMELHO
            elif segundos_restantes <= 5:
                cor_timer = (255, 165, 0)  
            else:
                cor_timer = BRANCO
            
            desenhar_texto(self.tela, f"Fechando em {segundos_restantes} segundos...",
                          (LARGURA_TELA // 2, ALTURA_TELA // 2 + 50),
                          cor_timer, 28, True)
        
        
        alpha = 128 + int(127 * math.sin(tempo * 0.005))
        cor_instrucoes = (255, 255, 255, alpha)
        desenhar_texto(self.tela, "Pressione ESC para sair agora",
                      (LARGURA_TELA // 2, ALTURA_TELA // 2 + 100),
                      cor_instrucoes, 24, True)
    
    def desenhar_apenas_vitoria(self):
        """Desenha apenas a tela de vitória sem nenhum elemento do jogo"""
        
        self.tela.fill((5, 5, 10))
        
        
        self.desenhar_tela_vitoria()
        
        pygame.display.flip()
    
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
                        if self.estado == "vitoria":
                            print("=" * 50)
                            print("🚪 JOGADOR PRESSIONOU ESC!")
                            print("SAINDO DO JOGO IMEDIATAMENTE...")
                            print("=" * 50)
                        self.rodando = False  
                
                
                elif evento.key == pygame.K_F10:
                    self.modo_dev = not self.modo_dev
                    if not self.modo_dev:
                        self.dev_menu_aberto = False
                
                
                elif self.estado == "jogando":
                    
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
                        
                        
                        if dx == 0 and dy == 0:
                            dy = -1
                        
                        
                        if dx != 0 and dy != 0:
                            dx *= 0.707
                            dy *= 0.707
                        
                        self.jogador.usar_dash(dx, dy)
                    
                    
                    elif self.modo_dev:
                        if evento.key == pygame.K_F1:
                            
                            self.jogador.xp = self.jogador.xp_para_proximo
                            opcoes = self.upgrade_manager.obter_opcoes_upgrade(self.jogador)
                            if opcoes == "todos_maximos":
                                self.mostrar_mensagem_maximos()
                            else:
                                self.tela_upgrade = TelaUpgrade(opcoes)
                                self.estado = "upgrade"
                        
                        elif evento.key == pygame.K_F2:
                            
                            self.inicio_jogo -= 60000  
                        
                        elif evento.key == pygame.K_F3:
                            
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
                            
                            if not self.boss:
                                self.spawnar_boss()
                        
                        elif evento.key == pygame.K_F6:
                            
                            self.jogador.hp = self.jogador.hp_max
                        
                        elif evento.key == pygame.K_F7:
                            
                            self.dev_menu_aberto = not self.dev_menu_aberto
                        
                        elif evento.key == pygame.K_F8:
                            
                            self.jogador.vida_infinita = not self.jogador.vida_infinita
                        
                        elif evento.key == pygame.K_F9:
                            
                            print("DEV: Dando todos os upgrades no nível máximo!")
                            
                            
                            self.jogador.vida_nivel = 10
                            self.jogador.hp_max = 100 + (self.jogador.vida_nivel * 20)
                            self.jogador.hp = self.jogador.hp_max  
                            
                            self.jogador.dano_nivel = 10
                            self.jogador.dano = 10 + (self.jogador.dano_nivel * 5)
                            
                            self.jogador.velocidade_nivel = 10
                            self.jogador.velocidade = int(3 + (self.jogador.velocidade_nivel * 0.5))
                            
                            self.jogador.alcance_nivel = 10
                            self.jogador.alcance_tiro = 300 + (self.jogador.alcance_nivel * 30)
                            
                            self.jogador.cadencia_nivel = 10
                            self.jogador.cooldown_tiro = max(50, 500 - (self.jogador.cadencia_nivel * 40))
                            
                            self.jogador.projeteis_nivel = 10
                            self.jogador.projeteis_simultaneos = 1 + (self.jogador.projeteis_nivel // 2)
                            
                            self.jogador.atravessar_nivel = 10
                            self.jogador.atravessar_inimigos = self.jogador.atravessar_nivel
                            
                            self.jogador.coleta_nivel = 10
                            self.jogador.raio_coleta = 30 + (self.jogador.coleta_nivel * 30)
                            
                            
                            self.jogador.espada_nivel = 10
                            self.jogador.dash_nivel = 10
                            self.jogador.bomba_nivel = 10
                            self.jogador.raios_nivel = 10
                            self.jogador.campo_nivel = 10
                            self.jogador.escudo_nivel = 10
                            
                            
                            setattr(self.jogador, 'regeneracao', 5)
                            setattr(self.jogador, 'critico_chance', 0.5)
                            setattr(self.jogador, 'clone_fantasma', True)
                            setattr(self.jogador, 'tiros_triplos', True)
                            setattr(self.jogador, 'dano_acumulativo', True)
                            setattr(self.jogador, 'padrao_espiral', True)
                            setattr(self.jogador, 'xp_multiplicador', 3.0)
                            setattr(self.jogador, 'ondas_choque', True)
                            setattr(self.jogador, 'dash_cooldown_lendario', True)
                            setattr(self.jogador, 'dash_explosao', True)
                            setattr(self.jogador, 'bombas_nucleares', True)
                            setattr(self.jogador, 'tempestade_permanente', True)
                            setattr(self.jogador, 'buraco_negro', True)
                            
                            print(f"Todos os upgrades E efeitos lendários aplicados!")
                        
                        elif evento.key == pygame.K_F11:
                            
                            if self.boss and self.boss.ativo:
                                hp_2_porcento = int(self.boss.hp_max * 0.02)
                                self.boss.hp = hp_2_porcento
                                print(f"DEV: Boss agora tem {hp_2_porcento} HP ({self.boss.hp}/{self.boss.hp_max}) - 2%")
                            else:
                                print("DEV: Nenhum boss ativo para modificar HP!")
            
            
            if self.estado == "upgrade" and self.tela_upgrade:
                escolha = self.tela_upgrade.processar_input(evento)
                if escolha >= 0:
                    upgrade_escolhido = self.tela_upgrade.opcoes[escolha]
                    self.upgrade_manager.aplicar_upgrade(self.jogador, upgrade_escolhido)
                    self.tela_upgrade = None
                    self.estado = "jogando"
            
            
            if self.estado == "jogando":
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if evento.button == 1:  
                        mouse_x, mouse_y = evento.pos
                        x_barra, y_barra, largura_barra = self.obter_posicao_barra_volume()
                        
                        
                        area_barra = pygame.Rect(x_barra - 5, y_barra - 5, largura_barra + 10, 18)
                        
                        if area_barra.collidepoint(mouse_x, mouse_y):
                            self.arrastando_volume = True
                            
                            proporcao = (mouse_x - x_barra) / largura_barra
                            proporcao = max(0, min(1, proporcao))  
                            self.atualizar_volume(proporcao)
                
                elif evento.type == pygame.MOUSEBUTTONUP:
                    if evento.button == 1:  
                        self.arrastando_volume = False
                
                elif evento.type == pygame.MOUSEMOTION:
                    mouse_x, mouse_y = evento.pos
                    x_icone, y_icone = self.obter_posicao_icone_volume()
                    x_barra, y_barra, largura_barra = self.obter_posicao_barra_volume()
                    
                    
                    area_icone = pygame.Rect(x_icone, y_icone, 32, 32)
                    area_barra = pygame.Rect(x_barra - 5, y_barra - 5, largura_barra + 10, 18)
                    
                    
                    if area_icone.collidepoint(mouse_x, mouse_y) or area_barra.collidepoint(mouse_x, mouse_y):
                        self.mostrar_controle_volume = True
                        self.tempo_ultimo_mouse_volume = pygame.time.get_ticks()
                    
                    
                    if self.arrastando_volume:
                        proporcao = (mouse_x - x_barra) / largura_barra
                        proporcao = max(0, min(1, proporcao))  
                        self.atualizar_volume(proporcao)
        
        return True
    
    def executar(self):
        """Loop principal do jogo"""
        while self.rodando:
            self.processar_eventos()
            
            
            if self.estado == "vitoria":
                
                tempo_atual = pygame.time.get_ticks()
                if tempo_atual - self.tempo_vitoria >= self.duracao_vitoria:
                    print("=" * 50)
                    print("⏰ TIMER DE VITÓRIA EXPIRADO!")
                    print("FECHANDO O JOGO AUTOMATICAMENTE...")
                    print("=" * 50)
                    self.rodando = False
                    break
                
                self.desenhar_apenas_vitoria()
                self.relogio.tick(FPS)
                continue
            
            
            if self.estado == "jogando" and not self.pausado:
                self.atualizar()
            
            self.desenhar()
            
            self.relogio.tick(FPS)
        
        pygame.quit()
        sys.exit()

    def atualizar_habilidades(self):
        """Atualiza todas as habilidades especiais"""
        
        bomba_dados = self.jogador.verificar_bomba_automatica()
        if bomba_dados:
            bomba = Bomba(bomba_dados['pos'][0], bomba_dados['pos'][1], 
                         bomba_dados['dano'], bomba_dados['raio'],
                         bomba_dados['pos_inicial'], bomba_dados['tempo_voo'])
            self.bombas.append(bomba)
        
        
        raios_dados = self.jogador.verificar_raios_automaticos()
        if raios_dados:
            
            for _ in range(raios_dados['quantidade']):
                
                angulo = random.uniform(0, 2 * math.pi)
                distancia = random.uniform(50, 150)
                x = self.jogador.pos[0] + math.cos(angulo) * distancia
                y = self.jogador.pos[1] + math.sin(angulo) * distancia
                
                raio = Raio(x, y, raios_dados['dano'])
                self.raios.append(raio)
        
        
        for raio in self.raios[:]:
            raio.atualizar()
            if not raio.ativo:
                self.raios.remove(raio)
        
        
        for bomba in self.bombas[:]:
            bomba.atualizar()
            if not bomba.ativo:
                self.bombas.remove(bomba)
        
        
        for campo in self.campos[:]:
            campo.atualizar()
            if not campo.ativo:
                self.campos.remove(campo)
        
        
        self.campo_permanente.atualizar()
        
        
        self.processar_colisoes_habilidades()
        
        
        if self.boss and not self.boss.ativo:
            print("🔍 DEBUG: Boss morto detectado em processar_colisoes_habilidades!")
            self.processar_vitoria_boss()
    
    def processar_colisoes_habilidades(self):
        """Processa colisões das habilidades especiais"""
        
        for espada in self.jogador.obter_espadas():
            for inimigo in self.inimigos[:]:
                if espada.colidir_com_inimigo(inimigo):
                    if not inimigo.ativo:
                        xp = inimigo.morrer()
                        if xp:
                            self.xps.append(xp)
                        self.inimigos.remove(inimigo)
            
            
            if self.boss and self.boss.ativo:
                if espada.colidir_com_inimigo(self.boss):
                    
                    boss_morreu = self.boss.receber_dano(espada.dano)
                    if boss_morreu:
                        print("⚔️ DEBUG: Boss morreu por espada orbital!")
                        self.processar_vitoria_boss()
                        return
        
        
        for raio in self.raios:
            for inimigo in self.inimigos[:]:
                if raio.colidir_com_inimigo(inimigo):
                    if not inimigo.ativo:
                        xp = inimigo.morrer()
                        if xp:
                            self.xps.append(xp)
                        self.inimigos.remove(inimigo)
            
            
            if self.boss and self.boss.ativo:
                if raio.colidir_com_inimigo(self.boss):
                    boss_morreu = self.boss.receber_dano(raio.dano)
                    if boss_morreu:
                        print("🚨 BOSS MORREU POR RAIO!")
                        self.processar_vitoria_boss()
                        return
        
        
        for bomba in self.bombas:
            for inimigo in self.inimigos[:]:
                if bomba.colidir_com_inimigo(inimigo):
                    if not inimigo.ativo:
                        xp = inimigo.morrer()
                        if xp:
                            self.xps.append(xp)
                        self.inimigos.remove(inimigo)
            
            
            if self.boss and self.boss.ativo:
                if bomba.colidir_com_inimigo(self.boss):
                    boss_morreu = self.boss.receber_dano(bomba.dano)
                    if boss_morreu:
                        print("🚨 BOSS MORREU POR BOMBA!")
                        self.processar_vitoria_boss()
                        return
        
        
        for inimigo in self.inimigos[:]:
            campo_matou = self.campo_permanente.afetar_inimigo(inimigo)
            if campo_matou and not inimigo.ativo:
                xp = inimigo.morrer()
                if xp:
                    self.xps.append(xp)
                self.inimigos.remove(inimigo)
        
        
        if self.boss and self.boss.ativo:
            campo_matou = self.campo_permanente.afetar_inimigo(self.boss)
            if campo_matou:
                print("🚨 BOSS MORREU POR CAMPO PERMANENTE!")
                self.processar_vitoria_boss()
                return
        
        
        for campo in self.campos:
            for inimigo in self.inimigos:
                campo.afetar_inimigo(inimigo)
            if self.boss and self.boss.ativo:
                campo_matou = campo.afetar_inimigo(self.boss)
                if campo_matou:
                    print("🚨 BOSS MORREU POR CAMPO GRAVITACIONAL!")
                    self.processar_vitoria_boss()
                    return
        
        
        if self.boss and not self.boss.ativo:
            print("🔍 DEBUG: Boss morto detectado em processar_colisoes_habilidades!")
            self.processar_vitoria_boss()

    def desenhar_barra_boss(self):
        """Desenha a barra de vida do boss na parte inferior da tela"""
        if not self.boss or not self.boss.ativo:
            return
        
        
        largura_barra = LARGURA_TELA - 100
        altura_barra = 30
        x_barra = 50
        y_barra = ALTURA_TELA - 60
        
        
        pygame.draw.rect(self.tela, (50, 0, 0), (x_barra - 2, y_barra - 2, largura_barra + 4, altura_barra + 4))
        pygame.draw.rect(self.tela, (0, 0, 0), (x_barra, y_barra, largura_barra, altura_barra))
        
        
        proporcao_vida = self.boss.hp / self.boss.hp_max
        largura_vida = int(largura_barra * proporcao_vida)
        
        
        if proporcao_vida > 0.6:
            cor_vida = (255, 0, 0)  
        elif proporcao_vida > 0.3:
            cor_vida = (255, 100, 0)  
        else:
            cor_vida = (255, 200, 0)  
        
        if largura_vida > 0:
            pygame.draw.rect(self.tela, cor_vida, (x_barra, y_barra, largura_vida, altura_barra))
        
        
        texto_boss = "BOSS"
        desenhar_texto(self.tela, texto_boss, (x_barra + largura_barra // 2 - 50, y_barra - 30), 
                      VERMELHO, 24, sombra=True)

    def atualizar_inimigos(self):
        """Atualiza todos os inimigos e processa projéteis"""
        for inimigo in self.inimigos[:]:
            if not inimigo.ativo:
                self.inimigos.remove(inimigo)
                continue
            
            
            resultado = inimigo.atualizar(self.jogador.pos)
            
            
            if resultado and hasattr(resultado, 'atualizar'):
                self.projeteis_inimigos.append(resultado)
            elif resultado and isinstance(resultado, list):
                
                self.projeteis_inimigos.extend(resultado)
            
            
            if hasattr(inimigo, 'alcance_ataque') and hasattr(inimigo, 'tempo_ultimo_ataque'):
                
                if inimigo.tipo == "tanque":
                    distancia = calcular_distancia(inimigo.pos, self.jogador.pos)
                    if distancia < inimigo.alcance_ataque:
                        tempo_atual = pygame.time.get_ticks()
                        if tempo_atual - inimigo.tempo_ultimo_ataque > inimigo.cooldown_ataque:
                            if self.jogador.receber_dano(inimigo.dano):
                                inimigo.tempo_ultimo_ataque = tempo_atual
            else:
                
                distancia = calcular_distancia(inimigo.pos, self.jogador.pos)
                if distancia < inimigo.raio + self.jogador.raio:
                    self.jogador.receber_dano(inimigo.dano)

    def mostrar_mensagem_maximos(self):
        """Ativa a mensagem de todos upgrades coletados"""
        self.mostrando_mensagem_maximos = True
        self.tempo_mensagem_maximos = pygame.time.get_ticks() + 1000  

    def desenhar_mensagem_maximos(self):
        """Desenha a mensagem de todos upgrades coletados"""
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        overlay.set_alpha(150)
        overlay.fill(PRETO)
        self.tela.blit(overlay, (0, 0))
        
        
        largura_msg = 600
        altura_msg = 200
        x_msg = LARGURA_TELA // 2 - largura_msg // 2
        y_msg = ALTURA_TELA // 2 - altura_msg // 2
        
        pygame.draw.rect(self.tela, (50, 50, 50), (x_msg, y_msg, largura_msg, altura_msg))
        pygame.draw.rect(self.tela, DOURADO, (x_msg, y_msg, largura_msg, altura_msg), 3)
        
        desenhar_texto(self.tela, "TODOS OS UPGRADES COLETADOS!", 
                      (LARGURA_TELA // 2 - 200, ALTURA_TELA // 2 - 50), DOURADO, 36, sombra=True)
        desenhar_texto(self.tela, "Continue jogando para enfrentar o BOSS!", 
                      (LARGURA_TELA // 2 - 160, ALTURA_TELA // 2 + 30), BRANCO, 20, sombra=True)

    def desenhar_menu_dev(self):
        """Desenha o menu de desenvolvedor"""
        if not self.dev_menu_aberto:
            
            desenhar_texto(self.tela, "DEV MODE (F7)", (10, 10), AMARELO, 16)
            desenhar_texto(self.tela, "F1:Level F2:+1min F3:Stats F4:Skill F5:Boss F6:Heal F8:God F9:MaxAll F11:Boss 2%", 
                          (10, 30), BRANCO, 14)
            
            if self.jogador.vida_infinita:
                desenhar_texto(self.tela, "VIDA INFINITA ATIVA", (10, 50), VERDE, 16)
            return
            
        
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        overlay.set_alpha(180)
        overlay.fill(PRETO)
        self.tela.blit(overlay, (0, 0))
        
        
        largura_menu = 500
        altura_menu = 450
        x_menu = LARGURA_TELA // 2 - largura_menu // 2
        y_menu = ALTURA_TELA // 2 - altura_menu // 2
        
        pygame.draw.rect(self.tela, (40, 40, 40), (x_menu, y_menu, largura_menu, altura_menu))
        pygame.draw.rect(self.tela, DOURADO, (x_menu, y_menu, largura_menu, altura_menu), 3)
        
        
        desenhar_texto(self.tela, "MENU DESENVOLVEDOR", 
                      (x_menu + largura_menu // 2 - 140, y_menu + 20), DOURADO, 24)
        
        y_atual = y_menu + 60
        espaco = 35
        
        
        comandos = [
            ("F1", "Subir de nível instantaneamente", VERDE),
            ("F2", "Avançar 1 minuto no tempo", AZUL_CLARO),  
            ("F3", "Dar upgrades básicos (level 1)", AMARELO),
            ("F4", "Dar habilidade especial aleatória", ROXO),
            ("F5", "Spawnar boss instantaneamente", VERMELHO),
            ("F6", "Curar jogador completamente", VERDE),
            ("F7", "Fechar este menu", BRANCO),
            ("F8", f"Vida Infinita: {'ON' if self.jogador.vida_infinita else 'OFF'}", 
             VERDE if self.jogador.vida_infinita else VERMELHO),
            ("F9", "TODOS upgrades nível MÁXIMO", DOURADO),
            ("F11", "Boss com 2% de vida", VERMELHO)
        ]
        
        for tecla, descricao, cor in comandos:
            
            pygame.draw.rect(self.tela, cor, (x_menu + 20, y_atual - 2, 30, 25))
            desenhar_texto(self.tela, tecla, (x_menu + 25, y_atual), PRETO, 16)
            
            
            desenhar_texto(self.tela, descricao, (x_menu + 65, y_atual), BRANCO, 18)
            y_atual += espaco
        
        
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
                pygame.mixer.music.stop()  
                pygame.mixer.music.load(self.caminho_musica_boss)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play(-1)  
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
                pygame.mixer.music.play(-1)  
                self.musica_boss_carregada = False
                print("Voltando para música inicial!")
            except Exception as e:
                print(f"Aviso: Erro ao voltar para música inicial: {e}")

    def atualizar_volume(self, novo_volume):
        """Atualiza o volume de todos os sons do jogo"""
        self.volume = novo_volume
        pygame.mixer.music.set_volume(novo_volume)  
        

    def obter_posicao_icone_volume(self):
        """Retorna a posição do ícone de volume"""
        return (20, ALTURA_TELA - 40)  
    
    def obter_posicao_barra_volume(self):
        """Retorna a posição e tamanho da barra de volume"""
        x_icone, y_icone = self.obter_posicao_icone_volume()
        x_barra = x_icone + 35   
        y_barra = y_icone + 10   
        largura_barra = 100      
        return x_barra, y_barra, largura_barra
    
    def desenhar_controle_volume(self):
        """Desenha o controle de volume no canto inferior esquerdo"""
        
        x_icone, y_icone = self.obter_posicao_icone_volume()
        self.tela.blit(self.imagem_volume, (x_icone, y_icone))
        
        
        x_barra, y_barra, largura_barra = self.obter_posicao_barra_volume()
        
        
        barra_rect = pygame.Rect(x_barra, y_barra, largura_barra, 8)
        pygame.draw.rect(self.tela, (50, 50, 50), barra_rect)  
        
        
        largura_atual = int(largura_barra * self.volume)
        if largura_atual > 0:
            pygame.draw.rect(self.tela, (100, 255, 100), 
                           (x_barra, y_barra, largura_atual, 8))
        
        
        pygame.draw.rect(self.tela, BRANCO, barra_rect, 1)

    def atualizar_boss(self):
        """Atualiza o estado do boss e seus projéteis"""
        if not self.boss or not self.boss.ativo:
            return
        
        
        novos_projeteis = self.boss.atualizar(self.jogador.pos)
        if novos_projeteis:
            self.projeteis_boss.extend(novos_projeteis)
        
        
        for proj_boss in self.projeteis_boss[:]:
            proj_boss.atualizar()
            if not proj_boss.ativo:
                self.projeteis_boss.remove(proj_boss)
        
        
        if self.boss and not self.boss.ativo:
            print("🔍 DEBUG: Boss morto detectado em atualizar_boss!")
            self.processar_vitoria_boss()

    def processar_colisoes_boss(self):
        """Processa colisões relacionadas ao boss"""
        if not self.boss or not self.boss.ativo:
            return
        
        
        self.boss.colidir_com_jogador(self.jogador)
        
        
        for proj_boss in self.projeteis_boss[:]:
            if proj_boss.colidir_com_jogador(self.jogador):
                pass  
        
        
        for projetil in self.projeteis[:]:
            if not projetil.ativo or not self.boss or not self.boss.ativo:
                continue
                
            distancia = calcular_distancia(projetil.pos, self.boss.pos)
            if distancia < projetil.raio + self.boss.raio:
                hp_antes = self.boss.hp
                boss_morreu = self.boss.receber_dano(projetil.dano)
                projetil.ativo = False
                
                
                if boss_morreu:
                    print("🔍 DEBUG: Boss morreu por projétil!")
                    self.processar_vitoria_boss()
                    return
        
        
        if self.boss and not self.boss.ativo:
            print("🔍 DEBUG: Boss morto detectado em processar_colisoes_boss!")
            self.processar_vitoria_boss()

    def spawnar_boss(self):
        """Spawna o boss no mapa"""
        if self.boss:
            return
        
        self.boss = Boss(
            LARGURA_MAPA // 2 + random.randint(-200, 200),
            ALTURA_MAPA // 2 + random.randint(-200, 200)
        )
        
        
        if self.som_boss_spawn:
            self.som_boss_spawn.play()
        
        
        self.tocar_musica_boss()
        
        
        self.inimigos.clear()
        
        self.xps.clear()

    def atualizar_projeteis(self):
        """Atualiza todos os projéteis do jogo"""
        for projetil in self.projeteis[:]:
            projetil.atualizar()
            if not projetil.ativo:
                self.projeteis.remove(projetil)
        
        
        for proj_inimigo in self.projeteis_inimigos[:]:
            proj_inimigo.atualizar()
            if not proj_inimigo.ativo:
                self.projeteis_inimigos.remove(proj_inimigo)

    def atualizar_itens(self):
        """Atualiza todos os itens do jogo"""
        for item in self.itens[:]:
            item.atualizar()
            if not item.ativo:
                self.itens.remove(item)

    def atualizar_xps(self):
        """Atualiza todos os XPs do jogo"""
        for xp in self.xps[:]:
            xp.atualizar(self.jogador.pos)
            if not xp.ativo:
                self.xps.remove(xp)

    def processar_vitoria_boss(self):
        """Processa a vitória do boss"""
        print("🎉 BOSS DERROTADO! VITÓRIA ALCANÇADA! 🎉")
        
        
        self.estado = "vitoria"
        
        self.tempo_vitoria = pygame.time.get_ticks()
        
        self.parar_musica_boss()
        
        self.projeteis.clear()
        self.projeteis_boss.clear()
        self.projeteis_inimigos.clear()
        self.inimigos.clear()
        self.xps.clear()
        self.itens.clear()
        self.raios.clear()
        self.bombas.clear()
        self.campos.clear()
        
        self.boss = None
        
        print("Tela de vitória ativada! Jogo terminará em 10 segundos ou ESC para sair.")

if __name__ == "__main__":
    jogo = Jogo()
    jogo.executar() 