import random
from config import *

class UpgradeManager:
    def __init__(self):
        # Definir todos os tipos de upgrade disponíveis
        self.upgrades_basicos = {
            'vida': {
                'nome': 'Vida Extra',
                'descricao': '+10 HP (Máx. 5 upgrades)',
                'tipo': 'vida',
                'nivel_max': 5
            },
            'dano': {
                'nome': 'Força',
                'descricao': '+5 de dano nos ataques',
                'tipo': 'dano',
                'nivel_max': 8
            },
            'velocidade': {
                'nome': 'Velocidade',
                'descricao': '+20% velocidade de movimento',
                'tipo': 'velocidade',
                'nivel_max': 6
            },
            'alcance': {
                'nome': 'Alcance',
                'descricao': '+30% alcance dos ataques',
                'tipo': 'alcance',
                'nivel_max': 5
            },
            'cadencia': {
                'nome': 'Cadência',
                'descricao': '+25% velocidade de ataque',
                'tipo': 'cadencia',
                'nivel_max': 6
            },
            'atravessar': {
                'nome': 'Penetração',
                'descricao': 'Projéteis atravessam +1 inimigo',
                'tipo': 'atravessar',
                'nivel_max': 4
            },
            'projeteis': {
                'nome': 'Múltiplos Tiros',
                'descricao': '+1 projétil simultâneo',
                'tipo': 'projeteis',
                'nivel_max': 4
            },
            'coleta': {
                'nome': 'Magnetismo XP',
                'descricao': '+20px raio de coleta de XP',
                'tipo': 'coleta',
                'nivel_max': 5
            }
        }
        
        self.upgrades_habilidades = {
            'espada': {
                'nome': 'Espada Orbital',
                'descricao': 'Espada que orbita e ataca inimigos',
                'tipo': 'espada',
                'nivel_max': 5
            },
            'dash': {
                'nome': 'Dash Temporal',
                'descricao': 'Teleporte rápido com invulnerabilidade',
                'tipo': 'dash',
                'nivel_max': 5
            },
            'bomba': {
                'nome': 'Bomba Automática',
                'descricao': 'Bombas explodem automaticamente',
                'tipo': 'bomba',
                'nivel_max': 5
            },
            'raios': {
                'nome': 'Raios Tempestade',
                'descricao': 'Raios automáticos com ramificações',
                'tipo': 'raios',
                'nivel_max': 5
            },
            'campo': {
                'nome': 'Campo Gravitacional',
                'descricao': 'Atrai e danifica inimigos constantemente',
                'tipo': 'campo',
                'nivel_max': 5
            }
        }
        
        # Contadores de cartas por tipo
        self.contadores_cartas = {
            'vida': 0, 'dano': 0, 'velocidade': 0, 'alcance': 0, 
            'cadencia': 0, 'atravessar': 0, 'projeteis': 0, 'coleta': 0,
            'espada': 0, 'dash': 0, 'bomba': 0, 'raios': 0, 'campo': 0
        }
        
        # Sistema de cartas lendárias
        self.cartas_lendarias_disponiveis = set()
        self.cartas_lendarias_obtidas = set()
    
    def obter_opcoes_upgrade(self, jogador):
        """Gera 3 opções de upgrade para o jogador escolher"""
        # Primeiro verificar se há cartas lendárias disponíveis
        self.verificar_cartas_lendarias()
        
        opcoes = []
        
        # Se há carta lendária disponível, incluir uma
        if self.cartas_lendarias_disponiveis:
            carta_lendaria = list(self.cartas_lendarias_disponiveis)[0]
            opcoes.append(self.criar_carta_lendaria(carta_lendaria))
            self.cartas_lendarias_disponiveis.remove(carta_lendaria)
            self.cartas_lendarias_obtidas.add(carta_lendaria)
        
        # Preencher o resto com cartas normais
        while len(opcoes) < 3:
            carta = self.gerar_carta_normal(jogador)
            if carta:
                opcoes.append(carta)
            else:
                # Fallback para cartas sempre disponíveis
                opcoes.append(self.gerar_carta_fallback(jogador))
        
        return opcoes[:3]
    
    def verificar_cartas_lendarias(self):
        """Verifica quais cartas lendárias devem ser desbloqueadas"""
        # Verificar cada tipo de upgrade para ver se atingiu 5 cartas
        for tipo, contador in self.contadores_cartas.items():
            if contador >= 5:
                carta_lendaria = f"{tipo}_lendaria"
                if carta_lendaria not in self.cartas_lendarias_obtidas:
                    self.cartas_lendarias_disponiveis.add(carta_lendaria)
    
    def gerar_carta_normal(self, jogador):
        """Gera uma carta de upgrade normal"""
        opcoes_disponiveis = []
        
        # Stats básicos - verificar se ainda pode melhorar
        if jogador.vida_nivel < 10:
            opcoes_disponiveis.append('vida')
        if jogador.dano_nivel < 10:
            opcoes_disponiveis.append('dano')
        if jogador.velocidade_nivel < 8:
            opcoes_disponiveis.append('velocidade')
        if jogador.alcance_nivel < 8:
            opcoes_disponiveis.append('alcance')
        if jogador.cadencia_nivel < 8:
            opcoes_disponiveis.append('cadencia')
        if jogador.atravessar_nivel < 5:
            opcoes_disponiveis.append('atravessar')
        if jogador.projeteis_nivel < 5:
            opcoes_disponiveis.append('projeteis')
        if jogador.coleta_nivel < 5:
            opcoes_disponiveis.append('coleta')
        
        # Habilidades especiais
        if jogador.espada_nivel < 5:
            opcoes_disponiveis.append('espada')
        if jogador.dash_nivel < 5:
            opcoes_disponiveis.append('dash')
        if jogador.bomba_nivel < 5:
            opcoes_disponiveis.append('bomba')
        if jogador.raios_nivel < 5:
            opcoes_disponiveis.append('raios')
        if jogador.campo_nivel < 5:
            opcoes_disponiveis.append('campo')
        
        if not opcoes_disponiveis:
            return None
        
        tipo_escolhido = random.choice(opcoes_disponiveis)
        return self.criar_carta_upgrade(tipo_escolhido, jogador)
    
    def criar_carta_upgrade(self, tipo, jogador):
        """Cria uma carta de upgrade baseada no tipo"""
        cartas_info = {
            'vida': {
                'id': 'vida',
                'nome': '❤️ Vida Extra',
                'descricao': f'+20 HP máximo (Nível {jogador.vida_nivel + 1})',
                'tipo': 'vida'
            },
            'dano': {
                'id': 'dano', 
                'nome': '⚔️ Força',
                'descricao': f'+3 de dano (Nível {jogador.dano_nivel + 1})',
                'tipo': 'dano'
            },
            'velocidade': {
                'id': 'velocidade',
                'nome': '💨 Velocidade',
                'descricao': f'+15% velocidade (Nível {jogador.velocidade_nivel + 1})',
                'tipo': 'velocidade'
            },
            'alcance': {
                'id': 'alcance',
                'nome': '🎯 Alcance',
                'descricao': f'+25% alcance (Nível {jogador.alcance_nivel + 1})',
                'tipo': 'alcance'
            },
            'cadencia': {
                'id': 'cadencia',
                'nome': '⚡ Cadência',
                'descricao': f'+20% velocidade ataque (Nível {jogador.cadencia_nivel + 1})',
                'tipo': 'cadencia'
            },
            'atravessar': {
                'id': 'atravessar',
                'nome': '🔥 Penetração',
                'descricao': f'+1 inimigo atravessado (Nível {jogador.atravessar_nivel + 1})',
                'tipo': 'atravessar'
            },
            'projeteis': {
                'id': 'projeteis',
                'nome': '🔫 Múltiplos Tiros',
                'descricao': f'+1 projétil (Nível {jogador.projeteis_nivel + 1})',
                'tipo': 'projeteis'
            },
            'coleta': {
                'id': 'coleta',
                'nome': '🧲 Magnetismo XP',
                'descricao': f'+30px raio coleta (Nível {jogador.coleta_nivel + 1})',
                'tipo': 'coleta'
            },
            'espada': {
                'id': 'espada',
                'nome': '⚔️ Espada Orbital',
                'descricao': f'Espada que orbita e ataca (Nível {jogador.espada_nivel + 1})',
                'tipo': 'espada'
            },
            'dash': {
                'id': 'dash',
                'nome': '⚡ Dash Temporal',
                'descricao': f'Movimento rápido + invulnerável (Nível {jogador.dash_nivel + 1})',
                'tipo': 'dash'
            },
            'bomba': {
                'id': 'bomba',
                'nome': '💥 Bomba Automática',
                'descricao': f'Bombas automáticas (Nível {jogador.bomba_nivel + 1})',
                'tipo': 'bomba'
            },
            'raios': {
                'id': 'raios',
                'nome': '⚡ Raios Tempestade',
                'descricao': f'Raios automáticos (Nível {jogador.raios_nivel + 1})',
                'tipo': 'raios'
            },
            'campo': {
                'id': 'campo',
                'nome': '🌀 Campo Gravitacional',
                'descricao': f'Atrai e danifica inimigos (Nível {jogador.campo_nivel + 1})',
                'tipo': 'campo'
            }
        }
        
        return cartas_info.get(tipo)
    
    def gerar_carta_fallback(self, jogador):
        """Gera uma carta de fallback - sempre dano ou vida"""
        opcoes_fallback = ['dano', 'vida', 'velocidade']
        tipo = random.choice(opcoes_fallback)
        return self.criar_carta_upgrade(tipo, jogador)
    
    def criar_carta_lendaria(self, tipo_lendaria):
        """Cria uma carta lendária com efeitos especiais"""
        cartas_lendarias = {
            'vida_lendaria': {
                'id': 'vida_lendaria',
                'nome': '💎 CORAÇÃO DOURADO',
                'descricao': '+100 HP máximo + Regeneração contínua',
                'tipo': 'vida_lendaria',
                'raridade': 'lendaria'
            },
            'dano_lendaria': {
                'id': 'dano_lendaria', 
                'nome': '💎 FORÇA SUPREMA',
                'descricao': '+200% de dano + 25% chance crítico',
                'tipo': 'dano_lendaria',
                'raridade': 'lendaria'
            },
            'velocidade_lendaria': {
                'id': 'velocidade_lendaria',
                'nome': '💎 VENTO DIVINO', 
                'descricao': '+150% velocidade + Clone fantasma',
                'tipo': 'velocidade_lendaria',
                'raridade': 'lendaria'
            },
            'alcance_lendaria': {
                'id': 'alcance_lendaria',
                'nome': '💎 PRECISÃO INFINITA',
                'descricao': '+300% alcance + Atravessa infinito',
                'tipo': 'alcance_lendaria',
                'raridade': 'lendaria'
            },
            'cadencia_lendaria': {
                'id': 'cadencia_lendaria',
                'nome': '💎 RAJADA ETERNA',
                'descricao': '+400% cadência + Tiros triplos',
                'tipo': 'cadencia_lendaria',
                'raridade': 'lendaria'
            },
            'atravessar_lendaria': {
                'id': 'atravessar_lendaria',
                'nome': '💎 PERFURAÇÃO CÓSMICA',
                'descricao': 'Atravessa infinito + Dano cumulativo',
                'tipo': 'atravessar_lendaria',
                'raridade': 'lendaria'
            },
            'projeteis_lendaria': {
                'id': 'projeteis_lendaria',
                'nome': '💎 CHUVA DE METEOROS',
                'descricao': '+5 projéteis + Padrão espiral 360°',
                'tipo': 'projeteis_lendaria',
                'raridade': 'lendaria'
            },
            'coleta_lendaria': {
                'id': 'coleta_lendaria',
                'nome': '💎 MAGNETISMO ABSOLUTO',
                'descricao': 'Atração tela inteira + XP dobrado',
                'tipo': 'coleta_lendaria',
                'raridade': 'lendaria'
            },
            'espada_lendaria': {
                'id': 'espada_lendaria',
                'nome': '💎 LÂMINAS DO CAOS',
                'descricao': '+3 espadas + Ondas de choque',
                'tipo': 'espada_lendaria',
                'raridade': 'lendaria'
            },
            'dash_lendaria': {
                'id': 'dash_lendaria',
                'nome': '💎 TELETRANSPORTE',
                'descricao': 'Sem cooldown + Explosão ao chegar',
                'tipo': 'dash_lendaria',
                'raridade': 'lendaria'
            },
            'bomba_lendaria': {
                'id': 'bomba_lendaria',
                'nome': '💎 APOCALIPSE',
                'descricao': 'Bombas nucleares + Efeito cadeia',
                'tipo': 'bomba_lendaria',
                'raridade': 'lendaria'
            },
            'raios_lendaria': {
                'id': 'raios_lendaria',
                'nome': '💎 TEMPESTADE ETERNA',
                'descricao': 'Tempestade permanente + Raios saltadores',
                'tipo': 'raios_lendaria',
                'raridade': 'lendaria'
            },
            'campo_lendaria': {
                'id': 'campo_lendaria',
                'nome': '💎 BURACO NEGRO',
                'descricao': 'Campo massivo + Dano contínuo extremo',
                'tipo': 'campo_lendaria',
                'raridade': 'lendaria'
            }
        }
        
        return cartas_lendarias.get(tipo_lendaria)
    
    def aplicar_upgrade(self, jogador, upgrade_opcao):
        """Aplica um upgrade ao jogador e incrementa contador"""
        upgrade_id = upgrade_opcao['id']
        
        # Incrementar contador para cartas normais
        if upgrade_id in self.contadores_cartas:
            self.contadores_cartas[upgrade_id] += 1
        
        # Aplicar efeitos do upgrade
        if upgrade_id == 'vida':
            jogador.vida_nivel += 1
            jogador.hp_max += 20
            jogador.hp = jogador.hp_max  # Curar completamente
        
        elif upgrade_id == 'dano':
            jogador.dano_nivel += 1
            jogador.dano += 3
        
        elif upgrade_id == 'velocidade':
            jogador.velocidade_nivel += 1
            jogador.velocidade *= 1.15  # +15%
        
        elif upgrade_id == 'alcance':
            jogador.alcance_nivel += 1
            jogador.alcance_tiro *= 1.25  # +25%
        
        elif upgrade_id == 'cadencia':
            jogador.cadencia_nivel += 1
            jogador.cooldown_tiro = max(50, int(jogador.cooldown_tiro * 0.8))  # +20% velocidade
        
        elif upgrade_id == 'atravessar':
            jogador.atravessar_nivel += 1
            jogador.atravessar_inimigos += 1
        
        elif upgrade_id == 'projeteis':
            jogador.projeteis_nivel += 1
            jogador.projeteis_simultaneos += 1
        
        elif upgrade_id == 'coleta':
            jogador.coleta_nivel += 1
            jogador.raio_coleta += 30
        
        elif upgrade_id == 'espada':
            jogador.espada_nivel += 1
            jogador.atualizar_espadas()  # Atualizar espadas orbitais
        
        elif upgrade_id == 'dash':
            jogador.dash_nivel += 1
        
        elif upgrade_id == 'bomba':
            jogador.bomba_nivel += 1
        
        elif upgrade_id == 'raios':
            jogador.raios_nivel += 1
        
        elif upgrade_id == 'campo':
            jogador.campo_nivel += 1
        
        # Aplicar efeitos lendários
        elif upgrade_id.endswith('_lendaria'):
            self.aplicar_efeito_lendario(jogador, upgrade_id)
    
    def aplicar_efeito_lendario(self, jogador, tipo):
        """Aplica efeitos especiais das cartas lendárias"""
        if tipo == 'vida_lendaria':
            jogador.hp_max += 100
            jogador.hp = jogador.hp_max
            jogador.regeneracao = getattr(jogador, 'regeneracao', 0) + 2  # +2 HP/seg
        
        elif tipo == 'dano_lendaria':
            jogador.dano = int(jogador.dano * 3)  # +200% = 3x
            jogador.critico_chance = getattr(jogador, 'critico_chance', 0) + 0.25
        
        elif tipo == 'velocidade_lendaria':
            jogador.velocidade *= 2.5  # +150% = 2.5x
            jogador.clone_fantasma = True
        
        elif tipo == 'alcance_lendaria':
            jogador.alcance_tiro *= 4  # +300% = 4x
            jogador.atravessar_inimigos = 999  # Infinito
        
        elif tipo == 'cadencia_lendaria':
            jogador.cooldown_tiro = max(20, jogador.cooldown_tiro // 5)  # +400%
            jogador.tiros_triplos = True
        
        elif tipo == 'atravessar_lendaria':
            jogador.atravessar_inimigos = 999
            jogador.dano_acumulativo = True
        
        elif tipo == 'projeteis_lendaria':
            jogador.projeteis_simultaneos += 5
            jogador.padrao_espiral = True
        
        elif tipo == 'coleta_lendaria':
            jogador.raio_coleta = 2000  # Tela inteira
            jogador.xp_multiplicador = getattr(jogador, 'xp_multiplicador', 1.0) * 2.0
        
        elif tipo == 'espada_lendaria':
            jogador.espada_nivel += 3
            jogador.ondas_choque = True
            jogador.atualizar_espadas()
        
        elif tipo == 'dash_lendaria':
            jogador.dash_cooldown_lendario = True
            jogador.dash_explosao = True
        
        elif tipo == 'bomba_lendaria':
            jogador.bomba_nivel += 2
            jogador.bombas_nucleares = True
        
        elif tipo == 'raios_lendaria':
            jogador.raios_nivel += 2
            jogador.tempestade_permanente = True
        
        elif tipo == 'campo_lendaria':
            jogador.campo_nivel = 10  # Máximo especial
            jogador.buraco_negro = True 