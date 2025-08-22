import pygame
import sys
from pygame import gfxdraw  # círculos AA

# =========================
# INICIAL
# =========================
pygame.init()

WIDTH, HEIGHT = 1366, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Crossing the banks")

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PRIMARY = (0, 120, 255)
PRIMARY_DARK = (0, 90, 190)
GRAY_PANEL = (255, 255, 255, 215)
GRAY_TEXT = (70, 70, 70)

#Titulo
complete = False
last_status = ""

# Fontes
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 26)
marker_font = pygame.font.Font(None, 30)  # texto dentro do círculo

# Sprites
sprites = {
    "F": pygame.transform.smoothscale(
        pygame.image.load("assets/fazendeiro.png").convert_alpha(), (80, 148)
    ),
    "C": pygame.transform.smoothscale(
        pygame.image.load("assets/cabra.png").convert_alpha(), (96, 96)
    ),
    "L": pygame.transform.smoothscale(
        pygame.image.load("assets/lobo.png").convert_alpha(), (96, 96)
    ),
    "A": pygame.transform.smoothscale(
        pygame.image.load("assets/alface.png").convert_alpha(), (96, 96)
    ),
}
boat_img = pygame.transform.smoothscale(
    pygame.image.load("assets/barco.png").convert_alpha(), (192, 57)
)

# =========================
# carregar a img Diagrama
# =========================
DIAGRAM_H = 280
DIAGRAM_W = 1156
DIAGRAM_POS = (105, 10)  # onde o diagrama é blitado
diagram_src = pygame.image.load("assets/diagram.png").convert_alpha()
diagram_img = pygame.transform.smoothscale(diagram_src, (DIAGRAM_W, DIAGRAM_H))

# =========================
# Background Rio e as Margens
# =========================
rio_src = pygame.image.load("assets/rio.png").convert_alpha()
rio_img = pygame.transform.smoothscale(rio_src, (WIDTH, 468))

names = {"F": "Fazendeiro", "C": "Cabra", "L": "Lobo", "A": "Alface"}

# =========================
# carregar a img Game Over e completed 
# =========================

gameOver_src = pygame.image.load("assets/over.png").convert_alpha()
gameOver_img = pygame.transform.smoothscale(gameOver_src, (500,306))
completed_src = pygame.image.load("assets/completed.png").convert_alpha()
completed_img = pygame.transform.smoothscale(completed_src, (400,257))

# =========================
# ESTADOS DO AFD
# =========================
estados = {
    "q0": {"FC": "q1"},
    "q1": {"FC": "q0", "F_": "q2"},
    "q2": {"F_": "q1", "FL": "q3", "FA": "q4"},
    "q3": {"FC": "q5", "FL": "q2"},
    "q4": {"FA": "q2", "FC": "q6"},
    "q5": {"FC": "q3", "FA": "q7"},
    "q6": {"FC": "q4", "FL": "q7"},
    "q7": {"F_": "q8", "FA": "q5", "FL": "q6"},
    "q8": {"F_": "q7", "FC": "q9"},
    "q9": {"FC": "q8"},
}
ESTADO_INICIAL = "q0"
ESTADO_FINAL = {"q9"}
estado_atual = ESTADO_INICIAL
# =========================
# Estado visual
# =========================
left_bank = ["F", "C", "L", "A"]
right_bank = []
boat_side = "left"
boat_x = 350
boat_y = 550

# Layout
MARGIN_Y_START = 300
MARGIN_SPACING = 110
FARMER_SPACING = 40
FARMER_MARGIN_Y_OFFSET = -1
PASSENGER_BOAT_X_OFFSET = 15
PASSENGER_BOAT_X_SPACING = 80
NON_FARMER_BOAT_Y = -50
FARMER_BOAT_Y = -98

# =========================
#  Posições do circulo no diagrama
# =========================
state_pos_norm = {
    "q0": (0.03706712802768166, 0.525),
    "q1": (0.17487543252595156, 0.525),
    "q2": (0.3052681660899654, 0.525),
    "q3": (0.4362560553633218, 0.25357142857142856),
    "q4": (0.43655121107266434, 0.7994285714285714),
    "q5": (0.5666089965397924, 0.25357142857142856),
    "q6": (0.5667439446366782, 0.7994285714285714),
    "q7": (0.6980968858131488, 0.525),
    "q8": (0.828719723183391, 0.525),
    "q9": (0.9661, 0.525),
}

