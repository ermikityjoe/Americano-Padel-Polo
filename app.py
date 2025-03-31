import streamlit as st
import pandas as pd
import random
from itertools import combinations, cycle
import math

# --- Constantes ---
TOURNAMENT_TYPE_AMERICANO = "Americano (Parejas Rotativas)"
TOURNAMENT_TYPE_PAREJAS_FIJAS = "Parejas Fijas (Round Robin)"
PAIRING_METHOD_RANDOM = "Sorteo Aleatorio"
PAIRING_METHOD_MANUAL = "Selección Manual"

# --- Funciones de Generación de Fixture ---

def generate_round_robin_pairs_fixture(pairs, num_courts):
    """
    Genera un fixture Round Robin para parejas fijas, asegurando llenar
    las rondas según el número de pistas disponibles de forma más robusta.
    """
    num_pairs = len(pairs)
    if num_pairs < 2:
        st.warning("Se necesitan al menos 2 parejas para generar un fixture.")
        return {"rounds": []}

    fixture = {"rounds": []}
    all_matches_list = list(combinations(pairs, 2))
    if not all_matches_list:
        st.info("No hay partidos posibles entre las parejas dadas.")
        return {"rounds": []}

    # Opcional: Barajar la lista completa de partidos al inicio
    # random.shuffle(all_matches_list)

    matches_per_round_limit = min(num_courts, num_pairs // 2) if num_pairs > 1 else 0
    if matches_per_round_limit <= 0:
        st.warning(f"No se pueden jugar partidos con {num_courts} pistas y {num_pairs} parejas (0 partidos por ronda).")
        return {"rounds": []}

    remaining_matches = set(all_matches_list) # Usar set para eficiencia al quitar
    round_num_actual = 0
    pair_names_global = {f"{p[0]}/{p[1]}" for p in pairs}

    while remaining_matches:
        round_num_actual += 1
        current_round_matches_data = []
        pairs_playing_in_this_round_names = set()
        matches_added_to_this_round = set() # Matches (tuples) añadidos a esta ronda

        # Iterar sobre una copia ordenada o barajada de los partidos restantes
        # Usar una lista ordenada puede hacer el llenado más predecible
        potential_matches_for_round = sorted(list(remaining_matches))
        # O barajar para más aleatoriedad en el orden de rondas:
        # potential_matches_for_round = list(remaining_matches)
        # random.shuffle(potential_matches_for_round)


        for match_tuple in potential_matches_for_round:
            # Si la ronda ya está llena, parar de buscar para esta ronda
            if len(current_round_matches_data) >= matches_per_round_limit:
                break

            pair1_tuple, pair2_tuple = match_tuple
            # Validar formato de tupla por si acaso
            if not (isinstance(pair1_tuple, tuple) and len(pair1_tuple) == 2 and
                    isinstance(pair2_tuple, tuple) and len(pair2_tuple) == 2):
                 st.warning(f"Ignorando formato de partido inválido: {match_tuple}")
                 continue

            pair1_name = f"{pair1_tuple[0]}/{pair1_tuple[1]}"
            pair2_name = f"{pair2_tuple[0]}/{pair2_tuple[1]}"

            # Comprobar si alguna de las parejas ya está jugando en esta ronda
            if pair1_name not in pairs_playing_in_this_round_names and \
               pair2_name not in pairs_playing_in_this_round_names:
                # Añadir el partido a la ronda actual
                current_round_matches_data.append({
                    "pair1": pair1_tuple,
                    "pair2": pair2_tuple,
                    "score1": None,
                    "score2": None
                    # Court se asigna después
                })
                # Marcar parejas como ocupadas en esta ronda
                pairs_playing_in_this_round_names.add(pair1_name)
                pairs_playing_in_this_round_names.add(pair2_name)
                # Marcar este partido para eliminarlo del pool global después
                matches_added_to_this_round.add(match_tuple)

        # Asignar número de pista a los partidos encontrados para la ronda
        for court_idx, match_data in enumerate(current_round_matches_data):
            match_data["court"] = court_idx + 1

        # Calcular parejas que descansan
        resting_pairs_names = list(pair_names_global - pairs_playing_in_this_round_names)

        # Añadir la ronda al fixture si se encontraron partidos
        if current_round_matches_data:
            fixture["rounds"].append({
                "round_num": round_num_actual,
                "matches": current_round_matches_data,
                "resting": resting_pairs_names
            })
            # Eliminar los partidos añadidos del pool global
            remaining_matches -= matches_added_to_this_round
        elif remaining_matches:
             # Si no se añadió nada pero quedan partidos, indica un problema
             st.warning(f"Ronda {round_num_actual} no pudo llenarse. Quedan {len(remaining_matches)} partidos. Puede ser un problema de lógica o configuración.")
             # Intentar mostrar los partidos restantes para depuración
             # st.write("Partidos restantes:", remaining_matches)
             break # Evitar bucle infinito

    # Comprobación final (opcional)
    if remaining_matches:
        st.warning(f"Generación de fixture finalizada, pero {len(remaining_matches)} partidos quedaron sin asignar.")

    # Asegurar que se devuelva algo, incluso si las rondas están vacías
    if "rounds" not in fixture:
        fixture["rounds"] = []

    return fixture


# --- Función generate_americano_fixture sin cambios ---
def generate_americano_fixture(players, num_courts):
    """Genera un fixture Americano SIMPLIFICADO (rotación aleatoria)."""
    num_players = len(players)
    if num_players < 4:
        st.warning("Se necesitan al menos 4 jugadores para el formato Americano.")
        return {"rounds": []}

    num_rounds = max(1, num_players - 1) # Intentar N-1 rondas

    fixture = {"rounds": []}
    all_players = list(players)
    played_pairs_history = set()

    for _ in range(num_rounds):
        round_matches = []
        players_this_round = list(all_players)
        random.shuffle(players_this_round)

        max_matches_in_round = min(num_courts, len(players_this_round) // 4)
        if max_matches_in_round <= 0: continue

        possible_pairs = list(combinations(players_this_round, 2))
        random.shuffle(possible_pairs)

        potential_pairs = []
        players_already_paired = set()
        for p1, p2 in possible_pairs:
            pair_tuple = tuple(sorted((p1, p2)))
            priority = 1 if pair_tuple not in played_pairs_history else 0
            if p1 not in players_already_paired and p2 not in players_already_paired:
                 potential_pairs.append((priority, pair_tuple))

        potential_pairs.sort(key=lambda x: x[0], reverse=True)

        final_round_pairs = []
        players_in_final_pairs = set()
        for _, pair_tuple in potential_pairs:
            p1, p2 = pair_tuple
            if p1 not in players_in_final_pairs and p2 not in players_in_final_pairs:
                final_round_pairs.append(pair_tuple)
                players_in_final_pairs.add(p1)
                players_in_final_pairs.add(p2)

        match_count = 0
        assigned_players_in_match = set()
        available_pairs_for_match = list(final_round_pairs)
        random.shuffle(available_pairs_for_match)

        while match_count < max_matches_in_round and len(available_pairs_for_match) >= 2:
            pair1 = available_pairs_for_match.pop(0)
            found_opponent = False
            for i in range(len(available_pairs_for_match)):
                pair2 = available_pairs_for_match[i]
                if not set(pair1) & set(pair2):
                    available_pairs_for_match.pop(i)
                    played_pairs_history.add(tuple(sorted(pair1)))
                    played_pairs_history.add(tuple(sorted(pair2)))
                    round_matches.append({
                        "court": match_count + 1, "pair1": pair1, "pair2": pair2,
                        "score1": None, "score2": None
                    })
                    assigned_players_in_match.update(pair1)
                    assigned_players_in_match.update(pair2)
                    match_count += 1
                    found_opponent = True
                    break

        players_resting = [p for p in all_players if p not in assigned_players_in_match]

        if round_matches:
            fixture["rounds"].append({
                "round_num": len(fixture["rounds"]) + 1,
                "matches": round_matches, "resting": players_resting
            })

    if "rounds" not in fixture: fixture["rounds"] = []
    elif not fixture["rounds"] and num_players >= 4:
         st.warning("No se pudieron generar rondas Americano. Revisa jugadores/pistas.")

    return fixture

# --- Funciones de Cálculo de Clasificación (sin cambios, pero con validaciones añadidas) ---
def calculate_standings_americano(players, fixture_data):
    """Calcula la clasificación individual para torneo Americano."""
    standings = {p: {"JG": 0, "JR": 0, "DG": 0, "PG": 0, "PP": 0, "PE": 0, "PJ": 0} for p in players}
    if not fixture_data or 'rounds' not in fixture_data: return standings, []

    for p in players: standings[p] = {"JG": 0, "JR": 0, "DG": 0, "PG": 0, "PP": 0, "PE": 0, "PJ": 0}
    processed_match_ids_for_stats = set()

    for round_idx, round_data in enumerate(fixture_data['rounds']):
        for match_idx, match in enumerate(round_data.get('matches', [])):
            match_id = f"r{round_data.get('round_num', '?')}_m{match_idx}"

            score1 = st.session_state.get(f"score1_{match_id}")
            score2 = st.session_state.get(f"score2_{match_id}")

            s1 = int(score1) if score1 is not None else None
            s2 = int(score2) if score2 is not None else None

            if s1 is not None and s2 is not None:
                 if 'pair1' not in match or 'pair2' not in match or \
                    not isinstance(match['pair1'], (tuple, list)) or len(match['pair1']) != 2 or \
                    not isinstance(match['pair2'], (tuple, list)) or len(match['pair2']) != 2:
                      st.warning(f"Skipping score calculation for invalid match structure in round {round_data.get('round_num', '?')}")
                      continue
                 pair1, pair2 = match['pair1'], match['pair2']
                 # Asegurar que los jugadores existen en standings
                 if not all(p in standings for p in pair1) or not all(p in standings for p in pair2):
                      st.warning(f"Skipping score calculation due to unknown players in round {round_data.get('round_num', '?')}")
                      continue

                 for p in pair1: standings[p]['JG'] += s1; standings[p]['JR'] += s2
                 for p in pair2: standings[p]['JG'] += s2; standings[p]['JR'] += s1

                 if match_id not in processed_match_ids_for_stats:
                    if s1 > s2:   res1, res2 = 'PG', 'PP'
                    elif s2 > s1: res1, res2 = 'PP', 'PG'
                    else:         res1, res2 = 'PE', 'PE'
                    for p in pair1: standings[p]['PJ'] += 1; standings[p][res1] += 1
                    for p in pair2: standings[p]['PJ'] += 1; standings[p][res2] += 1
                    processed_match_ids_for_stats.add(match_id)

    for p in players: standings[p]['DG'] = standings[p]['JG'] - standings[p]['JR']
    sorted_players = sorted(players, key=lambda p: (standings[p]['PG'], standings[p]['DG'], standings[p]['JG']), reverse=True)
    return standings, sorted_players

def calculate_standings_pairs(pairs, fixture_data):
    """Calcula la clasificación por parejas para torneo Round Robin."""
    pair_names = {f"{p[0]}/{p[1]}" for p in pairs}
    standings = {name: {"JG": 0, "JR": 0, "DG": 0, "PG": 0, "PP": 0, "PE": 0, "PJ": 0} for name in pair_names}
    if not fixture_data or 'rounds' not in fixture_data: return standings, []

    for name in pair_names: standings[name] = {"JG": 0, "JR": 0, "DG": 0, "PG": 0, "PP": 0, "PE": 0, "PJ": 0}
    processed_match_ids_for_stats = set()

    for round_idx, round_data in enumerate(fixture_data['rounds']):
        for match_idx, match in enumerate(round_data.get('matches', [])):
            match_id = f"r{round_data.get('round_num','?')}_m{match_idx}"

            score1 = st.session_state.get(f"score1_{match_id}")
            score2 = st.session_state.get(f"score2_{match_id}")

            s1 = int(score1) if score1 is not None else None
            s2 = int(score2) if score2 is not None else None

            if s1 is not None and s2 is not None:
                if 'pair1' not in match or 'pair2' not in match or \
                   not isinstance(match['pair1'], (tuple, list)) or len(match['pair1']) != 2 or \
                   not isinstance(match['pair2'], (tuple, list)) or len(match['pair2']) != 2:
                     st.warning(f"Skipping score calculation for invalid match structure in round {round_data.get('round_num', '?')}")
                     continue
                pair1_tuple, pair2_tuple = match['pair1'], match['pair2']
                pair1_name = f"{pair1_tuple[0]}/{pair1_tuple[1]}"
                pair2_name = f"{pair2_tuple[0]}/{pair2_tuple[1]}"
                if pair1_name not in standings or pair2_name not in standings:
                     st.warning(f"Skipping score calculation for unknown pairs: {pair1_name}, {pair2_name}")
                     continue

                standings[pair1_name]['JG'] += s1; standings[pair1_name]['JR'] += s2
                standings[pair2_name]['JG'] += s2; standings[pair2_name]['JR'] += s1

                if match_id not in processed_match_ids_for_stats:
                    standings[pair1_name]['PJ'] += 1
                    standings[pair2_name]['PJ'] += 1
                    if s1 > s2:   standings[pair1_name]['PG'] += 1; standings[pair2_name]['PP'] += 1
                    elif s2 > s1: standings[pair1_name]['PP'] += 1; standings[pair2_name]['PG'] += 1
                    else:         standings[pair1_name]['PE'] += 1; standings[pair2_name]['PE'] += 1
                    processed_match_ids_for_stats.add(match_id)

    for name in pair_names: standings[name]['DG'] = standings[name]['JG'] - standings[name]['JR']
    sorted_pair_names = sorted(pair_names, key=lambda name: (standings[name]['PG'], standings[name]['DG'], standings[name]['JG']), reverse=True)
    return standings, sorted_pair_names

# --- Funciones de Formateo y UI Auxiliares (sin cambios) ---
def generate_standings_text(standings_data, sorted_keys, tournament_name, is_pairs=False):
    """Genera texto formateado para clasificación (individual o parejas)."""
    entity_label = "Pareja" if is_pairs else "Jugador"
    header = f"--- CLASIFICACIÓN: {tournament_name} ({entity_label}) ---\n"
    separator = "-" * 75 + "\n"
    col_headers = f"{'Pos':<4} {entity_label:<30} {'PJ':<4} {'PG':<4} {'PE':<4} {'PP':<4} {'JG':<6} {'JR':<6} {'DG':<6}\n"

    lines = [header, separator, col_headers, separator]

    for i, key in enumerate(sorted_keys):
        stats = standings_data.get(key, {})
        lines.append(
            f"{i+1:<4} {key:<30} {stats.get('PJ', 0):<4} {stats.get('PG', 0):<4} {stats.get('PE', 0):<4} {stats.get('PP', 0):<4} {stats.get('JG', 0):<6} {stats.get('JR', 0):<6} {stats.get('DG', 0):<6}\n"
        )

    lines.append(separator)
    return "".join(lines)

def display_player_inputs(num_players_to_show):
    """Muestra dinámicamente los campos de entrada para nombres de jugadores."""
    player_names_inputs = {}
    st.subheader("Nombres de los Jugadores")
    cols_players = st.columns(3)
    for i in range(num_players_to_show):
        default_name = st.session_state.player_inputs.get(i, f"Jugador {i+1}")
        player_name = cols_players[i % 3].text_input(
             f"Jugador {i + 1}", value=default_name, key=f"player_{i}"
        )
        player_names_inputs[i] = player_name
        st.session_state.player_inputs[i] = player_name
    return player_names_inputs

# --- Interfaz Principal de Streamlit ---

st.set_page_config(page_title="Gestor Torneos Pádel", layout="wide")
st.title("🏓 Gestor de Torneos de Pádel")

# --- Inicialización del Estado de Sesión (sin cambios) ---
if 'app_phase' not in st.session_state:
    st.session_state.app_phase = 'config_base'
    st.session_state.config = {'num_players': 8, 'num_courts': 2, 'name': "Torneo Pádel"}
    st.session_state.players = []
    st.session_state.pairs = []
    st.session_state.fixture = None
    st.session_state.tournament_type = None
    st.session_state.pairing_method = None
    st.session_state.player_inputs = {}
    st.session_state.manual_pair_selections = {}
    score_keys = [k for k in st.session_state.keys() if k.startswith('score1_') or k.startswith('score2_')]
    for k in score_keys: del st.session_state[k]

# --- FASE 0: Configuración Base (sin cambios) ---
if st.session_state.app_phase == 'config_base':
    st.header("1. Configuración Base del Torneo")
    with st.form("base_config_form"):
        conf_name = st.text_input("Nombre del Torneo", st.session_state.config.get('name', "Torneo Pádel"))
        col1, col2 = st.columns(2)
        with col1:
            conf_num_players = st.number_input("Número total de jugadores", min_value=4, step=1, value=st.session_state.config.get('num_players', 8))
        with col2:
            conf_num_courts = st.number_input("Número de pistas disponibles", min_value=1, step=1, value=st.session_state.config.get('num_courts', 2))
        submitted_base_config = st.form_submit_button("Confirmar Configuración Base")
        if submitted_base_config:
            if conf_num_players < 4: st.error("Se necesitan al menos 4 jugadores.")
            else:
                 st.session_state.config['name'] = conf_name
                 st.session_state.config['num_players'] = conf_num_players
                 st.session_state.config['num_courts'] = conf_num_courts
                 st.session_state.app_phase = 'config_players'
                 st.rerun()

# --- FASE 1: Ingreso de Nombres de Jugadores (sin cambios) ---
elif st.session_state.app_phase == 'config_players':
    st.header("2. Ingreso de Jugadores")
    st.info(f"**Torneo:** {st.session_state.config.get('name')} | **Jugadores:** {st.session_state.config.get('num_players')} | **Pistas:** {st.session_state.config.get('num_courts')}")
    with st.form("player_entry_form"):
        num_players_to_enter = st.session_state.config.get('num_players', 0)
        display_player_inputs(num_players_to_enter)
        submitted_players = st.form_submit_button("Confirmar Jugadores y Continuar")
        if submitted_players:
            final_players = [st.session_state.player_inputs.get(i, "").strip() for i in range(num_players_to_enter)]
            final_players = [p for p in final_players if p]
            valid = True
            if len(final_players) != num_players_to_enter:
                st.error(f"Error: Se esperaban {num_players_to_enter} nombres, pero se encontraron {len(final_players)} no vacíos.")
                valid = False
            elif len(set(final_players)) != len(final_players):
                 st.error("Error: Hay nombres duplicados.")
                 valid = False
            if valid:
                st.session_state.players = final_players
                st.session_state.app_phase = 'config_pairing'
                st.rerun()
    st.divider()
    if st.button("⬅️ Volver a Configuración Base"):
         st.session_state.app_phase = 'config_base'
         st.rerun()

# --- FASE 2: Configuración del Tipo de Torneo y Parejas (Lógica de Sorteo Aleatorio ajustada) ---
elif st.session_state.app_phase == 'config_pairing':
    st.header("3. Formato del Torneo y Parejas")
    st.info(f"**Torneo:** {st.session_state.config.get('name')} | **Jugadores ({len(st.session_state.players)}):** {', '.join(st.session_state.players)} | **Pistas:** {st.session_state.config.get('num_courts')}")

    tournament_type = st.radio("Selecciona el formato:", (TOURNAMENT_TYPE_AMERICANO, TOURNAMENT_TYPE_PAREJAS_FIJAS), key='tournament_type_radio', horizontal=True, index=0 if st.session_state.tournament_type != TOURNAMENT_TYPE_PAREJAS_FIJAS else 1)
    st.session_state.tournament_type = tournament_type

    # --- Opciones Parejas Fijas ---
    if tournament_type == TOURNAMENT_TYPE_PAREJAS_FIJAS:
        if len(st.session_state.players) % 2 != 0:
            st.error(f"Error: Se requiere un número par de jugadores ({len(st.session_state.players)} ingresados) para Parejas Fijas.")
            if st.button("⬅️ Volver a Editar Jugadores"): st.session_state.app_phase = 'config_players'; st.rerun()
            st.stop()

        st.subheader("Configuración de Parejas")
        pairing_method = st.radio("¿Formar parejas?", (PAIRING_METHOD_RANDOM, PAIRING_METHOD_MANUAL), key='pairing_method_radio', horizontal=True, index=0 if st.session_state.pairing_method != PAIRING_METHOD_MANUAL else 1)
        st.session_state.pairing_method = pairing_method

        # --- Selección Manual (sin cambios respecto a versión anterior, asumida funcional) ---
        if pairing_method == PAIRING_METHOD_MANUAL:
            st.markdown("**Asigna los jugadores a las parejas:**")
            num_pairs_needed = len(st.session_state.players) // 2
            potential_partners = [''] + list(st.session_state.players)
            cols_pairing = st.columns(2)
            with st.form("manual_pairs_form"):
                 all_selections_valid_form = True
                 current_form_pairs = {}
                 current_form_assigned = set()
                 for i in range(num_pairs_needed):
                     pair_key_base = f"manual_pair_{i}"
                     sel1 = st.session_state.manual_pair_selections.get(f"{pair_key_base}_p1", '')
                     sel2 = st.session_state.manual_pair_selections.get(f"{pair_key_base}_p2", '')
                     options1 = [''] + [p for p in potential_partners[1:] if p not in current_form_assigned or p == sel1]
                     try: index1 = options1.index(sel1)
                     except ValueError: index1 = 0
                     new_sel1 = cols_pairing[0].selectbox(f"Pareja {i+1} - J1", options=options1, key=f"{pair_key_base}_p1_sel", index=index1)
                     st.session_state.manual_pair_selections[f"{pair_key_base}_p1"] = new_sel1
                     temp_assigned_for_p2 = current_form_assigned.copy()
                     if new_sel1: temp_assigned_for_p2.add(new_sel1)
                     options2 = [''] + [p for p in potential_partners[1:] if p not in temp_assigned_for_p2 or p == sel2]
                     try: index2 = options2.index(sel2)
                     except ValueError: index2 = 0
                     new_sel2 = cols_pairing[1].selectbox(f"Pareja {i+1} - J2", options=options2, key=f"{pair_key_base}_p2_sel", index=index2)
                     st.session_state.manual_pair_selections[f"{pair_key_base}_p2"] = new_sel2
                     if new_sel1 and new_sel2:
                          if new_sel1 == new_sel2: st.warning(f"Pareja {i+1}: Jugadores deben ser diferentes."); all_selections_valid_form = False
                          else: current_form_pairs[i] = tuple(sorted((new_sel1, new_sel2))); current_form_assigned.add(new_sel1); current_form_assigned.add(new_sel2)
                     elif new_sel1 or new_sel2: st.warning(f"Pareja {i+1}: Ambos jugadores deben ser seleccionados."); all_selections_valid_form = False
                 confirm_manual_pairs = st.form_submit_button("Confirmar Parejas Manuales y Generar Fixture")
                 if confirm_manual_pairs:
                    final_manual_pairs = list(current_form_pairs.values())
                    final_assigned_players = set(p for pair in final_manual_pairs for p in pair)
                    if not all_selections_valid_form: st.error("Corrige errores en la selección.")
                    elif len(final_manual_pairs) != num_pairs_needed: st.error(f"Completa las {num_pairs_needed} parejas.")
                    elif len(final_assigned_players) != len(st.session_state.players): st.error(f"No se asignaron todos los jugadores ({len(final_assigned_players)}/{len(st.session_state.players)}).")
                    elif len(set(final_manual_pairs)) != len(final_manual_pairs): st.error("Parejas duplicadas detectadas.")
                    else:
                         st.session_state.pairs = final_manual_pairs
                         st.session_state.fixture = generate_round_robin_pairs_fixture(st.session_state.pairs, st.session_state.config['num_courts'])
                         if st.session_state.fixture and st.session_state.fixture.get('rounds'):
                              st.session_state.app_phase = 'viewing'; st.success("Parejas asignadas y fixture generado."); st.rerun()
                         else: st.error("Error al generar fixture Round Robin.")

        # --- Sorteo Aleatorio (Flujo Corregido) ---
        elif pairing_method == PAIRING_METHOD_RANDOM:
            st.markdown("**Las parejas se sortearán aleatoriamente.**")
            if st.button("Sortear Parejas y Generar Fixture"):
                players_to_pair = list(st.session_state.players); random.shuffle(players_to_pair)
                random_pairs = [tuple(sorted((players_to_pair[i], players_to_pair[i+1]))) for i in range(0, len(players_to_pair), 2)]
                if len(random_pairs) == len(st.session_state.players) // 2:
                     st.session_state.pairs = random_pairs
                     st.success("Parejas Sorteadas:")
                     for p1, p2 in st.session_state.pairs: st.write(f"- {p1} / {p2}")
                     # Generar Fixture INMEDIATAMENTE después de sortear
                     st.session_state.fixture = generate_round_robin_pairs_fixture(st.session_state.pairs, st.session_state.config['num_courts'])
                     # Validar y pasar a visualización
                     if st.session_state.fixture and st.session_state.fixture.get('rounds'):
                          st.session_state.app_phase = 'viewing'
                          st.success("Fixture Round Robin generado.")
                          # Usar rerun para forzar la actualización a la fase de visualización
                          # Puede que los mensajes parpadeen, es un comportamiento de Streamlit
                          st.rerun()
                     else: st.error("Error al generar fixture Round Robin después del sorteo.")
                else: st.error("Error durante el sorteo aleatorio.")

    # --- Opciones Americano (sin cambios) ---
    elif tournament_type == TOURNAMENT_TYPE_AMERICANO:
        st.markdown("**Se generarán parejas rotativas aleatoriamente.**")
        if st.button("Generar Fixture Americano"):
            st.session_state.fixture = generate_americano_fixture(st.session_state.players, st.session_state.config['num_courts'])
            if st.session_state.fixture and st.session_state.fixture.get('rounds'):
                 st.session_state.app_phase = 'viewing'; st.success("Fixture Americano generado."); st.rerun()
            else: st.error("Error al generar fixture Americano.")

    # Botón Volver
    st.divider()
    if st.button("⬅️ Volver a Ingresar Jugadores"):
         st.session_state.app_phase = 'config_players'
         st.session_state.tournament_type = None; st.session_state.pairing_method = None
         st.session_state.pairs = []; st.session_state.manual_pair_selections = {}
         st.rerun()

# --- FASE 3: Visualización del Torneo (sin cambios significativos) ---
elif st.session_state.app_phase == 'viewing':
    st.header(f"🏆 Torneo: {st.session_state.config.get('name', 'Sin Nombre')}")
    tournament_mode_display = st.session_state.get('tournament_type', 'Desconocido')
    st.subheader(f"Formato: {tournament_mode_display}")

    # Mostrar detalles
    if tournament_mode_display == TOURNAMENT_TYPE_PAREJAS_FIJAS:
        st.write("**Parejas:**")
        num_pairs_display = len(st.session_state.get('pairs', []))
        pair_cols = st.columns(min(3, num_pairs_display) if num_pairs_display > 0 else 1)
        for i, pair_tuple in enumerate(st.session_state.get('pairs', [])):
             p1, p2 = pair_tuple; pair_cols[i % len(pair_cols)].write(f"- {p1} / {p2}")
        st.caption(f"{len(st.session_state.players)} jugadores | {st.session_state.config.get('num_courts', '?')} pistas")
    elif tournament_mode_display == TOURNAMENT_TYPE_AMERICANO:
         st.caption(f"{len(st.session_state.players)} jugadores | {st.session_state.config.get('num_courts', '?')} pistas | Parejas rotativas")

    # Calcular standings
    standings_data, sorted_keys = {}, []
    is_classification_pairs = (st.session_state.tournament_type == TOURNAMENT_TYPE_PAREJAS_FIJAS)
    if st.session_state.fixture and 'rounds' in st.session_state.fixture:
        if is_classification_pairs:
            if 'pairs' in st.session_state and st.session_state.pairs: standings_data, sorted_keys = calculate_standings_pairs(st.session_state.pairs, st.session_state.fixture)
            else: st.error("Error: No se encontraron las parejas para calcular la clasificación.")
        else:
            if 'players' in st.session_state and st.session_state.players: standings_data, sorted_keys = calculate_standings_americano(st.session_state.players, st.session_state.fixture)
            else: st.error("Error: No se encontraron los jugadores para calcular la clasificación.")
    else:
        st.error("Error crítico: No se encontró un fixture válido para visualizar."); st.stop()

    # Pestañas Rondas / Clasificación
    tab1, tab2 = st.tabs(["📝 Rondas y Resultados", "📊 Clasificación"])
    with tab1:
        st.subheader("Partidos por Ronda")
        if not st.session_state.fixture or not st.session_state.fixture.get('rounds'): st.warning("No hay rondas generadas.")
        else:
            round_tabs = st.tabs([f"Ronda {r.get('round_num', '?')}" for r in st.session_state.fixture['rounds']])
            for i, round_data in enumerate(st.session_state.fixture['rounds']):
                with round_tabs[i]:
                    st.markdown(f"**Ronda {round_data.get('round_num', '?')}**")
                    if round_data.get('resting'):
                         resting_label = "Parejas descansan" if is_classification_pairs else "Jugadores descansan"
                         st.caption(f"{resting_label}: {', '.join(round_data['resting'])}")
                    if not round_data.get('matches'): st.info("No hay partidos en esta ronda."); continue
                    for match_idx, match in enumerate(round_data.get('matches', [])):
                        if 'pair1' not in match or 'pair2' not in match: st.warning(f"Saltando partido inválido"); continue
                        p1_tuple, p2_tuple = match['pair1'], match['pair2']
                        if not (isinstance(p1_tuple, (list, tuple)) and len(p1_tuple)==2 and isinstance(p2_tuple, (list, tuple)) and len(p2_tuple)==2): st.warning(f"Saltando formato inválido"); continue
                        p1_name, p2_name = f"{p1_tuple[0]}/{p1_tuple[1]}", f"{p2_tuple[0]}/{p2_tuple[1]}"
                        col_match, col_score1, col_score2 = st.columns([3, 1, 1])
                        with col_match: st.markdown(f"**Pista {match.get('court', '?')}**: {p1_name} **vs** {p2_name}")
                        match_id = f"r{round_data.get('round_num', '?')}_m{match_idx}"; score1_key, score2_key = f"score1_{match_id}", f"score2_{match_id}"
                        with col_score1: st.number_input(f"G {p1_name}", min_value=0, step=1, value=st.session_state.get(score1_key), key=score1_key, format="%d", label_visibility="collapsed")
                        with col_score2: st.number_input(f"G {p2_name}", min_value=0, step=1, value=st.session_state.get(score2_key), key=score2_key, format="%d", label_visibility="collapsed")
                        st.divider()
    with tab2:
        st.subheader(f"Tabla de Clasificación ({'Parejas' if is_classification_pairs else 'Individual'})")
        if not standings_data or not sorted_keys: st.info("Aún no hay resultados.")
        else:
             standings_list = []
             entity_label = "Pareja" if is_classification_pairs else "Jugador"
             for pos, key in enumerate(sorted_keys):
                 stats = standings_data.get(key, {}); row = {"Pos": pos + 1, entity_label: key}
                 row.update({'PJ': stats.get('PJ', 0), 'PG': stats.get('PG', 0), 'PE': stats.get('PE', 0), 'PP': stats.get('PP', 0), 'JG': stats.get('JG', 0), 'JR': stats.get('JR', 0), 'DG': stats.get('DG', 0)})
                 standings_list.append(row)
             df_standings = pd.DataFrame(standings_list)
             cols_to_show = ['Pos', entity_label, 'PJ', 'PG', 'PE', 'PP', 'JG', 'JR', 'DG']
             cols_exist = [col for col in cols_to_show if col in df_standings.columns]; df_display = df_standings[cols_exist]
             if 'Pos' in df_display.columns: st.dataframe(df_display.set_index('Pos'), use_container_width=True)
             else: st.dataframe(df_display, use_container_width=True)
             st.download_button(f"📄 Descargar Clasificación ({entity_label}) (.txt)", generate_standings_text(standings_data, sorted_keys, st.session_state.config.get('name', 'Torneo'), is_classification_pairs), f"clasificacion_{st.session_state.config.get('name', 'torneo').replace(' ', '_')}_{entity_label.lower()}.txt", 'text/plain')

    # Botón Reiniciar
    st.divider()
    if st.button("⚠️ Empezar Nuevo Torneo (Borrar Todo)"):
        keys_to_delete = list(st.session_state.keys());
        for key in keys_to_delete: del st.session_state[key]
        st.rerun()