# Privacidad de ubicación

Jahamina no inicia la geolocalización al abrir una pantalla. El conductor debe iniciar el viaje, aceptar el permiso del navegador y activar explícitamente **Compartir ubicación**.

Solo el conductor y pasajeros con reserva aceptada pueden consultar la posición. Cancelar una reserva retira ese acceso; finalizar el viaje detiene la publicación y elimina la posición activa de Redis.

PostgreSQL conserva el ciclo de seguimiento y la última posición conocida para representar el estado. Redis contiene la posición activa con expiración. No se almacena cada muestra ni un historial detallado del recorrido, y las coordenadas exactas no deben aparecer en logs normales.

Limitaciones reales:

- no hay seguimiento con la aplicación cerrada o en segundo plano;
- la precisión depende del dispositivo, navegador y permiso;
- una posición antigua se presenta como desactualizada;
- no hay navegación giro a giro ni ETA inventada;
- los servicios geográficos públicos son apropiados para desarrollo, no para producción.
