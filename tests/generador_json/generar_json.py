import re
import json
import os
from pathlib import Path
import fitz  # PyMuPDF

ENTRADA = "entrada"
SALIDA = "salida"

def extraer_texto_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    texto = ""
    for pagina in doc:
        texto += pagina.get_text()
    return texto

def extraer_respuestas_correctas(texto):
    correctas = {}
    bloques = re.findall(r'PREGUNTAS\s+RESPUESTAS(.*?)\n\n', texto, re.DOTALL | re.IGNORECASE)

    for bloque in bloques:
        lineas = bloque.strip().splitlines()
        for linea in lineas:
            match = re.match(r'(\d+)\s+([a-cA-C])', linea)
            if match:
                num = int(match.group(1))
                letra = match.group(2).lower()
                correctas[num] = letra
    return correctas

def parsear_preguntas(texto, respuestas_correctas):
    preguntas = []
    lineas = texto.splitlines()

    pregunta_actual = None
    respuestas_actuales = []
    numero_actual = None

    for linea in lineas:
        linea = linea.strip()

        #match_pregunta = re.match(r'^(\d+)\.\-\s*(.+)', linea)
        #match_pregunta = re.match(r'^(\d+)\)\s*(.+)', linea)
        #match_pregunta = re.match(r'^(\d+)(?:\.\-|\))\s*(.+)', linea)
        match_pregunta = re.match(r'^(\d+)(?:\.\-|\)|\.)\s*(.+)', linea)
        if match_pregunta:
            if pregunta_actual and respuestas_actuales and numero_actual:
                letra_correcta = respuestas_correctas.get(numero_actual, "a")
                idx_correcto = ord(letra_correcta) - ord("a")
                preguntas.append({
                    "number": numero_actual,
                    "question": pregunta_actual,
                    "options": respuestas_actuales,
                    "answer_index": idx_correcto
                })

            numero_actual = int(match_pregunta.group(1))
            pregunta_actual = match_pregunta.group(2)
            respuestas_actuales = []
            continue

        match_respuesta = re.match(r'^([a-cA-C])\)\s*(.+)', linea)
        if match_respuesta:
            respuestas_actuales.append(match_respuesta.group(2))
            continue

        if respuestas_actuales:
            respuestas_actuales[-1] += ' ' + linea
        elif pregunta_actual:
            pregunta_actual += ' ' + linea

    # Guardar la última pregunta
    if pregunta_actual and respuestas_actuales and numero_actual:
        letra_correcta = respuestas_correctas.get(numero_actual, "a")
        idx_correcto = ord(letra_correcta) - ord("a")
        preguntas.append({
            "number": numero_actual,
            "question": pregunta_actual,
            "options": respuestas_actuales,
            "answer_index": idx_correcto
        })

    return preguntas

def main():
    Path(SALIDA).mkdir(exist_ok=True)
    preguntas_totales = 0
    preguntas_sin_respuesta = []

    if not os.path.exists(ENTRADA):
        print(f"❌ La carpeta '{ENTRADA}' no existe. Crea esa carpeta y mete los PDFs.")
        return

    for archivo in os.listdir(ENTRADA):
        if archivo.endswith(".pdf"):
            ruta_pdf = os.path.join(ENTRADA, archivo)
            texto = extraer_texto_pdf(ruta_pdf)

            respuestas_correctas = extraer_respuestas_correctas(texto)
            preguntas = parsear_preguntas(texto, respuestas_correctas)

            preguntas.sort(key=lambda x: x["number"])  # Ordenar por número
            
            for idx, pregunta in enumerate(preguntas, start=1):
                pregunta["number"] = idx
            
            for pregunta in preguntas:
                numero_pregunta = pregunta["number"]
                if numero_pregunta not in respuestas_correctas:
                    preguntas_sin_respuesta.append(numero_pregunta)

            nombre_json = Path(archivo).stem.lower().replace(" ", "_") + ".json"
            ruta_salida = os.path.join(SALIDA, nombre_json)

            with open(ruta_salida, "w", encoding="utf-8") as f:
                json.dump(preguntas, f, indent=4, ensure_ascii=False)

            preguntas_totales += len(preguntas)
            print(f"✅ Generado: {ruta_salida} ({len(preguntas)} preguntas)")

    if preguntas_sin_respuesta:
        print(f"\n⚠️ ¡Advertencia! Algunas preguntas no tienen respuesta en la tabla:")
        for num in preguntas_sin_respuesta:
            print(f"  - Pregunta {num}")

    print(f"\n✔️ Total de preguntas procesadas: {preguntas_totales}")

if __name__ == "__main__":
    main()
