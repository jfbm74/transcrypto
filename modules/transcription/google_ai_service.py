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
        
        # Crear el prompt para el modelo
        prompt = f"""
        Por favor, convierte la siguiente transcripción en un acta de reunión formal. 

        Formato esperado:
        1. Título "ACTA DE REUNIÓN"
        2. Fecha y hora (extráelas del contenido si es posible, si no están, usa "No especificado")
        3. Asistentes (usa roles o nombres si están presentes en la conversación, sino "No especificado")
        4. Orden del día (temas principales agrupados temáticamente)
        5. Desarrollo (resumen por temas tratados, sin omitir detalles relevantes)
        6. Acuerdos y compromisos (extrae **todos los compromisos concretos**, responsables y fechas si se mencionan)
        7. Conclusión (resumen de lo acordado con énfasis en próximos pasos)

        Aquí está la transcripción:
        
        {transcription}
        """
        
        # Generar la respuesta
        response = model.generate_content(prompt)
        
        # Obtener el texto generado
        acta_text = response.text
        
        return {"success": True, "acta": acta_text}
    
    except Exception as e:
        current_app.logger.error(f"Error al generar el acta con Google AI: {str(e)}")
        return {"success": False, "error": str(e)}