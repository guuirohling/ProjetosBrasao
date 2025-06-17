import pandas as pd
from datetime import datetime, timedelta
from utils.normalizacao import normaliza_nome

def descontar_almoco_e_sobreposicao(df, tecnico, dias_uteis, horas_dia):
    tecnico_chave = normaliza_nome(tecnico)
    df = df[df["tecnico_key"] == tecnico_chave].copy()
    if df.empty:
        return pd.DataFrame({
            "date": dias_uteis,
            "calendar_id": tecnico,
            "horas_disponiveis": horas_dia,
            "horas_agendadas": 0.0,
            "tecnico_key": tecnico_chave
        })
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce").dt.tz_localize(None)
    df["end_time"] = pd.to_datetime(df["end_time"], errors="coerce").dt.tz_localize(None)
    results = []
    for dia in dias_uteis:
        dia_base = dia.date()
        agenda_dia = df[df["date"] == dia_base]
        if agenda_dia.empty:
            results.append({"date": dia, "calendar_id": tecnico, "horas_disponiveis": horas_dia, "horas_agendadas": 0.0, "tecnico_key": tecnico_chave})
            continue
        intervals = []
        for _, row in agenda_dia.iterrows():
            inicio = row["start_time"]
            fim = row["end_time"]
            almoco_ini = datetime.combine(inicio.date(), datetime.min.time()) + timedelta(hours=12)
            almoco_fim = almoco_ini + timedelta(hours=1, minutes=30)
            if fim > almoco_ini and inicio < almoco_fim:
                inicio_almoco = max(inicio, almoco_ini)
                fim_almoco = min(fim, almoco_fim)
                if inicio < almoco_ini:
                    intervals.append([inicio, min(fim, almoco_ini)])
                if fim > almoco_fim:
                    intervals.append([max(inicio, almoco_fim), fim])
            else:
                intervals.append([inicio, fim])
        if not intervals:
            soma_horas = 0.0
        else:
            intervals = sorted(intervals, key=lambda x: x[0])
            merged = []
            s, e = intervals[0]
            for start, end in intervals[1:]:
                if start <= e:
                    e = max(e, end)
                else:
                    merged.append([s, e])
                    s, e = start, end
            merged.append([s, e])
            soma_horas = sum([(end - start).total_seconds() / 3600 for start, end in merged])
        results.append({"date": dia, "calendar_id": tecnico, "horas_disponiveis": horas_dia, "horas_agendadas": soma_horas, "tecnico_key": tecnico_chave})
    return pd.DataFrame(results)
