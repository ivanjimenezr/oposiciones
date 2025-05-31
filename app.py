import streamlit as st
import json
import os
import random

TESTS_FOLDER = "tests"

# Cargar tests disponibles
test_files = [f for f in os.listdir(TESTS_FOLDER) if f.endswith(".json")]
test_names = [os.path.splitext(f)[0].capitalize() for f in test_files]
test_map = dict(zip(test_names, test_files))

st.title("🧠 Test Ayuntamiento de Madrid")
selected_test = st.selectbox("Selecciona un test:", test_names)

# Reiniciar estado si se cambia de test
if st.session_state.get("test") != selected_test:
    with open(os.path.join(TESTS_FOLDER, test_map[selected_test]), "r", encoding="utf-8") as f:
        questions = json.load(f)
        random.shuffle(questions)
        st.session_state.shuffled_questions = questions
    st.session_state.test = selected_test
    st.session_state.current = 0
    st.session_state.score = 0
    st.session_state.correct = None
    st.session_state[f"answered_{0}"] = False

questions = st.session_state.shuffled_questions
current = st.session_state.current

# Si aún hay preguntas
if current < len(questions):
    q = questions[current]
    st.subheader(f"Pregunta {current + 1} de {len(questions)}")
    st.write(q["question"])

    letras = ["a", "b", "c", "d", "e", "f"]
    opciones_marcadas = [f"{letras[i]}) {op}" for i, op in enumerate(q["options"])]

    selected = st.radio("Elige una respuesta:", opciones_marcadas, key=f"q{current}")

    if not st.session_state.get(f"answered_{current}", False):
        if st.button("Responder", key=f"responder_{current}"):
            # Extraer texto real de la opción elegida (quitando la letra)
            texto_elegido = selected.split(") ", 1)[1]
            idx = q["options"].index(texto_elegido)
            is_correct = idx == q["answer_index"]
            st.session_state.correct = is_correct
            st.session_state[f"answered_{current}"] = True
            if is_correct:
                st.session_state.score += 1
            st.rerun()
    else:
        if st.session_state.correct:
            st.success("✅ ¡Correcto!")
        else:
            respuesta_correcta = q["options"][q["answer_index"]]
            letra_correcta = letras[q["answer_index"]]
            st.error(f"❌ Incorrecto. La respuesta correcta era: {letra_correcta}) {respuesta_correcta}")

        if current < len(questions) - 1:
            if st.button("Siguiente"):
                st.session_state.current += 1
                st.session_state.correct = None
                st.session_state[f"answered_{st.session_state.current}"] = False
                st.rerun()
        else:
            st.balloons()
            st.success("🎉 ¡Has terminado el test!")
            st.write(f"Tu puntuación final: **{st.session_state.score} / {len(questions)}**")
            if st.button("Volver a empezar"):
                del st.session_state.test
                st.rerun()
