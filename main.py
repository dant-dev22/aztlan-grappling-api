from fastapi import FastAPI
from mangum import Mangum
from models import ParticipantCreate, ParticipantResponse
from datetime import datetime
from uuid import uuid4
from fastapi.responses import JSONResponse
import mysql.connector
import logging

app = FastAPI()
handler = Mangum(app)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

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

@app.get("/")
async def hello():
    return "si entre" 