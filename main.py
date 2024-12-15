from fastapi import FastAPI, HTTPException, UploadFile
from mangum import Mangum
from models import ParticipantCreate, ParticipantResponse
from datetime import datetime
from uuid import uuid4
from fastapi.responses import JSONResponse
import mysql.connector
import logging
import boto3
import os

app = FastAPI()
handler = Mangum(app)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client('s3')
S3_BUCKET_NAME = 'aztlang-grappling-images'

@app.post("/participants")
async def register_participant(participant: ParticipantCreate):
    generated_id = uuid4()
    generated_id_str = str(generated_id)
    short_id = generated_id_str[:6]
    aztlan_id = f"{short_id}"

    try:
        # Conexión a MySQL
        cnx = mysql.connector.connect(
            host='database-aztlan.c5sk4swwkhp4.us-east-1.rds.amazonaws.com',
            user='admin',
            password='d4nt3r4d',
            database='database_aztlan'
        )
        cursor = cnx.cursor()

        query = """
        INSERT INTO participants (aztlan_id, name, birth_date, weight, academy, height, category, payment_proof, email, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            aztlan_id,
            participant.name, 
            participant.birth_date, 
            participant.weight, 
            participant.academy, 
            participant.height, 
            participant.category, 
            participant.payment_proof, 
            participant.email, 
            datetime.utcnow()
        ))

        cnx.commit()

        cursor.close()
        cnx.close()

        return JSONResponse(content={"message": "Participante registrado con éxito", "aztlan_id": aztlan_id}, status_code=201)

    except mysql.connector.Error as err:
        return JSONResponse(content={"error": f"Error de base de datos: {err}"}, status_code=500)

@app.get("/participants/{participant_id}", response_model=ParticipantResponse)
async def read_participant(participant_id: str):
    try:
        cnx = mysql.connector.connect(
            host='database-aztlan.c5sk4swwkhp4.us-east-1.rds.amazonaws.com',
            user='admin',
            password='d4nt3r4d',
            database='database_aztlan'
        )
        cursor = cnx.cursor(dictionary=True) 

        query = "SELECT * FROM participants WHERE aztlan_id = %s"
        cursor.execute(query, (participant_id,))
        db_participant = cursor.fetchone()

        if not db_participant:
            return JSONResponse(content={"message": f"Participante con ID {participant_id} no encontrado"}, status_code=404)

        cursor.close()
        cnx.close()

        return ParticipantResponse(**db_participant)

    except mysql.connector.Error as err:
        return JSONResponse(content={"error": f"Error de base de datos: {err}"}, status_code=500)

@app.get("/participants")
async def get_all_participants():
    try:
        cnx = mysql.connector.connect(
            host='database-aztlan.c5sk4swwkhp4.us-east-1.rds.amazonaws.com',
            user='admin',
            password='d4nt3r4d',
            database='database_aztlan'
        )
        cursor = cnx.cursor()

        query = "SELECT * FROM participants"
        cursor.execute(query)

        participants = cursor.fetchall()
        logger.info(f"Se encontraron {len(participants)} participantes en la base de datos.")

        participants_list = [
            {
                "id": row[0],
                "aztlan_id": row[1],
                "name": row[2],
                "birth_date": row[3],
                "weight": row[4],
                "academy": row[5],
                "height": row[6],
                "category": row[7],
                "payment_proof": row[8],
                "created_at": row[9]
            }
            for row in participants
        ]

        cursor.close()
        cnx.close()

        return participants_list

    except mysql.connector.Error as err:
        return JSONResponse(content={"error": f"Error de base de datos: {err}"}, status_code=500)

@app.delete("/participants/{participant_id}")
async def delete_participant(participant_id: str):
    logger.info(f"Eliminando participante con ID {participant_id}")
    try:
        cnx = mysql.connector.connect(
            host='database-aztlan.c5sk4swwkhp4.us-east-1.rds.amazonaws.com',
            user='admin',
            password='d4nt3r4d',
            database='database_aztlan'
        )
        cursor = cnx.cursor()

        select_query = "SELECT * FROM participants WHERE aztlan_id = %s"
        cursor.execute(select_query, (participant_id,))
        participant = cursor.fetchone()

        if not participant:
            logger.warning(f"Participante con ID {participant_id} no encontrado para eliminar")
            cursor.close()
            cnx.close()
            return JSONResponse(content={"message": "Participant not found"}, status_code=404)

        delete_query = "DELETE FROM participants WHERE aztlan_id = %s"
        cursor.execute(delete_query, (participant_id,))
        cnx.commit()

        logger.info(f"Participante con ID {participant_id} eliminado con éxito")

        cursor.close()
        cnx.close()

        return JSONResponse(content={"message": "Participante eliminado con éxito", "participant_id": participant_id}, status_code=200)

    except mysql.connector.Error as err:
        logger.error(f"Error al eliminar participante con ID {participant_id}: {err}")
        return JSONResponse(content={"error": f"Error de base de datos: {err}"}, status_code=500)

@app.post("/participants/{aztlan_id}/upload")
async def upload_payment_proof(
    aztlan_id: str,
    file: UploadFile,
):
    logger.info(f"Subiendo comprobante de pago para el participante {aztlan_id}")
    
    try:
        # Llamar a la función read_participant para obtener el participante
        participant_response = await read_participant(aztlan_id)
        
        # Si el participante no existe, se maneja aquí
        if isinstance(participant_response, JSONResponse) and participant_response.status_code == 404:
            logger.warning(f"Participante con ID {aztlan_id} no encontrado para subir comprobante")
            raise HTTPException(status_code=404, detail="Participant not found")

        # Comprobar el formato de archivo
        file_extension = os.path.splitext(file.filename)[1]
        if file_extension not in [".jpg", ".jpeg", ".png"]:
            logger.warning(f"Formato de archivo inválido: {file_extension}")
            raise HTTPException(status_code=400, detail="Invalid file format. Only JPG and PNG are allowed.")
        
        # Crear nombre único para el archivo
        unique_filename = f"comprobante-{aztlan_id}{file_extension}"

        # Subir archivo a S3
        try:
            s3_client.upload_fileobj(
                file.file,
                S3_BUCKET_NAME,
                unique_filename,
                ExtraArgs={"ContentType": file.content_type}
            )
            logger.info(f"Comprobante de pago subido exitosamente para el participante {aztlan_id}")
        except Exception as e:
            logger.error(f"Error al subir el archivo a S3: {e}")
            raise HTTPException(status_code=500, detail="Error uploading file to S3.")

        # Conexión a la base de datos para guardar la información directamente
        cnx = mysql.connector.connect(
            host='database-aztlan.c5sk4swwkhp4.us-east-1.rds.amazonaws.com',
            user='admin',
            password='d4nt3r4d',
            database='database_aztlan'
        )
        cursor = cnx.cursor()

        payment_proof_url = f"{unique_filename}"
        query = """
            INSERT INTO payments (aztlan_id, payment_proof, created_at)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (aztlan_id, payment_proof_url, datetime.utcnow()))
        cnx.commit()

        cursor.close()
        cnx.close()

        return JSONResponse(content={"message": "Payment proof uploaded and registered successfully"}, status_code=200)
    
    except Exception as e:
        logger.error(f"Error al subir comprobante de pago: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/participants/{aztlan_id}/payment-proof-url")
async def get_payment_proof_url(aztlan_id: str):
    try:
        cnx = mysql.connector.connect(
            host='database-aztlan.c5sk4swwkhp4.us-east-1.rds.amazonaws.com',
            user='admin',
            password='d4nt3r4d',
            database='database_aztlan'
        )
        cursor = cnx.cursor(dictionary=True)

        query = "SELECT payment_proof FROM payments WHERE aztlan_id = %s"
        cursor.execute(query, (aztlan_id,))
        db_result = cursor.fetchone()

        if db_result is None or db_result['payment_proof'] is None:
            return JSONResponse(content={"message": f"No payment proof found for participant {aztlan_id}"}, status_code=404)

        payment_proof_filename = db_result['payment_proof']

        base_url = "https://aztlang-grappling-images.s3.us-east-1.amazonaws.com/"
        payment_proof_url = f"{base_url}{payment_proof_filename}"

        return {"payment_proof_url": payment_proof_url}
    
    except Exception as e:
        logging.error(f"Error: {e}")
        return JSONResponse(content={"error": "Internal Server Error"}, status_code=500)

@app.get("/")
async def hello():
    return "si entre" 