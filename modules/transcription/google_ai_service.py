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
        response = model.generate_content(prompt, generation_config=generation_config)
        
        # Obtener el texto generado
        acta_text = response.text
        
        current_app.logger.info("Acta generada exitosamente con Google AI (Gemini)")
        
        return {"success": True, "acta": acta_text, "provider": "Google AI (Gemini)"}
    
    except Exception as e:
        current_app.logger.error(f"Error al generar el acta con Google AI: {str(e)}")
        return {"success": False, "error": str(e), "provider": "Google AI (Gemini)"}

def extract_requirements_with_google(transcription):
    """Extrae requerimientos funcionales, no funcionales y RFC a partir de una transcripción usando Google AI"""
    try:
        # Inicializar el cliente
        initialize_google_ai_client()
        
        # Configurar el modelo - usar un modelo adecuado para textos extensos
        model = genai.GenerativeModel('gemini-1.5-pro')

        # Configuración optimizada para análisis de requisitos preciso
        generation_config = {
            "temperature": 0.1,        # Temperatura muy baja para respuestas precisas y estructuradas
            "top_p": 0.95,             # Filtrado de probabilidad conservador
            "top_k": 40,               # Considerar un buen rango de tokens
            "max_output_tokens": 8192, # Asegurar suficiente espacio para una respuesta detallada
        }
        
        # Crear el prompt para el modelo
        prompt = f"""
        Actúa como un ingeniero de requerimientos experimentado especializado en análisis y documentación de requisitos de software. Tu tarea es analizar la siguiente transcripción de reunión y extraer todos los requerimientos del sistema mencionados.

        INSTRUCCIONES ESPECÍFICAS:
        1. Analiza minuciosamente la transcripción completa, sin omitir ninguna información relevante.
        2. Identifica y categoriza claramente todos los requerimientos mencionados (explícita o implícitamente).
        3. Distingue entre requerimientos funcionales, no funcionales y restricciones.
        4. Asigna prioridades basadas en el énfasis y contexto de la discusión (Alta/Media/Baja).
        5. Detecta posibles conflictos o ambigüedades entre los requerimientos.
        6. Captura criterios de aceptación cuando se mencionen.
        7. Identifica stakeholders relacionados con cada requerimiento.

        FORMATO DEL DOCUMENTO DE REQUERIMIENTOS:
        1. TÍTULO: "DOCUMENTO DE ESPECIFICACIÓN DE REQUERIMIENTOS"
        2. INFORMACIÓN GENERAL:
           - Fecha de extracción
           - Fuente (transcripción de reunión)
           - Contexto del proyecto (extraído de la transcripción)
        3. STAKEHOLDERS IDENTIFICADOS:
           - Lista de personas mencionadas y sus roles/intereses
        4. REQUERIMIENTOS FUNCIONALES:
           - ID único (RF-XX)
           - Descripción clara y precisa
           - Prioridad asignada
           - Stakeholder(s) relacionado(s)
           - Criterios de aceptación (si se mencionan)
           - Dependencias con otros requerimientos (si existen)
        5. REQUERIMIENTOS NO FUNCIONALES:
           - ID único (RNF-XX)
           - Categoría (Rendimiento, Seguridad, Usabilidad, etc.)
           - Descripción clara y métrica cuando sea posible
           - Prioridad asignada
           - Justificación (extraída del contexto)
        6. RESTRICCIONES TÉCNICAS Y DE NEGOCIO:
           - ID único (RT-XX/RN-XX)
           - Descripción
           - Impacto en el proyecto
        7. SOLICITUDES DE CAMBIO (RFC):
           - ID único (RFC-XX)
           - Descripción del cambio propuesto
           - Justificación
           - Impacto estimado
           - Prioridad sugerida
        8. SUPUESTOS Y DEPENDENCIAS:
           - Lista de supuestos extraídos de la transcripción
           - Dependencias externas identificadas
        9. GLOSARIO DE TÉRMINOS:
           - Términos técnicos o de dominio mencionados en la transcripción
           - Definiciones extraídas del contexto
        10. PUNTOS DE AMBIGÜEDAD:
            - Aspectos que requieren clarificación adicional
            - Posibles conflictos entre requerimientos

        TRANSCRIPCIÓN:
        {transcription}

        Importante: Sé metódico y exhaustivo. Cada requerimiento debe ser atómico, consistente, verificable y rastreable. Utiliza un lenguaje claro y preciso. Evita interpretaciones subjetivas y céntrate en las necesidades explícitas e implícitas mencionadas en la transcripción. El documento debe permitir a un equipo de desarrollo comprender completamente lo que se necesita construir.
        """
        
        # Generar la respuesta
        response = model.generate_content(prompt, generation_config=generation_config)
        
        # Obtener el texto generado
        requirements_doc = response.text
        
        current_app.logger.info("Documento de requerimientos generado exitosamente con Google AI (Gemini)")
        
        return {"success": True, "requirements_doc": requirements_doc, "provider": "Google AI (Gemini)"}
    
    except Exception as e:
        current_app.logger.error(f"Error al generar documento de requerimientos con Google AI: {str(e)}")
        return {"success": False, "error": str(e), "provider": "Google AI (Gemini)"}