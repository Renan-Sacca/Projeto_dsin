import os
import sys
from sqlalchemy.orm import Session

# Garante que o diretório da app esteja no path
sys.path.append(os.getcwd())

from app.database.connection import SessionLocal, engine
from app.models.user import User, UserType
from app.models.client import Client
from app.models.service import Service
from app.models.appointment import Appointment, AppointmentService, AppointmentStatus
from app.core.security import hash_password
from app.core.config import get_settings

def reset_system():
    settings = get_settings()
    db = SessionLocal()
    print("\n" + "="*50)
    print("🚀 INICIANDO RESET DO SISTEMA (MODO TESTE)")
    print("="*50)
    
    try:
        # 1. Limpar Agendamentos
        print(" -> Removendo agendamentos e histórico...")
        db.query(AppointmentService).delete()
        db.query(Appointment).delete()
        
        # 2. Limpar Clientes
        print(" -> Removendo todos os registros de clientes...")
        db.query(Client).delete()
        
        # 3. Limpar Usuários (Exceto o Super Admin)
        print(f" -> Removendo usuários (exceto {settings.ADMIN_EMAIL})...")
        db.query(User).filter(User.email != settings.ADMIN_EMAIL).delete()
        
        # 4. Resetar o Super Admin
        admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if admin:
            print(" -> Resetando credenciais e tokens do Administrador Principal...")
            admin.google_id = None
            admin.google_access_token = None
            admin.google_refresh_token = None
            admin.google_token_expiry = None
            admin.senha_hash = hash_password(settings.ADMIN_PASSWORD)
            admin.tipo = UserType.ADMIN
        else:
            print(" -> Recriando Administrador Principal...")
            admin = User(
                nome=settings.ADMIN_NAME,
                email=settings.ADMIN_EMAIL,
                senha_hash=hash_password(settings.ADMIN_PASSWORD),
                tipo=UserType.ADMIN,
                ativo=True
            )
            db.add(admin)

        db.commit()

        # 5. Gerar 15 Clientes Aleatórios
        print("\n -> Gerando 15 clientes aleatórios para teste...")
        import random
        from datetime import datetime, timedelta
        
        nomes = ["Ana", "Bruno", "Carla", "Diego", "Elena", "Fabio", "Gisele", "Hugo", "Isabela", "João", "Kelly", "Lucas", "Marina", "Natan", "Olivia", "Paulo", "Rafaela", "Samuel", "Tatiana", "Vitor"]
        sobrenomes = ["Silva", "Santos", "Oliveira", "Souza", "Pereira", "Costa", "Ferreira", "Rodrigues", "Almeida", "Nascimento", "Moreira", "Carvalho", "Lopes", "Barbosa", "Mendes"]
        
        services = db.query(Service).all()
        
        for i in range(15):
            nome_completo = f"{random.choice(nomes)} {random.choice(sobrenomes)} {i+1}"
            email = f"cliente{i+1}@teste.com"
            
            # Cria Usuário
            user = User(
                nome=nome_completo,
                email=email,
                senha_hash=hash_password("cliente123"),
                tipo=UserType.CLIENT,
                ativo=True
            )
            db.add(user)
            db.flush()
            
            # Cria Cliente
            client = Client(
                user_id=user.id,
                telefone=f"149{random.randint(10000000, 99999999)}"
            )
            db.add(client)
            db.flush()

        # 6. Gerar 2 Agendamentos por cliente (evitando conflitos de duração)
        if services:
            print(" -> Gerando 30 agendamentos sem sobreposições...")
            occupied_intervals = [] # Lista de tuplas (start, end)
            all_clients = db.query(Client).all()
            
            for client in all_clients:
                for _ in range(2):
                    attempts = 0
                    while attempts < 30:
                        days_ahead = random.randint(0, 7)
                        hour = random.randint(8, 17)
                        minute = random.choice([0, 15, 30, 45])
                        
                        dt_start = datetime.now() + timedelta(days=days_ahead)
                        dt_start = dt_start.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        
                        # Escolhe 1 ou 2 serviços primeiro para saber a duração
                        num_serv = random.randint(1, min(2, len(services)))
                        chosen_services = random.sample(services, k=num_serv)
                        total_duration = sum([s.duracao_minutos for s in chosen_services])
                        dt_end = dt_start + timedelta(minutes=total_duration)
                        
                        # Verifica sobreposição
                        conflict = False
                        for start, end in occupied_intervals:
                            if (dt_start < end) and (dt_end > start):
                                conflict = True
                                break
                        
                        if not conflict:
                            occupied_intervals.append((dt_start, dt_end))
                            
                            status = random.choice([AppointmentStatus.PENDING, AppointmentStatus.APPROVED])
                            
                            appt = Appointment(
                                client_id=client.id,
                                data_hora=dt_start,
                                status=status,
                                criado_por=admin.id
                            )
                            db.add(appt)
                            db.flush()
                            
                            for s in chosen_services:
                                link = AppointmentService(appointment_id=appt.id, service_id=s.id)
                                db.add(link)
                            break
                        
                        attempts += 1

        db.commit()
        print("\n" + "="*50)
        print("✅ SISTEMA RESETADO E POVOADO COM SUCESSO!")
        print("Senha padrão para os novos clientes: cliente123")
        print("Agendamentos de teste criados para os próximos 7 dias.")
        print("Serviços PRESERVADOS.")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE O RESET: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_system()
