import streamlit as st
import pandas as pd
import random
from itertools import combinations, cycle
import math
from collections import deque # Usaremos deque para rotación eficiente

# --- Constantes ---
TOURNAMENT_TYPE_AMERICANO = "Americano (Parejas Rotativas)"
TOURNAMENT_TYPE_PAREJAS_FIJAS = "Parejas Fijas (Round Robin)"
PAIRING_METHOD_RANDOM = "Sorteo Aleatorio"
PAIRING_METHOD_MANUAL = "Selección Manual"

# --- Funciones de Generación de Fixture ---

def generate_round_robin_pairs_fixture(pairs_list, num_courts):
    """
    Genera un fixture Round Robin para parejas fijas usando el algoritmo
    estándar (método del círculo), adaptado para parejas.
    Garantiza N-1 rondas con N/2 partidos por ronda si N (nº parejas) es par.
    """
    num_pairs = len(pairs_list)
    if num_pairs < 2:
        st.warning("Se necesitan al menos 2 parejas para generar un fixture.")
        return {"rounds": []}

    fixture = {"rounds": []}
    working_pairs_list = list(pairs_list)
    is_odd = False
    if num_pairs % 2 != 0:
        working_pairs_list.append("BYE"); num_pairs += 1; is_odd = True

    n = num_pairs; num_rounds = n - 1; matches_per_round_algo = n // 2
    matches_per_round_display = min(num_courts, matches_per_round_algo)
    if matches_per_round_display <= 0:
        st.warning(f"No se pueden jugar partidos con {num_courts} pistas y {len(pairs_list)} parejas."); return {"rounds": []}

    rotating_items = deque(working_pairs_list)
    all_original_pair_names = {f"{p[0]}/{p[1]}" for p in pairs_list} # Nombres de las parejas originales

    for round_num in range(1, num_rounds + 1):
        round_matches_data_algo = []; pairs_playing_this_round_algo = set()
        current_round_deque = rotating_items.copy()
        for i in range(matches_per_round_algo):
            item1 = current_round_deque[i]; item2 = current_round_deque[n - 1 - i]
            if item1 != "BYE" and item2 != "BYE":
                 if isinstance(item1, tuple) and isinstance(item2, tuple):
                    round_matches_data_algo.append({"pair1": item1, "pair2": item2, "score1": None, "score2": None})
                    pairs_playing_this_round_algo.add(f"{item1[0]}/{item1[1]}"); pairs_playing_this_round_algo.add(f"{item2[0]}/{item2[1]}")
                 else: st.error(f"Error RR interno: {item1} vs {item2}")

        final_round_matches_display = []; pairs_playing_names_display = set()
        # Opcional: random.shuffle(round_matches_data_algo)
        for court_idx, match_data in enumerate(round_matches_data_algo):
             if court_idx < matches_per_round_display:
                 match_data["court"] = court_idx + 1; final_round_matches_display.append(match_data)
                 pairs_playing_names_display.add(f"{match_data['pair1'][0]}/{match_data['pair1'][1]}"); pairs_playing_names_display.add(f"{match_data['pair2'][0]}/{match_data['pair2'][1]}")

        resting_pairs_names = list(all_original_pair_names - pairs_playing_names_display)
        if final_round_matches_display:
            fixture["rounds"].append({"round_num": round_num, "matches": final_round_matches_display, "resting": resting_pairs_names})

        if len(rotating_items) > 1: last_item = rotating_items.pop(); rotating_items.insert(1, last_item)

    if "rounds" not in fixture: fixture["rounds"] = []
    elif not fixture["rounds"] and len(pairs_list)>=2: st.warning("Fixture RR generado sin rondas asignadas.")
    return fixture

