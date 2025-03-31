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
    # Podría mejorarse con algoritmos de scheduling más complejos
    
    matches_per_round = min(num_courts, num_pairs // 2) # Max partidos simultáneos
    num_rounds_needed = math.ceil(len(matches_to_play) / matches_per_round) if matches_per_round > 0 else 0

    match_iterator = iter(matches_to_play)
    
    for round_num in range(1, num_rounds_needed + 1):
        round_matches = []
        pairs_in_round = set()
        
        added_matches_count = 0
        temp_matches_for_round = [] # Almacenar temporalmente antes de asignar pista

        # Intentar llenar las pistas disponibles
        successful_match_additions = 0
        processed_matches_indices = set() # Track indices from matches_to_play

        # Re-iterar si es necesario para llenar pistas, evitando conflictos
        available_matches = [(idx, match) for idx, match in enumerate(matches_to_play) if idx not in processed_matches_indices]
        
        current_round_pair_names = set() # Nombres de las parejas ya asignadas a esta ronda

        for idx, (pair1_tuple, pair2_tuple) in available_matches:
             if successful_match_additions >= matches_per_round:
                 break # Ya tenemos suficientes partidos para las pistas

             # Verificar si alguna de estas parejas ya juega en esta ronda
             pair1_name = f"{pair1_tuple[0]}/{pair1_tuple[1]}"
             pair2_name = f"{pair2_tuple[0]}/{pair2_tuple[1]}"
             
             if pair1_name not in current_round_pair_names and pair2_name not in current_round_pair_names:
                 # Añadir partido a la ronda
                 temp_matches_for_round.append({
                     "pair1": pair1_tuple,
                     "pair2": pair2_tuple,
                     "score1": None,
                     "score2": None
                 })
                 current_round_pair_names.add(pair1_name)
                 current_round_pair_names.add(pair2_name)
                 processed_matches_indices.add(idx) # Marcar este partido como usado
                 successful_match_additions += 1

        # Asignar número de pista
        for i, match_data in enumerate(temp_matches_for_round):
            match_data["court"] = i + 1
            round_matches.append(match_data)

        # Calcular parejas que descansan (si aplica)
        all_pair_names_in_fixture = {f"{p[0]}/{p[1]}" for p in pairs}
        resting_pairs_names = list(all_pair_names_in_fixture - current_round_pair_names)


        if round_matches:
             fixture["rounds"].append({
                 "round_num": round_num,
                 "matches": round_matches,
                 "resting": resting_pairs_names # Lista de nombres de parejas
             })
             
        # Eliminar los partidos ya asignados de la lista principal (ineficiente, mejor usar índices)
        matches_to_play = [match for idx, match in enumerate(matches_to_play) if idx not in processed_matches_indices]
             
    # Si quedan partidos sin asignar (debería ser raro con ceil), añadirlos en rondas extra
    # (Esta parte es un fallback, idealmente el cálculo inicial de rondas es correcto)
    while matches_to_play:
         round_num += 1
         round_matches = []
         pairs_in_round = set()
         added_matches_count = 0
         # ... (lógica similar a la anterior para llenar una ronda con los restantes)
         # Simplificado por ahora: asumir que el cálculo inicial funciona
         print(f"Advertencia: Quedaron partidos sin asignar, revisar lógica de distribución. Partidos restantes: {matches_to_play}")
         break


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
        # Priorizar parejas que no han jugado juntas
        for p1, p2 in possible_pairs:
            pair_tuple = tuple(sorted((p1, p2)))
            priority = 1 if pair_tuple not in played_pairs_history else 0
            if p1 not in players_already_paired and p2 not in players_already_paired:
                 potential_pairs.append((priority, pair_tuple))
                 # No añadir a players_already_paired hasta confirmar el par

        potential_pairs.sort(key=lambda x: x[0], reverse=True)
        
        final_round_pairs = []
        players_in_final_pairs = set()
        for _, pair_tuple in potential_pairs:
            p1, p2 = pair_tuple
            if p1 not in players_in_final_pairs and p2 not in players_in_final_pairs:
                final_round_pairs.append(pair_tuple)
                players_in_final_pairs.add(p1)
                players_in_final_pairs.add(p2)
                # played_pairs_history.add(pair_tuple) # Añadir al historial SOLO si se usa en un partido

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

                    # Añadir al historial ahora que se confirma
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
            # if not found_opponent: available_pairs_for_match.append(pair1) # Devolver si no se usó (opcional)

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

    processed_matches = set() # Evita doble conteo si se recalcula

    for round_idx, round_data in enumerate(fixture_data['rounds']):
        for match_idx, match in enumerate(round_data['matches']):
            match_id = f"r{round_data['round_num']}_m{match_idx}"
            
            score1 = st.session_state.get(f"score1_{match_id}")
            score2 = st.session_state.get(f"score2_{match_id}")
            
            s1 = int(score1) if score1 is not None else None
            s2 = int(score2) if score2 is not None else None

            match['score1'] = s1
            match['score2'] = s2

            if s1 is not None and s2 is not None and match_id not in processed_matches:
                pair1, pair2 = match['pair1'], match['pair2']
                
                # Sumar juegos
                for p in pair1: standings[p]['JG'] += s1; standings[p]['JR'] += s2
                for p in pair2: standings[p]['JG'] += s2; standings[p]['JR'] += s1

                # Determinar resultado
                if s1 > s2:   res1, res2 = 'PG', 'PP'
                elif s2 > s1: res1, res2 = 'PP', 'PG'
                else:         res1, res2 = 'PE', 'PE'

                # Sumar PJ, PG, PP, PE
                for p in pair1: standings[p]['PJ'] += 1; standings[p][res1] += 1
                for p in pair2: standings[p]['PJ'] += 1; standings[p][res2] += 1
                
                processed_matches.add(match_id) # Marcar como procesado

    for p in players: standings[p]['DG'] = standings[p]['JG'] - standings[p]['JR']
    
    sorted_players = sorted(players, key=lambda p: (standings[p]['PG'], standings[p]['DG'], standings[p]['JG']), reverse=True)
    return standings, sorted_players


def calculate_standings_pairs(pairs, fixture_data):
    """Calcula la clasificación por parejas para torneo Round Robin."""
    pair_names = {f"{p[0]}/{p[1]}" for p in pairs}
    standings = {name: {"JG": 0, "JR": 0, "DG": 0, "PG": 0, "PP": 0, "PE": 0, "PJ": 0} for name in pair_names}
    if not fixture_data or 'rounds' not in fixture_data: return standings, []

    processed_matches = set()

    for round_idx, round_data in enumerate(fixture_data['rounds']):
        for match_idx, match in enumerate(round_data['matches']):
            match_id = f"r{round_data['round_num']}_m{match_idx}"

            score1 = st.session_state.get(f"score1_{match_id}")
            score2 = st.session_state.get(f"score2_{match_id}")

            s1 = int(score1) if score1 is not None else None
            s2 = int(score2) if score2 is not None else None
            
            match['score1'] = s1
            match['score2'] = s2

            if s1 is not None and s2 is not None and match_id not in processed_matches:
                pair1_tuple, pair2_tuple = match['pair1'], match['pair2']
                pair1_name = f"{pair1_tuple[0]}/{pair1_tuple[1]}"
                pair2_name = f"{pair2_tuple[0]}/{pair2_tuple[1]}"

                # PJ
                standings[pair1_name]['PJ'] += 1
                standings[pair2_name]['PJ'] += 1
                # JG / JR
                standings[pair1_name]['JG'] += s1; standings[pair1_name]['JR'] += s2
                standings[pair2_name]['JG'] += s2; standings[pair2_name]['JR'] += s1
                # PG / PP / PE
                if s1 > s2:
                    standings[pair1_name]['PG'] += 1; standings[pair2_name]['PP'] += 1
                elif s2 > s1:
                    standings[pair1_name]['PP'] += 1; standings[pair2_name]['PG'] += 1
                else:
                    standings[pair1_name]['PE'] += 1; standings[pair2_name]['PE'] += 1
                
                processed_matches.add(match_id)

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
        stats = standings_data[key]
        lines.append(
            f"{i+1:<4} {key:<30} {stats['PJ']:<4} {stats['PG']:<4} {stats['PE']:<4} {stats['PP']:<4} {stats['JG']:<6} {stats['JR']:<6} {stats['DG']:<6}\n"
        )
    
    lines.append(separator)
    return "".join(lines)


def display_player_inputs(num_players_to_show):
    """Muestra dinámicamente los campos de entrada para nombres de jugadores."""
    player_names_inputs = {}
    cols_players = st.columns(3)
    for i in range(num_players_to_show):
        default_name = st.session_state.player_inputs.get(i, f"Jugador {i+1}")
        player_names_inputs[i] = cols_players[i % 3].text_input(
             f"Jugador {i + 1}",
             value=default_name,
             key=f"player_{i}" # Clave persistente
        )
        # Actualizar el valor en session_state inmediatamente para persistencia entre reruns
        st.session_state.player_inputs[i] = player_names_inputs[i]
    return player_names_inputs


# --- Interfaz Principal de Streamlit ---

st.set_page_config(page_title="Gestor Torneos Pádel", layout="wide")
st.title("🏓 Gestor de Torneos de Pádel")

# --- Inicialización del Estado de Sesión ---
# Mantener estados claros para las diferentes fases de la app
if 'app_phase' not in st.session_state:
    st.session_state.app_phase = 'config_players' # Fases: config_players, config_pairing, viewing
    st.session_state.config = {'num_players': 8, 'num_courts': 2, 'name': "Torneo Pádel"} # Defaults
    st.session_state.players = []
    st.session_state.pairs = [] # Lista de tuplas (p1, p2) si es torneo de parejas
    st.session_state.fixture = None
    st.session_state.tournament_type = None # Americano o Parejas Fijas
    st.session_state.pairing_method = None # Random o Manual (si aplica)
    st.session_state.player_inputs = {} # {index: name} para recordar entre reruns
    st.session_state.manual_pair_selections = {} # Para selects de parejas manuales

# --- Fase 1: Configuración de Jugadores y Torneo Base ---
if st.session_state.app_phase == 'config_players':
    st.header("1. Configuración del Torneo y Jugadores")

    with st.form("player_config_form"):
        st.session_state.config['name'] = st.text_input(
            "Nombre del Torneo",
            st.session_state.config.get('name', "Torneo Pádel")
        )

        col1, col2 = st.columns(2)
        with col1:
            # Usar 'on_change' para intentar actualizar, pero Streamlit reruns en widget interaction
            num_players_value = st.number_input(
                "Número total de jugadores",
                min_value=4,
                step=2, # Forzar par implicitamente? No, permitir impares y validar luego
                value=st.session_state.config.get('num_players', 8),
                key='num_players_widget' # Key para referenciar este widget
            )
            # Actualizar config en session state inmediatamente
            st.session_state.config['num_players'] = num_players_value

        with col2:
            num_courts_value = st.number_input(
                "Número de pistas disponibles",
                min_value=1,
                step=1,
                value=st.session_state.config.get('num_courts', 2)
            )
            st.session_state.config['num_courts'] = num_courts_value

        st.subheader("Nombres de los Jugadores")
        # Mostrar inputs basado en el valor actual del widget num_players
        num_players_to_display = st.session_state.config.get('num_players', 0)
        player_name_widgets = display_player_inputs(num_players_to_display)

        submitted_players = st.form_submit_button("Continuar a Opciones de Parejas/Formato")

        if submitted_players:
            # Recoger nombres finales de los widgets (o de session_state si es más fiable)
            final_players = [st.session_state.player_inputs.get(i, "").strip() for i in range(num_players_to_display)]
            final_players = [p for p in final_players if p] # Filtrar vacíos

            # Validaciones
            valid = True
            if len(final_players) != num_players_to_display:
                st.error(f"Error: Se esperaban {num_players_to_display} nombres de jugador, pero se encontraron {len(final_players)} no vacíos.")
                valid = False
            elif len(set(final_players)) != len(final_players):
                 st.error("Error: Hay nombres de jugador duplicados.")
                 valid = False
            # Validar si número de jugadores es par para parejas fijas más adelante

            if valid:
                st.session_state.players = final_players
                # Pasar a la siguiente fase
                st.session_state.app_phase = 'config_pairing'
                st.rerun() # Forzar rerun para mostrar la siguiente fase
            else:
                # Permanecer en esta fase, mostrar errores
                 pass

# --- Fase 2: Configuración del Tipo de Torneo y Parejas (si aplica) ---
elif st.session_state.app_phase == 'config_pairing':
    st.header("2. Formato del Torneo y Parejas")

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
        # Validar número par de jugadores
        if len(st.session_state.players) % 2 != 0:
            st.error(f"Error: Se requieren un número par de jugadores ({len(st.session_state.players)} ingresados) para el formato de Parejas Fijas.")
            # Botón para volver atrás
            if st.button("⬅️ Volver a Editar Jugadores"):
                 st.session_state.app_phase = 'config_players'
                 st.rerun()
            st.stop() # Detener ejecución si no es par

        st.subheader("Configuración de Parejas")
        pairing_method = st.radio(
            "¿Cómo deseas formar las parejas?",
            (PAIRING_METHOD_RANDOM, PAIRING_METHOD_MANUAL),
            key='pairing_method_radio',
            horizontal=True,
            index=0 if st.session_state.pairing_method != PAIRING_METHOD_MANUAL else 1
        )
        st.session_state.pairing_method = pairing_method

        # --- Selección Manual de Parejas ---
        if pairing_method == PAIRING_METHOD_MANUAL:
            st.markdown("**Asigna los jugadores a las parejas:**")
            num_pairs_needed = len(st.session_state.players) // 2
            potential_partners = list(st.session_state.players) # Lista para seleccionar
            manual_pairs = []
            assigned_players = set()

            cols_pairing = st.columns(2) # Dos columnas para la selección

            for i in range(num_pairs_needed):
                pair_key_base = f"manual_pair_{i}"
                
                # Obtener selecciones previas del estado si existen
                p1_selected = st.session_state.manual_pair_selections.get(f"{pair_key_base}_p1")
                p2_selected = st.session_state.manual_pair_selections.get(f"{pair_key_base}_p2")

                # Filtrar opciones disponibles (no asignados O el actualmente seleccionado)
                options1 = [p for p in potential_partners if p not in assigned_players or p == p1_selected]
                
                # Asegurar que el valor seleccionado esté en las opciones
                p1_index = options1.index(p1_selected) if p1_selected in options1 else 0 

                sel1 = cols_pairing[0].selectbox(f"Pareja {i+1} - Jugador 1", options1, key=f"{pair_key_base}_p1_sel", index=p1_index)
                st.session_state.manual_pair_selections[f"{pair_key_base}_p1"] = sel1 # Guardar selección

                # Actualizar asignados temporalmente para el segundo select
                temp_assigned = assigned_players.copy()
                if sel1: temp_assigned.add(sel1)
                
                options2 = [p for p in potential_partners if p not in temp_assigned or p == p2_selected]
                p2_index = options2.index(p2_selected) if p2_selected in options2 else 0
                
                sel2 = cols_pairing[1].selectbox(f"Pareja {i+1} - Jugador 2", options2, key=f"{pair_key_base}_p2_sel", index=p2_index)
                st.session_state.manual_pair_selections[f"{pair_key_base}_p2"] = sel2

                # Validar y guardar pareja si ambos son seleccionados y distintos
                if sel1 and sel2 and sel1 != sel2:
                    current_pair = tuple(sorted((sel1, sel2)))
                    manual_pairs.append(current_pair)
                    # Marcar como asignados DEFINITIVAMENTE para la siguiente iteración
                    assigned_players.add(sel1)
                    assigned_players.add(sel2)
                elif sel1 and sel2 and sel1 == sel2:
                     st.warning(f"Pareja {i+1}: ¡Un jugador no puede ser pareja de sí mismo!")


            # Botón para confirmar parejas manuales
            confirm_manual_pairs = st.button("Confirmar Parejas Manuales y Generar Fixture")
            if confirm_manual_pairs:
                 # Validar que todas las parejas se formaron correctamente
                 if len(manual_pairs) == num_pairs_needed and len(assigned_players) == len(st.session_state.players):
                      # Validar que no haya parejas duplicadas (aunque la lógica debería prevenirlo)
                     if len(set(manual_pairs)) == num_pairs_needed:
                         st.session_state.pairs = manual_pairs
                         st.session_state.fixture = generate_round_robin_pairs_fixture(st.session_state.pairs, st.session_state.config['num_courts'])
                         if st.session_state.fixture and st.session_state.fixture['rounds']:
                              st.session_state.app_phase = 'viewing'
                              st.success("Parejas asignadas y fixture Round Robin generado.")
                              st.rerun()
                         else:
                              st.error("Error al generar el fixture Round Robin.")
                     else:
                          st.error("Error: Se detectaron parejas duplicadas.")
                 else:
                      st.error(f"Error: No se asignaron correctamente todos los jugadores ({len(assigned_players)} de {len(st.session_state.players)}). Asegúrate de que cada pareja tenga dos jugadores diferentes.")

        # --- Sorteo Aleatorio de Parejas ---
        elif pairing_method == PAIRING_METHOD_RANDOM:
            st.markdown("**Las parejas se sortearán aleatoriamente.**")
            confirm_random_pairs = st.button("Sortear Parejas y Generar Fixture")
            if confirm_random_pairs:
                players_to_pair = list(st.session_state.players)
                random.shuffle(players_to_pair)
                random_pairs = []
                # Crear parejas tomando de dos en dos de la lista barajada
                for i in range(0, len(players_to_pair), 2):
                     if i + 1 < len(players_to_pair): # Asegurar que hay un compañero
                         random_pairs.append(tuple(sorted((players_to_pair[i], players_to_pair[i+1]))))
                
                if len(random_pairs) == len(st.session_state.players) // 2:
                     st.session_state.pairs = random_pairs
                     # Mostrar las parejas sorteadas
                     st.write("Parejas Sorteadas:")
                     for p1, p2 in st.session_state.pairs: st.write(f"- {p1} / {p2}")

                     st.session_state.fixture = generate_round_robin_pairs_fixture(st.session_state.pairs, st.session_state.config['num_courts'])
                     if st.session_state.fixture and st.session_state.fixture['rounds']:
                          st.session_state.app_phase = 'viewing'
                          st.success("Parejas sorteadas y fixture Round Robin generado.")
                          # No hacer rerun inmediato, mostrar las parejas sorteadas primero
                          # El usuario navegará a la visualización o se añadirá botón "Ver Fixture"
                          # Por ahora, rerun para pasar a la siguiente fase:
                          st.rerun()
                     else:
                          st.error("Error al generar el fixture Round Robin.")
                else:
                     st.error("Error durante el sorteo aleatorio de parejas.")

    # --- Opciones específicas para Americano ---
    elif tournament_type == TOURNAMENT_TYPE_AMERICANO:
        st.markdown("**Se generarán parejas rotativas aleatoriamente para cada ronda.**")
        confirm_americano = st.button("Generar Fixture Americano")
        if confirm_americano:
            st.session_state.fixture = generate_americano_fixture(st.session_state.players, st.session_state.config['num_courts'])
            if st.session_state.fixture and st.session_state.fixture['rounds']:
                 st.session_state.app_phase = 'viewing'
                 st.success("Fixture Americano (rotación aleatoria) generado.")
                 st.rerun()
            else:
                 st.error("Error al generar el fixture Americano.")

    # Botón para volver atrás en esta fase también
    st.divider()
    if st.button("⬅️ Volver a Editar Jugadores"):
         st.session_state.app_phase = 'config_players'
         # Podríamos limpiar estados de pairing si volvemos atrás? Opcional.
         # st.session_state.tournament_type = None
         # st.session_state.pairing_method = None
         # st.session_state.pairs = []
         st.rerun()

# --- Fase 3: Visualización del Torneo (Rondas y Clasificación) ---
elif st.session_state.app_phase == 'viewing':
    st.header(f"🏆 Torneo: {st.session_state.config.get('name', 'Sin Nombre')}")
    
    # Mostrar tipo de torneo
    tournament_mode_display = st.session_state.get('tournament_type', 'Desconocido')
    st.subheader(f"Formato: {tournament_mode_display}")
    
    if tournament_mode_display == TOURNAMENT_TYPE_PAREJAS_FIJAS:
        st.write("**Parejas:**")
        pair_cols = st.columns(3)
        for i, (p1, p2) in enumerate(st.session_state.pairs):
             pair_cols[i % 3].write(f"- {p1} / {p2}")
        st.caption(f"{len(st.session_state.players)} jugadores | {st.session_state.config.get('num_courts', '?')} pistas")

    elif tournament_mode_display == TOURNAMENT_TYPE_AMERICANO:
         st.caption(f"{len(st.session_state.players)} jugadores | {st.session_state.config.get('num_courts', '?')} pistas | Parejas rotativas")


    # --- Calcular standings ANTES de mostrar las pestañas ---
    standings_data, sorted_keys = {}, []
    is_classification_pairs = (st.session_state.tournament_type == TOURNAMENT_TYPE_PAREJAS_FIJAS)

    if st.session_state.fixture and 'rounds' in st.session_state.fixture:
        if is_classification_pairs:
            standings_data, sorted_keys = calculate_standings_pairs(st.session_state.pairs, st.session_state.fixture)
        else: # Americano (individual)
            standings_data, sorted_keys = calculate_standings_americano(st.session_state.players, st.session_state.fixture)
    else:
        st.error("Error: No se encontró un fixture válido en el estado.")

    # --- Pestañas de Rondas y Clasificación ---
    tab1, tab2 = st.tabs(["📝 Rondas y Resultados", "📊 Clasificación"])

    with tab1:
        st.subheader("Partidos por Ronda")
        
        if not st.session_state.fixture or not st.session_state.fixture['rounds']:
             st.warning("No hay rondas generadas para este torneo.")
        else:
            round_tabs = st.tabs([f"Ronda {r['round_num']}" for r in st.session_state.fixture['rounds']])

            for i, round_data in enumerate(st.session_state.fixture['rounds']):
                with round_tabs[i]:
                    st.markdown(f"**Ronda {round_data['round_num']}**")
                    if round_data['resting']:
                         resting_label = "Parejas descansan" if is_classification_pairs else "Jugadores descansan"
                         st.caption(f"{resting_label}: {', '.join(round_data['resting'])}")
                    
                    if not round_data['matches']:
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
                            st.markdown(f"**Pista {match['court']}**: {p1_name} **vs** {p2_name}")
                        
                        match_id = f"r{round_data['round_num']}_m{match_idx}"
                        score1_key = f"score1_{match_id}"
                        score2_key = f"score2_{match_id}"

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
            st.info("Aún no hay resultados ingresados.")
        else:
             standings_list = []
             entity_label = "Pareja" if is_classification_pairs else "Jugador"
             for pos, key in enumerate(sorted_keys):
                 stats = standings_data[key]
                 row = {"Pos": pos + 1, entity_label: key}
                 row.update(stats) # Añadir todas las stats calculadas
                 standings_list.append(row)
             
             df_standings = pd.DataFrame(standings_list)
             # Seleccionar y ordenar columnas para mostrar
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
             
    # Botón para reiniciar
    st.divider()
    if st.button("⚠️ Empezar Nuevo Torneo (Borrar Todo)"):
        # Limpiar TODO el estado de sesión para empezar de cero
        keys_to_delete = list(st.session_state.keys()) # Copia de claves
        for key in keys_to_delete:
             del st.session_state[key]
        st.rerun()