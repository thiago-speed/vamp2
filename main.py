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
from boss import Boss, ProjetilBoss
from inimigo import gerar_inimigo_aleatorio
from itens import gerar_item_aleatorio, usar_item_xp_magnetico, usar_item_bomba_tela, usar_item_coracao

class Jogo:
    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
        pygame.display.set_caption("Vampire Survivors - Demo")
        self.clock = pygame.time.Clock()
        
        # Inicialização do cenário espacial
        self.cenario = CenarioEspacial()
        
        # Estado do jogo
        self.estado = "jogando"  # "jogando", "upgrade", "game_over", "vitoria"
        self.inicio_jogo = pygame.time.get_ticks()
        
        # Câmera
        self.camera = [0, 0]
        
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
        
        # Modo Desenvolvedor
        self.modo_dev = True  # Ativar por padrão para testes
        self.dev_menu_aberto = False
        
    def obter_tempo_jogo(self):
        """Retorna o tempo de jogo em segundos"""
        return (pygame.time.get_ticks() - self.inicio_jogo) / 1000.0
    
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
        """Atualiza todos os elementos do jogo"""
        if self.estado != "jogando":
            return
        
        # Atualizar cenário
        self.cenario.atualizar()
        
        keys = pygame.key.get_pressed()
        
        # Atualizar jogador
        self.jogador.mover(keys)
        self.jogador.atualizar()
        
        # Atualizar espadas orbitais com lista de inimigos
        for espada in self.jogador.obter_espadas():
            espada.atualizar(self.inimigos)
        
        # Verificar se o jogador morreu
        if not self.jogador.esta_vivo():
            self.estado = "game_over"
            return
        
        # Verificar vitória (boss morto)
        if self.boss and not self.boss.ativo:
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
        
        pygame.display.flip()
    
    def desenhar_ui(self):
        """Desenha a interface do usuário com fontes melhoradas"""
        # Fundo semi-transparente para UI
        ui_fundo = pygame.Surface((300, 150))
        ui_fundo.set_alpha(120)
        ui_fundo.fill((0, 0, 0))
        self.tela.blit(ui_fundo, (5, 5))
        
        # Barra de vida melhorada
        desenhar_texto(self.tela, f"❤️ HP: {self.jogador.hp}/{self.jogador.hp_max}", 
                      (15, 15), VERMELHO, 24, sombra=True)
        
        # Level e XP com ícones
        desenhar_texto(self.tela, f"⭐ Level: {self.jogador.level}", 
                      (15, 45), DOURADO, 24, sombra=True)
        desenhar_texto(self.tela, f"✨ XP: {self.jogador.xp}/{self.jogador.xp_para_proximo}", 
                      (15, 75), AZUL_CLARO, 24, sombra=True)
        
        # Tempo de jogo com formatação corrigida
        tempo = self.obter_tempo_jogo()
        minutos = int(tempo // 60)
        segundos = int(tempo % 60)
        tempo_texto = f"⏰ Tempo: {minutos:02d}:{segundos:02d}"
        
        # Mudar cor quando se aproxima da arena do boss
        if tempo >= 780:  # 13 minutos - aviso
            cor_tempo = VERMELHO
            if tempo >= 840:  # 14 minutos - arena do boss
                tempo_texto += " 🏟️ ARENA DO BOSS!"
        else:
            cor_tempo = BRANCO
            
        desenhar_texto(self.tela, tempo_texto, (15, 105), cor_tempo, 24, sombra=True)
        
        # Coleta de XP se ativo
        if self.jogador.coleta_nivel > 0:
            desenhar_texto(self.tela, f"🔮 Coleta Nv.{self.jogador.coleta_nivel}", 
                          (15, 135), VERDE, 20, sombra=True)
        
        # Barra de vida do boss se ativo
        if self.boss and self.boss.ativo:
            self.desenhar_barra_boss()
        
        # Painel de habilidades (lado direito) melhorado
        x_habilidades = LARGURA_TELA - 280
        y_base = 15
        
        # Fundo do painel de habilidades
        painel_hab = pygame.Surface((270, 200))
        painel_hab.set_alpha(120)
        painel_hab.fill((0, 0, 0))
        self.tela.blit(painel_hab, (x_habilidades - 5, y_base - 5))
        
        desenhar_texto(self.tela, "🔥 HABILIDADES", (x_habilidades, y_base), 
                      (255, 215, 0), 20, sombra=True)
        y_base += 30
        
        # Dash (ESPAÇO) - única habilidade manual
        if self.jogador.dash_nivel > 0:
            if self.jogador.dash_cooldown > 0:
                cor = VERMELHO
                texto = f"⚡ Dash (ESPAÇO): {self.jogador.dash_cooldown//1000 + 1}s"
            else:
                cor = VERDE
                texto = f"⚡ Dash (ESPAÇO): PRONTO ✓"
            desenhar_texto(self.tela, texto, (x_habilidades, y_base), cor, 18, sombra=True)
            y_base += 25
        
        # Espada (automática)
        if self.jogador.espada_nivel > 0:
            texto = f"⚔️ Espada Nv.{self.jogador.espada_nivel}: ATIVA ✓"
            desenhar_texto(self.tela, texto, (x_habilidades, y_base), 
                          (255, 165, 0), 18, sombra=True)
            y_base += 25
        
        # Bomba (automática)
        if self.jogador.bomba_nivel > 0:
            tempo_restante = max(0, 8000 - (self.jogador.bomba_nivel * 1000) - 
                               (pygame.time.get_ticks() - self.jogador.ultimo_bomba_auto))
            if tempo_restante > 0:
                texto = f"💥 Próxima Bomba: {tempo_restante//1000 + 1}s"
                cor = VERMELHO
            else:
                texto = f"💥 Bomba Nv.{self.jogador.bomba_nivel}: PRONTA ✓"
                cor = VERDE
            desenhar_texto(self.tela, texto, (x_habilidades, y_base), cor, 18, sombra=True)
            y_base += 25
        
        # Raios (automáticos)
        if self.jogador.raios_nivel > 0:
            tempo_restante = max(0, 6000 - (self.jogador.raios_nivel * 800) - 
                               (pygame.time.get_ticks() - self.jogador.ultimo_raios_auto))
            if tempo_restante > 0:
                texto = f"⚡ Próximos Raios: {tempo_restante//1000 + 1}s"
                cor = VERMELHO
            else:
                texto = f"⚡ Raios Nv.{self.jogador.raios_nivel}: PRONTOS ✓"
                cor = VERDE
            desenhar_texto(self.tela, texto, (x_habilidades, y_base), cor, 18, sombra=True)
            y_base += 25
        
        # Campo gravitacional (sempre ativo)
        if self.jogador.campo_nivel > 0:
            if self.jogador.campo_nivel >= 5:
                texto = f"🌀 Campo Nv.{self.jogador.campo_nivel}: MÁXIMO ⭐"
                cor = (200, 100, 255)
            else:
                texto = f"🌀 Campo Nv.{self.jogador.campo_nivel}: ATIVO ✓"
                cor = (150, 100, 255)
            desenhar_texto(self.tela, texto, (x_habilidades, y_base), cor, 18, sombra=True)
            y_base += 25
        
        # Instruções de controle modernas (canto inferior direito)
        y_instrucoes = ALTURA_TELA - 80
        instrucoes_fundo = pygame.Surface((280, 70))
        instrucoes_fundo.set_alpha(100)
        instrucoes_fundo.fill((0, 0, 0))
        self.tela.blit(instrucoes_fundo, (x_habilidades - 5, y_instrucoes - 5))
        
        desenhar_texto(self.tela, "🎮 CONTROLES", (x_habilidades, y_instrucoes), 
                      (255, 215, 0), 18, sombra=True)
        desenhar_texto(self.tela, "🖱️ Mouse - Atirar", (x_habilidades, y_instrucoes + 20), 
                      BRANCO, 16, sombra=True)
        desenhar_texto(self.tela, "⌨️ WASD - Mover", (x_habilidades, y_instrucoes + 40), 
                      BRANCO, 16, sombra=True)
        if self.jogador.dash_nivel > 0:
            desenhar_texto(self.tela, "⚡ ESPAÇO - Dash", (x_habilidades, y_instrucoes + 60), 
                          AZUL_CLARO, 16, sombra=True)
    
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
                return False
            
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    if self.estado == "jogando":
                        pygame.quit()
                        exit()
                    elif self.estado in ["game_over", "vitoria"]:
                        pygame.quit()
                        exit()
                
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
        
        return True
    
    def executar(self):
        """Loop principal do jogo"""
        rodando = True
        
        while rodando:
            rodando = self.processar_eventos()
            
            self.atualizar()
            self.desenhar()
            
            self.clock.tick(FPS)
        
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
        
        # Texto do boss
        texto_boss = f"👹 BOSS: {self.boss.hp}/{self.boss.hp_max} HP"
        desenhar_texto(self.tela, texto_boss, (x_barra + largura_barra // 2 - 100, y_barra - 30), 
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
        
        desenhar_texto(self.tela, "🎉 TODOS OS UPGRADES COLETADOS! 🎉", 
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
                desenhar_texto(self.tela, "🛡️ VIDA INFINITA ATIVA", (10, 50), VERDE, 16)
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
        desenhar_texto(self.tela, "🎮 MENU DESENVOLVEDOR 🎮", 
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

if __name__ == "__main__":
    jogo = Jogo()
    jogo.executar() 