def state_center_px(state_id: str):
    u, v = state_pos_norm[state_id]
    x = DIAGRAM_POS[0] + int(u * DIAGRAM_W)
    y = DIAGRAM_POS[1] + int(v * DIAGRAM_H)
    return x, y

# =========================
#  Circulo com texto no diagrama
# =========================
def draw_state_marker(state_id: str):
    cx, cy = state_center_px(state_id)
    r_fill = 22
    r_border = 24
    fill_color = (255, 255, 255)
    border_color = PRIMARY

    # Sombra (leve)
    gfxdraw.filled_circle(screen, cx, cy + 2, r_border, (0, 0, 0, 90))
    gfxdraw.aacircle(screen, cx, cy + 2, r_border, (0, 0, 0, 90))

    # Preenchimento AA
    gfxdraw.filled_circle(screen, cx, cy, r_fill, fill_color)
    gfxdraw.aacircle(screen, cx, cy, r_fill, fill_color)

    # Borda AA com 2 camadas para ficar nítida
    for dr in range(0, 2):
        gfxdraw.aacircle(screen, cx, cy, r_border - dr, border_color)

    # Texto MAIÚSCULO no centro
    label = state_id.upper()
    text = marker_font.render(label, True, PRIMARY_DARK)
    screen.blit(text, text.get_rect(center=(cx, cy)))

# =========================
# Desenho da cena
# =========================
def draw_scene(boat_passengers, do_flip=True):
    screen.fill(WHITE)

    # Faixa do diagrama
    pygame.draw.rect(screen, (240, 240, 240), (0, 0, WIDTH, 300))
    pygame.draw.line(screen, BLACK, (0, 300), (WIDTH, 300), 2)
    screen.blit(diagram_img, DIAGRAM_POS)

    # Marcador do estado atual
    draw_state_marker(estado_atual)

    # desenha o background
    screen.blit(rio_img, (0, 300))
    k = 0
    # Objetos nas margens
    for side_list, x_start in [(left_bank, 50), (right_bank, WIDTH - 200)]:
        for i, obj in enumerate(side_list):
            y = MARGIN_Y_START + i * MARGIN_SPACING 

            if obj != "F" and k > 0:
                y += k
            if obj == "F":
                y += FARMER_MARGIN_Y_OFFSET
                k = FARMER_SPACING
            screen.blit(sprites[obj], (x_start, y))

    # Barco
    screen.blit(boat_img, (boat_x, boat_y))

    # Passageiros no barco
    for i, p in enumerate(boat_passengers):
        x = boat_x + PASSENGER_BOAT_X_OFFSET + i * PASSENGER_BOAT_X_SPACING
        y = boat_y + (FARMER_BOAT_Y if p == "F" else NON_FARMER_BOAT_Y)
        screen.blit(sprites[p], (x, y))

    # estado atual do autômato
    hud_text = font.render(f"Estado: {estado_atual.upper()}", True, BLACK)
    screen.blit(hud_text, (20, 260))

    if do_flip:
        pygame.display.flip()

