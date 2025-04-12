import google.generativeai as genai
from flask import current_app

def initialize_google_ai_client():
    """Inicializa el cliente de Google AI con la clave API configurada"""
    api_key = current_app.config.get('GOOGLE_AI_API_KEY', '')
    
    if not api_key:
        raise ValueError("No se ha configurado la clave de API de Google AI")
    
    genai.configure(api_key=api_key)
    current_app.logger.info("Cliente Google AI inicializado correctamente")
    return True

def generate_meeting_minutes_with_google(transcription):
    """Genera un acta de reunión basada en la transcripción usando Google AI"""
    try:
        # Inicializar el cliente
        initialize_google_ai_client()
        
        # Configurar el modelo - usar un modelo adecuado para textos extensos
        model = genai.GenerativeModel('gemini-1.5-pro')

        # Configuración optimizada para generar actas más detalladas
        generation_config = {
            "temperature": 0.2,        # Temperatura más baja para respuestas más precisas y menos creativas
            "top_p": 0.95,             # Filtrado de probabilidad conservador
            "top_k": 40,               # Considerar un buen rango de tokens
            "max_output_tokens": 8192, # Asegurar suficiente espacio para una respuesta detallada
        }
        
        # Crear el prompt para el modelo
        prompt = f"""
        Actúa como un secretario profesional especializado en la redacción de actas de reuniones empresariales. Tu tarea es transformar la siguiente transcripción en un acta formal, detallada y completa.

        INSTRUCCIONES ESPECÍFICAS:
        1. Analiza minuciosamente la transcripción completa, sin omitir ninguna sección relevante.
        2. Identifica todas las personas mencionadas y su rol en la conversación.
        3. Extrae explícitamente TODOS los compromisos, acuerdos y tareas asignadas, incluyendo responsables y fechas límite.
        4. Preserva el nivel de detalle técnico cuando sea importante para los acuerdos.
        5. Identifica los puntos de debate y las diferentes posiciones tomadas en la reunión.
        6. Organiza la información por temas, manteniendo una estructura clara.

        FORMATO DEL ACTA:
        1. TÍTULO: "ACTA DE REUNIÓN" seguido del tema principal.
        2. INFORMACIÓN GENERAL:
        - Fecha y hora (extráela de la transcripción, o indica "No especificada")
        - Duración aproximada (si se puede deducir)
        - Modalidad (presencial/virtual, si se menciona)
        3. ASISTENTES: Lista completa con nombres y cargos/roles.
        4. ORDEN DEL DÍA: Enumera todos los temas principales tratados.
        5. DESARROLLO:
        - Divide por secciones temáticas
        - Resume cada tema tratado incluyendo discusiones, opiniones y conclusiones
        - Incluye citas textuales relevantes cuando sea apropiado
        6. ACUERDOS Y COMPROMISOS:
        - Enumera TODOS los compromisos concretos adquiridos
        - Especifica claramente el responsable de cada tarea
        - Incluye fechas límite si se mencionan
        - Destaca cualquier entregable específico acordado
        7. CONCLUSIONES:
        - Resumen ejecutivo de los resultados de la reunión
        - Próximos pasos claramente definidos

        TRANSCRIPCIÓN:
        {transcription}

        Importante: No omitas ningún detalle relevante. El acta debe ser lo suficientemente completa como para que alguien que no asistió a la reunión pueda entender todos los temas tratados, acuerdos tomados y compromisos adquiridos.
        """
        
        # Generar la respuesta
        response = model.generate_content(prompt)
        
        # Obtener el texto generado
        acta_text = response.text
        
        current_app.logger.info("Acta generada exitosamente con Google AI (Gemini)")
        
        return {"success": True, "acta": acta_text, "provider": "Google AI (Gemini)"}
    
    except Exception as e:
        current_app.logger.error(f"Error al generar el acta con Google AI: {str(e)}")
        return {"success": False, "error": str(e), "provider": "Google AI (Gemini)"}