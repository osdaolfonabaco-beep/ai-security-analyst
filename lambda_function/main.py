import boto3
import os
import gzip
import json
import re
from collections import defaultdict

# --- Clientes de AWS ---
s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# --- Constantes y Configuración ---
IP_REGEX = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
# VAMOS A CORREGIR ESTA LÍNEA. Bajamos el umbral a 15 para nuestra prueba.
SUSPICIOUS_REQUEST_THRESHOLD = 15
LOG_CONTEXT_LINES = 20

def handler(event, context):
    """
    Función Lambda activada por S3 que analiza logs de acceso,
    identifica IPs sospechosas y utiliza Amazon Bedrock (IA)
    para realizar un análisis de ciberseguridad.
    """
    print("Iniciando el Analista de Seguridad Aumentado por IA...")

    try:
        # 1. Obtener el bucket y el nombre del archivo del evento
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        file_key = event['Records'][0]['s3']['object']['key']
        print(f"Nuevo archivo detectado: s3://{bucket_name}/{file_key}")

        # 2. Descargar y procesar el archivo de log
        download_path = f'/tmp/{os.path.basename(file_key)}'
        s3.download_file(bucket_name, file_key, download_path)
        print(f"Archivo descargado a {download_path}")

        ip_logs = defaultdict(list)
        ip_counts = defaultdict(int)

        open_func = gzip.open if download_path.endswith('.gz') else open
        with open_func(download_path, 'rt', encoding='utf-8') as f:
            for line in f:
                match = re.search(IP_REGEX, line)
                if match:
                    ip = match.group(1)
                    ip_counts[ip] += 1
                    if len(ip_logs[ip]) < LOG_CONTEXT_LINES:
                        ip_logs[ip].append(line.strip())

        print(f"Análisis inicial completado. Se encontraron {len(ip_counts)} IPs únicas.")

        # 3. Identificar IPs sospechosas y orquestar el análisis de IA
        final_report = []
        suspicious_ips = [ip for ip, count in ip_counts.items() if count > SUSPICIOUS_REQUEST_THRESHOLD]

        if not suspicious_ips:
            print("No se encontraron IPs que superen el umbral de sospecha. Misión cumplida.")
            return {'statusCode': 200, 'body': 'Análisis completado. Sin hallazgos notables.'}

        print(f"Detectadas {len(suspicious_ips)} IPs sospechosas. Enviando a análisis con IA...")

        for ip in suspicious_ips:
            print(f"--- Analizando IP: {ip} ---")

            context_logs = "\n".join(ip_logs[ip])
            prompt = f"""
                Eres un analista de ciberseguridad experto. Tu misión es analizar un conjunto de líneas de log de un servidor web asociadas a una única dirección IP y determinar la naturaleza de su actividad.

                **Dirección IP bajo análisis:** {ip}
                **Número total de solicitudes:** {ip_counts[ip]}

                **Muestra de Logs:**
                ```
                {context_logs}
                ```

                Basado en los logs proporcionados, responde ÚNICAMENTE en formato JSON con la siguiente estructura:
                {{
                    "ip_address": "{ip}",
                    "probable_attack_type": "...",
                    "confidence_level": "...",
                    "recommended_action": "..."
                }}

                **Instrucciones para los valores:**
                - "probable_attack_type": Identifica el patrón de ataque más probable. Opciones comunes son: 'Scanning/Reconnaissance', 'Brute-force Login', 'Web Scraping', 'SQL Injection Attempt', 'Path Traversal', 'Benign Traffic'. Si no estás seguro, usa 'Uncertain'.
                - "confidence_level": Describe tu nivel de confianza en el análisis. Usa uno de estos tres valores: 'Low', 'Medium', 'High'.
                - "recommended_action": Sugiere el siguiente paso práctico. Por ejemplo: 'Monitor further', 'Block IP at firewall', 'Investigate specific endpoint', 'No action needed'.
                """

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            })

            print(f"Enviando prompt a Bedrock para la IP: {ip}")

            response = bedrock.invoke_model(
                body=body,
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                accept='application/json',
                contentType='application/json'
            )

            response_body = json.loads(response.get('body').read())
            ai_response_text = response_body['content'][0]['text']

            print(f"Respuesta recibida de Bedrock: {ai_response_text}")

            try:
                analysis_result = json.loads(ai_response_text)
                final_report.append(analysis_result)
            except json.JSONDecodeError:
                print(f"ERROR: La respuesta de la IA para la IP {ip} no era un JSON válido.")
                final_report.append({
                    "ip_address": ip,
                    "error": "Failed to parse AI response."
                })

        print("\n--- INFORME FINAL DEL ANALISTA DE SEGURIDAD AUMENTADO POR IA ---")
        print(json.dumps(final_report, indent=2))
        print("----------------------------------------------------------------")

        return {
            'statusCode': 200,
            'body': json.dumps(final_report)
        }

    except Exception as e:
        print(f"ERROR CRÍTICO: Ha ocurrido un error inesperado en la ejecución. {str(e)}")
        raise e