# =========================
# Barra de entrada não-bloqueante
# =========================
def draw_input_bar(current_text, info_msg=""):
    agora = pygame.time.get_ticks()  # n mecher 

    panel_w = 800
    panel_h = 58
    panel_x = (WIDTH - panel_w) // 2
    panel_y = 340
    padding = 20

    # painel translúcido
    panel_surface = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel_surface.fill(GRAY_PANEL)
    screen.blit(panel_surface, (panel_x, panel_y))

    # prompt + conteúdo
    prompt = "Insira a sequência: "
    content = (prompt + current_text.upper().replace(" ", ""))
    max_w = panel_w - 2 * padding
    while font.size(content)[0] > max_w and len(content) > len(prompt):
        content = prompt + content[len(prompt) + 1:]
    text_surf = font.render(content, True, BLACK)
    screen.blit(text_surf, (panel_x + padding, panel_y + 8))

    # mensagem/ajuda
    hint = info_msg or "F = Fazend. L= Lobo C= Cabra A= Alface  •  Enter executa  •  Backspace apaga  •  Esc limpa"
    while small_font.size(hint)[0] > max_w and len(hint) > 3:
        hint = hint[:-4] + "..."
    hint_surf = small_font.render(hint, True, GRAY_TEXT)
    screen.blit(hint_surf, (panel_x + padding, panel_y + 34))

    # Efeito Game Over com fade + flash
    if complete:

        if last_status !="ok":
            ciclo = 2000  
            fase = (agora % ciclo) / (ciclo / 2)
            if fase > 1:
                fase = 2 - fase
            alpha = int(fase * 255)

        # Flash vermelho no fundo
            if last_status == "erro":
                flash_alpha = int(fase * 120)
                flash_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                flash_surface.fill((255, 0, 0, flash_alpha))
                screen.blit(flash_surface, (0, 0))

        # Fade da imagem
            game_over_temp = gameOver_img.copy()
            game_over_temp.set_alpha(alpha)
            screen.blit(game_over_temp, (433, 431))

        else:
            screen.blit(completed_img,(500,431))

# =========================
# Animação do barco
# =========================
def animate_boat(destination, passenger):
    global boat_x, boat_side
    step = 3 if destination == "right" else -3 # Ajuste aqui a velocidade por frame aqui.
    target_x = 850 if destination == "right" else 350 # ajuste dos limites do barco durante a travessia.

    boat_passengers = ["F"]
    if passenger != "F":
        boat_passengers.append(passenger)

    while (step > 0 and boat_x < target_x) or (step < 0 and boat_x > target_x):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        boat_x += step
        draw_scene(boat_passengers)
        pygame.time.delay(16) # tá setado para 60fps use fps para ms para calcular.

    boat_side = destination
   
    pygame.time.delay(200) # aqui define o delay para esvaziar o barco
    draw_scene([], do_flip=True) # Aqui desenha o barco vazio 

    pygame.time.delay(200) # Aqui vocês ajustam o delay de aparecer os personagens na margem de destino

# =========================
# Parser de símbolos (FC, FL, FA, F_)
# =========================
def parse_symbols(seq: str):
    s = seq.upper().replace(" ", "")
    symbols = []
    i = 0
    while i < len(s):
        if s[i] != "F":
            raise ValueError("Cada viagem deve começar com 'F'.")
        if i + 1 < len(s) and s[i + 1] in ("C", "L", "A"):
            symbols.append("F" + s[i + 1]); i += 2
        elif i + 1 < len(s) and s[i + 1] == "_":
            symbols.append("F_"); i += 2
        else:
            symbols.append("F_"); i += 1
    return symbols


# =========================
# simula o movimento para detectar resultado da ação invalida.
# =========================
def verificar_perigo(margem: set[str]) -> str | None:
    if "F" in margem:
        return None
    if {"L", "C", "A"}.issubset(margem):
        return "A cabra devorou a alface e o lobo a cabra."
    if {"L", "C"}.issubset(margem):
        return "O lobo devorou a cabra!"
    if {"C", "A"}.issubset(margem):
        return "A cabra devorou a alface!"
    return None


def simular_movimento_sombra(esq: set[str], dir: set[str], movimento: str) -> tuple[set[str], set[str]]:
    # Copias para não afetar o estado real
    l = set(esq)
    r = set(dir)

    # Define origem/destino pelo fazendeiro
    origem, destino = (l, r) if "F" in l else (r, l)

    # Passageiro(s): quaisquer letras além de 'F' (ex.: "FC", "FL", "F")
    passageiros = [ch for ch in movimento if ch in ("L", "C", "A")]

    # Embarca e atravessa (sombra)
    origem.discard("F")
    for p in passageiros:
        origem.discard(p)
    destino.add("F")
    for p in passageiros:
        destino.add(p)

    # Retorna novo estado simulado
    if origem is l:
        return l, r
    else:
        return r, l


