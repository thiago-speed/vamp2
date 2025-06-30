# Vampire Survivors Demo

Demo de jogo estilo Vampire Survivors feita em Python com Pygame.

## Como executar

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Execute o jogo:
```bash
python main.py
```

3. Para compilar em executável:
```bash
pyinstaller --onefile main.py
```

## Controles

- **WASD** ou **setas**: Mover jogador
- **1/2** ou **setas + Enter**: Escolher upgrades
- **ESC**: Sair do jogo

## Gameplay

- O jogador atira automaticamente no inimigo mais próximo
- Colete XP dos inimigos mortos para subir de nível
- Escolha upgrades a cada level up
- Sobreviva por 10 minutos para enfrentar o boss final
- Derrote o boss para vencer!

## Mecânicas

- 3 tipos de inimigos: Normal, Rápido, Tanque
- Upgrades básicos: dano, vida, projéteis, etc.
- Upgrades físicos: espada, raios, dash, bomba, escudo, campo
- Itens especiais: XP magnético, bomba de tela
- Minimapa no canto superior direito
- Dificuldade escala com o tempo 