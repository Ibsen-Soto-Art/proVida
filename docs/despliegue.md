# Despliegue — proVida en el VPS

Runbook para subir el sitio estático de proVida a `proVida.ibsen-soto.pro`, en el mismo VPS Hetzner (Ubuntu 24.04, Nginx, Docker) donde ya corre Compra y Listo. El DNS tipo A ya apunta al servidor — solo falta la configuración del lado del servidor.

Ajusta los comandos exactos de Nginx/Docker al patrón que ya uses para tus otros proyectos del portafolio (docker-compose vs. contenedores sueltos, Nginx en el host vs. en contenedor) — abajo están las dos variantes más comunes.

## 1. Clonar (o actualizar) el repo en el VPS

```bash
ssh tu_usuario@tu_vps

# primera vez:
git clone git@github.com:Ibsen-Soto-Art/proVida.git
cd proVida

# si ya existe:
cd proVida && git pull
```

## 2. Construir la imagen

```bash
docker build -t provida-sitio -f sitio/Dockerfile .
```

Esto corre las simulaciones de referencia y genera el sitio dentro del build (ver `sitio/generar.py` y `sitio/Dockerfile`) — la imagen final solo contiene Nginx + los archivos estáticos, sin Python. Verificado localmente antes de este runbook: `docker build` + `docker run` + `curl` devolviendo 200 en `/` y en `/img/seleccion.png`.

## 3. Correr el contenedor

**Si usas contenedores sueltos con Nginx en el host** (reverse proxy a `127.0.0.1:PUERTO`):

```bash
# elige un puerto libre en el host, ej. 8091 (verifica que no choque con otros proyectos: `docker ps` / `ss -tlnp`)
docker run -d --name provida-sitio --restart unless-stopped \
  -p 127.0.0.1:8091:80 \
  provida-sitio
```

**Si usas docker-compose con una red compartida** (Nginx en contenedor, sin publicar puertos al host):

```yaml
# docker-compose.yml (o el archivo que ya uses para agrupar tus proyectos)
services:
  provida-sitio:
    build:
      context: ./proVida
      dockerfile: sitio/Dockerfile
    container_name: provida-sitio
    restart: unless-stopped
    networks:
      - tu_red_compartida  # la misma que usa el contenedor de Nginx
```

## 4. Configurar Nginx

**Variante A — Nginx en el host:**

```nginx
# /etc/nginx/sites-available/provida.ibsen-soto.pro
server {
    listen 80;
    server_name proVida.ibsen-soto.pro;

    location / {
        proxy_pass http://127.0.0.1:8091;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/provida.ibsen-soto.pro /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

**Variante B — Nginx en contenedor:** agrega un `server` block equivalente a la configuración que ya usas para enrutar subdominios a contenedores por nombre de servicio (`proxy_pass http://provida-sitio:80;` en vez de `127.0.0.1:PUERTO`), siguiendo el mismo patrón que Compra y Listo.

## 5. HTTPS

```bash
sudo certbot --nginx -d proVida.ibsen-soto.pro
```

(Omite este paso si ya tienes un wildcard cert o un flujo distinto para tus subdominios — usa el que ya tengas configurado.)

## 6. Verificar

```bash
curl -I https://proVida.ibsen-soto.pro
```

Debe devolver `200 OK`. Confírmame cuando esté arriba para dejarlo anotado como cerrado en `docs/aprendizajes.md`.

## Actualizar el sitio más adelante

Como el build corre las simulaciones desde cero (no hay contenido pre-generado versionado), actualizar el sitio con un nuevo experimento o cambio de código es:

```bash
cd proVida && git pull
docker build -t provida-sitio -f sitio/Dockerfile .
docker stop provida-sitio && docker rm provida-sitio
# vuelve a correr el `docker run` del paso 3 (o `docker compose up -d --build` si usas compose)
```
