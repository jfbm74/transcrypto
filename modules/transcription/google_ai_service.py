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

# Mantener la función original para compatibilidad con el código existente
def generate_meeting_minutes_with_google(transcription):
    """
    Función de compatibilidad que llama a extract_requirements_with_google
    Esta función se mantiene para evitar errores de importación en el código existente
    """
    current_app.logger.info("Llamada a función heredada generate_meeting_minutes_with_google, redirigiendo a extract_requirements_with_google")
    result = extract_requirements_with_google(transcription)
    
    # Adaptar el resultado para mantener la estructura de respuesta esperada
    if result["success"]:
        return {
            "success": True,
            "acta": result["requirements_doc"],  # Mantener la clave 'acta' para compatibilidad
            "provider": "Google AI (Gemini)"
        }
    else:
        return result