def diagnosticar_consequencia(esq: set[str], dir: set[str], movimento: str) -> str | None:
    l_new, r_new = simular_movimento_sombra(esq, dir, movimento)
    # Checa as duas margens; se ambas tiverem perigo, prioriza a mensagem "caos"
    msg_esq = verificar_perigo(l_new)
    msg_dir = verificar_perigo(r_new)

    # Se as duas geram perigo, escolha a mais forte ou a da prioridade acima
    if msg_esq and msg_dir:
        # Garante que "caos" vença se existir em alguma margem
        if "bagunça" in msg_esq:
            return msg_esq
        if "bagunça" in msg_dir:
            return msg_dir
        # Caso contrário, retorna a do lobo-comendo, se houver
        if "lobo" in msg_esq:
            return msg_esq
        if "lobo" in msg_dir:
            return msg_dir
        return msg_esq  # fallback
    return msg_esq or msg_dir

# =========================
# Execução dos movimentos conforme AFD
# =========================
def execute_moves(moves_str):
    global left_bank, right_bank, boat_side, boat_x, estado_atual, complete
    complete= False

    # reset estado visual e do autômato
    left_bank = ["F", "C", "L", "A"]
    right_bank = []
    boat_side = "left"
    boat_x = 250
    estado_atual = ESTADO_INICIAL

    try:
        symbols = parse_symbols(moves_str)
    except ValueError as e:
        return ("erro", f"Entrada inválida: {e}")

    for symbol in symbols:
        passenger = "F" if symbol == "F_" else symbol[1]

        transicoes = estados.get(estado_atual, {})
        if symbol not in transicoes:
            motivo_hist = diagnosticar_consequencia(left_bank, right_bank, symbol)
            if motivo_hist:
                return ("erro", f"Movimento '{symbol}' inválido no estado:{estado_atual.upper()}. {motivo_hist}")
            return ("erro", f"Movimento '{symbol}' não permitido a partir de {estado_atual}.")
        proximo_estado = transicoes[symbol]

        if boat_side == "left":
            source, dest, destination_side = left_bank, right_bank, "right"
        else:
            source, dest, destination_side = right_bank, left_bank, "left"

        if "F" not in source:
            return ("erro", "Erro de estado: o fazendeiro não está na margem do barco.")
        if passenger != "F" and passenger not in source:
            return ("erro", f"Movimento inválido: {names.get(passenger, passenger)} não está na mesma margem do fazendeiro.")


        # Atualiza estado atual para próxima iteração
        estado_atual = proximo_estado
        boat_side = destination_side

        # Embarcar
        source.remove("F")
        if passenger != "F":
            source.remove(passenger)

        # Animar travessia
        animate_boat(destination_side, passenger)

        # Desembarcar
        dest.append("F")
        if passenger != "F":
            dest.append(passenger)

       
        # Atualiza estado do autômato e redesenha
        estado_atual = proximo_estado
        draw_scene([])
        pygame.time.delay(500) # Aqui vocês podem ajustar a espera pro barco voltar após renderizar os passageiros desembarcados.

    if estado_atual in ESTADO_FINAL:
        
        return ("ok", f" Sucesso! Estado final alcançado. Digite uma nova sequência acima.")
    else:
        return ("info", f" Sequência anterior concluída. Estado atual: {estado_atual} (não final). Insira uma nova acima.")

# =========================
# Loop principal
# =========================
clock = pygame.time.Clock()
current_input = ""   # texto digitado
last_msg = ""        # mensagem de status após executar

# Desenha assim que abre
draw_scene([], do_flip=False)
draw_input_bar(current_input, last_msg)
pygame.display.flip()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if current_input.strip():
                    status, last_msg = execute_moves(current_input)
                    complete =True
                    current_input = ""  # pronto para nova sequência
                    last_status = status
                else:
                    last_msg = "Digite uma sequência antes de pressionar Enter."
            elif event.key == pygame.K_BACKSPACE:
                current_input = current_input[:-1]
            elif event.key == pygame.K_ESCAPE:
                current_input = ""
                last_msg = ""
            else:
                ch = event.unicode.upper()
                if ch in ("F", "C", "L", "A", "_"):  # aceita apenas os símbolos permitidos
                    current_input += ch
                # ignora outros caracteres

    draw_scene([], do_flip=False)
    draw_input_bar(current_input, last_msg)
    pygame.display.flip()
    clock.tick(60)
