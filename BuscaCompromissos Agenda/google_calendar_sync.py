from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime
import os.path
import pandas as pd
import schedule
import time
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from datetime import timezone

# Escopo da API do Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

class CalendarSyncApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Calendar Sync")
        self.root.geometry("600x400")
        
        # Variáveis
        self.service = None
        self.calendar_ids = [
            'guilherme@brasaosistemas.com.br',
            'rafaelbruning@gmail.com',
            'humbertolocks@gmail.com',
            'czravr@gmail.com'
        ]
        # Período padrão para busca inicial e manual
        self.default_start_date = datetime.datetime(2025, 5, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.default_end_date = datetime.datetime(2025, 5, 31, 23, 59, 59, tzinfo=timezone.utc)
        
        # Interface
        self.create_widgets()
        
        # Tenta autenticar ao iniciar
        self.log_message("Iniciando autenticação...")
        threading.Thread(target=self.authenticate, daemon=True).start()
        
        # Inicia o agendamento em uma thread separada
        threading.Thread(target=self.schedule_task, daemon=True).start()
        
        # Executa a busca inicial após inicialização
        threading.Thread(target=self.initial_process_events, daemon=True).start()
    
    def create_widgets(self):
        # Frame principal
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status do agendamento
        ttk.Label(frame, text="Status do Agendamento:").grid(row=0, column=0, sticky=tk.W)
        self.status_var = tk.StringVar(value="Aguardando...")
        ttk.Label(frame, textvariable=self.status_var).grid(row=0, column=1, sticky=tk.W)
        
        # Botão para forçar autenticação
        ttk.Button(frame, text="Autenticar Manualmente", command=self.authenticate).grid(row=1, column=0, columnspan=2, pady=5)
        
        # Botão para executar busca de eventos
        ttk.Button(frame, text="Buscar Eventos Agora", command=self.run_process_events).grid(row=2, column=0, columnspan=2, pady=5)
        
        # Log de mensagens
        ttk.Label(frame, text="Log de Execução:").grid(row=3, column=0, sticky=tk.W)
        self.log_text = scrolledtext.ScrolledText(frame, width=60, height=15, wrap=tk.WORD)
        self.log_text.grid(row=4, column=0, columnspan=2, pady=5)
        
    def log_message(self, message):
        """Adiciona uma mensagem ao log com timestamp."""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def authenticate(self):
        """Autentica e retorna o serviço do Google Calendar."""
        try:
            creds = None
            token_file = 'token.json'
            credentials_file = 'credentials.json'
            
            if not os.path.exists(credentials_file):
                self.log_message(f"Erro: Arquivo '{credentials_file}' não encontrado.")
                self.log_message("Instruções: Acesse https://console.cloud.google.com/, crie um projeto, habilite a Google Calendar API, crie credenciais OAuth 2.0 (Desktop app), baixe o JSON e renomeie para 'credentials.json'.")
                return
            
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('calendar', 'v3', credentials=creds)
            self.log_message("Autenticação concluída com sucesso.")
        
        except Exception as e:
            self.log_message(f"Erro durante autenticação: {e}")
            if "access_denied" in str(e):
                self.log_message("Acesso negado: Verifique se sua conta está adicionada como testadora no OAuth Consent Screen (https://console.cloud.google.com/apis/credentials/consent).")
    
    def get_week_range(self):
        """Retorna o intervalo da semana atual (segunda a sexta)."""
        today = datetime.datetime.now()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + datetime.timedelta(days=4, hours=23, minutes=59, seconds=59)
        return start_of_week.replace(tzinfo=timezone.utc), end_of_week.replace(tzinfo=timezone.utc)
    
    def get_calendar_events(self, start_date, end_date):
        """Busca eventos de múltiplas agendas, excluindo sábado e domingo."""
        events_by_day = {}
        
        for calendar_id in self.calendar_ids:
            try:
                self.log_message(f"Buscando eventos da agenda {calendar_id}...")
                events_result = self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=start_date.isoformat(),
                    timeMax=end_date.isoformat(),
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                self.log_message(f"Encontrados {len(events)} eventos na agenda {calendar_id}.")
                
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    end = event['end'].get('dateTime', event['end'].get('date'))
                    summary = event.get('summary', 'Sem título')
                    
                    try:
                        start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                        end_dt = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
                    except ValueError as ve:
                        self.log_message(f"Erro ao processar evento '{summary}' na agenda {calendar_id}: Formato de data inválido ({ve}).")
                        continue
                    
                    if start_dt.weekday() >= 5:
                        continue
                    
                    duration = (end_dt - start_dt).total_seconds() / 60
                    
                    day = start_dt.date()
                    if day not in events_by_day:
                        events_by_day[day] = []
                    
                    events_by_day[day].append({
                        'calendar_id': calendar_id,
                        'summary': summary,
                        'start': start_dt,
                        'end': end_dt,
                        'duration_minutes': duration
                    })
            except HttpError as e:
                self.log_message(f"Erro ao acessar a agenda {calendar_id}: {e}")
                if e.resp.status == 400:
                    self.log_message("Possível causa: Formato de data inválido ou configuração incorreta da agenda.")
                elif e.resp.status == 403:
                    self.log_message("Possível causa: Permissões insuficientes para acessar a agenda.")
            except Exception as e:
                self.log_message(f"Erro inesperado ao acessar a agenda {calendar_id}: {e}")
        
        return events_by_day
    
    def events_to_dataframe(self, events_by_day):
        """Converte os eventos organizados por dia em um DataFrame."""
        data = []
        for day, events in events_by_day.items():
            for event in events:
                data.append({
                    'date': day,
                    'calendar_id': event['calendar_id'],
                    'event_name': event['summary'],
                    'start_time': event['start'],
                    'end_time': event['end'],
                    'duration_minutes': event['duration_minutes']
                })
        
        return pd.DataFrame(data)
    
    def process_events(self, start_date=None, end_date=None):
        """Processa os eventos com base no intervalo de datas ou semana atual."""
        try:
            if not self.service:
                self.log_message("Erro: Serviço do Google Calendar não autenticado. Tente autenticar manualmente.")
                return
            
            # Usa as datas fornecidas, se válidas; caso contrário, usa a semana atual
            if start_date is None or end_date is None:
                self.log_message("Nenhuma data fornecida. Usando intervalo da semana atual.")
                start_date, end_date = self.get_week_range()
            else:
                self.log_message(f"Usando período personalizado: {start_date} a {end_date}")
            
            self.log_message(f"Buscando eventos de {start_date} a {end_date}...")
            events_by_day = self.get_calendar_events(start_date, end_date)
            
            df_events = self.events_to_dataframe(events_by_day)
            
            if df_events.empty:
                self.log_message("Nenhum evento encontrado no período especificado.")
                return
            
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'calendar_events_{timestamp}.csv'
            df_events.to_csv(output_file, index=False)
            self.log_message(f"Eventos salvos em '{output_file}'")
            
            total_hours_per_day = df_events.groupby('date')['duration_minutes'].sum() / 60
            self.log_message("\nTotal de horas por dia:")
            self.log_message(str(total_hours_per_day))
            
            try:
                df_atendimentos = pd.read_excel('atendimentos.xlsx')
                self.log_message("Planilha de atendimentos carregada. Implemente a lógica de comparação.")
            except FileNotFoundError:
                self.log_message("Arquivo 'atendimentos.xlsx' não encontrado. Adicione o arquivo e ajuste o caminho.")
        
        except Exception as e:
            self.log_message(f"Erro durante o processamento: {e}")
    
    def initial_process_events(self):
        """Executa a busca inicial com o período personalizado."""
        # Aguarda a autenticação estar completa
        while not self.service:
            time.sleep(1)
        self.process_events(self.default_start_date, self.default_end_date)
    
    def run_process_events(self):
        """Executa process_events em uma thread separada com o período padrão."""
        threading.Thread(target=lambda: self.process_events(self.default_start_date, self.default_end_date), daemon=True).start()
    
    def schedule_task(self):
        """Agenda a execução do script toda sexta-feira às 17:00."""
        schedule.every().friday.at("17:00").do(self.process_events)
        self.status_var.set("Agendado para sexta-feira às 17:00")
        self.log_message("Agendamento configurado para toda sexta-feira às 17:00.")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    root = tk.Tk()
    app = CalendarSyncApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()