# --- Función generate_americano_fixture (sin cambios) ---
def generate_americano_fixture(players, num_courts):
    """Genera un fixture Americano SIMPLIFICADO (rotación aleatoria)."""
    num_players = len(players)
    if num_players < 4: st.warning("Min 4 jugadores para Americano."); return {"rounds": []}
    fixture = {"rounds": []}; all_players = list(players); played_pairs_history = set()
    num_rounds = max(1, num_players - 1)
    for _ in range(num_rounds):
        round_matches = []; players_this_round = list(all_players); random.shuffle(players_this_round)
        max_matches_in_round = min(num_courts, len(players_this_round) // 4)
        if max_matches_in_round <= 0: continue
        possible_pairs = list(combinations(players_this_round, 2)); random.shuffle(possible_pairs)
        potential_pairs = []; players_already_paired = set()
        for p1, p2 in possible_pairs:
            pair_tuple = tuple(sorted((p1, p2))); priority = 1 if pair_tuple not in played_pairs_history else 0
            if p1 not in players_already_paired and p2 not in players_already_paired: potential_pairs.append((priority, pair_tuple))
        potential_pairs.sort(key=lambda x: x[0], reverse=True)
        final_round_pairs = []; players_in_final_pairs = set()
        for _, pair_tuple in potential_pairs:
            p1, p2 = pair_tuple
            if p1 not in players_in_final_pairs and p2 not in players_in_final_pairs: final_round_pairs.append(pair_tuple); players_in_final_pairs.add(p1); players_in_final_pairs.add(p2)
        match_count = 0; assigned_players_in_match = set(); available_pairs_for_match = list(final_round_pairs); random.shuffle(available_pairs_for_match)
        while match_count < max_matches_in_round and len(available_pairs_for_match) >= 2:
            pair1 = available_pairs_for_match.pop(0); found_opponent = False
            for i in range(len(available_pairs_for_match)):
                pair2 = available_pairs_for_match[i]
                if not set(pair1) & set(pair2):
                    available_pairs_for_match.pop(i); played_pairs_history.add(tuple(sorted(pair1))); played_pairs_history.add(tuple(sorted(pair2)))
                    round_matches.append({"court":match_count+1,"pair1":pair1,"pair2":pair2,"score1":None,"score2":None})
                    assigned_players_in_match.update(pair1); assigned_players_in_match.update(pair2); match_count+=1; found_opponent=True; break
        players_resting=[p for p in all_players if p not in assigned_players_in_match]
        if round_matches: fixture["rounds"].append({"round_num":len(fixture["rounds"])+1,"matches":round_matches,"resting":players_resting})
    if "rounds" not in fixture: fixture["rounds"] = []
    elif not fixture["rounds"] and num_players>=4: st.warning("No se pudieron generar rondas Americano.")
    return fixture

# --- Funciones de Cálculo de Clasificación (sin cambios) ---
def calculate_standings_americano(players, fixture_data):
    """Calcula la clasificación individual para torneo Americano."""
    standings = {p: {"JG": 0, "JR": 0, "DG": 0, "PG": 0, "PP": 0, "PE": 0, "PJ": 0} for p in players}
    if not fixture_data or 'rounds' not in fixture_data: return standings, []
    for p in players: standings[p] = {"JG": 0, "JR": 0, "DG": 0, "PG": 0, "PP": 0, "PE": 0, "PJ": 0}
    processed_match_ids_for_stats = set()
    for round_idx, round_data in enumerate(fixture_data.get('rounds',[])):
        for match_idx, match in enumerate(round_data.get('matches', [])):
            match_id = f"r{round_data.get('round_num', '?')}_m{match_idx}"
            score1 = st.session_state.get(f"score1_{match_id}"); score2 = st.session_state.get(f"score2_{match_id}")
            s1 = int(score1) if score1 is not None else None; s2 = int(score2) if score2 is not None else None
            if s1 is not None and s2 is not None:
                 if 'pair1' not in match or 'pair2' not in match or not isinstance(match['pair1'],(list, tuple)) or len(match['pair1'])!=2 or not isinstance(match['pair2'],(list, tuple)) or len(match['pair2'])!=2: continue
                 pair1, pair2 = match['pair1'], match['pair2']
                 if not all(p in standings for p in pair1) or not all(p in standings for p in pair2): continue
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
    for round_idx, round_data in enumerate(fixture_data.get('rounds', [])):
        for match_idx, match in enumerate(round_data.get('matches', [])):
            match_id = f"r{round_data.get('round_num','?')}_m{match_idx}"
            score1 = st.session_state.get(f"score1_{match_id}"); score2 = st.session_state.get(f"score2_{match_id}")
            s1 = int(score1) if score1 is not None else None; s2 = int(score2) if score2 is not None else None
            if s1 is not None and s2 is not None:
                if 'pair1' not in match or 'pair2' not in match or not isinstance(match['pair1'],(list, tuple)) or len(match['pair1'])!=2 or not isinstance(match['pair2'],(list, tuple)) or len(match['pair2'])!=2: continue
                pair1_tuple, pair2_tuple = match['pair1'], match['pair2']; pair1_name = f"{pair1_tuple[0]}/{pair1_tuple[1]}"; pair2_name = f"{pair2_tuple[0]}/{pair2_tuple[1]}"
                if pair1_name not in standings or pair2_name not in standings: continue
                standings[pair1_name]['JG'] += s1; standings[pair1_name]['JR'] += s2; standings[pair2_name]['JG'] += s2; standings[pair2_name]['JR'] += s1
                if match_id not in processed_match_ids_for_stats:
                    standings[pair1_name]['PJ'] += 1; standings[pair2_name]['PJ'] += 1
                    if s1 > s2:   standings[pair1_name]['PG'] += 1; standings[pair2_name]['PP'] += 1
                    elif s2 > s1: standings[pair1_name]['PP'] += 1; standings[pair2_name]['PG'] += 1
                    else:         standings[pair1_name]['PE'] += 1; standings[pair2_name]['PE'] += 1
                    processed_match_ids_for_stats.add(match_id)
    for name in pair_names: standings[name]['DG'] = standings[name]['JG'] - standings[name]['JR']
    sorted_pair_names = sorted(pair_names, key=lambda name: (standings[name]['PG'], standings[name]['DG'], standings[name]['JG']), reverse=True)
    return standings, sorted_pair_names

# --- Funciones de Formateo y UI Auxiliares (sin cambios) ---
def generate_standings_text(standings_data, sorted_keys, tournament_name, is_pairs=False):
    entity_label = "Pareja" if is_pairs else "Jugador"; header = f"--- CLASIFICACIÓN: {tournament_name} ({entity_label}) ---\n"; separator = "-"*75+"\n"; col_headers = f"{'Pos':<4} {entity_label:<30} {'PJ':<4} {'PG':<4} {'PE':<4} {'PP':<4} {'JG':<6} {'JR':<6} {'DG':<6}\n"
    lines = [header, separator, col_headers, separator]
    for i, key in enumerate(sorted_keys):
        stats = standings_data.get(key, {}); lines.append(f"{i+1:<4} {key:<30} {stats.get('PJ',0):<4} {stats.get('PG',0):<4} {stats.get('PE',0):<4} {stats.get('PP',0):<4} {stats.get('JG',0):<6} {stats.get('JR',0):<6} {stats.get('DG',0):<6}\n")
    lines.append(separator); return "".join(lines)

def display_player_inputs(num_players_to_show):
    player_names_inputs = {}; st.subheader("Nombres Jugadores"); cols_players = st.columns(3)
    for i in range(num_players_to_show):
        default_name = st.session_state.player_inputs.get(i, f"Jugador {i+1}"); player_name = cols_players[i%3].text_input(f"Jugador {i+1}", value=default_name, key=f"player_{i}")
        player_names_inputs[i] = player_name; st.session_state.player_inputs[i] = player_name
    return player_names_inputs

# --- Interfaz Principal de Streamlit ---

st.set_page_config(page_title="Gestor Torneos Pádel", layout="wide"); st.title("🏓 Gestor de Torneos de Pádel")

# --- Inicialización del Estado de Sesión (CORREGIDO) ---
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
    # --- CORRECCIÓN AQUÍ ---
    # 1. Identificar las claves a borrar
    score_keys_to_delete = [k for k in st.session_state.keys() if k.startswith('score1_') or k.startswith('score2_')]
    # 2. Borrar las claves en un bucle separado
    for k in score_keys_to_delete:
        if k in st.session_state: # Buena práctica verificar si aún existe
            del st.session_state[k]
    # --- FIN CORRECCIÓN ---


# --- FASE 0: Configuración Base (sin cambios) ---
if st.session_state.app_phase == 'config_base':
    st.header("1. Configuración Base");
    with st.form("base_config_form"):
        conf_name = st.text_input("Nombre Torneo", st.session_state.config.get('name',"Torneo Pádel")); col1,col2=st.columns(2)
        with col1: conf_num_players = st.number_input("Nº Jugadores", 4, step=1, value=st.session_state.config.get('num_players', 8))
        with col2: conf_num_courts = st.number_input("Nº Pistas", 1, step=1, value=st.session_state.config.get('num_courts', 2))
        submitted = st.form_submit_button("Confirmar Configuración Base")
        if submitted:
            if conf_num_players < 4: st.error("Mínimo 4 jugadores.")
            else: st.session_state.config['name']=conf_name; st.session_state.config['num_players']=conf_num_players; st.session_state.config['num_courts']=conf_num_courts; st.session_state.app_phase='config_players'; st.rerun()

# --- FASE 1: Ingreso de Nombres (sin cambios) ---
elif st.session_state.app_phase == 'config_players':
    st.header("2. Ingreso Jugadores"); st.info(f"**Torneo:** {st.session_state.config.get('name')} | **Jugadores:** {st.session_state.config.get('num_players')} | **Pistas:** {st.session_state.config.get('num_courts')}")
    with st.form("player_entry_form"):
        num_players = st.session_state.config.get('num_players',0); display_player_inputs(num_players)
        submitted = st.form_submit_button("Confirmar Jugadores y Continuar")
        if submitted:
            players = [st.session_state.player_inputs.get(i,"").strip() for i in range(num_players)]; players = [p for p in players if p]; valid=True
            if len(players)!=num_players: st.error(f"{num_players} nombres esperados, {len(players)} encontrados."); valid=False
            elif len(set(players))!=len(players): st.error("Nombres duplicados."); valid=False
            if valid: st.session_state.players=players; st.session_state.app_phase='config_pairing'; st.rerun()
    st.divider();
    if st.button("⬅️ Volver Config Base"): st.session_state.app_phase='config_base'; st.rerun()

# --- FASE 2: Configuración Formato y Parejas (sin cambios lógicos) ---
elif st.session_state.app_phase == 'config_pairing':
    st.header("3. Formato y Parejas"); st.info(f"**Torneo:** {st.session_state.config.get('name')} | **Jugadores ({len(st.session_state.players)}):** {', '.join(st.session_state.players)} | **Pistas:** {st.session_state.config.get('num_courts')}")
    ttype = st.radio("Selecciona formato:", (TOURNAMENT_TYPE_AMERICANO, TOURNAMENT_TYPE_PAREJAS_FIJAS), key='tt_radio', horizontal=True, index=0 if st.session_state.tournament_type!=TOURNAMENT_TYPE_PAREJAS_FIJAS else 1); st.session_state.tournament_type=ttype
    if ttype == TOURNAMENT_TYPE_PAREJAS_FIJAS:
        if len(st.session_state.players)%2!=0: st.error(f"Nº par requerido ({len(st.session_state.players)}) para Parejas Fijas.");
        else:
            st.subheader("Config Parejas"); pmethod = st.radio("Formar parejas?", (PAIRING_METHOD_RANDOM, PAIRING_METHOD_MANUAL), key='pm_radio', horizontal=True, index=0 if st.session_state.pairing_method!=PAIRING_METHOD_MANUAL else 1); st.session_state.pairing_method=pmethod
            if pmethod == PAIRING_METHOD_MANUAL:
                st.markdown("**Asigna jugadores:**"); n_pairs=len(st.session_state.players)//2; pot_p=['']+list(st.session_state.players); cols=st.columns(2)
                with st.form("man_pairs_form"):
                    valid=True; c_pairs={}; c_assigned=set()
                    for i in range(n_pairs):
                        k=f"mp_{i}"; s1=st.session_state.manual_pair_selections.get(f"{k}_p1",''); s2=st.session_state.manual_pair_selections.get(f"{k}_p2",'')
                        op1=['']+[p for p in pot_p[1:] if p not in c_assigned or p==s1]; idx1=op1.index(s1) if s1 in op1 else 0; n_s1=cols[0].selectbox(f"P{i+1}-J1",op1,key=f"{k}_p1s",index=idx1); st.session_state.manual_pair_selections[f"{k}_p1"]=n_s1
                        tmp_ass=c_assigned.copy();
                        if n_s1:tmp_ass.add(n_s1)
                        op2=['']+[p for p in pot_p[1:] if p not in tmp_ass or p==s2]; idx2=op2.index(s2) if s2 in op2 else 0; n_s2=cols[1].selectbox(f"P{i+1}-J2",op2,key=f"{k}_p2s",index=idx2); st.session_state.manual_pair_selections[f"{k}_p2"]=n_s2
                        if n_s1 and n_s2:
                            if n_s1==n_s2: st.warning(f"P{i+1}: Diferentes."); valid=False
                            else: c_pairs[i]=tuple(sorted((n_s1,n_s2))); c_assigned.add(n_s1); c_assigned.add(n_s2)
                        elif n_s1 or n_s2: st.warning(f"P{i+1}: Ambos."); valid=False
                    submitted = st.form_submit_button("Confirmar y Generar Fixture")
                    if submitted:
                        f_pairs=list(c_pairs.values()); f_assigned=set(p for pair in f_pairs for p in pair)
                        if not valid: st.error("Corrige errores.")
                        elif len(f_pairs)!=n_pairs: st.error(f"Completa {n_pairs} parejas.")
                        elif len(f_assigned)!=len(st.session_state.players): st.error(f"No asignados todos ({len(f_assigned)}/{len(st.session_state.players)}).")
                        elif len(set(f_pairs))!=len(f_pairs): st.error("Parejas duplicadas.")
                        else:
                            st.session_state.pairs=f_pairs; st.session_state.fixture=generate_round_robin_pairs_fixture(st.session_state.pairs,st.session_state.config['num_courts'])
                            if st.session_state.fixture and st.session_state.fixture.get('rounds'): st.session_state.app_phase='viewing'; st.success("OK"); st.rerun()
                            else: st.error("Error generando fixture RR.")
            elif pmethod == PAIRING_METHOD_RANDOM:
                st.markdown("**Sorteo aleatorio.**")
                if st.button("Sortear y Generar Fixture"):
                    pl=list(st.session_state.players); random.shuffle(pl); r_pairs=[tuple(sorted((pl[i],pl[i+1]))) for i in range(0,len(pl),2)]
                    if len(r_pairs)==len(st.session_state.players)//2:
                         st.session_state.pairs=r_pairs; st.success("Parejas:"); [st.write(f"- {p1}/{p2}") for p1,p2 in st.session_state.pairs]
                         st.session_state.fixture=generate_round_robin_pairs_fixture(st.session_state.pairs,st.session_state.config['num_courts'])
                         if st.session_state.fixture and st.session_state.fixture.get('rounds'): st.session_state.app_phase='viewing'; st.success("Fixture RR OK"); st.rerun()
                         else: st.error("Error generando fixture RR post-sorteo.")
                    else: st.error("Error sorteo.")
    elif ttype == TOURNAMENT_TYPE_AMERICANO:
        st.markdown("**Parejas rotativas aleatorias.**")
        if st.button("Generar Fixture Americano"):
            st.session_state.fixture=generate_americano_fixture(st.session_state.players,st.session_state.config['num_courts'])
            if st.session_state.fixture and st.session_state.fixture.get('rounds'): st.session_state.app_phase='viewing'; st.success("Fixture Americano OK"); st.rerun()
            else: st.error("Error generando fixture Americano.")
    st.divider();
    if st.button("⬅️ Volver Ingreso Jugadores"): st.session_state.app_phase='config_players'; st.session_state.tournament_type=None; st.session_state.pairing_method=None; st.session_state.pairs=[]; st.session_state.manual_pair_selections={}; st.rerun()

# --- FASE 3: Visualización del Torneo (CORRECCIÓN en st.number_input value) ---
elif st.session_state.app_phase == 'viewing':
    st.header(f"🏆 Torneo: {st.session_state.config.get('name', 'Sin Nombre')}")
    tournament_mode_display = st.session_state.get('tournament_type', 'Desconocido')
    st.subheader(f"Formato: {tournament_mode_display}")

    if tournament_mode_display == TOURNAMENT_TYPE_PAREJAS_FIJAS:
        st.write("**Parejas:**"); num_pairs_display = len(st.session_state.get('pairs', []))
        pair_cols = st.columns(min(3, num_pairs_display) if num_pairs_display > 0 else 1)
        for i, pair_tuple in enumerate(st.session_state.get('pairs', [])): p1, p2 = pair_tuple; pair_cols[i % len(pair_cols)].write(f"- {p1} / {p2}")
        st.caption(f"{len(st.session_state.players)} jugadores | {st.session_state.config.get('num_courts', '?')} pistas")
    elif tournament_mode_display == TOURNAMENT_TYPE_AMERICANO:
         st.caption(f"{len(st.session_state.players)} jugadores | {st.session_state.config.get('num_courts', '?')} pistas | Parejas rotativas")

    standings_data, sorted_keys = {}, []; is_classification_pairs = (st.session_state.tournament_type == TOURNAMENT_TYPE_PAREJAS_FIJAS)
    if st.session_state.fixture and 'rounds' in st.session_state.fixture:
        if is_classification_pairs:
            if 'pairs' in st.session_state and st.session_state.pairs: standings_data, sorted_keys = calculate_standings_pairs(st.session_state.pairs, st.session_state.fixture)
            else: st.error("Error: No se encontraron parejas para calcular clasificación.")
        else:
            if 'players' in st.session_state and st.session_state.players: standings_data, sorted_keys = calculate_standings_americano(st.session_state.players, st.session_state.fixture)
            else: st.error("Error: No se encontraron jugadores para calcular clasificación.")
    else: st.error("Error crítico: No se encontró fixture válido."); st.stop()

    tab1, tab2 = st.tabs(["📝 Rondas y Resultados", "📊 Clasificación"])
    with tab1:
        st.subheader("Partidos por Ronda")
        if not st.session_state.fixture or not st.session_state.fixture.get('rounds'): st.warning("No hay rondas generadas.")
        else:
            # Asegurar que las rondas estén ordenadas por número de ronda si no lo están ya
            sorted_rounds = sorted(st.session_state.fixture['rounds'], key=lambda r: r.get('round_num', 0))
            round_tabs = st.tabs([f"Ronda {r.get('round_num', '?')}" for r in sorted_rounds])
            for i, round_data in enumerate(sorted_rounds):
                with round_tabs[i]:
                    st.markdown(f"**Ronda {round_data.get('round_num', '?')}**")
                    if round_data.get('resting'): resting_label = "Descansan" ; st.caption(f"{resting_label}: {', '.join(round_data['resting'])}") # Simplificado
                    if not round_data.get('matches'): st.info("No hay partidos en esta ronda."); continue
                    for match_idx, match in enumerate(round_data.get('matches', [])):
                        if 'pair1' not in match or 'pair2' not in match: continue
                        p1_tuple, p2_tuple = match['pair1'], match['pair2']
                        if not (isinstance(p1_tuple, (list, tuple)) and len(p1_tuple)==2 and isinstance(p2_tuple, (list, tuple)) and len(p2_tuple)==2): continue
                        p1_name, p2_name = f"{p1_tuple[0]}/{p1_tuple[1]}", f"{p2_tuple[0]}/{p2_tuple[1]}"
                        col_match, col_score1, col_score2 = st.columns([3, 1, 1])
                        with col_match: st.markdown(f"**Pista {match.get('court', '?')}**: {p1_name} **vs** {p2_name}")
                        match_id = f"r{round_data.get('round_num', '?')}_m{match_idx}"; score1_key, score2_key = f"score1_{match_id}", f"score2_{match_id}"
                        # --- CORRECCIÓN AQUÍ: Usar .get(key, 0) para valor inicial ---
                        with col_score1:
                            st.number_input(f"G {p1_name}", 0, key=score1_key, step=1, format="%d", label_visibility="collapsed", value=st.session_state.get(score1_key, 0)) # Valor por defecto 0
                        with col_score2:
                            st.number_input(f"G {p2_name}", 0, key=score2_key, step=1, format="%d", label_visibility="collapsed", value=st.session_state.get(score2_key, 0)) # Valor por defecto 0
                        # --- FIN CORRECCIÓN ---
                        st.divider()
    with tab2:
        st.subheader(f"Tabla de Clasificación ({'Parejas' if is_classification_pairs else 'Individual'})")
        if not standings_data or not sorted_keys: st.info("Aún no hay resultados.")
        else:
             standings_list = []; entity_label = "Pareja" if is_classification_pairs else "Jugador"
             for pos, key in enumerate(sorted_keys):
                 stats = standings_data.get(key, {}); row = {"Pos": pos + 1, entity_label: key}
                 row.update({'PJ': stats.get('PJ', 0), 'PG': stats.get('PG', 0), 'PE': stats.get('PE', 0), 'PP': stats.get('PP', 0), 'JG': stats.get('JG', 0), 'JR': stats.get('JR', 0), 'DG': stats.get('DG', 0)})
                 standings_list.append(row)
             df_standings = pd.DataFrame(standings_list); cols_to_show = ['Pos', entity_label, 'PJ', 'PG', 'PE', 'PP', 'JG', 'JR', 'DG']
             cols_exist = [col for col in cols_to_show if col in df_standings.columns]; df_display = df_standings[cols_exist]
             if 'Pos' in df_display.columns: st.dataframe(df_display.set_index('Pos'), use_container_width=True)
             else: st.dataframe(df_display, use_container_width=True)
             st.download_button(f"📄 Descargar Clasificación ({entity_label}) (.txt)", generate_standings_text(standings_data, sorted_keys, st.session_state.config.get('name', 'Torneo'), is_classification_pairs), f"clasificacion_{st.session_state.config.get('name', 'torneo').replace(' ', '_')}_{entity_label.lower()}.txt", 'text/plain')

    st.divider()
    if st.button("⚠️ Empezar Nuevo Torneo (Borrar Todo)"):
        keys_to_delete = list(st.session_state.keys());
        for key in keys_to_delete: del st.session_state[key]
        st.rerun()