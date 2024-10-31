from django.utils.timezone import now


def get_tiempo_restante(tarea):
    if tarea.fecha_vencimiento:
        delta = tarea.fecha_vencimiento - now()
        if delta.total_seconds() > 0:
            horas_restantes = delta.total_seconds() // 3600
            return f"{int(horas_restantes)} horas restantes"
        else:
            return "Tarea vencida"
    return "Sin fecha de vencimiento"