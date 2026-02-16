# Alexa Skill: Comida del Día

Skill de Alexa que lee tu plan de comidas semanal desde Google Sheets y te dice qué hay de comer y cenar cada día. Sin librerías de Google — solo descarga el CSV con `urllib`.

## Cómo funciona

1. Dices **"Alexa, abre comida del día"**
2. Te dice qué hay hoy de comida y cena
3. Pregunta si quieres consultar otro día
4. Puedes decir "mañana", "viernes", "pasado mañana", etc.
5. Di "ninguno", "nada" o "no" para salir

## Requisitos previos

- Tu Google Sheet debe ser **público** (o "cualquiera con el enlace puede ver")
  - Archivo > Compartir > Cambiar a "Cualquiera con el enlace"
- Una cuenta de Amazon Developer: https://developer.amazon.com/alexa/console

## Configuración

En `lambda_function.py`, reemplaza `TU_SPREADSHEET_ID_AQUI` con el ID de tu Google Sheet.

El ID es la parte de la URL entre `/d/` y `/edit`:
```
https://docs.google.com/spreadsheets/d/ESTE_ES_TU_ID/edit#gid=0
```

## Estructura del spreadsheet esperada

| (vacío) | Comida | Cena |
|---------|--------|------|
| Lunes   | pasta  | sopa |
| Martes  | ...    | ...  |
| ...     | ...    | ...  |
| Domingo | ...    | ...  |
| Lunes   | ...    | ...  |  ← Semana 2 (opcional)
| ...     | ...    | ...  |

- La primera fila es la cabecera (se ignora)
- La columna A tiene el día de la semana
- Puedes dejar celdas vacías si un día no tiene comida o cena
- Si tienes varias semanas, se alternan automáticamente usando el número de semana ISO

## Despliegue

### 1. Crear la Skill en Alexa Developer Console

1. Ve a https://developer.amazon.com/alexa/console/ask
2. **Create Skill** > Nombre: "Comida del Día" > Locale: **Spanish (ES)** > Modelo: **Custom** > Hosting: **Alexa-hosted (Python)**
3. Click **Create Skill** > Template: **Start from Scratch**

### 2. Configurar el Interaction Model

1. En el panel izquierdo, ve a **JSON Editor** (dentro de "Interaction Model")
2. Pega el contenido de `interaction_model.json`
3. Click **Save Model** y luego **Build Model**

### 3. Subir el código Lambda

1. Ve a la pestaña **Code** en la consola de Alexa
2. Reemplaza el contenido de `lambda_function.py` con el archivo de este proyecto
3. Click **Save** y luego **Deploy**

### 4. Probar

1. Ve a la pestaña **Test**
2. Activa el testing en modo **Development**
3. Escribe o di: "Abre comida del día"

## Ejemplos de uso

- **"Alexa, abre comida del día"** → Te dice qué hay hoy y pregunta por otro día
- **"Mañana"** → Te dice comida y cena de mañana
- **"Viernes"** → Te dice lo del viernes
- **"Ninguno"** → Cierra la skill con "¡Buen provecho!"

## Notas sobre semanas múltiples

Si tu spreadsheet tiene varias semanas (el día "Lunes" aparece más de una vez), la skill alterna entre ellas usando el número de semana ISO (pares/impares).

Para usar siempre la primera semana, cambia en `lambda_function.py`:
```python
week_index = 0  # Siempre usar la primera semana
```
