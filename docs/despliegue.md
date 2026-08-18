# Despliegue — proVida en el VPS

VPS Hetzner (Ubuntu 24.04), Nginx corriendo en el host (systemd) como reverse proxy, cada proyecto en su propio contenedor Docker publicando en `127.0.0.1:PUERTO`. Un archivo por subdominio en `/etc/nginx/sites-enabled/`. Certbot gestiona el bloque SSL y el redirect HTTP→HTTPS automáticamente. Puertos ya ocupados por otros proyectos: 8081 (Compra y Listo), 8082 (Faceco), 8083 (Juicios Evaluativos).

## 1. Sitio estático de resultados — `proVida.ibsen-soto.pro` (ya desplegado)

```bash
cd ~/proVida && git pull
docker build -t provida-sitio -f sitio/Dockerfile .
docker run -d --name provida-sitio --restart unless-stopped \
  -p 127.0.0.1:8084:80 \
  provida-sitio
```

Nginx (`/etc/nginx/sites-enabled/proVida.ibsen-soto.pro`, con el bloque SSL ya añadido por Certbot):

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name proVida.ibsen-soto.pro;

    location / {
        proxy_pass http://127.0.0.1:8084;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Certificado: `sudo certbot --nginx -d proVida.ibsen-soto.pro` (ya hecho).

**Actualizar el sitio más adelante** (el build corre las simulaciones desde cero, no hay contenido pre-generado versionado):

```bash
cd ~/proVida && git pull
docker build -t provida-sitio -f sitio/Dockerfile .
docker stop provida-sitio && docker rm provida-sitio
docker run -d --name provida-sitio --restart unless-stopped -p 127.0.0.1:8084:80 provida-sitio
```

## 2. Demo web en vivo — `proVida.ibsen-soto.pro/vivo`

A diferencia del sitio estático, esto necesita un **proceso persistente**: cada visitante mantiene su propia simulación corriendo en el servidor por WebSocket mientras tiene la página abierta. Vive bajo `/vivo` en el mismo dominio (no un subdominio nuevo) para no necesitar otro registro DNS ni otro certificado — ver `webapp/main.py`, que ya define todas sus rutas con ese prefijo.

**Reservas ya hechas para evitar choques:** puerto **8085** (siguiente libre tras el 8084 del sitio estático), y el propio código de `webapp/main.py` ya limita a 20 conexiones WebSocket simultáneas (rechaza el resto con código 1013) — una precaución razonable antes de exponer un proceso que corre indefinidamente por visitante en un VPS compartido con otros proyectos.

```bash
cd ~/proVida && git pull
docker build -t provida-webapp -f webapp/Dockerfile .
docker run -d --name provida-webapp --restart unless-stopped \
  -p 127.0.0.1:8085:80 \
  provida-webapp
```

Verifica que responde antes de tocar Nginx:

```bash
curl -I http://127.0.0.1:8085/vivo/
```

**Añade este bloque `location` dentro del `server` HTTPS existente** de `proVida.ibsen-soto.pro` (el que ya gestiona Certbot) — no crear un archivo nuevo, sino sumarle esta ruta al de arriba:

```nginx
    location /vivo/ {
        proxy_pass http://127.0.0.1:8085;

        # Necesario para WebSocket -- sin esto, Nginx trata la conexión
        # como HTTP normal y el navegador nunca completa el handshake.
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Los WebSocket son conexiones largas -- el timeout por defecto
        # (60s) cortaría la simulación en vivo cada minuto.
        proxy_read_timeout 3600s;
    }
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

**Verificar:**

```bash
curl -I https://proVida.ibsen-soto.pro/vivo/
```

Debe devolver `200 OK`. Para confirmar que el WebSocket también funciona de verdad, ábrelo en el navegador y confirma que la rejilla se mueve sola (no basta con que la página cargue).

**Actualizar más adelante:**

```bash
cd ~/proVida && git pull
docker build -t provida-webapp -f webapp/Dockerfile .
docker stop provida-webapp && docker rm provida-webapp
docker run -d --name provida-webapp --restart unless-stopped -p 127.0.0.1:8085:80 provida-webapp
```
