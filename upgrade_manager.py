import random
from config import *

class UpgradeManager:
    def __init__(self):
        # Contadores de cartas por tipo
        self.contadores_cartas = {
            'vida': 0, 'dano': 0, 'velocidade': 0, 'alcance': 0, 
            'cadencia': 0, 'atravessar': 0, 'projeteis': 0, 'coleta': 0,
            'espada': 0, 'dash': 0, 'bomba': 0, 'raios': 0, 'campo': 0
        }
        
        # Sistema de cartas lendárias
        self.cartas_lendarias_disponiveis = set()
        self.cartas_lendarias_obtidas = set()
        
        # Controle de cartas repetidas - cada carta só pode aparecer uma vez por seleção
        self.cartas_ja_oferecidas = set()
    
    def get_upgrades_basicos(self, jogador):
        """Retorna os upgrades básicos disponíveis"""
        return {
            'vida': {
                'nome': 'Vida Extra',
                'descricao': f'Nivel {jogador.vida_nivel} -> UPGRADE PRO NIVEL {jogador.vida_nivel + 1}',
                'tipo': 'vida'
            },
            'dano': {
                'nome': 'Forca',
                'descricao': f'Nivel {jogador.dano_nivel} -> UPGRADE PRO NIVEL {jogador.dano_nivel + 1}',
                'tipo': 'dano'
            },
            'velocidade': {
                'nome': 'Velocidade',
                'descricao': f'Nivel {jogador.velocidade_nivel} -> UPGRADE PRO NIVEL {jogador.velocidade_nivel + 1}',
                'tipo': 'velocidade'
            },
            'alcance': {
                'nome': 'Alcance',
                'descricao': f'Nivel {jogador.alcance_nivel} -> UPGRADE PRO NIVEL {jogador.alcance_nivel + 1}',
                'tipo': 'alcance'
            },
            'cadencia': {
                'nome': 'Cadencia',
                'descricao': f'Nivel {jogador.cadencia_nivel} -> UPGRADE PRO NIVEL {jogador.cadencia_nivel + 1}',
                'tipo': 'cadencia'
            },
            'atravessar': {
                'nome': 'Perfuracao',
                'descricao': f'Nivel {jogador.atravessar_nivel} -> UPGRADE PRO NIVEL {jogador.atravessar_nivel + 1}',
                'tipo': 'atravessar'
            },
            'projeteis': {
                'nome': 'Penetracao',
                'descricao': f'Nivel {jogador.projeteis_nivel} -> UPGRADE PRO NIVEL {jogador.projeteis_nivel + 1}',
                'tipo': 'projeteis'
            },
            'coleta': {
                'nome': 'Ima de XP',
                'descricao': f'Nivel {jogador.coleta_nivel} -> UPGRADE PRO NIVEL {jogador.coleta_nivel + 1}',
                'tipo': 'coleta'
            }
        }
        
    def get_upgrades_habilidades(self, jogador):
        """Retorna as habilidades especiais disponíveis"""
        return {
            'espada': {
                'nome': 'Espada Orbital',
                'descricao': f'Nivel {jogador.espada_nivel} -> UPGRADE PRO NIVEL {jogador.espada_nivel + 1}',
                'tipo': 'espada'
            },
            'dash': {
                'nome': 'Dash Temporal',
                'descricao': f'Nivel {jogador.dash_nivel} -> UPGRADE PRO NIVEL {jogador.dash_nivel + 1}',
                'tipo': 'dash'
            },
            'bomba': {
                'nome': 'Bomba Automatica',
                'descricao': f'Nivel {jogador.bomba_nivel} -> UPGRADE PRO NIVEL {jogador.bomba_nivel + 1}',
                'tipo': 'bomba'
            },
            'raios': {
                'nome': 'Raios Tempestade',
                'descricao': f'Nivel {jogador.raios_nivel} -> UPGRADE PRO NIVEL {jogador.raios_nivel + 1}',
                'tipo': 'raios'
            },
            'campo': {
                'nome': 'Campo Gravitacional',
                'descricao': f'Nivel {jogador.campo_nivel} -> UPGRADE PRO NIVEL {jogador.campo_nivel + 1}',
                'tipo': 'campo'
            }
        }
    
    def obter_opcoes_upgrade(self, jogador):
        """Gera 3 opções de upgrade para o jogador escolher - sem repetições"""
        # Limpar lista de cartas já oferecidas a cada nova seleção
        self.cartas_ja_oferecidas.clear()
        
        # Primeiro verificar se todos os upgrades estão no máximo
        if self.todos_upgrades_maximos(jogador):
            return "todos_maximos"  # Sinal especial
        
        # Primeiro verificar se há cartas lendárias disponíveis
        self.verificar_cartas_lendarias()
        
        opcoes = []
        tentativas = 0
        max_tentativas = 50  # Evitar loop infinito
        
        # Se há carta lendária disponível, incluir uma
        if self.cartas_lendarias_disponiveis and tentativas < max_tentativas:
            carta_lendaria = list(self.cartas_lendarias_disponiveis)[0]
            opcoes.append(self.criar_carta_lendaria(carta_lendaria))
            self.cartas_lendarias_disponiveis.remove(carta_lendaria)
            self.cartas_lendarias_obtidas.add(carta_lendaria)
            self.cartas_ja_oferecidas.add(carta_lendaria)
        
        # Preencher o resto com cartas normais (sem repetições)
        while len(opcoes) < 3 and tentativas < max_tentativas:
            tentativas += 1
            carta = self.gerar_carta_normal(jogador)
            if carta and carta['id'] not in self.cartas_ja_oferecidas:
                opcoes.append(carta)
                self.cartas_ja_oferecidas.add(carta['id'])
            elif not carta:
                # Fallback para cartas sempre disponíveis
                carta_fallback = self.gerar_carta_fallback(jogador)
                if carta_fallback and carta_fallback['id'] not in self.cartas_ja_oferecidas:
                    opcoes.append(carta_fallback)
                    self.cartas_ja_oferecidas.add(carta_fallback['id'])
        
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
        
        # Stats básicos - verificar se ainda pode melhorar E se não tem lendária
        if jogador.vida_nivel < 10 and 'vida_lendaria' not in self.cartas_lendarias_obtidas:
            opcoes_disponiveis.append('vida')
        if jogador.dano_nivel < 10 and 'dano_lendaria' not in self.cartas_lendarias_obtidas:
            opcoes_disponiveis.append('dano')
        if jogador.velocidade_nivel < 8 and 'velocidade_lendaria' not in self.cartas_lendarias_obtidas:
            opcoes_disponiveis.append('velocidade')
        if jogador.alcance_nivel < 8 and 'alcance_lendaria' not in self.cartas_lendarias_obtidas:
            opcoes_disponiveis.append('alcance')
        if jogador.cadencia_nivel < 8 and 'cadencia_lendaria' not in self.cartas_lendarias_obtidas:
            opcoes_disponiveis.append('cadencia')
        if jogador.atravessar_nivel < 5 and 'atravessar_lendaria' not in self.cartas_lendarias_obtidas:
            opcoes_disponiveis.append('atravessar')
        if jogador.projeteis_nivel < 5 and 'projeteis_lendaria' not in self.cartas_lendarias_obtidas:
            opcoes_disponiveis.append('projeteis')
        if jogador.coleta_nivel < 5 and 'coleta_lendaria' not in self.cartas_lendarias_obtidas:
            opcoes_disponiveis.append('coleta')
        
        # Habilidades especiais - verificar se não tem lendária
        if jogador.espada_nivel < 5 and 'espada_lendaria' not in self.cartas_lendarias_obtidas:
            opcoes_disponiveis.append('espada')
        if jogador.dash_nivel < 5 and 'dash_lendaria' not in self.cartas_lendarias_obtidas:
            opcoes_disponiveis.append('dash')
        if jogador.bomba_nivel < 5 and 'bomba_lendaria' not in self.cartas_lendarias_obtidas:
            opcoes_disponiveis.append('bomba')
        if jogador.raios_nivel < 5 and 'raios_lendaria' not in self.cartas_lendarias_obtidas:
            opcoes_disponiveis.append('raios')
        if jogador.campo_nivel < 5 and 'campo_lendaria' not in self.cartas_lendarias_obtidas:
            opcoes_disponiveis.append('campo')
        
        if not opcoes_disponiveis:
            return None
        
        tipo_escolhido = random.choice(opcoes_disponiveis)
        return self.criar_carta_upgrade(tipo_escolhido, jogador)
    
    def criar_carta_upgrade(self, tipo, jogador):
        """Cria uma carta de upgrade baseada no tipo"""
        # Usar os métodos que já criei para obter as informações corretas
        upgrades_basicos = self.get_upgrades_basicos(jogador)
        upgrades_habilidades = self.get_upgrades_habilidades(jogador)
        
        # Primeiro verificar nos básicos
        if tipo in upgrades_basicos:
            info = upgrades_basicos[tipo]
            return {
                'id': tipo,
                'nome': info['nome'],
                'descricao': info['descricao'],
                'tipo': tipo
            }
        
        # Depois verificar nas habilidades
        if tipo in upgrades_habilidades:
            info = upgrades_habilidades[tipo]
            return {
                'id': tipo,
                'nome': info['nome'],
                'descricao': info['descricao'],
                'tipo': tipo
            }
        
        # Fallback para tipos não encontrados
        return {
            'id': tipo,
            'nome': f'Upgrade {tipo.title()}',
            'descricao': f'Melhora {tipo}',
            'tipo': tipo
        }
    
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
                'nome': 'CORACAO DOURADO',
                'descricao': '+100 HP maximo + Regeneracao continua',
                'tipo': 'vida_lendaria',
                'raridade': 'lendaria'
            },
            'dano_lendaria': {
                'id': 'dano_lendaria', 
                'nome': 'FORCA SUPREMA',
                'descricao': '+200% de dano + 25% chance critico',
                'tipo': 'dano_lendaria',
                'raridade': 'lendaria'
            },
            'velocidade_lendaria': {
                'id': 'velocidade_lendaria',
                'nome': 'VENTO DIVINO', 
                'descricao': '+150% velocidade + Clone fantasma',
                'tipo': 'velocidade_lendaria',
                'raridade': 'lendaria'
            },
            'alcance_lendaria': {
                'id': 'alcance_lendaria',
                'nome': 'PRECISAO INFINITA',
                'descricao': '+300% alcance + Atravessa infinito',
                'tipo': 'alcance_lendaria',
                'raridade': 'lendaria'
            },
            'cadencia_lendaria': {
                'id': 'cadencia_lendaria',
                'nome': 'RAJADA ETERNA',
                'descricao': '+400% cadencia + Tiros triplos',
                'tipo': 'cadencia_lendaria',
                'raridade': 'lendaria'
            },
            'atravessar_lendaria': {
                'id': 'atravessar_lendaria',
                'nome': 'PERFURACAO COSMICA',
                'descricao': 'Atravessa infinito + Dano cumulativo',
                'tipo': 'atravessar_lendaria',
                'raridade': 'lendaria'
            },
            'projeteis_lendaria': {
                'id': 'projeteis_lendaria',
                'nome': 'CHUVA DE METEOROS',
                'descricao': '+5 projeteis + Padrao espiral 360 graus',
                'tipo': 'projeteis_lendaria',
                'raridade': 'lendaria'
            },
            'coleta_lendaria': {
                'id': 'coleta_lendaria',
                'nome': 'MAGNETISMO ABSOLUTO',
                'descricao': 'Atracao tela inteira + XP dobrado',
                'tipo': 'coleta_lendaria',
                'raridade': 'lendaria'
            },
            'espada_lendaria': {
                'id': 'espada_lendaria',
                'nome': 'LAMINAS DO CAOS',
                'descricao': '+3 espadas + Ondas de choque',
                'tipo': 'espada_lendaria',
                'raridade': 'lendaria'
            },
            'dash_lendaria': {
                'id': 'dash_lendaria',
                'nome': 'TELETRANSPORTE',
                'descricao': 'Sem cooldown + Explosao ao chegar',
                'tipo': 'dash_lendaria',
                'raridade': 'lendaria'
            },
            'bomba_lendaria': {
                'id': 'bomba_lendaria',
                'nome': 'APOCALIPSE',
                'descricao': 'Bombas nucleares + Efeito cadeia',
                'tipo': 'bomba_lendaria',
                'raridade': 'lendaria'
            },
            'raios_lendaria': {
                'id': 'raios_lendaria',
                'nome': 'TEMPESTADE ETERNA',
                'descricao': 'Tempestade permanente + Raios saltadores',
                'tipo': 'raios_lendaria',
                'raridade': 'lendaria'
            },
            'campo_lendaria': {
                'id': 'campo_lendaria',
                'nome': 'BURACO NEGRO',
                'descricao': 'Campo massivo + Dano continuo extremo',
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
            jogador.velocidade *= 2.0  # +100% = 2x (era 2.5x)
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
    
    def todos_upgrades_maximos(self, jogador):
        """Verifica se todos os upgrades estão no nível máximo ou têm carta lendária"""
        # Verificar stats básicos - considera máximo se tem lendária OU nível máximo
        if (not (jogador.vida_nivel >= 10 or 'vida_lendaria' in self.cartas_lendarias_obtidas) or
            not (jogador.dano_nivel >= 10 or 'dano_lendaria' in self.cartas_lendarias_obtidas) or 
            not (jogador.velocidade_nivel >= 8 or 'velocidade_lendaria' in self.cartas_lendarias_obtidas) or
            not (jogador.alcance_nivel >= 8 or 'alcance_lendaria' in self.cartas_lendarias_obtidas) or
            not (jogador.cadencia_nivel >= 8 or 'cadencia_lendaria' in self.cartas_lendarias_obtidas) or
            not (jogador.atravessar_nivel >= 5 or 'atravessar_lendaria' in self.cartas_lendarias_obtidas) or
            not (jogador.projeteis_nivel >= 5 or 'projeteis_lendaria' in self.cartas_lendarias_obtidas) or
            not (jogador.coleta_nivel >= 5 or 'coleta_lendaria' in self.cartas_lendarias_obtidas)):
            return False
        
        # Verificar habilidades especiais - considera máximo se tem lendária OU nível máximo
        if (not (jogador.espada_nivel >= 5 or 'espada_lendaria' in self.cartas_lendarias_obtidas) or
            not (jogador.dash_nivel >= 5 or 'dash_lendaria' in self.cartas_lendarias_obtidas) or
            not (jogador.bomba_nivel >= 5 or 'bomba_lendaria' in self.cartas_lendarias_obtidas) or
            not (jogador.raios_nivel >= 5 or 'raios_lendaria' in self.cartas_lendarias_obtidas) or
            not (jogador.campo_nivel >= 5 or 'campo_lendaria' in self.cartas_lendarias_obtidas)):
            return False
        
        # Verificar se ainda há cartas lendárias disponíveis
        self.verificar_cartas_lendarias()
        if self.cartas_lendarias_disponiveis:
            return False
        
        return True 