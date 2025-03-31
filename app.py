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
    """Genera un fixture Round Robin para parejas fijas."""
    num_pairs = len(pairs)
    if num_pairs < 2:
        return {"rounds": []}

    fixture = {"rounds": []}
    matches_to_play = list(combinations(pairs, 2))
    random.shuffle(matches_to_play) # Barajar para variar el orden

    # Algoritmo simple para distribuir partidos en rondas según pistas
    matches_per_round = min(num_courts, num_pairs // 2) if num_pairs > 1 else 0
    num_rounds_needed = math.ceil(len(matches_to_play) / matches_per_round) if matches_per_round > 0 else 0

    all_matches_tuples = list(matches_to_play) # Copia para trabajar
    round_num_actual = 0

    while all_matches_tuples:
        round_num_actual += 1
        round_matches_data = []
        pairs_in_this_round_check = set() # Para asegurar que una pareja no juegue dos veces en la ronda
        matches_added_this_round_indices = set() # Indices de all_matches_tuples

        # Iterar sobre los partidos restantes para llenar la ronda actual
        for idx, (pair1_tuple, pair2_tuple) in enumerate(all_matches_tuples):
            if len(round_matches_data) >= matches_per_round:
                break # Ronda llena

            pair1_name = f"{pair1_tuple[0]}/{pair1_tuple[1]}"
            pair2_name = f"{pair2_tuple[0]}/{pair2_tuple[1]}"

            # Comprobar si alguna de las parejas ya está jugando en esta ronda
            if pair1_name not in pairs_in_this_round_check and pair2_name not in pairs_in_this_round_check:
                round_matches_data.append({
                     # "court" se asignará después
                    "pair1": pair1_tuple,
                    "pair2": pair2_tuple,
                    "score1": None,
                    "score2": None
                })
                pairs_in_this_round_check.add(pair1_name)
                pairs_in_this_round_check.add(pair2_name)
                matches_added_this_round_indices.add(idx) # Marcar este índice para eliminar

        # Asignar número de pista
        for court_idx, match_data in enumerate(round_matches_data):
            match_data["court"] = court_idx + 1
            
        # Calcular parejas que descansan (si aplica)
        all_pair_names_in_fixture = {f"{p[0]}/{p[1]}" for p in pairs}
        resting_pairs_names = list(all_pair_names_in_fixture - pairs_in_this_round_check)

        if round_matches_data:
             fixture["rounds"].append({
                 "round_num": round_num_actual,
                 "matches": round_matches_data,
                 "resting": resting_pairs_names
             })

        # Eliminar partidos asignados de la lista principal (iterando inversamente por índices)
        remaining_matches_temp = []
        for idx, match in enumerate(all_matches_tuples):
             if idx not in matches_added_this_round_indices:
                 remaining_matches_temp.append(match)
        all_matches_tuples = remaining_matches_temp


    # Validar si se generaron rondas (deberían si hay partidos)
    if not fixture["rounds"] and len(pairs) >= 2:
         st.warning("No se pudieron generar rondas para el torneo de parejas.")


    return fixture


def generate_americano_fixture(players, num_courts):
    """Genera un fixture Americano SIMPLIFICADO (rotación aleatoria)."""
    num_players = len(players)
    if num_players < 4:
        return {"rounds": []}

    num_rounds = max(1, num_players - 1) # Intentar N-1 rondas

    fixture = {"rounds": []}
    all_players = list(players)
    played_pairs_history = set() # Para intentar minimizar repetición de compañeros

    for _ in range(num_rounds): # Iterar para crear el número deseado de rondas
        round_matches = []
        players_this_round = list(all_players)
        random.shuffle(players_this_round)

        max_matches_in_round = min(num_courts, len(players_this_round) // 4)
        if max_matches_in_round <= 0: continue # No se pueden formar partidos

        # --- Formar Parejas ---
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

        # --- Enfrentar Parejas ---
        match_count = 0
        assigned_players_in_match = set()
        available_pairs_for_match = list(final_round_pairs)
        random.shuffle(available_pairs_for_match)

        while match_count < max_matches_in_round and len(available_pairs_for_match) >= 2:
            pair1 = available_pairs_for_match.pop(0)
            found_opponent = False
            for i in range(len(available_pairs_for_match)):
                pair2 = available_pairs_for_match[i]
                if not set(pair1) & set(pair2): # Sin jugadores en común
                    available_pairs_for_match.pop(i) # Quitar oponente

                    played_pairs_history.add(tuple(sorted(pair1)))
                    played_pairs_history.add(tuple(sorted(pair2)))

                    round_matches.append({
                        "court": match_count + 1,
                        "pair1": pair1,
                        "pair2": pair2,
                        "score1": None,
                        "score2": None
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
                "matches": round_matches,
                "resting": players_resting
            })

    if not fixture["rounds"] and num_players >= 4:
         st.warning("No se pudieron generar rondas Americano. Revisa jugadores/pistas.")

    return fixture


# --- Funciones de Cálculo de Clasificación ---

def calculate_standings_americano(players, fixture_data):
    """Calcula la clasificación individual para torneo Americano."""
    standings = {p: {"JG": 0, "JR": 0, "DG": 0, "PG": 0, "PP": 0, "PE": 0, "PJ": 0} for p in players}
    if not fixture_data or 'rounds' not in fixture_data: return standings, []

    # Reiniciar a cero antes de recalcular
    for p in players: standings[p] = {"JG": 0, "JR": 0, "DG": 0, "PG": 0, "PP": 0, "PE": 0, "PJ": 0}
    processed_match_ids_for_stats = set() # Para evitar doble conteo de PJ/PG/PP/PE

    for round_idx, round_data in enumerate(fixture_data['rounds']):
        for match_idx, match in enumerate(round_data['matches']):
            match_id = f"r{round_data['round_num']}_m{match_idx}"

            score1 = st.session_state.get(f"score1_{match_id}")
            score2 = st.session_state.get(f"score2_{match_id}")

            s1 = int(score1) if score1 is not None else None
            s2 = int(score2) if score2 is not None else None

            match['score1'] = s1
            match['score2'] = s2

            if s1 is not None and s2 is not None:
                pair1, pair2 = match['pair1'], match['pair2']

                # Sumar juegos (se hace siempre que haya score)
                for p in pair1: standings[p]['JG'] += s1; standings[p]['JR'] += s2
                for p in pair2: standings[p]['JG'] += s2; standings[p]['JR'] += s1

                # Actualizar PJ/PG/PP/PE solo si no se ha procesado el partido para stats
                if match_id not in processed_match_ids_for_stats:
                    if s1 > s2:   res1, res2 = 'PG', 'PP'
                    elif s2 > s1: res1, res2 = 'PP', 'PG'
                    else:         res1, res2 = 'PE', 'PE'

                    for p in pair1: standings[p]['PJ'] += 1; standings[p][res1] += 1
                    for p in pair2: standings[p]['PJ'] += 1; standings[p][res2] += 1

                    processed_match_ids_for_stats.add(match_id) # Marcar como procesado para stats

    for p in players: standings[p]['DG'] = standings[p]['JG'] - standings[p]['JR']

    sorted_players = sorted(players, key=lambda p: (standings[p]['PG'], standings[p]['DG'], standings[p]['JG']), reverse=True)
    return standings, sorted_players


def calculate_standings_pairs(pairs, fixture_data):
    """Calcula la clasificación por parejas para torneo Round Robin."""
    pair_names = {f"{p[0]}/{p[1]}" for p in pairs}
    standings = {name: {"JG": 0, "JR": 0, "DG": 0, "PG": 0, "PP": 0, "PE": 0, "PJ": 0} for name in pair_names}
    if not fixture_data or 'rounds' not in fixture_data: return standings, []

    # Reiniciar a cero antes de recalcular
    for name in pair_names: standings[name] = {"JG": 0, "JR": 0, "DG": 0, "PG": 0, "PP": 0, "PE": 0, "PJ": 0}
    processed_match_ids_for_stats = set()

    for round_idx, round_data in enumerate(fixture_data['rounds']):
        for match_idx, match in enumerate(round_data['matches']):
            match_id = f"r{round_data['round_num']}_m{match_idx}"

            score1 = st.session_state.get(f"score1_{match_id}")
            score2 = st.session_state.get(f"score2_{match_id}")

            s1 = int(score1) if score1 is not None else None
            s2 = int(score2) if score2 is not None else None

            match['score1'] = s1
            match['score2'] = s2

            if s1 is not None and s2 is not None:
                pair1_tuple, pair2_tuple = match['pair1'], match['pair2']
                pair1_name = f"{pair1_tuple[0]}/{pair1_tuple[1]}"
                pair2_name = f"{pair2_tuple[0]}/{pair2_tuple[1]}"

                # Sumar juegos
                standings[pair1_name]['JG'] += s1; standings[pair1_name]['JR'] += s2
                standings[pair2_name]['JG'] += s2; standings[pair2_name]['JR'] += s1

                # Actualizar PJ/PG/PP/PE si no procesado
                if match_id not in processed_match_ids_for_stats:
                    standings[pair1_name]['PJ'] += 1
                    standings[pair2_name]['PJ'] += 1
                    if s1 > s2:
                        standings[pair1_name]['PG'] += 1; standings[pair2_name]['PP'] += 1
                    elif s2 > s1:
                        standings[pair1_name]['PP'] += 1; standings[pair2_name]['PG'] += 1
                    else:
                        standings[pair1_name]['PE'] += 1; standings[pair2_name]['PE'] += 1
                    processed_match_ids_for_stats.add(match_id)


    for name in pair_names: standings[name]['DG'] = standings[name]['JG'] - standings[name]['JR']

    sorted_pair_names = sorted(pair_names, key=lambda name: (standings[name]['PG'], standings[name]['DG'], standings[name]['JG']), reverse=True)
    return standings, sorted_pair_names

# --- Funciones de Formateo y UI Auxiliares ---

def generate_standings_text(standings_data, sorted_keys, tournament_name, is_pairs=False):
    """Genera texto formateado para clasificación (individual o parejas)."""
    entity_label = "Pareja" if is_pairs else "Jugador"
    header = f"--- CLASIFICACIÓN: {tournament_name} ({entity_label}) ---\n"
    separator = "-" * 75 + "\n"
    col_headers = f"{'Pos':<4} {entity_label:<30} {'PJ':<4} {'PG':<4} {'PE':<4} {'PP':<4} {'JG':<6} {'JR':<6} {'DG':<6}\n"

    lines = [header, separator, col_headers, separator]

    for i, key in enumerate(sorted_keys):
        stats = standings_data.get(key, {}) # Usar .get para evitar KeyError si algo falla
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
        # Recuperar valor existente si el usuario vuelve atrás
        default_name = st.session_state.player_inputs.get(i, f"Jugador {i+1}")
        player_name = cols_players[i % 3].text_input(
             f"Jugador {i + 1}",
             value=default_name,
             key=f"player_{i}" # Clave persistente
        )
        # Guardar en un dict temporal para el submit del formulario actual
        player_names_inputs[i] = player_name
        # Guardar también en session_state para persistencia entre reruns INMEDIATAMENTE
        st.session_state.player_inputs[i] = player_name
    return player_names_inputs


# --- Interfaz Principal de Streamlit ---

st.set_page_config(page_title="Gestor Torneos Pádel", layout="wide")
st.title("🏓 Gestor de Torneos de Pádel")

# --- Inicialización del Estado de Sesión ---
if 'app_phase' not in st.session_state:
    st.session_state.app_phase = 'config_base' # Fases: config_base, config_players, config_pairing, viewing
    st.session_state.config = {'num_players': 8, 'num_courts': 2, 'name': "Torneo Pádel"}
    st.session_state.players = []
    st.session_state.pairs = []
    st.session_state.fixture = None
    st.session_state.tournament_type = None
    st.session_state.pairing_method = None
    st.session_state.player_inputs = {} # {index: name}
    st.session_state.manual_pair_selections = {}

# --- FASE 0: Configuración Base (Nombre, Nº Jugadores, Nº Pistas) ---
if st.session_state.app_phase == 'config_base':
    st.header("1. Configuración Base del Torneo")

    with st.form("base_config_form"):
        conf_name = st.text_input(
            "Nombre del Torneo",
            st.session_state.config.get('name', "Torneo Pádel")
        )
        col1, col2 = st.columns(2)
        with col1:
            conf_num_players = st.number_input(
                "Número total de jugadores",
                min_value=4, # Mínimo para cualquier torneo
                step=1, # Permitir impares temporalmente, validar luego si es necesario
                value=st.session_state.config.get('num_players', 8)
            )
        with col2:
            conf_num_courts = st.number_input(
                "Número de pistas disponibles",
                min_value=1,
                step=1,
                value=st.session_state.config.get('num_courts', 2)
            )

        submitted_base_config = st.form_submit_button("Confirmar Configuración Base")

        if submitted_base_config:
            # Validar aquí si es necesario (e.g., mínimo de jugadores)
            if conf_num_players < 4:
                 st.error("Se necesitan al menos 4 jugadores.")
            else:
                 # Guardar configuración base en session_state
                 st.session_state.config['name'] = conf_name
                 st.session_state.config['num_players'] = conf_num_players
                 st.session_state.config['num_courts'] = conf_num_courts
                 # Pasar a la siguiente fase
                 st.session_state.app_phase = 'config_players'
                 st.rerun() # Forzar rerun para mostrar la fase de ingreso de nombres

# --- FASE 1: Ingreso de Nombres de Jugadores ---
elif st.session_state.app_phase == 'config_players':
    st.header("2. Ingreso de Jugadores")

    # Mostrar configuración base confirmada
    st.info(f"**Torneo:** {st.session_state.config.get('name')} | "
            f"**Jugadores:** {st.session_state.config.get('num_players')} | "
            f"**Pistas:** {st.session_state.config.get('num_courts')}")

    with st.form("player_entry_form"):
        num_players_to_enter = st.session_state.config.get('num_players', 0)
        # Mostrar los campos de entrada (la función guarda en st.session_state.player_inputs)
        display_player_inputs(num_players_to_enter)

        submitted_players = st.form_submit_button("Confirmar Jugadores y Continuar")

        if submitted_players:
            # Recoger nombres finales del estado de sesión donde se guardaron
            final_players = [st.session_state.player_inputs.get(i, "").strip() for i in range(num_players_to_enter)]
            final_players = [p for p in final_players if p] # Filtrar vacíos

            # Validaciones
            valid = True
            if len(final_players) != num_players_to_enter:
                st.error(f"Error: Se esperaban {num_players_to_enter} nombres de jugador, pero se encontraron {len(final_players)} no vacíos.")
                valid = False
            elif len(set(final_players)) != len(final_players):
                 st.error("Error: Hay nombres de jugador duplicados.")
                 valid = False

            if valid:
                st.session_state.players = final_players
                # Pasar a la siguiente fase
                st.session_state.app_phase = 'config_pairing'
                st.rerun()
            else:
                # Permanecer en esta fase, mostrar errores
                 pass

    # Botón para volver a la configuración base
    st.divider()
    if st.button("⬅️ Volver a Configuración Base"):
         st.session_state.app_phase = 'config_base'
         # Borrar nombres de jugadores si volvemos atrás? Opcional
         # st.session_state.player_inputs = {}
         # st.session_state.players = []
         st.rerun()


# --- FASE 2: Configuración del Tipo de Torneo y Parejas (si aplica) ---
elif st.session_state.app_phase == 'config_pairing':
    st.header("3. Formato del Torneo y Parejas")

    # Mostrar configuración confirmada
    st.info(f"**Torneo:** {st.session_state.config.get('name')} | "
            f"**Jugadores ({len(st.session_state.players)}):** {', '.join(st.session_state.players)} | "
            f"**Pistas:** {st.session_state.config.get('num_courts')}")

    tournament_type = st.radio(
        "Selecciona el formato del torneo:",
        (TOURNAMENT_TYPE_AMERICANO, TOURNAMENT_TYPE_PAREJAS_FIJAS),
        key='tournament_type_radio',
        horizontal=True,
        index=0 if st.session_state.tournament_type != TOURNAMENT_TYPE_PAREJAS_FIJAS else 1
    )
    st.session_state.tournament_type = tournament_type

    # --- Opciones específicas para Parejas Fijas ---
    if tournament_type == TOURNAMENT_TYPE_PAREJAS_FIJAS:
        if len(st.session_state.players) % 2 != 0:
            st.error(f"Error: Se requieren un número par de jugadores ({len(st.session_state.players)} ingresados) para el formato de Parejas Fijas.")
            if st.button("⬅️ Volver a Editar Jugadores"):
                 st.session_state.app_phase = 'config_players'
                 st.rerun()
            st.stop()

        st.subheader("Configuración de Parejas")
        pairing_method = st.radio(
            "¿Cómo deseas formar las parejas?",
            (PAIRING_METHOD_RANDOM, PAIRING_METHOD_MANUAL),
            key='pairing_method_radio',
            horizontal=True,
            index=0 if st.session_state.pairing_method != PAIRING_METHOD_MANUAL else 1
        )
        st.session_state.pairing_method = pairing_method

        if pairing_method == PAIRING_METHOD_MANUAL:
            st.markdown("**Asigna los jugadores a las parejas:**")
            num_pairs_needed = len(st.session_state.players) // 2
            potential_partners = [''] + list(st.session_state.players) # Añadir opción vacía
            manual_pairs_dict = {} # Usar dict para evitar duplicados de pareja temporalmente
            assigned_players_manual = set() # Jugadores ya usados en una pareja válida

            cols_pairing = st.columns(2)

            with st.form("manual_pairs_form"):
                 all_selections_valid = True
                 for i in range(num_pairs_needed):
                     pair_key_base = f"manual_pair_{i}"
                     
                     # Filtrar opciones disponibles: no asignados O el actualmente seleccionado para ESTE dropdown
                     current_sel1 = st.session_state.manual_pair_selections.get(f"{pair_key_base}_p1", '')
                     options1 = [''] + [p for p in potential_partners[1:] if p not in assigned_players_manual or p == current_sel1]
                     try:
                        index1 = options1.index(current_sel1) if current_sel1 in options1 else 0
                     except ValueError: index1 = 0 # Si el valor guardado ya no es válido

                     sel1 = cols_pairing[0].selectbox(f"Pareja {i+1} - Jugador 1", options=options1, key=f"{pair_key_base}_p1_sel", index=index1)
                     st.session_state.manual_pair_selections[f"{pair_key_base}_p1"] = sel1 # Guardar selección

                     # Asignados temporalmente para el segundo select (incluye el jugador 1 de esta pareja)
                     temp_assigned = assigned_players_manual.copy()
                     if sel1: temp_assigned.add(sel1)
                     
                     current_sel2 = st.session_state.manual_pair_selections.get(f"{pair_key_base}_p2", '')
                     options2 = [''] + [p for p in potential_partners[1:] if p not in temp_assigned or p == current_sel2]
                     try:
                        index2 = options2.index(current_sel2) if current_sel2 in options2 else 0
                     except ValueError: index2 = 0

                     sel2 = cols_pairing[1].selectbox(f"Pareja {i+1} - Jugador 2", options=options2, key=f"{pair_key_base}_p2_sel", index=index2)
                     st.session_state.manual_pair_selections[f"{pair_key_base}_p2"] = sel2

                     # Validar selección de esta pareja en el submit
                     if sel1 and sel2:
                          if sel1 == sel2:
                               st.warning(f"Pareja {i+1}: Jugadores deben ser diferentes.")
                               all_selections_valid = False
                          else:
                               # Añadir a dict temporal para checkear duplicados y asignar al final
                               manual_pairs_dict[i] = tuple(sorted((sel1, sel2)))
                               # Marcar como usados TEMPORALMENTE para los siguientes selects
                               assigned_players_manual.add(sel1)
                               assigned_players_manual.add(sel2)
                     elif sel1 or sel2: # Si solo uno está seleccionado
                           st.warning(f"Pareja {i+1}: Ambos jugadores deben ser seleccionados.")
                           all_selections_valid = False
                     # else: # Ambos vacíos, es válido si no es el submit final

                 confirm_manual_pairs = st.form_submit_button("Confirmar Parejas Manuales y Generar Fixture")
                 if confirm_manual_pairs:
                    final_manual_pairs = list(manual_pairs_dict.values())
                    final_assigned_players = set(p for pair in final_manual_pairs for p in pair)

                    if not all_selections_valid:
                         st.error("Hay errores en la selección de parejas. Por favor, corrígelos.")
                    elif len(final_manual_pairs) != num_pairs_needed:
                         st.error(f"Debes completar todas las {num_pairs_needed} parejas.")
                    elif len(final_assigned_players) != len(st.session_state.players):
                         st.error(f"No se asignaron todos los jugadores ({len(final_assigned_players)} de {len(st.session_state.players)}). Revisa las selecciones.")
                    elif len(set(final_manual_pairs)) != len(final_manual_pairs):
                         st.error("Se detectaron parejas duplicadas en la selección.")
                    else:
                         # ¡Éxito!
                         st.session_state.pairs = final_manual_pairs
                         st.session_state.fixture = generate_round_robin_pairs_fixture(st.session_state.pairs, st.session_state.config['num_courts'])
                         if st.session_state.fixture and st.session_state.fixture['rounds']:
                              st.session_state.app_phase = 'viewing'
                              st.success("Parejas asignadas y fixture Round Robin generado.")
                              st.rerun()
                         else:
                              st.error("Error al generar el fixture Round Robin.")


        elif pairing_method == PAIRING_METHOD_RANDOM:
            st.markdown("**Las parejas se sortearán aleatoriamente.**")
            if st.button("Sortear Parejas y Generar Fixture"):
                players_to_pair = list(st.session_state.players)
                random.shuffle(players_to_pair)
                random_pairs = [tuple(sorted((players_to_pair[i], players_to_pair[i+1])))
                                for i in range(0, len(players_to_pair), 2)]

                if len(random_pairs) == len(st.session_state.players) // 2:
                     st.session_state.pairs = random_pairs
                     st.write("Parejas Sorteadas:")
                     for p1, p2 in st.session_state.pairs: st.write(f"- {p1} / {p2}")

                     st.session_state.fixture = generate_round_robin_pairs_fixture(st.session_state.pairs, st.session_state.config['num_courts'])
                     if st.session_state.fixture and st.session_state.fixture['rounds']:
                          # Añadir botón para continuar explicitamente
                          if st.button("Continuar a Visualización"):
                              st.session_state.app_phase = 'viewing'
                              st.rerun()
                     else:
                          st.error("Error al generar el fixture Round Robin.")
                else:
                     st.error("Error durante el sorteo aleatorio de parejas.")

    # --- Opciones específicas para Americano ---
    elif tournament_type == TOURNAMENT_TYPE_AMERICANO:
        st.markdown("**Se generarán parejas rotativas aleatoriamente para cada ronda.**")
        if st.button("Generar Fixture Americano"):
            st.session_state.fixture = generate_americano_fixture(st.session_state.players, st.session_state.config['num_courts'])
            if st.session_state.fixture and st.session_state.fixture['rounds']:
                 st.session_state.app_phase = 'viewing'
                 st.success("Fixture Americano (rotación aleatoria) generado.")
                 st.rerun()
            else:
                 st.error("Error al generar el fixture Americano. Puede que no haya suficientes jugadores/pistas para todas las rondas deseadas.")

    # Botón para volver a la fase de ingreso de jugadores
    st.divider()
    if st.button("⬅️ Volver a Ingresar Jugadores"):
         st.session_state.app_phase = 'config_players'
         # Limpiar estados de esta fase si volvemos
         st.session_state.tournament_type = None
         st.session_state.pairing_method = None
         st.session_state.pairs = []
         st.session_state.manual_pair_selections = {}
         st.rerun()


# --- FASE 3: Visualización del Torneo (Rondas y Clasificación) ---
elif st.session_state.app_phase == 'viewing':
    st.header(f"🏆 Torneo: {st.session_state.config.get('name', 'Sin Nombre')}")

    tournament_mode_display = st.session_state.get('tournament_type', 'Desconocido')
    st.subheader(f"Formato: {tournament_mode_display}")

    # Mostrar detalles específicos del formato
    if tournament_mode_display == TOURNAMENT_TYPE_PAREJAS_FIJAS:
        st.write("**Parejas:**")
        pair_cols = st.columns(min(3, len(st.session_state.pairs))) # Ajustar columnas a número de parejas
        for i, (p1, p2) in enumerate(st.session_state.pairs):
             pair_cols[i % len(pair_cols)].write(f"- {p1} / {p2}")
        st.caption(f"{len(st.session_state.players)} jugadores | {st.session_state.config.get('num_courts', '?')} pistas")
    elif tournament_mode_display == TOURNAMENT_TYPE_AMERICANO:
         st.caption(f"{len(st.session_state.players)} jugadores | {st.session_state.config.get('num_courts', '?')} pistas | Parejas rotativas")

    # --- Calcular standings ANTES de mostrar las pestañas ---
    standings_data, sorted_keys = {}, []
    is_classification_pairs = (st.session_state.tournament_type == TOURNAMENT_TYPE_PAREJAS_FIJAS)

    # Recalcular standings siempre en esta fase para reflejar cambios en resultados
    if st.session_state.fixture and 'rounds' in st.session_state.fixture:
        if is_classification_pairs:
            standings_data, sorted_keys = calculate_standings_pairs(st.session_state.pairs, st.session_state.fixture)
        else: # Americano (individual)
            standings_data, sorted_keys = calculate_standings_americano(st.session_state.players, st.session_state.fixture)
    else:
        # Mostrar error si no hay fixture (aunque no debería llegarse aquí sin fixture)
        st.error("Error crítico: No se encontró un fixture válido para visualizar.")
        st.stop() # Detener si no hay nada que mostrar

    # --- Pestañas de Rondas y Clasificación ---
    tab1, tab2 = st.tabs(["📝 Rondas y Resultados", "📊 Clasificación"])

    with tab1:
        st.subheader("Partidos por Ronda")

        if not st.session_state.fixture or not st.session_state.fixture['rounds']:
             st.warning("No hay rondas generadas o disponibles en el fixture.")
        else:
            # Usar st.expander si hay muchas rondas? O mantener tabs? Tabs está bien por ahora.
            round_tabs = st.tabs([f"Ronda {r['round_num']}" for r in st.session_state.fixture['rounds']])

            for i, round_data in enumerate(st.session_state.fixture['rounds']):
                with round_tabs[i]:
                    st.markdown(f"**Ronda {round_data['round_num']}**")
                    if round_data.get('resting'): # Usar .get por seguridad
                         resting_label = "Parejas descansan" if is_classification_pairs else "Jugadores descansan"
                         st.caption(f"{resting_label}: {', '.join(round_data['resting'])}")

                    if not round_data.get('matches'):
                        st.info("No hay partidos programados en esta ronda.")
                        continue

                    # Mostrar partidos y campos para resultados
                    for match_idx, match in enumerate(round_data['matches']):
                        p1_tuple = match['pair1']
                        p2_tuple = match['pair2']
                        p1_name = f"{p1_tuple[0]} / {p1_tuple[1]}"
                        p2_name = f"{p2_tuple[0]} / {p2_tuple[1]}"

                        col_match, col_score1, col_score2 = st.columns([3, 1, 1])

                        with col_match:
                            st.markdown(f"**Pista {match.get('court', '?')}**: {p1_name} **vs** {p2_name}")

                        match_id = f"r{round_data['round_num']}_m{match_idx}"
                        score1_key = f"score1_{match_id}"
                        score2_key = f"score2_{match_id}"

                        # Usar formato %d para asegurar que no muestre decimales
                        with col_score1:
                            st.number_input(f"Games {p1_name}", min_value=0, step=1,
                                            value=st.session_state.get(score1_key), key=score1_key, format="%d", label_visibility="collapsed")
                        with col_score2:
                            st.number_input(f"Games {p2_name}", min_value=0, step=1,
                                            value=st.session_state.get(score2_key), key=score2_key, format="%d", label_visibility="collapsed")
                        st.divider()

    with tab2:
        st.subheader(f"Tabla de Clasificación ({'Parejas' if is_classification_pairs else 'Individual'})")

        if not standings_data or not sorted_keys:
            st.info("Aún no hay resultados ingresados o suficientes para calcular la clasificación.")
        else:
             standings_list = []
             entity_label = "Pareja" if is_classification_pairs else "Jugador"
             for pos, key in enumerate(sorted_keys):
                 stats = standings_data.get(key, {}) # Usar .get por seguridad
                 row = {"Pos": pos + 1, entity_label: key}
                 # Añadir stats asegurando que existen
                 row.update({
                    'PJ': stats.get('PJ', 0), 'PG': stats.get('PG', 0), 'PE': stats.get('PE', 0), 'PP': stats.get('PP', 0),
                    'JG': stats.get('JG', 0), 'JR': stats.get('JR', 0), 'DG': stats.get('DG', 0)
                 })
                 standings_list.append(row)

             df_standings = pd.DataFrame(standings_list)
             cols_to_show = ['Pos', entity_label, 'PJ', 'PG', 'PE', 'PP', 'JG', 'JR', 'DG']
             df_display = df_standings[cols_to_show]

             st.dataframe(df_display.set_index('Pos'), use_container_width=True)

             # Botón de descarga
             st.download_button(
                 label=f"📄 Descargar Clasificación ({entity_label}) (.txt)",
                 data=generate_standings_text(standings_data, sorted_keys, st.session_state.config.get('name', 'Torneo'), is_classification_pairs),
                 file_name=f"clasificacion_{st.session_state.config.get('name', 'torneo').replace(' ', '_')}_{entity_label.lower()}.txt",
                 mime='text/plain'
             )

    # Botón para reiniciar TODO
    st.divider()
    if st.button("⚠️ Empezar Nuevo Torneo (Borrar Todo)"):
        keys_to_delete = list(st.session_state.keys())
        for key in keys_to_delete:
             del st.session_state[key]
        # Re-inicializar valores por defecto para empezar limpio
        st.session_state.app_phase = 'config_base'
        st.session_state.config = {'num_players': 8, 'num_courts': 2, 'name': "Torneo Pádel"}
        st.session_state.players = []
        st.session_state.pairs = []
        st.session_state.fixture = None
        st.session_state.tournament_type = None
        st.session_state.pairing_method = None
        st.session_state.player_inputs = {}
        st.session_state.manual_pair_selections = {}
        st.rerun()