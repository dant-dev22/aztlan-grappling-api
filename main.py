from fastapi import FastAPI
from mangum import Mangum
from models import ParticipantCreate, ParticipantResponse
from datetime import datetime
from uuid import uuid4
from fastapi.responses import JSONResponse
import mysql.connector


app = FastAPI()
handler = Mangum(app)

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

@app.get("/")
async def hello():
    return "si entre" 